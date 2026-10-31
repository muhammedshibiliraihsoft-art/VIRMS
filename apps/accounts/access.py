from django.utils import timezone

from apps.accounts.models import RoleAssignment
from apps.tenants.models import TenantMembership


def active_roles(user):
    if not user.is_authenticated or not user.is_active:
        return set()
    now = timezone.now()
    return set(
        RoleAssignment.objects.filter(
            user=user, effective_from__lte=now, effective_until__isnull=True
        ).values_list("role", flat=True)
    )


def active_tenant_ids(user):
    if not user.is_authenticated or not user.is_active:
        return set()
    now = timezone.now()
    return set(
        TenantMembership.objects.filter(
            user=user,
            tenant__is_active=True,
            effective_from__lte=now,
            effective_until__isnull=True,
        ).values_list("tenant_id", flat=True)
    )
