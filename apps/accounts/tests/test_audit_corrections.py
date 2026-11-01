from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.accounts.lifecycle import (
    reset_account,
    revoke_account_sessions,
    set_account_status,
)
from apps.accounts.login_admission import admit_login
from apps.accounts.models import AccountSecurityEvent, CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.tenants.admin_scope import managed_companies
from apps.tenants.commands import end_scope_row
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership
from apps.tenants.selectors import company_context, visible_branches, visible_companies


class AuditCorrectionTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Audit", slug="audit")
        self.actor = make_user(
            "operator", role="back_office", tenant=self.company, account_kind="platform"
        )
        self.actor.is_staff = self.actor.is_superuser = True
        self.actor.save()
        self.user = make_user("accountant", role="accountant", tenant=self.company)
        self.target = make_user("investor", role="investor", tenant=self.company)
        self.membership = self.user.tenant_memberships.get()
        self.branch = Branch.objects.create(tenant=self.company, name="Branch")

    def test_accountant_cannot_mutate_investor_or_media_lifecycle(self):
        for role in ("investor", "media"):
            target = make_user("denied-" + role, role=role, tenant=self.company)
            for operation, extra in (
                (reset_account, {}),
                (set_account_status, {"active": False}),
                (set_account_status, {"active": True}),
                (revoke_account_sessions, {}),
            ):
                with self.assertRaises(PermissionDenied):
                    operation(
                        actor=self.user,
                        user_id=target.pk,
                        reason="Reviewed recovery",
                        **extra,
                    )
        self.target.refresh_from_db()
        self.assertEqual(self.target.auth_epoch, 1)
        self.assertTrue(self.target.is_active)
        self.assertFalse(
            AccountSecurityEvent.objects.filter(subject=self.target).exists()
        )

    def test_reason_required_before_mutation_and_saved_for_platform(self):
        for reason in (None, "", " ", "x" * 501, "bad\nreason"):
            with self.assertRaises(ValidationError):
                reset_account(actor=self.actor, user_id=self.target.pk, reason=reason)
        self.target.refresh_from_db()
        self.assertEqual(self.target.auth_epoch, 1)
        reset_account(
            actor=self.actor, user_id=self.target.pk, reason="Verified recovery"
        )
        self.assertEqual(
            AccountSecurityEvent.objects.get(subject=self.target).reason,
            "Verified recovery",
        )

    def _history(self, model, **fields):
        now = timezone.now()
        model.objects.create(
            **fields,
            assigned_by=self.actor,
            effective_from=now - timedelta(days=3),
            effective_until=now - timedelta(days=2),
        )
        model.objects.create(
            **fields,
            assigned_by=self.actor,
            effective_from=now + timedelta(days=2),
            effective_until=now + timedelta(days=3),
        )

    def test_expired_and_future_assignment_do_not_combine(self):
        self._history(BranchAssignment, membership=self.membership, branch=self.branch)
        self.assertFalse(visible_branches(self.user, self.company.pk).exists())
        end_scope_row(
            actor=self.actor,
            row=CompanyRoleGrant.objects.get(membership=self.membership),
        )
        CompanyRoleGrant.objects.create(
            membership=self.membership,
            branch=self.branch,
            role="accountant",
            assigned_by=self.actor,
        )
        self.assertFalse(visible_companies(self.user).exists())

    def test_expired_and_future_grant_do_not_combine(self):
        # History is immutable: end the existing grant through the command.
        end_scope_row(
            actor=self.actor,
            row=CompanyRoleGrant.objects.get(membership=self.membership),
        )
        self._history(CompanyRoleGrant, membership=self.membership, role="accountant")
        BranchAssignment.objects.create(
            membership=self.membership, branch=self.branch, assigned_by=self.actor
        )
        self.assertFalse(visible_companies(self.user).exists())
        self.assertFalse(visible_branches(self.user, self.company.pk).exists())

    def test_admin_expired_and_future_memberships_do_not_combine(self):
        membership = self.actor.tenant_memberships.get()
        from apps.tenants.commands import end_membership

        end_membership(actor=self.actor, membership=membership)
        self._history(TenantMembership, user=self.actor, tenant=self.company)
        self.assertFalse(managed_companies(self.actor).exists())

    def test_scope_end_records_branch(self):
        row = BranchAssignment.objects.create(
            membership=self.membership, branch=self.branch, assigned_by=self.actor
        )
        end_scope_row(actor=self.actor, row=row)
        event = AccountSecurityEvent.objects.get(action="assignment.end")
        self.assertEqual(event.branch_id, self.branch.pk)

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=2,
    )
    def test_active_inactive_missing_have_identical_admission(self):
        now = timezone.now()
        inactive = make_user("inactive")
        inactive.is_active = False
        inactive.save()
        request = RequestFactory().post(
            "/api/v1/auth/login/", REMOTE_ADDR="198.51.100.12"
        )
        with patch("apps.accounts.login_admission.timezone.now", return_value=now):
            outcomes = [
                [admit_login(request, name) for _ in range(3)]
                for name in (self.user.login_id, inactive.login_id, "nonexistent")
            ]
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1], outcomes[2])

    def test_stale_operator_cannot_mutate_after_revocation(self):
        from apps.accounts.models import User

        User.objects.filter(pk=self.actor.pk).update(
            auth_epoch=self.actor.auth_epoch + 1
        )
        for operation, extra in (
            (reset_account, {}),
            (set_account_status, {"active": False}),
            (revoke_account_sessions, {}),
        ):
            with self.assertRaises(PermissionDenied):
                operation(
                    actor=self.actor,
                    user_id=self.target.pk,
                    reason="Verified recovery",
                    **extra,
                )

    def test_accountant_api_lifecycle_is_hidden_even_with_scoped_grant(self):
        from django.urls import reverse

        self.client.force_login(self.user)
        for route in ("account-reset", "account-status", "account-revoke"):
            response = self.client.post(
                reverse(route, args=[self.target.pk]),
                data={"reason": "Verified recovery", "is_active": False},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 404)

    def test_platform_api_missing_reason_is_rejected(self):
        from django.urls import reverse

        self.client.force_login(self.actor)
        for route in ("account-reset", "account-status", "account-revoke"):
            response = self.client.post(
                reverse(route, args=[self.target.pk]),
                data={"is_active": False},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def test_branch_grant_end_records_branch(self):
        BranchAssignment.objects.create(
            membership=self.membership, branch=self.branch, assigned_by=self.actor
        )
        row = CompanyRoleGrant.objects.create(
            membership=self.membership,
            branch=self.branch,
            role="media",
            assigned_by=self.actor,
        )
        end_scope_row(actor=self.actor, row=row)
        self.assertEqual(
            AccountSecurityEvent.objects.get(action="role.end").branch_id,
            self.branch.pk,
        )

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=2,
    )
    def test_api_login_throttle_does_not_enumerate(self):
        from django.urls import reverse

        from apps.accounts.models import LoginAttempt

        inactive = make_user("inactive-api")
        inactive.is_active = False
        inactive.save()
        results = []
        now = timezone.now()
        for identity in (self.user.login_id, inactive.login_id, "missing-api"):
            LoginAttempt.objects.all().delete()
            with patch("apps.accounts.login_admission.timezone.now", return_value=now):
                responses = [
                    self.client.post(
                        reverse("auth-login"),
                        data={"login_id": identity, "password": "wrong password"},
                        content_type="application/json",
                    )
                    for _ in range(3)
                ]
            results.append(
                [
                    (r.status_code, r.json()["detail"], r.get("Retry-After"))
                    for r in responses
                ]
            )
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertEqual([r[0] for r in results[0]], [401, 401, 429])

    @override_settings(
        VIRMS_LOGIN_GLOBAL_LIMIT=100,
        VIRMS_LOGIN_SOURCE_LIMIT=100,
        VIRMS_LOGIN_IDENTIFIER_LIMIT=2,
    )
    def test_admin_login_throttle_does_not_enumerate(self):
        from apps.accounts.admin_login import VIRMSAdminAuthenticationForm
        from apps.accounts.models import LoginAttempt

        inactive = make_user("inactive-admin")
        inactive.is_active = False
        inactive.save()
        results = []
        for identity in (self.actor.login_id, inactive.login_id, "missing-admin"):
            LoginAttempt.objects.all().delete()
            errors = []
            for _ in range(3):
                form = VIRMSAdminAuthenticationForm(
                    RequestFactory().post("/admin/login/", REMOTE_ADDR="198.51.100.8"),
                    data={"username": identity, "password": "wrong password"},
                )
                self.assertFalse(form.is_valid())
                errors.append(str(form.non_field_errors()))
            results.append(errors)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_context_prefetch_excludes_history(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self._history(BranchAssignment, membership=self.membership, branch=self.branch)
        self._history(CompanyRoleGrant, membership=self.membership, role="media")
        with CaptureQueriesContext(connection) as queries:
            context, _ = company_context(self.user)
        self.assertEqual(context[0]["roles"], ["accountant"])
        self.assertEqual(context[0]["branches"], [])
        prefetches = [
            q["sql"]
            for q in queries
            if q["sql"].startswith(
                (
                    'SELECT "accounts_companyrolegrant".',
                    'SELECT "tenants_branchassignment".',
                )
            )
        ]
        self.assertEqual(len(prefetches), 2)
        for query in prefetches:
            self.assertIn('"effective_from" <=', query)
            self.assertIn('"effective_until" >', query)

    def test_admission_key_cardinality_is_bounded_for_rotating_input(self):
        from apps.accounts.login_admission import _key

        for kind in ("identifier", "source"):
            keys = {_key(kind, str(index)) for index in range(65537)}
            self.assertLessEqual(len(keys), 65536)
