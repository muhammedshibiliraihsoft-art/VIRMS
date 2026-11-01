"""Company scope for Django Admin command adapters.

Superuser status alone never exposes Company records. The actor needs an active
Platform account, an active back-office assignment and a current membership in
each Company shown by these adapters.
"""

from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.accounts.models import RoleAssignment, User
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.selectors import current_interval


def is_platform_admin_actor(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and user.is_active
        and user.is_staff
        and user.is_superuser
        and not user.must_change_password
        and user.account_kind == User.AccountKind.PLATFORM
        and RoleAssignment.objects.filter(
            user=user, role=RoleAssignment.Role.BACK_OFFICE
        )
        .filter(current_interval())
        .exists()
    )


def managed_companies(user):
    if not is_platform_admin_actor(user):
        return Tenant.objects.none()
    at = timezone.now()
    membership = TenantMembership.objects.filter(
        user=user, tenant_id=OuterRef("pk")
    ).filter(current_interval(at))
    return Tenant.objects.annotate(_managed=Exists(membership)).filter(_managed=True)
