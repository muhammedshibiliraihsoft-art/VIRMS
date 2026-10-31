import multiprocessing
import uuid
from datetime import timedelta

from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from apps.accounts.login_admission import _key, admit_login, clear_identifier_budget
from apps.accounts.models import LoginAttempt, User


def _request(remote_addr="198.51.100.10"):
    request = RequestFactory().post("/api/v1/auth/login/")
    request.META["REMOTE_ADDR"] = remote_addr
    return request


class LoginAdmissionPolicyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            login_id="known-account",
            email="known-account@example.invalid",
        )

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=1,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=100,
    )
    def test_source_budget_is_shared_across_identifiers(self):
        self.assertEqual(admit_login(_request(), "missing-one")[0], True)
        admitted, retry_after = admit_login(_request(), "missing-two")
        self.assertFalse(admitted)
        self.assertGreater(retry_after, 0)

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=2,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=100,
    )
    def test_global_budget_is_shared_across_source_addresses(self):
        self.assertTrue(admit_login(_request("198.51.100.1"), "missing-one")[0])
        self.assertTrue(admit_login(_request("198.51.100.2"), "missing-two")[0])
        admitted, retry_after = admit_login(_request("198.51.100.3"), "missing-three")
        self.assertFalse(admitted)
        self.assertGreater(retry_after, 0)

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=1,
        VIRMS_LOGIN_IDENTIFIER_WINDOW_SECONDS=10,
    )
    def test_identifier_window_reopens_after_expiry(self):
        request = _request()
        self.assertTrue(admit_login(request, self.user.login_id)[0])
        self.assertFalse(admit_login(request, self.user.login_id)[0])
        row = LoginAttempt.objects.get(key=_key("identifier", self.user.login_id))
        expired = timezone.now() - timedelta(seconds=11)
        LoginAttempt.objects.filter(pk=row.pk).update(
            updated_at=expired,
            retry_after=expired,
        )

        self.assertTrue(admit_login(request, self.user.login_id)[0])

    def test_success_clears_only_identifier_budget(self):
        request = _request()
        self.assertTrue(admit_login(request, self.user.login_id)[0])
        clear_identifier_budget(self.user.login_id)

        self.assertFalse(
            LoginAttempt.objects.filter(
                key=_key("identifier", self.user.login_id)
            ).exists()
        )
        self.assertTrue(LoginAttempt.objects.filter(key=_key("global", "all")).exists())
        self.assertTrue(
            LoginAttempt.objects.filter(key=_key("source", "198.51.100.10")).exists()
        )

    def test_login_body_size_rejects_missing_invalid_and_oversized_lengths(self):
        from apps.accounts.auth_views import login_content_length_is_bounded

        request = _request()
        for raw in (None, "", "not-a-number", "-1", "8193"):
            request.META.pop("CONTENT_LENGTH", None)
            if raw is not None:
                request.META["CONTENT_LENGTH"] = raw
            self.assertFalse(login_content_length_is_bounded(request))
        request.META["CONTENT_LENGTH"] = "8192"
        self.assertTrue(login_content_length_is_bounded(request))

    def test_login_attempt_cleanup_deletes_one_bounded_batch(self):
        expired_at = timezone.now() - timedelta(minutes=10)
        LoginAttempt.objects.bulk_create(
            [
                LoginAttempt(
                    key=uuid.uuid4().hex * 2,
                    failures=1,
                    retry_after=expired_at,
                )
                for _ in range(1001)
            ]
        )

        call_command("prune_login_attempts", batch_size=500)

        self.assertEqual(LoginAttempt.objects.count(), 501)


class LoginAdmissionMultiprocessTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create(
            login_id="parallel-account",
            email="parallel-account@example.invalid",
        )

    def test_concurrent_processes_share_atomic_identifier_budget(self):
        from apps.accounts.testing_helpers import admit_login_in_process

        context = multiprocessing.get_context("spawn")
        worker_count = 8
        barrier = context.Barrier(worker_count)
        result_queue = context.Queue()
        database_name = connection.settings_dict["NAME"]
        processes = [
            context.Process(
                target=admit_login_in_process,
                args=(
                    self.user.login_id,
                    "198.51.100.55",
                    database_name,
                    barrier,
                    result_queue,
                ),
            )
            for _ in range(worker_count)
        ]

        for process in processes:
            process.start()
        try:
            results = [result_queue.get(timeout=45) for _ in processes]
        finally:
            for process in processes:
                process.join(timeout=45)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)

        self.assertTrue(all(process.exitcode == 0 for process in processes))
        self.assertEqual(sum(1 for admitted, _ in results if admitted), 3)
        bucket = LoginAttempt.objects.get(key=_key("identifier", self.user.login_id))
        self.assertEqual(bucket.failures, 3)

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=1,
    )
    def test_lowercase_equivalent_ids_share_budget_but_casefold_only_ids_do_not(self):
        sharp_s = User.objects.create_user(
            login_id="ß", email="sharp-s@example.invalid"
        )
        double_s = User.objects.create_user(
            login_id="SS", email="double-s@example.invalid"
        )
        self.assertEqual(sharp_s.login_id, "ß")
        self.assertEqual(double_s.login_id, "ss")
        request = _request()
        self.assertTrue(admit_login(request, "ß")[0])
        self.assertFalse(admit_login(request, "ß")[0])
        self.assertTrue(admit_login(request, "SS")[0])
