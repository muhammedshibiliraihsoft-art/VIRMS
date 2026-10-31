from django.db import models
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


class Tenant(TimestampedUUIDModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TenantMembership(TimestampedUUIDModel):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="tenant_memberships"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name="memberships"
    )
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="assigned_memberships"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(effective_until__isnull=True)
                | models.Q(effective_until__gt=models.F("effective_from")),
                name="membership_valid_interval",
            ),
            models.UniqueConstraint(
                fields=["user", "tenant"],
                condition=models.Q(effective_until__isnull=True),
                name="one_open_tenant_membership",
            ),
        ]
