from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound
from types import SimpleNamespace

from apps.accounts.models import CompanyRoleGrant, RoleAssignment, User
from apps.accounts.policy import require_action
from apps.accounts.tests.test_users import make_user
from apps.accounting.policies import (
    AccountingAction,
    accounting_scope,
    require_accounting_module_enabled,
)
from apps.accounting.models import AccountingCategory, AccountingEvent
from apps.tenants.models import (
    Branch,
    BranchAssignment,
    CompanyModuleState,
    Tenant,
    TenantMembership,
)


class AccountingPolicyTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="north")
        self.other_company = Tenant.objects.create(name="South", slug="south")
        self.branch_a = Branch.objects.create(tenant=self.company, name="A")
        self.branch_b = Branch.objects.create(tenant=self.company, name="B")
        self.other_branch = Branch.objects.create(
            tenant=self.other_company, name="Other"
        )
        self.company_accountant = make_user(
            "p4-company-accountant", role="accountant", tenant=self.company
        )
        self.owner = make_user("p4-owner", role="owner", tenant=self.company)
        self.branch_accountant = self.make_branch_user(
            "p4-branch-accountant", self.branch_a, "accountant"
        )
        self.branch_owner = self.make_branch_user(
            "p4-branch-owner", self.branch_a, "owner"
        )

    def make_branch_user(self, login_id, branch, role):
        user = make_user(login_id, tenant=self.company)
        membership = user.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=role,
            branch=branch,
            assigned_by=user,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=branch,
            assigned_by=user,
        )
        return user

    def test_company_accountant_can_correct_other_branch_in_same_company(self):
        scope = accounting_scope(
            self.company_accountant, self.company.pk, AccountingAction.CORRECT
        )

        self.assertTrue(scope.is_company_accountant)
        self.assertEqual(scope.validate_write_branch(self.branch_b.pk), self.branch_b)
        self.assertIsNone(
            scope.validate_write_branch(None, allow_company_wide=True)
        )
        with self.assertRaises(PermissionDenied):
            scope.validate_write_branch(None)
        with self.assertRaises(NotFound):
            scope.validate_write_branch(self.other_branch.pk)

    def test_branch_accountant_is_limited_to_assigned_branch(self):
        scope = accounting_scope(
            self.branch_accountant, self.company.pk, AccountingAction.CORRECT
        )

        self.assertFalse(scope.is_company_accountant)
        self.assertEqual(scope.validate_write_branch(self.branch_a.pk), self.branch_a)
        with self.assertRaises(PermissionDenied):
            scope.validate_write_branch(None)
        with self.assertRaises(NotFound):
            scope.validate_write_branch(self.branch_b.pk)
        with self.assertRaises(NotFound):
            accounting_scope(
                self.branch_accountant,
                self.other_company.pk,
                AccountingAction.CORRECT,
            )

    def test_owner_has_read_only_accounting_access(self):
        scope = accounting_scope(self.owner, self.company.pk, AccountingAction.READ)
        self.assertTrue(scope.is_company_wide_reader)
        with self.assertRaises(PermissionDenied):
            accounting_scope(self.owner, self.company.pk, AccountingAction.POST)

        branch_scope = accounting_scope(
            self.branch_owner, self.company.pk, AccountingAction.READ
        )
        self.assertEqual(branch_scope.allowed_branch_ids, frozenset({self.branch_a.pk}))

    def test_company_owner_read_scope_does_not_widen_branch_accountant_writes(self):
        user = make_user(
            "p4-owner-plus-branch-accountant", role="owner", tenant=self.company
        )
        membership = user.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role="accountant",
            branch=self.branch_a,
            assigned_by=user,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch_a,
            assigned_by=user,
        )

        read_scope = accounting_scope(user, self.company.pk, AccountingAction.READ)
        self.assertTrue(read_scope.is_company_wide_reader)
        write_scope = accounting_scope(user, self.company.pk, AccountingAction.CORRECT)
        self.assertEqual(write_scope.validate_write_branch(self.branch_a.pk), self.branch_a)
        with self.assertRaises(NotFound):
            write_scope.validate_record(
                SimpleNamespace(
                    tenant_id=self.other_company.pk,
                    branch_id=self.branch_b.pk,
                )
            )
        with self.assertRaises(NotFound):
            write_scope.validate_write_branch(self.branch_b.pk)

    def test_platform_back_office_cannot_read_or_post_company_finance(self):
        platform = User.objects.create_superuser(
            login_id="p4-platform",
            email="p4-platform@example.invalid",
            password="P4-test-only-account-password-123!",
            must_change_password=False,
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform, tenant=self.company, assigned_by=platform
        )

        with self.assertRaises(NotFound):
            accounting_scope(platform, self.company.pk, AccountingAction.READ)
        with self.assertRaises(NotFound):
            accounting_scope(platform, self.company.pk, AccountingAction.POST)

    def test_module_must_be_configured_and_enabled_for_root_posting(self):
        scope = accounting_scope(
            self.company_accountant, self.company.pk, AccountingAction.POST
        )
        with transaction.atomic():
            with self.assertRaises(PermissionDenied):
                require_accounting_module_enabled(scope)

        CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state="disabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )
        with transaction.atomic():
            with self.assertRaises(PermissionDenied):
                require_accounting_module_enabled(scope)

        CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state="enabled",
            version=2,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )
        with transaction.atomic():
            require_accounting_module_enabled(scope)

    def test_accounting_action_allowlist_is_integrated_with_shared_policy(self):
        self.assertEqual(
            require_action(
                self.company_accountant,
                "accounting.income.create",
                company=self.company,
                branch=self.branch_b,
            ),
            self.company_accountant,
        )
        with self.assertRaises(Http404):
            require_action(
                self.branch_accountant,
                "accounting.income.create",
                company=self.company,
                branch=self.branch_b,
            )
        with self.assertRaises(PermissionDenied):
            require_action(
                self.company_accountant,
                "accounting.future.wildcard",
                company=self.company,
            )
        with self.assertRaises(PermissionDenied):
            require_action(
                self.branch_accountant,
                "accounting.category.manage",
                company=self.company,
                branch=self.branch_a,
            )

    def test_policy_scope_rejects_unauthenticated_identity_and_client_time(self):
        class ForgedPrincipal:
            pk = self.company_accountant.pk
            is_authenticated = False

        with self.assertRaises((PermissionDenied, NotFound)):
            accounting_scope(
                ForgedPrincipal(), self.company.pk, AccountingAction.READ
            )
        with self.assertRaises(TypeError):
            accounting_scope(
                self.company_accountant,
                self.company.pk,
                AccountingAction.READ,
                at=None,
            )

    def test_company_wide_queryset_and_branchless_record_are_company_scoped(self):
        foreign_actor = make_user(
            "p4-foreign-accountant", role="accountant", tenant=self.other_company
        )
        foreign_category = AccountingCategory.objects.create(
            tenant=self.other_company,
            kind=AccountingCategory.Kind.INCOME,
            label="Foreign income",
            created_by=foreign_actor,
        )
        foreign_revision = CompanyModuleState.objects.create(
            tenant=self.other_company,
            module_code="accounting",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=foreign_actor,
        )
        foreign_record = AccountingEvent.objects.create(
            tenant=self.other_company,
            branch=None,
            event_type=AccountingEvent.EventType.INCOME,
            amount="20.00",
            effective_at=timezone.now(),
            actor=foreign_actor,
            module_revision=foreign_revision,
            category=foreign_category,
            description="Foreign Company entry",
            source_reference="FOREIGN-1",
        )
        local_record = AccountingEvent.objects.create(
            tenant=self.company,
            branch=None,
            event_type=AccountingEvent.EventType.INCOME,
            amount="30.00",
            effective_at=timezone.now(),
            actor=self.company_accountant,
            module_revision=CompanyModuleState.objects.create(
                tenant=self.company,
                module_code="accounting",
                state="enabled",
                version=1,
                effective_from=timezone.now(),
                changed_by=self.company_accountant,
            ),
            category=AccountingCategory.objects.create(
                tenant=self.company,
                kind=AccountingCategory.Kind.INCOME,
                label="Local income",
                created_by=self.company_accountant,
            ),
            description="Local Company entry",
            source_reference="LOCAL-1",
        )
        scope = accounting_scope(
            self.company_accountant, self.company.pk, AccountingAction.READ
        )
        rows = scope.filter_branch_records(AccountingEvent.objects.all())
        self.assertEqual(set(rows.values_list("pk", flat=True)), {local_record.pk})
        with self.assertRaises(NotFound):
            scope.validate_record(foreign_record)

    def test_branch_accountant_cannot_manage_shared_company_accounts(self):
        with self.assertRaises(PermissionDenied):
            accounting_scope(
                self.branch_accountant, self.company.pk, AccountingAction.MANAGE
            )

    def test_must_change_password_and_expired_branch_assignment_fail_closed(self):
        pending = make_user(
            "p4-pending-password",
            role="accountant",
            tenant=self.company,
            must_change=True,
        )
        with self.assertRaises(PermissionDenied):
            accounting_scope(pending, self.company.pk, AccountingAction.READ)

        membership = self.branch_accountant.tenant_memberships.get(
            tenant=self.company
        )
        assignment = membership.branch_assignments.get(branch=self.branch_a)
        assignment.effective_until = timezone.now()
        assignment.save(update_fields=["effective_until", "updated_at"])
        with self.assertRaises(PermissionDenied):
            accounting_scope(
                self.branch_accountant, self.company.pk, AccountingAction.CORRECT
            )
