from dataclasses import dataclass

from apps.accounts.models import CompanyRoleGrant
from apps.tenants.models import BranchAssignment
from apps.tenants.selectors import current_interval


@dataclass(frozen=True)
class BusinessScope:
    is_company_accountant: bool
    is_company_owner: bool
    allowed_branch_ids: frozenset

    @property
    def is_company_reader(self):
        return self.is_company_accountant or self.is_company_owner


def business_scope(*, actor, company):
    """Resolve authorized Phase 5 Branch visibility from current server grants.

    Call only after `accounts.policy.require_action` has validated active
    membership and the requested domain action.
    """
    membership = actor.tenant_memberships.filter(tenant=company).filter(
        current_interval()
    ).first()
    if membership is None:
        return BusinessScope(False, False, frozenset())
    grants = CompanyRoleGrant.objects.filter(
        membership=membership,
        role__in=(CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT),
    ).filter(current_interval())
    company_roles = set(
        grants.filter(branch__isnull=True).values_list("role", flat=True)
    )
    branch_grants = grants.filter(branch__tenant=company, branch__isnull=False)
    assigned_ids = BranchAssignment.objects.filter(
        membership=membership, branch_id__in=branch_grants.values("branch_id")
    ).filter(current_interval()).values_list("branch_id", flat=True)
    return BusinessScope(
        is_company_accountant=CompanyRoleGrant.Role.ACCOUNTANT in company_roles,
        is_company_owner=CompanyRoleGrant.Role.OWNER in company_roles,
        allowed_branch_ids=frozenset(assigned_ids),
    )
