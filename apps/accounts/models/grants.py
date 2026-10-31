from django.db import models
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


class CompanyRoleGrant(TimestampedUUIDModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ACCOUNTANT = "accountant", "Accountant / Operations"
        INVESTOR = "investor", "Investor"
        MEDIA = "media", "Media"

    membership = models.ForeignKey(
        "tenants.TenantMembership", on_delete=models.PROTECT, related_name="role_grants"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    branch = models.ForeignKey(
        "tenants.Branch", null=True, blank=True, on_delete=models.PROTECT
    )
    assigned_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    role__in=["owner", "accountant", "investor", "media"]
                ),
                name="company_role_known",
            ),
            models.CheckConstraint(
                condition=models.Q(effective_until__isnull=True)
                | models.Q(effective_until__gt=models.F("effective_from")),
                name="company_role_interval",
            ),
            models.UniqueConstraint(
                fields=["membership", "role"],
                condition=models.Q(effective_until__isnull=True, branch__isnull=True),
                name="one_open_company_role",
            ),
            models.UniqueConstraint(
                fields=["membership", "role", "branch"],
                condition=models.Q(effective_until__isnull=True, branch__isnull=False),
                name="one_open_branch_role",
            ),
        ]
