from django.test import SimpleTestCase


class CredentialResponseCacheTests(SimpleTestCase):
    def test_credential_routes_do_not_cache_unauthenticated_responses(self):
        paths = [
            "/api/v1/auth/accounts/provision/",
            "/api/v1/auth/accounts/00000000-0000-0000-0000-000000000001/reset/",
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.post(path, {}, content_type="application/json")
                self.assertEqual(response.status_code, 401)
                self.assertIn("no-store", response.get("Cache-Control", ""))
