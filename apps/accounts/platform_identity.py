"""Fail-closed predicates for explicit technical Platform identities."""

from django.db.models import Q
from django.utils import timezone

from .models import CompanyRoleGrant, RoleAssignment, User


def has_company_business_history(user_or_id):
    user_id = getattr(user_or_id, "pk", user_or_id)
    return (
        RoleAssignment.objects.filter(user_id=user_id)
        .exclude(role=RoleAssignment.Role.BACK_OFFICE)
        .exists()
        or CompanyRoleGrant.objects.filter(membership__user_id=user_id).exists()
    )


def is_platform_identity_candidate(user):
    """Return true only for an explicitly classified Platform account with no business history."""
    return (
        user is not None
        and user.account_kind == User.AccountKind.PLATFORM
        and not has_company_business_history(user.pk)
    )


def is_platform_actor(user, at=None):
    """Require a current Back Office role and no legacy Company role/grant history."""
    if not is_platform_identity_candidate(user):
        return False
    at = at or timezone.now()
    return (
        RoleAssignment.objects.filter(
            user_id=user.pk,
            role=RoleAssignment.Role.BACK_OFFICE,
            effective_from__lte=at,
        )
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gt=at))
        .exists()
    )
