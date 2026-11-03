from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


COMPANY_MODULE_STATES = ("enabled", "disabled")


class CompanyModuleCode(models.TextChoices):
    ACCOUNTING = "accounting", "Accounting"
    INVESTMENT = "investment", "Investment"
    GARAGE = "garage", "Garage"
    INVESTOR_PORTAL = "investor_portal", "Investor Portal"
    VEHICLE_MANAGEMENT = "vehicle_management", "Vehicle Management"
    VEHICLE_EXPENSE_MANAGEMENT = (
        "vehicle_expense_management",
        "Vehicle Expense Management",
    )
    SALES_RECEIVABLES = "sales_receivables", "Sales and Receivables"
    MEDIA_VEHICLE_PUBLICATION = (
        "media_vehicle_publication",
        "Media / Vehicle Publication",
    )
    PUBLIC_VEHICLE_ACCESS = "public_vehicle_access", "Public Vehicle Access"
    LABOUR = "labour", "Labour"
    REPORTS_DASHBOARD = "reports_dashboard", "Reports and Dashboard"
    AUDIT_CORRECTIONS = "audit_corrections", "Audit and Corrections"
    GST_TAX_INVOICE = "gst_tax_invoice", "GST / Tax / Invoice capability"
    OWNER_AI_ASSISTANT = "owner_ai_assistant", "Owner AI Assistant"


class CompanyModuleState(TimestampedUUIDModel):
    class State(models.TextChoices):
        ENABLED = "enabled", "Enabled"
        DISABLED = "disabled", "Disabled"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="module_states",
    )
    module_code = models.CharField(max_length=40, choices=CompanyModuleCode.choices)
    state = models.CharField(max_length=8, choices=State.choices)
    version = models.PositiveIntegerField()
    effective_from = models.DateTimeField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="company_module_state_changes",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "module_code", "version"],
                name="company_module_rev_unique",
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1),
                name="company_module_rev_version_ck",
            ),
            models.CheckConstraint(
                condition=Q(module_code__in=CompanyModuleCode.values),
                name="company_module_rev_code_ck",
            ),
            models.CheckConstraint(
                condition=Q(state__in=COMPANY_MODULE_STATES),
                name="company_module_rev_state_ck",
            ),
        ]
        ordering = ["tenant_id", "module_code", "version"]

    def clean(self):
        super().clean()
        if self.effective_from and not timezone.is_aware(self.effective_from):
            raise ValidationError({"effective_from": "An aware timestamp is required."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Company module-state revisions are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Company module-state revisions cannot be deleted.")

    def __str__(self):
        return f"{self.tenant_id}:{self.module_code}@{self.version}={self.state}"
