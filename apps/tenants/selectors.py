from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.utils import timezone

from apps.accounts.platform_identity import is_platform_actor

READ_ROLES = ("owner", "accountant", "media")
# Self context describes the caller's own scope; it does not grant core reads.
CONTEXT_ROLES = (*READ_ROLES, "investor")


def current_interval(at=None):
    at = at or timezone.now()
    return Q(effective_from__lte=at) & (
        Q(effective_until__isnull=True) | Q(effective_until__gt=at)
    )


def visible_companies(user, at=None):
    """Return active Company metadata inside the user's current read grants."""
    from apps.accounts.models import CompanyRoleGrant, User
    from apps.tenants.models import BranchAssignment, Tenant, TenantMembership

    at = at or timezone.now()
    if not user.is_authenticated or not user.is_active or user.must_change_password:
        return Tenant.objects.none()
    platform = user.account_kind == User.AccountKind.PLATFORM
    if platform and not is_platform_actor(user, at):
        return Tenant.objects.none()
    membership = TenantMembership.objects.filter(
        user=user, tenant_id=OuterRef("pk"), tenant__is_active=True
    ).filter(current_interval(at))
    if not platform:
        assignment = BranchAssignment.objects.filter(
            membership_id=OuterRef("membership_id"), branch_id=OuterRef("branch_id")
        ).filter(current_interval(at))
        grant = (
            CompanyRoleGrant.objects.filter(
                membership_id=OuterRef("pk"), role__in=READ_ROLES
            )
            .filter(current_interval(at))
            .annotate(_assigned=Exists(assignment))
            .filter(Q(branch__isnull=True) | Q(_assigned=True))
        )
        membership = membership.annotate(_readable=Exists(grant)).filter(_readable=True)
    return (
        Tenant.objects.filter(is_active=True)
        .annotate(_member=Exists(membership))
        .filter(_member=True)
        .order_by("name", "id")
    )


def visible_branches(user, company_id, at=None):
    """Return assigned Branches with an effective matching Company read grant."""
    from apps.accounts.models import User
    from apps.tenants.models import Branch

    at = at or timezone.now()
    if not user.is_authenticated or not user.is_active or user.must_change_password:
        return Branch.objects.none()
    if not visible_companies(user, at).filter(pk=company_id).exists():
        return Branch.objects.none()
    platform = user.account_kind == User.AccountKind.PLATFORM and is_platform_actor(
        user, at
    )
    from apps.accounts.models import CompanyRoleGrant
    from apps.tenants.models import BranchAssignment

    grant = (
        CompanyRoleGrant.objects.filter(
            membership_id=OuterRef("membership_id"), role__in=READ_ROLES
        )
        .filter(current_interval(at))
        .filter(Q(branch__isnull=True) | Q(branch_id=OuterRef("branch_id")))
    )
    assignment = (
        BranchAssignment.objects.filter(
            branch_id=OuterRef("pk"),
            membership__user=user,
            membership__tenant_id=company_id,
            membership__effective_from__lte=at,
        )
        .filter(current_interval(at))
        .filter(
            Q(membership__effective_until__isnull=True)
            | Q(membership__effective_until__gt=at)
        )
    )
    if not platform:
        assignment = assignment.annotate(_granted=Exists(grant)).filter(_granted=True)
    return (
        Branch.objects.filter(tenant_id=company_id)
        .annotate(_visible=Exists(assignment))
        .filter(_visible=True)
        .order_by("name", "id")
    )


def company_context(user, at=None, *, limit=50, branch_limit=20):
    """Bounded self-context projection; it does not grant access by itself."""
    from apps.accounts.models import CompanyRoleGrant, User
    from apps.tenants.models import BranchAssignment, Tenant, TenantMembership

    at = at or timezone.now()
    if not user.is_authenticated or not user.is_active or user.must_change_password:
        return [], False
    platform = user.account_kind == User.AccountKind.PLATFORM
    if platform and not is_platform_actor(user, at):
        return [], False

    effective_assignment = BranchAssignment.objects.filter(
        membership_id=OuterRef("membership_id"), branch_id=OuterRef("branch_id")
    ).filter(current_interval(at))
    context_grants = (
        CompanyRoleGrant.objects.filter(role__in=CONTEXT_ROLES)
        .filter(current_interval(at))
        .annotate(_assigned=Exists(effective_assignment))
        .filter(Q(branch__isnull=True) | Q(_assigned=True))
    )
    context_membership = TenantMembership.objects.filter(
        user=user, tenant_id=OuterRef("pk")
    ).filter(current_interval(at))
    if not platform:
        context_membership = context_membership.annotate(
            _has_context=Exists(context_grants.filter(membership_id=OuterRef("pk")))
        ).filter(_has_context=True)
    company_ids = list(
        Tenant.objects.filter(is_active=True)
        .annotate(_member=Exists(context_membership))
        .filter(_member=True)
        .order_by("name", "id")
        .values_list("pk", flat=True)[: limit + 1]
    )
    truncated = len(company_ids) > limit
    company_ids = company_ids[:limit]
    context_grant = (
        CompanyRoleGrant.objects.filter(
            membership_id=OuterRef("membership_id"), role__in=CONTEXT_ROLES
        )
        .filter(current_interval(at))
        .filter(Q(branch__isnull=True) | Q(branch_id=OuterRef("branch_id")))
    )
    assignments = BranchAssignment.objects.filter(current_interval(at))
    if not platform:
        assignments = assignments.annotate(_granted=Exists(context_grant)).filter(
            _granted=True
        )
    branch_roles = context_grant.order_by("role").values("role").distinct()
    assignments = (
        assignments.annotate(_context_roles=ArraySubquery(branch_roles))
        .select_related("branch")
        .order_by("branch__name", "branch_id", "id")
    )
    role_summary = context_grants.order_by("membership_id", "role").distinct(
        "membership_id", "role"
    )
    company_wide_roles = (
        CompanyRoleGrant.objects.filter(
            membership_id=OuterRef("pk"), branch__isnull=True, role__in=CONTEXT_ROLES
        )
        .filter(current_interval(at))
        .order_by("role")
        .values("role")
        .distinct()
    )
    memberships = (
        TenantMembership.objects.filter(
            user=user, tenant_id__in=company_ids, tenant__is_active=True
        )
        .filter(current_interval(at))
        .annotate(_company_wide_roles=ArraySubquery(company_wide_roles))
        .select_related("tenant")
        .prefetch_related(
            Prefetch("role_grants", queryset=role_summary, to_attr="context_roles"),
            Prefetch(
                "branch_assignments",
                queryset=assignments[: branch_limit + 1],
                to_attr="context_branches",
            ),
        )
        .order_by("tenant__name", "tenant_id", "id")[: limit + 1]
    )
    memberships = list(memberships)
    truncated = truncated or len(memberships) > limit
    memberships = memberships[:limit]
    result = []
    for membership in memberships:
        roles = sorted({row.role for row in membership.context_roles})
        rows = list(membership.context_branches)
        branches_truncated = len(rows) > branch_limit
        branches = []
        seen = set()
        for row in rows[:branch_limit]:
            if row.branch_id not in seen:
                branches.append(
                    {
                        "id": str(row.branch_id),
                        "name": row.branch.name,
                        "roles": sorted(set(row._context_roles)),
                    }
                )
                seen.add(row.branch_id)
        result.append(
            {
                "id": str(membership.tenant_id),
                "name": membership.tenant.name,
                "roles": roles,
                "company_wide_roles": sorted(set(membership._company_wide_roles)),
                "branches_truncated": branches_truncated,
                "branches": sorted(
                    branches, key=lambda item: (item["name"], item["id"])
                ),
            }
        )
    return result, truncated
