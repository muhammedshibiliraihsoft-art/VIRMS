import json
import os
import subprocess
import sys
import threading
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.login_admission import _key, clear_identifier_budget
from apps.accounts.models import (
    AccountSecurityEvent,
    CompanyRoleGrant,
    LoginAttempt,
    RoleAssignment,
    User,
)
from apps.accounts.policy import require_action
from apps.accounts.tests.test_users import make_user
from apps.tenants.commands import end_membership, end_scope_row, grant_role
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership
from apps.tenants.selectors import visible_branches, visible_companies


def api_login(client, login_id, password, ip="198.51.100.41"):
    client.get("/api/v1/auth/csrf/")
    return client.post(
        "/api/v1/auth/login/",
        json.dumps({"login_id": login_id, "password": password}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        REMOTE_ADDR=ip,
    )


def admin_login(login_id, password, ip="198.51.100.41"):
    client = Client(enforce_csrf_checks=True)
    client.get("/admin/login/")
    return client.post(
        "/admin/login/",
        {"username": login_id, "password": password},
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        REMOTE_ADDR=ip,
    )


class PlatformCompanyRoleGrantGuardTests(TestCase):
    def test_backoffice_cannot_grant_company_role_to_platform_membership(self):
        platform = User.objects.create_superuser(
            login_id="platform-role-guard",
            email="platform-role-guard@example.invalid",
            password="Synthetic private role guard test password 2026!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        company = Tenant.objects.create(name="Guarded", slug="guarded")
        membership = TenantMembership.objects.create(
            user=platform,
            tenant=company,
            assigned_by=platform,
        )

        with self.assertRaisesRegex(
            ValidationError, "Company role grants require a Company account"
        ):
            grant_role(actor=platform, membership=membership, role="accountant")

        self.assertFalse(
            CompanyRoleGrant.objects.filter(membership=membership).exists()
        )
        self.assertEqual(
            RoleAssignment.objects.filter(user=platform)
            .values_list("role", flat=True)
            .get(),
            RoleAssignment.Role.BACK_OFFICE,
        )


class ProductionMiddlewareOrderingTests(TestCase):
    def test_security_middleware_wraps_whitenoise_in_nonlocal_settings(self):
        environment = os.environ.copy()
        environment.update(
            {
                "DJANGO_ENV": "staging",
                "DJANGO_SECRET_KEY": "synthetic-phase1-settings-test-secret-value-only-1234567890",
                "DJANGO_ALLOWED_HOSTS": "testserver",
                "DB_NAME": "synthetic",
                "DB_USER": "synthetic",
                "DB_PASSWORD": "synthetic",
                "DB_HOST": "127.0.0.1",
                "OBJECT_STORAGE_ENDPOINT": "http://127.0.0.1:9",
                "OBJECT_STORAGE_BUCKET": "synthetic",
                "OBJECT_STORAGE_ACCESS_KEY": "synthetic",
                "OBJECT_STORAGE_SECRET_KEY": "synthetic",
            }
        )
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json; from core.settings import MIDDLEWARE; "
                "print(json.dumps(MIDDLEWARE))",
            ],
            cwd=Path(__file__).resolve().parents[3],
            env=environment,
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        middleware = json.loads(result.stdout)
        self.assertLess(
            middleware.index("django.middleware.security.SecurityMiddleware"),
            middleware.index("whitenoise.middleware.WhiteNoiseMiddleware"),
        )


@override_settings(
    VIRMS_LOGIN_IDENTIFIER_LIMIT=2,
    VIRMS_LOGIN_GLOBAL_LIMIT=1000,
    VIRMS_LOGIN_SOURCE_LIMIT=1000,
)
class LoginAdmissionRegressionTests(TestCase):
    password = "Synthetic correct login credential 2026!"

    def setUp(self):
        self.platform_user = User.objects.create_superuser(
            login_id="admission-platform",
            email="admission-platform@example.invalid",
            password=self.password,
        )

    def counter(self, kind, value):
        return LoginAttempt.objects.get(key=_key(kind, value)).failures

    def test_repeated_successful_api_logins_do_not_consume_identifier_failures(self):
        for index in range(4):
            client = Client(enforce_csrf_checks=True)
            response = api_login(
                client,
                self.platform_user.login_id,
                self.password,
                ip=f"198.51.100.{40 + index}",
            )
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)

    def test_wrong_then_correct_then_correct_resets_only_that_identifier(self):
        client = Client(enforce_csrf_checks=True)
        other_id = "unrelated-unknown-login"

        self.assertEqual(api_login(client, other_id, "wrong").status_code, 401)
        self.assertEqual(
            api_login(client, self.platform_user.login_id, "wrong").status_code, 401
        )
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 1)
        self.assertEqual(self.counter("identifier", other_id), 1)

        self.assertEqual(
            api_login(client, self.platform_user.login_id, self.password).status_code,
            200,
        )
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)
        self.assertEqual(self.counter("identifier", other_id), 1)
        self.assertEqual(
            api_login(client, self.platform_user.login_id, self.password).status_code,
            200,
        )
        self.assertEqual(self.counter("identifier", other_id), 1)

        source_failures = self.counter("source", "198.51.100.41")
        global_failures = self.counter("global", "all")
        clear_identifier_budget(self.platform_user.login_id)
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)
        self.assertEqual(self.counter("identifier", other_id), 1)
        self.assertEqual(self.counter("source", "198.51.100.41"), source_failures)
        self.assertEqual(self.counter("global", "all"), global_failures)

    def test_successful_django_admin_logins_do_not_consume_identifier_failures(self):
        for _ in range(4):
            response = admin_login(self.platform_user.login_id, self.password)
            self.assertEqual(response.status_code, 302)
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)

    def test_valid_nonstaff_admin_denial_is_not_recorded_as_bad_credentials(self):
        company_user = make_user("company-login", role="accountant")
        company_password = "A-Long-Private-Test-Passphrase-123!"

        response = admin_login(company_user.login_id, company_password)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.counter("identifier", company_user.login_id), 0)
        self.assertEqual(
            api_login(
                Client(enforce_csrf_checks=True),
                company_user.login_id,
                company_password,
            ).status_code,
            200,
        )
        self.assertEqual(self.counter("identifier", company_user.login_id), 0)

    def test_wrong_password_increments_identifier_budget(self):
        response = api_login(
            Client(enforce_csrf_checks=True), self.platform_user.login_id, "wrong"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 1)

    def test_pruning_removes_bounded_expired_rows_but_keeps_live_identifier_state(self):
        old = timezone.now() - timedelta(days=1)
        LoginAttempt.objects.bulk_create(
            [
                LoginAttempt(key=f"{index:064x}", retry_after=old, failures=1)
                for index in range(510)
            ]
        )
        LoginAttempt.objects.all().update(updated_at=old)

        call_command("prune_login_attempts", batch_size=500)

        self.assertEqual(LoginAttempt.objects.count(), 10)
        response = api_login(
            Client(enforce_csrf_checks=True), self.platform_user.login_id, "wrong"
        )
        self.assertEqual(response.status_code, 401)
        live_key = _key("identifier", self.platform_user.login_id)
        call_command("prune_login_attempts", batch_size=500)
        self.assertTrue(LoginAttempt.objects.filter(key=live_key, failures=1).exists())

    @override_settings(VIRMS_LOGIN_IDENTIFIER_LIMIT=100, VIRMS_LOGIN_SOURCE_LIMIT=2)
    def test_correct_credentials_can_hit_intended_source_admission_budget(self):
        statuses = [
            api_login(
                Client(enforce_csrf_checks=True),
                self.platform_user.login_id,
                self.password,
                ip="198.51.100.55",
            ).status_code
            for _ in range(3)
        ]

        self.assertEqual(statuses, [200, 200, 429])
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)
        self.assertEqual(self.counter("source", "198.51.100.55"), 2)
        self.assertEqual(self.counter("global", "all"), 2)

    @override_settings(VIRMS_LOGIN_IDENTIFIER_LIMIT=100, VIRMS_LOGIN_GLOBAL_LIMIT=2)
    def test_correct_credentials_can_hit_intended_global_admission_budget(self):
        LoginAttempt.objects.all().delete()
        statuses = [
            api_login(
                Client(enforce_csrf_checks=True),
                self.platform_user.login_id,
                self.password,
                ip=f"198.51.100.{60 + index}",
            ).status_code
            for index in range(3)
        ]

        self.assertEqual(statuses, [200, 200, 429])
        self.assertEqual(self.counter("identifier", self.platform_user.login_id), 0)
        self.assertEqual(self.counter("global", "all"), 2)


class LifecycleEndNowRegressionTests(TestCase):
    def test_membership_role_and_assignment_end_now_and_audit_once(self):
        company = Tenant.objects.create(name="End Now", slug="end-now")
        operator = make_user(
            "end-now-operator",
            role="back_office",
            tenant=company,
            account_kind="platform",
        )

        for kind in ("membership", "role", "assignment"):
            user = make_user(f"end-now-{kind}", role="accountant", tenant=company)
            membership = user.tenant_memberships.get()
            branch = Branch.objects.create(tenant=company, name=kind)
            assignment = BranchAssignment.objects.create(
                membership=membership, branch=branch, assigned_by=operator
            )
            row = (
                membership
                if kind == "membership"
                else (membership.role_grants.get() if kind == "role" else assignment)
            )
            row.effective_until = timezone.now() + timedelta(days=1)
            row.save(update_fields=["effective_until", "updated_at"])

            self.assertTrue(
                visible_branches(user, company.pk).filter(pk=branch.pk).exists()
            )
            action = {
                "membership": "membership.end",
                "role": "role.end",
                "assignment": "assignment.end",
            }[kind]
            if kind == "membership":
                end_membership(actor=operator, membership=row)
            else:
                end_scope_row(actor=operator, row=row)

            row.refresh_from_db()
            self.assertLessEqual(row.effective_until, timezone.now())
            self.assertFalse(
                visible_branches(user, company.pk).filter(pk=branch.pk).exists()
            )
            with self.assertRaises(PermissionDenied):
                require_action(user, "core.branch.read", company=company, branch=branch)
            if kind != "assignment":
                self.assertFalse(visible_companies(user).filter(pk=company.pk).exists())
            event = AccountSecurityEvent.objects.get(subject=user, action=action)
            if kind == "assignment":
                self.assertEqual(event.branch_id, branch.pk)

            if kind == "membership":
                end_membership(actor=operator, membership=row)
            else:
                end_scope_row(actor=operator, row=row)
            self.assertEqual(
                AccountSecurityEvent.objects.filter(
                    subject=user, action=action
                ).count(),
                1,
            )

    def test_already_expired_intervals_are_noop_without_duplicate_audit(self):
        company = Tenant.objects.create(name="Already Ended", slug="already-ended")
        operator = make_user(
            "already-ended-operator",
            role="back_office",
            tenant=company,
            account_kind="platform",
        )
        now = timezone.now()

        for kind in ("membership", "role", "assignment"):
            user = make_user(f"already-ended-{kind}")
            membership = user.tenant_memberships.create(
                tenant=company,
                assigned_by=operator,
                effective_from=now - timedelta(days=3),
                effective_until=now - timedelta(days=1),
            )
            branch = Branch.objects.create(tenant=company, name=f"expired-{kind}")
            grant = membership.role_grants.create(
                membership=membership,
                role="accountant",
                assigned_by=operator,
                effective_from=now - timedelta(days=3),
                effective_until=now - timedelta(days=1),
            )
            assignment = BranchAssignment.objects.create(
                membership=membership,
                branch=branch,
                assigned_by=operator,
                effective_from=now - timedelta(days=3),
                effective_until=now - timedelta(days=1),
            )
            row = {
                "membership": membership,
                "role": grant,
                "assignment": assignment,
            }[kind]
            original = row.effective_until

            if kind == "membership":
                end_membership(actor=operator, membership=row)
            else:
                end_scope_row(actor=operator, row=row)

            row.refresh_from_db()
            self.assertEqual(row.effective_until, original)
            self.assertFalse(
                AccountSecurityEvent.objects.filter(
                    subject=user,
                    action__in=["membership.end", "role.end", "assignment.end"],
                ).exists()
            )

    def test_admin_finite_interval_actions_use_shared_end_now_commands(self):
        company = Tenant.objects.create(name="Admin End", slug="admin-end")
        actor = make_user(
            "admin-end-operator",
            role="back_office",
            tenant=company,
            account_kind="platform",
        )
        actor.is_staff = actor.is_superuser = True
        actor.save(update_fields=["is_staff", "is_superuser", "updated_at"])
        self.client.force_login(actor)
        now = timezone.now()

        for kind, path, action, event_action in (
            (
                "membership",
                "tenants/tenantmembership",
                "end_selected_memberships",
                "membership.end",
            ),
            ("role", "accounts/companyrolegrant", "end_selected_grants", "role.end"),
            (
                "assignment",
                "tenants/branchassignment",
                "end_selected_assignments",
                "assignment.end",
            ),
        ):
            user = make_user(f"admin-ended-{kind}", tenant=company)
            membership = user.tenant_memberships.get()
            membership.effective_until = now + timedelta(days=1)
            membership.save(update_fields=["effective_until", "updated_at"])
            branch = Branch.objects.create(tenant=company, name=f"admin-{kind}")
            assignment = BranchAssignment.objects.create(
                membership=membership,
                branch=branch,
                assigned_by=actor,
                effective_from=now - timedelta(days=1),
                effective_until=now + timedelta(days=1),
            )
            grant = membership.role_grants.create(
                membership=membership,
                branch=branch if kind == "role" else None,
                role="accountant",
                assigned_by=actor,
                effective_from=now - timedelta(days=1),
                effective_until=now + timedelta(days=1),
            )
            row = {
                "membership": membership,
                "role": grant,
                "assignment": assignment,
            }[kind]

            for _ in range(2):
                response = self.client.post(
                    f"/admin/{path}/",
                    {"action": action, "_selected_action": [str(row.pk)]},
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)

            row.refresh_from_db()
            self.assertLessEqual(row.effective_until, timezone.now())
            self.assertFalse(visible_branches(user, company.pk).exists())
            self.assertEqual(
                AccountSecurityEvent.objects.filter(
                    subject=user, action=event_action
                ).count(),
                1,
            )
            event = AccountSecurityEvent.objects.get(subject=user, action=event_action)
            self.assertEqual(event.actor_id, actor.pk)
            self.assertEqual(event.company_id, company.pk)
            self.assertEqual(
                event.branch_id,
                branch.pk if kind in {"role", "assignment"} else None,
            )


class CompanyContextBranchBoundTests(TestCase):
    def test_auth_me_bound_ordering_truncation_and_full_page_authority(self):
        company = Tenant.objects.create(name="Bounded", slug="bounded")
        user = make_user("bounded-context", role="accountant", tenant=company)
        membership = user.tenant_memberships.get()
        self.client.force_login(user)

        created = 0
        bounded_bytes = None
        query_count = None
        for size in (1, 25, 75, 250):
            branches = Branch.objects.bulk_create(
                [
                    Branch(tenant=company, name=f"B{index:04}")
                    for index in range(created, size)
                ]
            )
            BranchAssignment.objects.bulk_create(
                [
                    BranchAssignment(
                        membership=membership, branch=branch, assigned_by=user
                    )
                    for branch in branches
                ]
            )
            created = size

            with CaptureQueriesContext(connection) as queries:
                response = self.client.get("/api/v1/auth/me/")
            if query_count is None:
                query_count = len(queries)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(queries), query_count)
            result = response.json()["companies"][0]
            if size == 25:
                bounded_bytes = len(response.content)
            if size > 25:
                self.assertEqual(len(response.content), bounded_bytes)
            self.assertEqual(len(result["branches"]), min(size, 20))
            self.assertEqual(result["branches_truncated"], size > 20)
            self.assertEqual(
                result["branches"],
                self.client.get("/api/v1/auth/me/").json()["companies"][0]["branches"],
            )

        page = self.client.get(f"/api/v1/tenants/{company.pk}/branches/").json()
        last_page = self.client.get(
            f"/api/v1/tenants/{company.pk}/branches/?page=13"
        ).json()
        self.assertEqual(page["count"], 250)
        self.assertLessEqual(len(page["results"]), 20)
        self.assertEqual(len(last_page["results"]), 10)
        self.assertEqual(last_page["results"][-1]["name"], "B0249")
        self.assertTrue(
            visible_branches(user, company.pk).filter(name="B0249").exists()
        )
        target = Branch.objects.get(tenant=company, name="B0249")
        self.assertEqual(
            require_action(user, "core.branch.read", company=company, branch=target).pk,
            user.pk,
        )


class LoginAttemptCleanupConcurrencyTests(TransactionTestCase):
    def test_pruner_skips_identifier_state_locked_by_concurrent_refresh(self):
        from django.db import close_old_connections

        from apps.accounts.login_admission import prune_expired_attempts

        old = timezone.now() - timedelta(days=1)
        row = LoginAttempt.objects.create(
            key=_key("identifier", "refresh-race"), failures=1, retry_after=old
        )
        LoginAttempt.objects.filter(pk=row.pk).update(updated_at=old)
        locked = threading.Event()
        release = threading.Event()
        errors = []

        def refresh():
            close_old_connections()
            try:
                with transaction.atomic():
                    current = LoginAttempt.objects.select_for_update().get(pk=row.pk)
                    locked.set()
                    if not release.wait(10):
                        raise RuntimeError("release timeout")
                    current.retry_after = timezone.now() + timedelta(minutes=10)
                    current.save(update_fields=["retry_after", "updated_at"])
            except Exception as error:
                errors.append(str(error))
                locked.set()
            finally:
                close_old_connections()

        thread = threading.Thread(target=refresh)
        thread.start()
        try:
            self.assertTrue(locked.wait(10))
            self.assertEqual(prune_expired_attempts(), 0)
        finally:
            release.set()
            thread.join(15)

        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(prune_expired_attempts(), 0)
        self.assertTrue(LoginAttempt.objects.filter(pk=row.pk, failures=1).exists())
