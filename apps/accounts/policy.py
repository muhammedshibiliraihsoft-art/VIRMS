"""Authoritative new scoped policy; legacy route readers cut over only in P1-17."""

from django.core.exceptions import PermissionDenied

from apps.tenants.models import BranchAssignment, TenantMembership
from apps.tenants.selectors import current_interval

from .models import CompanyRoleGrant, RoleAssignment, User

PLATFORM_ACTIONS = {
    "company.create",
    "company.rename",
    "company.suspend",
    "company.activate",
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
COMPANY_ACCOUNT_ACTIONS = {
    f"account.{verb}.{role}"
    for verb in ("reset", "status", "revoke")
    for role in ("investor", "media")
}
READ_ACTIONS = {"core.company.read", "core.branch.read"}
SELF_ACTIONS = {"self.password", "self.me", "self.logout"}


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
    platform = (
        current.account_kind == User.AccountKind.PLATFORM
        and RoleAssignment.objects.filter(user=current, role="back_office")
        .filter(current_interval())
        .exists()
    )
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
            deny()
        from apps.tenants.models import Branch

        resource_branch = (
            resource.pk
            if isinstance(resource, Branch)
            else getattr(resource, "branch_id", None)
        )
        if resource_branch is not None and (
            branch is None or branch.pk != resource_branch
        ):
            deny()
    if action in PLATFORM_ACTIONS:
        if not platform:
            deny()
        return current
    if action in PLATFORM_SCOPED_LIFECYCLE_ACTIONS and platform:
        # Back Office lifecycle authority remains constrained to the single
        # current Company membership and exact target resolved by the caller.
        return current
    if (
        action
        not in READ_ACTIONS
        | {
            "account.provision.investor",
            "account.provision.media",
        }
        | COMPANY_ACCOUNT_ACTIONS
    ):
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
