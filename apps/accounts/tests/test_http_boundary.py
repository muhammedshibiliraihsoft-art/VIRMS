import json
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User


class HTTPBoundaryTests(TestCase):
    def test_request_id_validated_and_returned(self):
        client = Client()
        response = client.get(reverse("health-live"), HTTP_X_REQUEST_ID="bad-id")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response["X-Request-ID"], "bad-id")
        response = client.get(
            reverse("health-live"),
            HTTP_X_REQUEST_ID="3d50a316-a139-49f5-90ca-bc43f28e721e",
        )
        self.assertEqual(
            response["X-Request-ID"], "3d50a316-a139-49f5-90ca-bc43f28e721e"
        )

    def test_unknown_api_route_has_safe_request_id_error(self):
        response = self.client.get("/api/v1/auth/not-a-route/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "http_404")
        self.assertEqual(response.json()["request_id"], response["X-Request-ID"])
        self.assertNotIn("traceback", response.content.decode().lower())

    def test_liveness_and_readiness(self):
        self.assertEqual(
            self.client.get(reverse("health-live")).json(), {"status": "live"}
        )
        ready = self.client.get(reverse("health-ready"))
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json(), {"status": "ready"})

    def test_readiness_rejects_pending_migrations(self):
        from unittest.mock import MagicMock

        executor = MagicMock()
        executor.loader.graph.leaf_nodes.return_value = [("accounts", "0009_pending")]
        executor.migration_plan.return_value = [(object(), False)]
        with patch(
            "django.db.migrations.executor.MigrationExecutor",
            return_value=executor,
        ):
            response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unready"})

    def test_api_400_401_403_404_and_405_errors_have_code_and_request_id(self):
        bad_request = self.client.post(
            reverse("auth-login"), data="{", content_type="application/json"
        )
        unauthorized = self.client.get(reverse("auth-me"))
        strict = Client(enforce_csrf_checks=True)
        forbidden = strict.post(
            reverse("auth-login"), data="{}", content_type="application/json"
        )
        missing = self.client.get("/api/v1/auth/not-a-route/")
        wrong_method = self.client.get(reverse("auth-login"))

        for response, status in [
            (bad_request, 400),
            (unauthorized, 401),
            (forbidden, 403),
            (missing, 404),
            (wrong_method, 405),
        ]:
            with self.subTest(status=status):
                self.assertEqual(response.status_code, status)
                payload = response.json()
                self.assertEqual(payload["code"], f"http_{status}")
                self.assertEqual(payload["request_id"], response["X-Request-ID"])

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=1,
    )
    def test_api_429_preserves_retry_after_and_no_store(self):
        User.objects.create_user(
            login_id="rate-limited",
            email="rate-limited@example.invalid",
            password="A-long-private-rate-limit-test-passphrase-123!",
        )
        body = json.dumps({"login_id": "rate-limited", "password": "wrong"})
        self.client.post(reverse("auth-login"), body, content_type="application/json")

        response = self.client.post(
            reverse("auth-login"), body, content_type="application/json"
        )

        self.assertEqual(response.status_code, 429)
        self.assertTrue(response["Retry-After"].isdigit())
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response.json()["code"], "http_429")
        self.assertEqual(response.json()["request_id"], response["X-Request-ID"])
        self.assertNotIn("wrong", response.content.decode())

    def test_409_500_and_503_are_safe_and_correlated(self):
        from django.test import RequestFactory

        from core.http import api_error, handler500

        request = RequestFactory().get("/api/v1/test/conflict/")
        request.request_id = "3d50a316-a139-49f5-90ca-bc43f28e721e"
        conflict = api_error(request, 409, "Conflict", "http_409")
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(
            json.loads(conflict.content)["request_id"], conflict["X-Request-ID"]
        )

        request.path = "/api/v1/test/failure/"
        failed = handler500(request)
        self.assertEqual(failed.status_code, 500)
        self.assertEqual(json.loads(failed.content)["detail"], "Request failed")
        self.assertNotIn("traceback", failed.content.decode().lower())

        with patch(
            "core.health.connection.cursor", side_effect=RuntimeError("sentinel-secret")
        ):
            unready = self.client.get(reverse("health-ready"))
        self.assertEqual(unready.status_code, 503)
        self.assertEqual(unready.json(), {"status": "unready"})
        self.assertNotIn("sentinel-secret", unready.content.decode())

    def test_api_error_does_not_echo_password_sentinel(self):
        sentinel = "private-password-sentinel-DO-NOT-ECHO"
        response = self.client.post(
            reverse("auth-login"),
            json.dumps({"login_id": "missing-user", "password": sentinel}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(sentinel, response.content.decode())
