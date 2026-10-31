from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.test import TestCase

from apps.accounts.audit import record_event
from apps.accounts.models import AccountSecurityEvent, User


class AuditFoundationTests(TestCase):
    def test_secret_metadata_rejected(self):
        with self.assertRaises(ValidationError):
            record_event(action="company.create", metadata={"password": "sentinel"})
        self.assertEqual(AccountSecurityEvent.objects.count(), 0)

    def test_audit_rollback_and_immutability(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                record_event(action="company.create")
                raise RuntimeError("rollback")
        self.assertEqual(AccountSecurityEvent.objects.count(), 0)
        event = record_event(action="company.create")
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE accounts_accountsecurityevent SET outcome='other' WHERE id=%s",
                    [event.pk],
                )
        with self.assertRaises(DatabaseError), transaction.atomic():
            AccountSecurityEvent.objects.filter(pk=event.pk).delete()

    def test_ordinary_attack_events_do_not_create_durable_audit(self):
        with self.assertRaises(ValidationError):
            record_event(action="login.failed")
        self.assertFalse(AccountSecurityEvent.objects.exists())


class SessionFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            login_id="session-user",
            email="session@example.invalid",
            password="a sufficiently long synthetic passphrase",
            must_change_password=False,
        )

    def test_epoch_revokes_existing_session(self):
        self.client.force_login(self.user)
        User.objects.filter(pk=self.user.pk).update(auth_epoch=2)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_temporary_session_cannot_enter_admin(self):
        self.user.must_change_password = True
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/").status_code, 403)

    def test_idle_and_absolute_expiry(self):
        import time

        for key, age in [("issued_at", 43201), ("last_activity", 3601)]:
            self.client.force_login(self.user)
            session = self.client.session
            if key == "last_activity":
                from apps.accounts.models import SessionActivity
                from apps.accounts.session_security import session_digest

                SessionActivity.objects.filter(
                    key_hash=session_digest(session.session_key)
                ).update(last_activity=int(time.time()) - age)
            else:
                session[key] = int(time.time()) - age
                session.save()
            self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)


class ScopeFoundationTests(TestCase):
    def setUp(self):
        from apps.accounts.models import RoleAssignment
        from apps.tenants.models import Tenant, TenantMembership

        self.operator = User.objects.create_user(
            login_id="platform",
            email="p@example.invalid",
            must_change_password=False,
            account_kind="platform",
        )
        RoleAssignment.objects.create(
            user=self.operator, role="back_office", assigned_by=self.operator
        )
        self.a = Tenant.objects.create(name="A", slug="a")
        self.b = Tenant.objects.create(name="B", slug="b")
        TenantMembership.objects.create(
            user=self.operator, tenant=self.a, assigned_by=self.operator
        )
        self.user = User.objects.create_user(
            login_id="member", email="m@example.invalid", must_change_password=False
        )
        self.member = TenantMembership.objects.create(
            user=self.user, tenant=self.a, assigned_by=self.operator
        )

    def test_platform_does_not_imply_foreign_company_or_business_module(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.policy import require_action

        for kwargs in [dict(company=self.b), dict(company=self.a, module="accounting")]:
            with self.assertRaises(PermissionDenied):
                require_action(self.operator, "company.rename", **kwargs)
        with self.assertRaises(PermissionDenied):
            require_action(self.operator, "financial.post", company=self.a)

    def test_company_creation_does_not_grant_membership(self):
        from apps.tenants.commands import create_company

        company = create_company(actor=self.operator, name="C", slug="c")
        self.assertFalse(company.memberships.exists())
        self.assertTrue(
            AccountSecurityEvent.objects.filter(
                resource_id=company.pk, action="company.create"
            ).exists()
        )

    def test_owner_grant_is_explicit_and_cannot_write(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.policy import require_action
        from apps.tenants.commands import grant_role, set_company

        with self.assertRaises(PermissionDenied):
            require_action(self.user, "core.company.read", company=self.a)
        grant_role(actor=self.operator, membership=self.member, role="owner")
        require_action(self.user, "core.company.read", company=self.a)
        with self.assertRaises(PermissionDenied):
            set_company(actor=self.user, company=self.a, name="Forbidden")
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "unknown.action", company=self.a)

    def test_global_business_role_never_grants_new_policy_access(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.models import RoleAssignment
        from apps.accounts.policy import require_action

        RoleAssignment.objects.create(
            user=self.user, role="accountant", assigned_by=self.operator
        )
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "account.provision.media", company=self.a)

    def test_company_account_with_legacy_back_office_role_is_not_platform(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.models import RoleAssignment
        from apps.accounts.policy import require_action

        RoleAssignment.objects.create(
            user=self.user, role="back_office", assigned_by=self.operator
        )
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "branch.create", company=self.a)
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "account.reset.investor", company=self.a)

    def test_branch_assignment_and_grant_intersection(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.policy import require_action
        from apps.tenants.commands import (
            assign_branch,
            create_branch,
            end_scope_row,
            grant_role,
        )

        branch = create_branch(actor=self.operator, company=self.a, name="North")
        row = assign_branch(actor=self.operator, membership=self.member, branch=branch)
        grant_role(
            actor=self.operator, membership=self.member, role="media", branch=branch
        )
        require_action(self.user, "core.branch.read", company=self.a, branch=branch)
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "core.company.read", company=self.a)
        end_scope_row(actor=self.operator, row=row)
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "core.branch.read", company=self.a, branch=branch)

    def test_parent_membership_end_preserves_and_disables_grants(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.models import CompanyRoleGrant
        from apps.accounts.policy import require_action
        from apps.tenants.commands import end_membership, grant_role

        row = grant_role(actor=self.operator, membership=self.member, role="accountant")
        end_membership(actor=self.operator, membership=self.member)
        self.assertTrue(CompanyRoleGrant.objects.filter(pk=row.pk).exists())
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "account.provision.media", company=self.a)

    def test_finite_future_and_ended_membership_validity(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.tenants.models import TenantMembership
        from apps.tenants.selectors import current_interval

        self.member.effective_until = timezone.now() + timedelta(days=1)
        self.member.save()
        self.assertTrue(
            TenantMembership.objects.filter(pk=self.member.pk)
            .filter(current_interval())
            .exists()
        )
        self.member.effective_until = timezone.now() - timedelta(microseconds=1)
        self.member.save()
        self.assertFalse(
            TenantMembership.objects.filter(pk=self.member.pk)
            .filter(current_interval())
            .exists()
        )

    def test_company_suspend_preserves_identity_and_recovery_scope(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.policy import require_action
        from apps.tenants.commands import set_company

        old = self.a.pk
        set_company(actor=self.operator, company=self.a, is_active=False)
        with self.assertRaises(PermissionDenied):
            require_action(self.operator, "core.company.read", company=self.a)
        restored = set_company(actor=self.operator, company=self.a, is_active=True)
        self.assertEqual(old, restored.pk)

    def test_direct_sql_company_scope_and_ownership_guards(self):
        from apps.accounts.models import CompanyRoleGrant
        from apps.tenants.models import Branch, BranchAssignment

        foreign = Branch.objects.create(tenant=self.b, name="Foreign")
        for model, kwargs in [
            (BranchAssignment, {}),
            (CompanyRoleGrant, {"role": "owner"}),
        ]:
            with self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.create(
                    membership=self.member,
                    branch=foreign,
                    assigned_by=self.operator,
                    **kwargs,
                )
        with self.assertRaises(DatabaseError), transaction.atomic():
            Branch.objects.filter(pk=foreign.pk).update(tenant=self.a)
        with self.assertRaises(DatabaseError), transaction.atomic():
            self.member.delete()

    def test_company_wide_and_branch_role_uniqueness(self):
        from apps.accounts.models import CompanyRoleGrant

        CompanyRoleGrant.objects.create(
            membership=self.member, role="owner", assigned_by=self.operator
        )
        with self.assertRaises(DatabaseError), transaction.atomic():
            CompanyRoleGrant.objects.create(
                membership=self.member, role="owner", assigned_by=self.operator
            )

    def test_scoped_read_selectors_hide_ungranted_company_and_branch(self):
        from apps.tenants.commands import assign_branch, create_branch, grant_role
        from apps.tenants.selectors import visible_branches, visible_companies

        self.assertFalse(visible_companies(self.user).exists())
        branch = create_branch(actor=self.operator, company=self.a, name="Visible")
        assign_branch(actor=self.operator, membership=self.member, branch=branch)
        grant_role(
            actor=self.operator, membership=self.member, role="media", branch=branch
        )
        self.assertEqual(list(visible_companies(self.user)), [self.a])
        self.assertEqual(list(visible_branches(self.user, self.a.pk)), [branch])
        self.assertFalse(visible_branches(self.user, self.b.pk).exists())

    def test_raw_primitives_cannot_run_without_transaction(self):
        # TestCase has an outer transaction: the primitive is deliberately private,
        # while exposed commands must still enforce policy for callers.
        from django.core.exceptions import PermissionDenied

        from apps.tenants.commands import create_branch

        with self.assertRaises(PermissionDenied):
            create_branch(actor=self.user, company=self.a, name="Denied")


class PrivatePasswordTests(TestCase):
    def setUp(self):
        self.old = "synthetic long private passphrase for tests"
        self.user = User.objects.create_user(
            login_id="private-user", email="private@example.invalid", password=self.old
        )
        self.client.force_login(self.user)

    def change(self, password):
        import json

        return self.client.post(
            "/api/v1/auth/password/change/",
            json.dumps(
                {
                    "current_password": self.old,
                    "new_password": password,
                    "confirm_password": password,
                }
            ),
            content_type="application/json",
        )

    def test_same_and_short_password_rejected(self):
        for password in [self.old, "brief"]:
            self.assertEqual(self.change(password).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.must_change_password)

    def test_current_session_retained_and_other_session_revoked(self):
        from django.test import Client

        other = Client()
        other.force_login(self.user)
        response = self.change("a different long synthetic private test passphrase")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertEqual(self.user.auth_epoch, 2)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(other.get("/api/v1/auth/me/").status_code, 401)

    def test_stale_session_after_reset_cannot_overwrite_credentials(self):
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory

        from apps.accounts.passwords import change_private_password

        request = RequestFactory().post("/")
        request.user = self.user
        request.session = self.client.session
        current = User.objects.get(pk=self.user.pk)
        current.set_password("an administrator issued synthetic temporary credential")
        current.save()
        with self.assertRaises(PermissionDenied):
            change_private_password(
                request,
                current_password=self.old,
                new_password="another synthetic long private phrase",
                confirmation="another synthetic long private phrase",
            )
        current.refresh_from_db()
        self.assertTrue(
            current.check_password(
                "an administrator issued synthetic temporary credential"
            )
        )


class AuditPrivilegeTests(TestCase):
    def test_denial_evidence_bounded(self):
        from apps.accounts.audit import record_sensitive_denial

        actor = User.objects.create_user(
            login_id="denied", email="denied@example.invalid"
        )
        for _ in range(5):
            record_sensitive_denial(actor=actor)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="admin.denied").count(), 1
        )
        self.assertIsNone(record_sensitive_denial(actor=None))

    def test_runtime_role_cannot_mutate_or_truncate(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE ROLE virms_test_audit_runtime NOLOGIN")
            cursor.execute("GRANT USAGE ON SCHEMA public TO virms_test_audit_runtime")
            cursor.execute(
                "GRANT SELECT, INSERT ON accounts_accountsecurityevent TO virms_test_audit_runtime"
            )
        for sql in [
            "UPDATE accounts_accountsecurityevent SET outcome='changed'",
            "DELETE FROM accounts_accountsecurityevent",
            "TRUNCATE accounts_accountsecurityevent",
        ]:
            with self.assertRaises(DatabaseError), transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL ROLE virms_test_audit_runtime")
                    cursor.execute(sql)


class SessionLeaseTests(TestCase):
    def test_touch_never_regresses_when_completions_arrive_out_of_order(self):
        from apps.accounts.models import SessionActivity
        from apps.accounts.session_security import touch_activity

        row = SessionActivity.objects.create(
            key_hash="a" * 64, issued_at=1000, last_activity=1000
        )
        self.assertEqual(touch_activity(row.pk, 1200), 1)
        self.assertEqual(touch_activity(row.pk, 1100), 0)
        row.refresh_from_db()
        self.assertEqual(row.last_activity, 1200)

    def test_revoke_between_authentication_and_session_issuance_denied(self):
        from django.core.exceptions import PermissionDenied
        from django.test import RequestFactory

        from apps.accounts.session_security import stamp_session

        user = User.objects.create_user(
            login_id="stale",
            email="stale@example.invalid",
            password="synthetic long private credential",
        )
        request = RequestFactory().post("/")
        request.session = self.client.session
        User.objects.filter(pk=user.pk).update(auth_epoch=2)
        with self.assertRaises(PermissionDenied):
            stamp_session(sender=User, request=request, user=user)


class ScopeReviewRegressionTests(ScopeFoundationTests):
    def test_database_rejects_direct_second_company_membership(self):
        from django.db import IntegrityError

        from apps.tenants.models import TenantMembership

        with self.assertRaises(IntegrityError), transaction.atomic():
            TenantMembership.objects.create(
                user=self.user, tenant=self.b, assigned_by=self.operator
            )

        import uuid

        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO tenants_tenantmembership "
                    "(id, user_id, tenant_id, assigned_by_id, effective_from, "
                    "created_at, updated_at) VALUES (%s, %s, %s, %s, now(), now(), now())",
                    [uuid.uuid4(), self.user.pk, self.b.pk, self.operator.pk],
                )

    def test_independent_company_accounts_keep_separate_credentials_and_epochs(self):
        from apps.tenants.models import TenantMembership

        other = User.objects.create_user(
            login_id="member-b",
            email="member-b@example.invalid",
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            password="independent synthetic password phrase",
        )
        TenantMembership.objects.create(
            user=other, tenant=self.b, assigned_by=self.operator
        )
        self.assertNotEqual(other.pk, self.user.pk)
        User.objects.filter(pk=self.user.pk).update(auth_epoch=2)
        other.refresh_from_db()
        self.assertEqual(other.auth_epoch, 1)
        self.assertTrue(other.check_password("independent synthetic password phrase"))

    def test_business_account_cannot_join_second_company(self):
        from apps.tenants.commands import add_membership
        from apps.tenants.models import TenantMembership

        TenantMembership.objects.create(
            user=self.operator, tenant=self.b, assigned_by=self.operator
        )
        with self.assertRaises(ValidationError):
            add_membership(actor=self.operator, company=self.b, user=self.user)
        self.assertFalse(
            TenantMembership.objects.filter(user=self.user, tenant=self.b).exists()
        )

    def test_same_company_different_branch_resource_is_denied(self):
        from django.core.exceptions import PermissionDenied

        from apps.accounts.policy import require_action
        from apps.tenants.commands import assign_branch, create_branch, grant_role

        one = create_branch(actor=self.operator, company=self.a, name="One")
        two = create_branch(actor=self.operator, company=self.a, name="Two")
        assign_branch(actor=self.operator, membership=self.member, branch=one)
        grant_role(
            actor=self.operator, membership=self.member, role="media", branch=one
        )
        with self.assertRaises(PermissionDenied):
            require_action(
                self.user, "core.branch.read", company=self.a, branch=one, resource=two
            )

    def test_future_finite_membership_prevents_overlap(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.tenants.commands import add_membership
        from apps.tenants.models import TenantMembership

        other = User.objects.create_user(
            login_id="future",
            email="future@example.invalid",
            must_change_password=False,
        )
        TenantMembership.objects.create(
            user=other,
            tenant=self.a,
            assigned_by=self.operator,
            effective_from=timezone.now() + timedelta(days=1),
            effective_until=timezone.now() + timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            add_membership(actor=self.operator, company=self.a, user=other)

    def test_future_finite_assignment_prevents_overlap(self):
        from datetime import timedelta

        from django.utils import timezone

        from apps.tenants.commands import assign_branch, create_branch
        from apps.tenants.models import BranchAssignment

        branch = create_branch(actor=self.operator, company=self.a, name="Future")
        BranchAssignment.objects.create(
            membership=self.member,
            branch=branch,
            assigned_by=self.operator,
            effective_from=timezone.now() + timedelta(days=1),
            effective_until=timezone.now() + timedelta(days=2),
        )
        with self.assertRaises(ValidationError):
            assign_branch(actor=self.operator, membership=self.member, branch=branch)
