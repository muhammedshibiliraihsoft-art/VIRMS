from django.db.models import Exists, OuterRef, Prefetch, Q
from django.utils import timezone

READ_ROLES = ("owner", "accountant", "media")


def current_interval(at=None):
    at = at or timezone.now()
    return Q(effective_from__lte=at) & (
        Q(effective_until__isnull=True) | Q(effective_until__gt=at)
    )


def visible_companies(user, at=None):
    """Return active Company metadata inside the user's current read grants."""
    from apps.accounts.models import CompanyRoleGrant, RoleAssignment, User
    from apps.tenants.models import BranchAssignment, Tenant, TenantMembership

    at = at or timezone.now()
    if not user.is_authenticated or not user.is_active or user.must_change_password:
        return Tenant.objects.none()
    platform = (
        RoleAssignment.objects.filter(
            user=user, user__account_kind=User.AccountKind.PLATFORM, role="back_office"
        )
        .filter(current_interval(at))
        .exists()
    )
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
    from apps.accounts.models import RoleAssignment, User
    from apps.tenants.models import Branch

    at = at or timezone.now()
    if not user.is_authenticated or not user.is_active or user.must_change_password:
        return Branch.objects.none()
    if not visible_companies(user, at).filter(pk=company_id).exists():
        return Branch.objects.none()
    platform = (
        RoleAssignment.objects.filter(
            user=user, user__account_kind=User.AccountKind.PLATFORM, role="back_office"
        )
        .filter(current_interval(at))
        .exists()
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


def company_context(user, at=None, *, limit=50):
    """Bounded self-context projection; it does not grant access by itself."""
    from apps.accounts.models import CompanyRoleGrant
    from apps.tenants.models import BranchAssignment, TenantMembership

    at = at or timezone.now()
    company_ids = list(
        visible_companies(user, at).values_list("pk", flat=True)[: limit + 1]
    )
    truncated = len(company_ids) > limit
    company_ids = company_ids[:limit]
    memberships = (
        TenantMembership.objects.filter(
            user=user, tenant_id__in=company_ids, tenant__is_active=True
        )
        .filter(current_interval(at))
        .select_related("tenant")
        .prefetch_related(
            Prefetch(
                "role_grants",
                queryset=CompanyRoleGrant.objects.filter(current_interval(at)),
            ),
            Prefetch(
                "branch_assignments",
                queryset=BranchAssignment.objects.filter(
                    current_interval(at)
                ).select_related("branch"),
            ),
        )
    )
    result = []
    for membership in memberships:
        grants = [
            grant
            for grant in membership.role_grants.all()
            if grant.effective_from <= at
            and (grant.effective_until is None or grant.effective_until > at)
        ]
        assignments = [
            row
            for row in membership.branch_assignments.all()
            if row.effective_from <= at
            and (row.effective_until is None or row.effective_until > at)
        ]
        granted_branch_ids = {grant.branch_id for grant in grants if grant.branch_id}
        company_wide = any(grant.branch_id is None for grant in grants)
        branches = [
            row.branch
            for row in assignments
            if company_wide or row.branch_id in granted_branch_ids
        ]
        result.append(
            {
                "id": str(membership.tenant_id),
                "name": membership.tenant.name,
                "roles": sorted({grant.role for grant in grants}),
                "branches": [
                    {"id": str(branch.pk), "name": branch.name}
                    for branch in sorted(
                        branches, key=lambda item: (item.name, str(item.pk))
                    )
                ],
            }
        )
    return result, truncated
