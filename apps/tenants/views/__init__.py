from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone

from apps.accounts.access import active_roles
from apps.accounts.models import RoleAssignment
from apps.tenants.models import Tenant
from apps.tenants.serializers import TenantSummarySerializer


class TenantScopeMixin:
    serializer_class = TenantSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        allowed_roles = {
            RoleAssignment.Role.OWNER,
            RoleAssignment.Role.ACCOUNTANT,
            RoleAssignment.Role.MEDIA,
            RoleAssignment.Role.BACK_OFFICE,
        }
        if not active_roles(self.request.user).intersection(allowed_roles):
            return Tenant.objects.none()
        now = timezone.now()
        return (
            Tenant.objects.filter(
                is_active=True,
                memberships__user=self.request.user,
                memberships__effective_from__lte=now,
                memberships__effective_until__isnull=True,
            )
            .distinct()
            .order_by("name", "id")
        )


class TenantList(TenantScopeMixin, ListAPIView):
    pass


class TenantDetail(TenantScopeMixin, RetrieveAPIView):
    pass
