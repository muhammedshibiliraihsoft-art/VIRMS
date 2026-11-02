import json
from datetime import timedelta

from django.core.management import call_command
from django.db import connection, transaction
from django.test import (
    Client,
    RequestFactory,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.utils import timezone

from apps.accounts.login_admission import _key, login_attempt
from apps.accounts.models import (
    AccountSecurityEvent,
    CompanyRoleGrant,
    LoginAttempt,
    User,
)
from apps.accounts.tests.test_users import make_user
from apps.tenants.commands import end_membership, end_scope_row
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership
from apps.tenants.selectors import visible_branches, visible_companies


@override_settings(
    VIRMS_LOGIN_IDENTIFIER_LIMIT=2,
    VIRMS_LOGIN_GLOBAL_LIMIT=1000,
    VIRMS_LOGIN_SOURCE_LIMIT=1000,
)
class FinalLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            login_id="good-login",
            email="good@example.invalid",
            password="Synthetic correct login credential 2026!",
        )

    def _login(self, client, admin=False, correct=True, ip="198.51.100.1"):
        client.get("/admin/login/" if admin else "/api/v1/auth/csrf/")
        data = {
            "username" if admin else "login_id": self.user.login_id,
            "password": (
                "Synthetic correct login credential 2026!" if correct else "wrong"
            ),
        }
        kw = {"HTTP_X_CSRFTOKEN": client.cookies["csrftoken"].value, "REMOTE_ADDR": ip}
        if admin:
            return client.post("/admin/login/", data, **kw)
        return client.post(
            "/api/v1/auth/login/",
            json.dumps(data),
            content_type="application/json",
            **kw,
        )

    def test_correct_and_wrong_correct_sequences_api_admin_devices(self):
        for admin in (False, True):
            for devices in (False, True):
                for wrong_first in (False, True):
                    LoginAttempt.objects.all().delete()
                    client = Client(enforce_csrf_checks=True)
                    if wrong_first:
                        self._login(client, admin, False)
                    for i in range(4):
                        if devices:
                            client = Client(enforce_csrf_checks=True)
                        response = self._login(
                            client, admin, True, "198.51.100." + str(i + 1)
                        )
                        self.assertEqual(response.status_code, 302 if admin else 200)
                    self.assertEqual(
                        LoginAttempt.objects.get(
                            key=_key("identifier", self.user.login_id)
                        ).failures,
                        0,
                    )
                    self.assertGreater(
                        LoginAttempt.objects.get(key=_key("global", "all")).failures, 0
                    )

    @override_settings(VIRMS_LOGIN_GLOBAL_LIMIT=2)
    def test_rotating_input_cannot_create_state_after_global_limit(self):
        for i in range(2):
            request = RequestFactory().post("/", REMOTE_ADDR=f"198.51.100.{i + 1}")
            with login_attempt(request, f"missing-{i}") as outcome:
                self.assertTrue(outcome.allowed)
                outcome.authenticated = False
        before = LoginAttempt.objects.count()
        self.assertEqual(before, 5)
        for i in range(3, 30):
            request = RequestFactory().post("/", REMOTE_ADDR=f"198.51.100.{i}")
            with login_attempt(request, f"missing-{i}") as outcome:
                self.assertFalse(outcome.allowed)
        self.assertEqual(LoginAttempt.objects.count(), before)

    def test_incomplete_admin_form_cannot_clear_identifier_failures(self):
        client = Client(enforce_csrf_checks=True)
        self._login(client, admin=True, correct=False)
        key = _key("identifier", self.user.login_id)
        self.assertEqual(LoginAttempt.objects.get(key=key).failures, 1)
        for data in (
            {"username": self.user.login_id},
            {"username": self.user.login_id, "password": ""},
        ):
            client.get("/admin/login/")
            response = client.post(
                "/admin/login/",
                data,
                HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(LoginAttempt.objects.get(key=key).failures, 1)

    def test_blank_admin_username_still_consumes_source_and_global_admission(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/admin/login/")
        response = client.post(
            "/admin/login/",
            {"username": "", "password": "some-input"},
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
            REMOTE_ADDR="198.51.100.92",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LoginAttempt.objects.get(key=_key("global", "all")).failures, 1)
        self.assertEqual(
            LoginAttempt.objects.get(key=_key("source", "198.51.100.92")).failures,
            1,
        )
        self.assertFalse(LoginAttempt.objects.filter(key=_key("identifier", "")).exists())

    def test_other_identifier_failures_survive_success(self):
        request = RequestFactory().post("/", REMOTE_ADDR="198.51.100.8")
        for _ in range(2):
            with login_attempt(request, "other-id") as result:
                result.authenticated = False
        self.assertEqual(self._login(Client()).status_code, 200)
        with login_attempt(request, "other-id") as result:
            self.assertFalse(result.allowed)
        self.assertEqual(
            LoginAttempt.objects.get(key=_key("identifier", "other-id")).failures, 2
        )

    def test_live_state_survives_pruning_and_old_state_is_bounded(self):
        old = timezone.now() - timedelta(days=1)
        LoginAttempt.objects.bulk_create(
            [
                LoginAttempt(key=f"{i:064x}", retry_after=old, failures=1)
                for i in range(510)
            ]
        )
        LoginAttempt.objects.all().update(updated_at=old)
        call_command("prune_login_attempts", batch_size=500)
        self.assertEqual(LoginAttempt.objects.count(), 10)
        self._login(Client(), correct=False)
        live = LoginAttempt.objects.get(key=_key("identifier", self.user.login_id))
        call_command("prune_login_attempts", batch_size=500)
        self.assertTrue(LoginAttempt.objects.filter(pk=live.pk, failures=1).exists())


class TemporalEndTests(TestCase):
    def test_all_end_types_open_finite_expired_audit_and_access(self):
        company = Tenant.objects.create(name="Scope", slug="scope")
        operator = make_user(
            "scope-operator",
            role="back_office",
            tenant=company,
            account_kind="platform",
        )
        for kind in ("membership", "role", "assignment"):
            for finite in (False, True):
                user = make_user(kind + str(finite), role="accountant", tenant=company)
                membership = user.tenant_memberships.get()
                branch = Branch.objects.create(tenant=company, name=kind + str(finite))
                assignment = BranchAssignment.objects.create(
                    membership=membership, branch=branch, assigned_by=operator
                )
                row = (
                    membership
                    if kind == "membership"
                    else (
                        CompanyRoleGrant.objects.get(membership=membership)
                        if kind == "role"
                        else assignment
                    )
                )
                if finite:
                    row.effective_until = timezone.now() + timedelta(days=1)
                    row.save()
                self.assertTrue(visible_branches(user, company.pk).exists())
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
                self.assertFalse(visible_branches(user, company.pk).exists())
                if kind != "assignment":
                    self.assertFalse(visible_companies(user).exists())
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

    def test_admin_finite_end_actions_and_branch_audit(self):
        company = Tenant.objects.create(name="Admin scope", slug="admin-scope")
        actor = make_user(
            "finite-admin", role="back_office", tenant=company, account_kind="platform"
        )
        actor.is_staff = actor.is_superuser = True
        actor.save()
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
            user = make_user("admin-" + kind, tenant=company)
            membership = user.tenant_memberships.get()
            membership.effective_until = now + timedelta(days=1)
            membership.save()
            branch = Branch.objects.create(tenant=company, name=kind)
            assignment = BranchAssignment.objects.create(
                membership=membership,
                branch=branch,
                assigned_by=actor,
                effective_from=now - timedelta(days=1),
                effective_until=now + timedelta(days=1),
            )
            grant = CompanyRoleGrant.objects.create(
                membership=membership,
                branch=branch if kind == "role" else None,
                role="accountant",
                assigned_by=actor,
                effective_from=now - timedelta(days=1),
                effective_until=now + timedelta(days=1),
            )
            row = {"membership": membership, "role": grant, "assignment": assignment}[
                kind
            ]
            for _ in range(2):
                response = self.client.post(
                    "/admin/" + path + "/",
                    {"action": action, "_selected_action": [str(row.pk)]},
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
            row.refresh_from_db()
            self.assertLessEqual(row.effective_until, timezone.now())
            self.assertFalse(visible_branches(user, company.pk).exists())
            event = AccountSecurityEvent.objects.get(subject=user, action=event_action)
            if kind != "membership":
                self.assertEqual(event.branch_id, branch.pk)

    def test_initially_expired_rows_are_noop_without_new_audit(self):
        company = Tenant.objects.create(name="Expired", slug="expired")
        actor = make_user(
            "expired-actor", role="back_office", tenant=company, account_kind="platform"
        )
        now = timezone.now()
        for kind in ("membership", "role", "assignment"):
            user = make_user("expired-" + kind)
            membership = TenantMembership.objects.create(
                user=user,
                tenant=company,
                assigned_by=actor,
                effective_from=now - timedelta(days=3),
                effective_until=(
                    now - timedelta(days=1) if kind == "membership" else None
                ),
            )
            branch = Branch.objects.create(tenant=company, name=kind)
            grant = CompanyRoleGrant.objects.create(
                membership=membership,
                role="accountant",
                assigned_by=actor,
                effective_from=now - timedelta(days=3),
                effective_until=now - timedelta(days=1),
            )
            assignment = BranchAssignment.objects.create(
                membership=membership,
                branch=branch,
                assigned_by=actor,
                effective_from=now - timedelta(days=3),
                effective_until=now - timedelta(days=1),
            )
            row = {"membership": membership, "role": grant, "assignment": assignment}[
                kind
            ]
            original = row.effective_until
            if kind == "membership":
                end_membership(actor=actor, membership=row)
            else:
                end_scope_row(actor=actor, row=row)
            row.refresh_from_db()
            self.assertEqual(row.effective_until, original)
            self.assertFalse(
                AccountSecurityEvent.objects.filter(
                    subject=user,
                    action__in=["membership.end", "role.end", "assignment.end"],
                ).exists()
            )


class ContextBoundsTests(TestCase):
    def test_current_branch_sizes_truncation_order_and_full_pagination(self):
        company = Tenant.objects.create(name="Context", slug="context")
        user = make_user("bounded-context", role="accountant", tenant=company)
        membership = user.tenant_memberships.get()
        self.client.force_login(user)
        created = 0
        bounded_bytes = None
        query_count = None
        for size in (1, 25, 75, 250):
            branches = Branch.objects.bulk_create(
                [Branch(tenant=company, name=f"B{i:04}") for i in range(created, size)]
            )
            BranchAssignment.objects.bulk_create(
                [
                    BranchAssignment(membership=membership, branch=b, assigned_by=user)
                    for b in branches
                ]
            )
            created = size
            from django.test.utils import CaptureQueriesContext

            with CaptureQueriesContext(connection) as queries:
                response = self.client.get("/api/v1/auth/me/")
            if query_count is None:
                query_count = len(queries)
            self.assertEqual(len(queries), query_count)
            print(
                f"Bounded me: {size} current branches, {len(queries)} queries, {len(response.content)} bytes"
            )
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
            self.assertEqual(page["count"], size)
            self.assertLessEqual(len(page["results"]), 20)
        second_page = self.client.get(
            f"/api/v1/tenants/{company.pk}/branches/?page=2"
        ).json()
        self.assertEqual(len(second_page["results"]), 20)
        self.assertEqual(second_page["results"][0]["name"], "B0020")
        old = Branch.objects.create(tenant=company, name="A-old")
        future = Branch.objects.create(tenant=company, name="A-future")
        now = timezone.now()
        BranchAssignment.objects.create(
            membership=membership,
            branch=old,
            assigned_by=user,
            effective_from=now - timedelta(days=2),
            effective_until=now - timedelta(days=1),
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=future,
            assigned_by=user,
            effective_from=now + timedelta(days=1),
        )
        self.assertEqual(
            self.client.get("/api/v1/auth/me/").json()["companies"][0]["branches"][0][
                "name"
            ],
            "B0000",
        )


class CleanupConcurrencyTests(TransactionTestCase):
    def test_cleanup_skips_locked_state_that_is_being_refreshed(self):
        import threading

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
                    current.save()
            except Exception as exc:
                errors.append(str(exc))
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
