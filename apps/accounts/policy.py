"""Authoritative new scoped policy; legacy route readers cut over only in P1-17."""

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from apps.tenants.models import BranchAssignment, TenantMembership
from apps.tenants.selectors import current_interval

from .models import CompanyRoleGrant, User
from .platform_identity import is_platform_actor

PLATFORM_ACTIONS = {
    "company.create",
    "company.rename",
    "company.suspend",
    "company.activate",
    "module.configure",
    "branch.create",
    "branch.rename",
    "membership.add",
    "membership.end",
    "role.add",
    "role.end",
    "assignment.add",
    "assignment.end",
    "account.provision.owner",
    "account.provision.accountant",
    "account.reset.owner",
    "account.reset.accountant",
    "account.status.owner",
    "account.status.accountant",
    "account.revoke.owner",
    "account.revoke.accountant",
}
PLATFORM_SCOPED_LIFECYCLE_ACTIONS = {
    f"account.{verb}.{role}"
    for verb in ("reset", "status", "revoke")
    for role in ("investor", "media")
}
READ_ACTIONS = {"core.company.read", "core.branch.read"}
SELF_ACTIONS = {"self.password", "self.me", "self.logout"}
ACCOUNTING_READ_ACTIONS = {
    "accounting.event.read",
    "accounting.report.read",
}
ACCOUNTING_WRITE_ACTIONS = {
    "accounting.income.create",
    "accounting.expense.create",
    "accounting.receipt.create",
    "accounting.payment.create",
    "accounting.event.correct",
    "accounting.account.manage",
    "accounting.category.manage",
    "accounting.opening_balance.create",
    "accounting.transfer.create",
}
ACCOUNTING_COMPANY_ONLY_ACTIONS = {
    "accounting.account.manage",
    "accounting.category.manage",
    "accounting.opening_balance.create",
    "accounting.transfer.create",
}
ACCOUNTING_ACTIONS = ACCOUNTING_READ_ACTIONS | ACCOUNTING_WRITE_ACTIONS
BUSINESS_READ_ACTIONS = {
    "investment.profile.read",
    "investment.interim.read",
    "investment.fund.read",
    "vehicle.read",
    "garage.job.read",
    "labour.person.read",
}
BUSINESS_WRITE_ACTIONS = {
    "investment.profile.manage",
    "investment.interim.manage",
    "investment.fund.credit",
    "investment.fund.credit.correct",
    "investment.fund.return",
    "investment.fund.use",
    "vehicle.create",
    "garage.job.create",
    "garage.job.status",
    "garage.work.create",
    "garage.cost.link",
    "garage.charge.record",
    "garage.receipt.record",
    "garage.receipt.correct",
    "garage.customer_cost.create",
    "garage.customer_cost.correct",
    "garage.customer_cost.payment",
    "garage.customer_cost.payment.correct",
    "garage.customer_cost.refund",
    "labour.person.create",
    "labour.person.update",
    "labour.person.status",
    "labour.payment.create",
    "labour.payment.correct",
    "vehicle.edit",
    "vehicle.branch.move",
    "vehicle.purchase.create",
    "vehicle.purchase.pay",
    "vehicle.expense.create",
    "vehicle.expense.pay",
    "vehicle.expense.refund",
    "vehicle.expense.fund",
    "vehicle.purchase.refund",
    "vehicle.purchase.correct",
    "vehicle.expense.correct",
    "vehicle.sale.create",
    "vehicle.sale.receipt",
    "vehicle.sale.refund",
    "vehicle.sale.correct",
}
BUSINESS_COMPANY_ONLY_ACTIONS = {
    "investment.interim.manage",
    "investment.fund.use",
    "vehicle.branch.move",
    "vehicle.expense.fund",
    "vehicle.purchase.correct",
}
BUSINESS_ACTIONS = BUSINESS_READ_ACTIONS | BUSINESS_WRITE_ACTIONS


def require_action(
    actor, action, *, company=None, branch=None, resource=None, module=None, fields=None
):
    def deny():
        raise PermissionDenied("Not authorized")

    if not getattr(actor, "is_authenticated", False):
        deny()
    current = User.objects.filter(pk=actor.pk, is_active=True).first()
    if current is None or module is not None or fields:
        deny()
    if action in SELF_ACTIONS:
        if resource is not None and resource.pk != current.pk:
            deny()
        return current
    if current.must_change_password:
        deny()
    platform = is_platform_actor(current)
    if current.account_kind == User.AccountKind.PLATFORM and not platform:
        deny()
    if action == "company.create":
        if not platform or company is not None or branch is not None:
            deny()
        return current
    if company is None:
        deny()
    # Refresh Company state; a stale caller object cannot bypass suspension.
    from apps.tenants.models import Tenant

    company = Tenant.objects.filter(pk=company.pk).first()
    if company is None or (not company.is_active and action != "company.activate"):
        deny()
    membership = (
        TenantMembership.objects.filter(user=current, tenant=company)
        .filter(current_interval())
        .first()
    )
    if membership is None or (branch is not None and branch.tenant_id != company.pk):
        deny()
    if resource is not None:
        scope = (
            resource.pk
            if isinstance(resource, Tenant)
            else getattr(resource, "tenant_id", None)
        )
        if scope is None and hasattr(resource, "membership_id"):
            scope = resource.membership.tenant_id
        if scope != company.pk:
            if action in ACCOUNTING_ACTIONS:
                raise Http404("Not found")
            deny()
        from apps.tenants.models import Branch

        resource_branch = (
            resource.pk
            if isinstance(resource, Branch)
            else getattr(resource, "branch_id", None)
        )
        if action not in ACCOUNTING_ACTIONS and resource_branch is not None and (
            branch is None or branch.pk != resource_branch
        ):
            deny()
    if action in ACCOUNTING_ACTIONS:
        return _require_accounting_action(
            current,
            membership=membership,
            company=company,
            action=action,
            branch=branch,
            resource=resource,
        )
    if action in BUSINESS_ACTIONS:
        return _require_business_action(
            current,
            membership=membership,
            company=company,
            action=action,
            branch=branch,
        )
    if action in PLATFORM_ACTIONS:
        if not platform:
            deny()
        return current
    if action in PLATFORM_SCOPED_LIFECYCLE_ACTIONS and platform:
        # Back Office lifecycle authority remains constrained to the single
        # current Company membership and exact target resolved by the caller.
        return current
    if action not in READ_ACTIONS | {
        "account.provision.investor",
        "account.provision.media",
    }:
        deny()
    if platform and action == "core.company.read":
        return current  # Only minimal Company context, never business/financial data.
    roles = (
        {"owner", "accountant", "media"} if action in READ_ACTIONS else {"accountant"}
    )
    grants = CompanyRoleGrant.objects.filter(
        membership=membership, role__in=roles
    ).filter(current_interval())
    if branch is None:
        grants = grants.filter(branch__isnull=True)
    else:
        if (
            not BranchAssignment.objects.filter(membership=membership, branch=branch)
            .filter(current_interval())
            .exists()
        ):
            deny()
        from django.db.models import Q

        grants = grants.filter(Q(branch__isnull=True) | Q(branch=branch))
    if not grants.exists():
        deny()
    return current


def _require_accounting_action(
    current, *, membership, company, action, branch, resource
):
    """Apply the finite Accounting action allowlist without changing other modules."""
    from apps.tenants.models import BranchAssignment

    if current.account_kind != User.AccountKind.COMPANY:
        raise PermissionDenied("Accounting access required.")

    at = timezone.now()
    grants = CompanyRoleGrant.objects.filter(
        membership=membership,
        role__in=(CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT),
    ).filter(current_interval(at))
    company_grants = grants.filter(branch__isnull=True)
    company_accountant = company_grants.filter(
        role=CompanyRoleGrant.Role.ACCOUNTANT
    ).exists()

    if action in ACCOUNTING_READ_ACTIONS:
        eligible_roles = {CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT}
    else:
        eligible_roles = {CompanyRoleGrant.Role.ACCOUNTANT}
        if action in ACCOUNTING_COMPANY_ONLY_ACTIONS and not company_accountant:
            raise PermissionDenied("Company Accountant access required.")

    if company_grants.filter(role__in=eligible_roles).exists():
        return current
    target_branch_ids = set()
    if branch is not None:
        if branch.tenant_id != company.pk:
            raise Http404("Branch not found")
        target_branch_ids.add(branch.pk)
    if resource is not None:
        resource_branch_id = getattr(resource, "branch_id", None)
        if resource_branch_id is not None:
            target_branch_ids.add(resource_branch_id)
    if not target_branch_ids:
        # A branch-only actor may list their own records without a filter;
        # the request handler must apply the returned Branch scope.
        branch_grants = grants.filter(
            branch__tenant=company,
            role__in=eligible_roles,
        )
        assigned = BranchAssignment.objects.filter(
            membership=membership,
            branch_id__in=branch_grants.values("branch_id"),
        ).filter(current_interval(at))
        if branch_grants.exists() and assigned.exists():
            return current
        raise PermissionDenied("Accounting access required.")
    has_action_scope = grants.filter(
        role__in=eligible_roles,
        branch__tenant=company,
    ).exists()
    if not has_action_scope:
        raise PermissionDenied("Accounting access required.")
    for branch_id in target_branch_ids:
        branch_grants = grants.filter(
            branch_id=branch_id,
            role__in=eligible_roles,
        )
        if not branch_grants.exists() or not BranchAssignment.objects.filter(
            membership=membership,
            branch_id=branch_id,
        ).filter(current_interval(at)).exists():
            raise Http404("Branch not found")
    return current


def _require_business_action(current, *, membership, company, action, branch):
    """Apply explicit read/write rules for the Phase 5 domain APIs."""
    from apps.tenants.models import BranchAssignment

    if current.account_kind != User.AccountKind.COMPANY:
        raise PermissionDenied("Company business access required.")
    at = timezone.now()
    grants = CompanyRoleGrant.objects.filter(
        membership=membership,
        role__in=(CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT),
    ).filter(current_interval(at))
    company_accountant = grants.filter(
        role=CompanyRoleGrant.Role.ACCOUNTANT, branch__isnull=True
    ).exists()
    allowed_roles = (
        (CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT)
        if action in BUSINESS_READ_ACTIONS
        else (CompanyRoleGrant.Role.ACCOUNTANT,)
    )
    if action in BUSINESS_COMPANY_ONLY_ACTIONS and not company_accountant:
        raise PermissionDenied("Company-level Accountant access required.")

    if branch is None:
        if grants.filter(role__in=allowed_roles, branch__isnull=True).exists():
            return current
        branch_grants = grants.filter(
            role__in=allowed_roles, branch__tenant=company, branch__isnull=False
        )
        assigned = BranchAssignment.objects.filter(
            membership=membership,
            branch_id__in=branch_grants.values("branch_id"),
        ).filter(current_interval(at))
        if branch_grants.exists() and assigned.exists():
            return current
        raise PermissionDenied("Company business access required.")

    if branch.tenant_id != company.pk:
        raise PermissionDenied("Branch not found.")
    if grants.filter(
        role__in=allowed_roles, branch__isnull=True
    ).exists():
        return current
    if not grants.filter(role__in=allowed_roles, branch=branch).exists() or not (
        BranchAssignment.objects.filter(membership=membership, branch=branch)
        .filter(current_interval(at))
        .exists()
    ):
        raise PermissionDenied("Branch access required.")
    return current
