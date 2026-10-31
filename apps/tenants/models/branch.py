from django.db import models
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


class Branch(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="branches"
    )
    name = models.CharField(max_length=100)


class BranchAssignment(TimestampedUUIDModel):
    membership = models.ForeignKey(
        "tenants.TenantMembership",
        on_delete=models.PROTECT,
        related_name="branch_assignments",
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="assignments"
    )
    assigned_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(effective_until__isnull=True)
                | models.Q(effective_until__gt=models.F("effective_from")),
                name="branch_assignment_interval",
            ),
            models.UniqueConstraint(
                fields=["membership", "branch"],
                condition=models.Q(effective_until__isnull=True),
                name="one_open_branch_assignment",
            ),
        ]
