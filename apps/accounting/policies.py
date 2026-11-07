from dataclasses import dataclass
from enum import StrEnum

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.accounts.models import CompanyRoleGrant, User
from apps.accounts.policy import require_action
from apps.tenants.models import (
    Branch,
    BranchAssignment,
    CompanyModuleCode,
    CompanyModuleState,
    Tenant,
    TenantMembership,
)
from apps.tenants.selectors import current_interval


class AccountingAction(StrEnum):
    READ = "read"
    REPORT = "report"
    POST = "post"
    CORRECT = "correct"
    MANAGE = "manage"


READ_ACTIONS = {AccountingAction.READ, AccountingAction.REPORT}
WRITE_ACTIONS = {
    AccountingAction.POST,
    AccountingAction.CORRECT,
    AccountingAction.MANAGE,
}
_UNSET = object()


@dataclass(frozen=True)
class AccountingScope:
    actor: User
    company: Tenant
    membership: TenantMembership
    action: AccountingAction
    is_company_accountant: bool
    is_company_wide_reader: bool
    allowed_branch_ids: frozenset

    def validate_write_branch(self, branch_id, *, allow_company_wide=False):
        if self.action not in WRITE_ACTIONS:
            raise PermissionDenied("Accounting write access required.")
        if branch_id is None:
            if self.is_company_accountant and allow_company_wide:
                return None
            raise PermissionDenied("Branch assignment required.")
        branch = Branch.objects.filter(
            pk=branch_id, tenant_id=self.company.pk
        ).first()
        if branch is None:
            raise NotFound("Branch not found.")
        if not self.is_company_accountant and branch.pk not in self.allowed_branch_ids:
            raise NotFound("Branch not found.")
        return branch

    def validate_record(self, record):
        if self.action not in READ_ACTIONS | WRITE_ACTIONS:
            raise PermissionDenied("Accounting access required.")
        if getattr(record, "tenant_id", None) != self.company.pk:
            raise NotFound("Accounting record not found.")
        branch_id = getattr(record, "branch_id", None)
        if self.is_company_accountant or (
            self.action in READ_ACTIONS and self.is_company_wide_reader
        ):
            if branch_id is None:
                return
            if not Branch.objects.filter(
                pk=branch_id, tenant_id=self.company.pk
            ).exists():
                raise NotFound("Accounting record not found.")
            return
        if branch_id is None or branch_id not in self.allowed_branch_ids:
            raise NotFound("Accounting record not found.")

    def validate_replacement_branch(
        self,
        branch_id,
        *,
        original_record,
        allow_company_wide=False,
    ):
        self.validate_record(original_record)
        original_branch_id = original_record.branch_id
        if self.is_company_accountant:
            return self.validate_write_branch(
                branch_id,
                allow_company_wide=allow_company_wide,
            )
        if branch_id != original_branch_id:
            raise PermissionDenied("Branch Accountant cannot reassign Branch.")
        return self.validate_write_branch(
            branch_id,
            allow_company_wide=allow_company_wide,
        )

    def filter_branch_records(self, queryset, *, field="branch_id", branch_id=_UNSET):
        queryset = queryset.filter(tenant_id=self.company.pk)
        if self.is_company_accountant or (
            self.action in READ_ACTIONS and self.is_company_wide_reader
        ):
            if branch_id is _UNSET:
                return queryset
            if branch_id is not None and not Branch.objects.filter(
                pk=branch_id, tenant_id=self.company.pk
            ).exists():
                raise NotFound("Branch not found.")
            return queryset.filter(**{field: branch_id})

        if branch_id is _UNSET:
            return queryset.filter(**{f"{field}__in": self.allowed_branch_ids})
        if branch_id is None or branch_id not in self.allowed_branch_ids:
            raise NotFound("Branch not found.")
        return queryset.filter(**{field: branch_id})


def accounting_scope(
    actor,
    company_id,
    action,
    *,
    branch_id=None,
    permission_action=None,
    resource=None,
):
    """Resolve Accounting scope from current server-side identity and grants."""
    try:
        action = AccountingAction(action)
    except (TypeError, ValueError):
        raise PermissionDenied("Unsupported Accounting action.") from None

    at = timezone.now()
    current_actor = User.objects.filter(pk=getattr(actor, "pk", None)).first()
    if (
        current_actor is None
        or not current_actor.is_active
        or current_actor.account_kind != User.AccountKind.COMPANY
    ):
        raise NotFound("Company not found.")
    if current_actor.must_change_password:
        raise PermissionDenied("Password change is required.")

    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    branch = None
    if branch_id is not None:
        branch = Branch.objects.filter(
            pk=branch_id,
            tenant=company,
        ).first()
        if branch is None:
            raise NotFound("Branch not found.")
    elif resource is not None and getattr(resource, "branch_id", None) is not None:
        branch = Branch.objects.filter(
            pk=resource.branch_id,
            tenant=company,
        ).first()
        if branch is None:
            raise NotFound("Accounting record not found.")
    membership = (
        TenantMembership.objects.filter(user=current_actor, tenant=company)
        .filter(current_interval(at))
        .first()
    )
    if membership is None:
        raise NotFound("Company not found.")
    action_to_policy = {
        AccountingAction.READ: "accounting.event.read",
        AccountingAction.REPORT: "accounting.report.read",
        AccountingAction.POST: "accounting.income.create",
        AccountingAction.CORRECT: "accounting.event.correct",
        AccountingAction.MANAGE: "accounting.account.manage",
    }
    require_action(
        actor,
        permission_action or action_to_policy[action],
        company=company,
        branch=branch,
        resource=resource,
    )

    grants = (
        CompanyRoleGrant.objects.filter(
            membership=membership,
            role__in=(CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT),
            branch__isnull=True,
        )
        .filter(current_interval(at))
    )
    company_roles = set(grants.values_list("role", flat=True))
    branch_grants = (
        CompanyRoleGrant.objects.filter(
            membership=membership,
            role__in=(CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT),
            branch__tenant=company,
            branch__isnull=False,
        )
        .filter(current_interval(at))
    )
    active_assigned_branch_ids = set(
        BranchAssignment.objects.filter(
            membership=membership,
            branch_id__in=branch_grants.values("branch_id"),
        )
        .filter(current_interval(at))
        .values_list("branch_id", flat=True)
    )
    accountant_branch_ids = set(
        branch_grants.filter(
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch_id__in=active_assigned_branch_ids,
        ).values_list("branch_id", flat=True)
    )
    owner_branch_ids = set(
        branch_grants.filter(
            role=CompanyRoleGrant.Role.OWNER,
            branch_id__in=active_assigned_branch_ids,
        ).values_list("branch_id", flat=True)
    )
    accountant = (
        CompanyRoleGrant.Role.ACCOUNTANT in company_roles
        or bool(accountant_branch_ids)
    )
    owner = CompanyRoleGrant.Role.OWNER in company_roles or (
        bool(owner_branch_ids)
    )
    company_accountant = (
        CompanyRoleGrant.Role.ACCOUNTANT in company_roles
    )
    company_wide_reader = bool(
        company_roles
        & {CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT}
    )

    if not accountant and not owner:
        if action in READ_ACTIONS:
            raise NotFound("Company not found.")
        raise PermissionDenied("Accountant access required.")
    if action in READ_ACTIONS:
        allowed_branch_ids = active_assigned_branch_ids
    elif action == AccountingAction.MANAGE:
        if not company_accountant:
            raise PermissionDenied("Company Accountant access required.")
    elif action in {AccountingAction.POST, AccountingAction.CORRECT}:
        if not accountant:
            raise PermissionDenied("Accountant access required.")
    else:
        raise PermissionDenied("Unsupported Accounting action.")

    if action in WRITE_ACTIONS:
        allowed_branch_ids = accountant_branch_ids

    # Avoid unused role state while making the owner/read boundary explicit.
    if owner and not accountant and action not in READ_ACTIONS:
        raise PermissionDenied("Owner Accounting access is read-only.")

    return AccountingScope(
        actor=current_actor,
        company=company,
        membership=membership,
        action=action,
        is_company_accountant=company_accountant,
        is_company_wide_reader=company_wide_reader,
        allowed_branch_ids=frozenset(allowed_branch_ids),
    )


def lock_accounting_module_revision(scope):
    """Serialize an Accounting command with module-state transitions.

    Call only after entering ``transaction.atomic()`` and after locking the actor
    through the existing account lock helper. The Tenant lock is held until the
    surrounding transaction commits or rolls back.
    """
    if not connection.in_atomic_block:
        raise RuntimeError("Accounting module checks require transaction.atomic().")
    Tenant.objects.select_for_update().get(pk=scope.company.pk)
    return (
        CompanyModuleState.objects.filter(
            tenant_id=scope.company.pk,
            module_code=CompanyModuleCode.ACCOUNTING,
        )
        .order_by("-version", "-id")
        .first()
    )


def require_accounting_module_enabled(scope):
    """Require an enabled revision for a new root Accounting record."""
    if scope.action not in {AccountingAction.POST, AccountingAction.MANAGE}:
        raise PermissionDenied("This Accounting action does not create a new root record.")
    revision = (
        lock_accounting_module_revision(scope)
    )
    if revision is None or revision.state != CompanyModuleState.State.ENABLED:
        raise PermissionDenied("Accounting module is not enabled.")
    return revision
