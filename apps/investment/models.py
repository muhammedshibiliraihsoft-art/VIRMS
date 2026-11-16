from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


class Investor(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investors"
    )
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investors_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investors_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(name__gt=""), name="investor_name_ck")
        ]
        indexes = [models.Index(fields=("tenant", "is_active", "name", "id"), name="investor_scope_idx")]

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor records are retained.")


class InvestorInterimConfiguration(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_interim_configurations"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="interim_configurations"
    )
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    effective_date = models.DateField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_interim_configs_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_interim_configurations",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=Decimal("0.00")),
                name="investor_interim_amount_ck",
            ),
            models.UniqueConstraint(
                fields=("investor", "effective_date"),
                name="investor_interim_effective_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_date", "id"),
                name="investor_interim_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Interim configurations are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Interim configurations are retained.")


class InvestorFundCredit(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_fund_credits"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="fund_credits"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="investor_fund_credits"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    reference = models.CharField(max_length=200)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_fund_credits_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_fund_credits",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")), name="investor_credit_amount_ck"
            ),
            models.CheckConstraint(
                condition=Q(reference__gt=""), name="investor_credit_reference_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_at", "id"),
                name="investor_credit_fifo_idx",
            ),
            models.Index(
                fields=("tenant", "branch", "investor", "effective_at", "id"),
                name="investor_credit_branch_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Fund credits are append-only.")
        self.reference = (self.reference or "").strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Fund credits are retained.")


class InvestorFundCreditCorrection(TimestampedUUIDModel):
    """Append-only correction to the Investor attribution of a confirmed Fund credit."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_fund_credit_corrections"
    )
    credit = models.ForeignKey(
        InvestorFundCredit, on_delete=models.PROTECT, related_name="attribution_corrections"
    )
    version = models.PositiveIntegerField()
    from_investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="fund_credit_corrections_from"
    )
    to_investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="fund_credit_corrections_to"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_fund_credit_corrections_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_fund_credit_corrections",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="invest_credit_corr_amount_ck",
            ),
            models.CheckConstraint(
                condition=~Q(from_investor=models.F("to_investor")),
                name="invest_credit_corr_diff_investor_ck",
            ),
            models.CheckConstraint(
                condition=Q(reason__gt=""), name="invest_credit_corr_reason_ck"
            ),
            models.UniqueConstraint(
                fields=("credit", "version"), name="invest_credit_corr_version_uq"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "credit", "version"),
                name="invest_credit_corr_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Fund credit corrections are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Fund credit corrections are retained.")


class InvestorPrincipalReturn(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_principal_returns"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="principal_returns"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="investor_principal_returns"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    reference = models.CharField(max_length=200)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_principal_returns_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_principal_returns",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")), name="investor_return_amount_ck"
            ),
            models.CheckConstraint(
                condition=Q(reference__gt=""), name="investor_return_reference_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_at", "id"),
                name="investor_return_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor principal returns are append-only.")
        self.reference = (self.reference or "").strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor principal returns are retained.")


class InvestorPrincipalReturnAllocation(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_return_allocations"
    )
    principal_return = models.ForeignKey(
        InvestorPrincipalReturn, on_delete=models.PROTECT, related_name="allocations"
    )
    credit = models.ForeignKey(
        InvestorFundCredit, on_delete=models.PROTECT, related_name="return_allocations"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_return_allocations_recorded",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")), name="investor_return_alloc_amount_ck"
            ),
            models.UniqueConstraint(
                fields=("principal_return", "credit"),
                name="investor_return_credit_uq",
            ),
        ]
        indexes = [models.Index(fields=("tenant", "credit"), name="investor_return_credit_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor return allocations are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor return allocations are retained.")


class InvestorFundUse(TimestampedUUIDModel):
    """Investor principal committed to one approved Vehicle source record."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_fund_uses"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="fund_uses"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="investor_fund_uses"
    )
    purchase = models.ForeignKey(
        "vehicles.VehiclePurchase",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fund_uses",
    )
    expense = models.ForeignKey(
        "vehicles.VehicleExpense",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fund_uses",
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_fund_uses_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_fund_uses",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="investor_fund_use_amount_ck"),
            models.CheckConstraint(
                condition=(
                    Q(purchase__isnull=False, expense__isnull=True)
                    | Q(purchase__isnull=True, expense__isnull=False)
                ),
                name="investor_fund_use_source_ck",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "investor", "effective_at", "id"), name="investor_fund_use_scope_idx")
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Fund uses are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Fund uses are retained.")


class InvestorFundUseAllocation(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_fund_use_allocations"
    )
    fund_use = models.ForeignKey(
        InvestorFundUse, on_delete=models.PROTECT, related_name="allocations"
    )
    credit = models.ForeignKey(
        InvestorFundCredit, on_delete=models.PROTECT, related_name="use_allocations"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_fund_use_allocations_recorded",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="investor_fund_use_alloc_amount_ck"),
            models.UniqueConstraint(fields=("fund_use", "credit"), name="investor_fund_use_credit_uq"),
        ]
        indexes = [
            models.Index(fields=("tenant", "credit"), name="investor_fund_use_credit_idx")
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Fund use allocations are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Fund use allocations are retained.")


class InvestorFundUseAdjustment(TimestampedUUIDModel):
    """Append-only credit-lot changes caused by an approved Vehicle cost correction."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_fund_use_adjustments"
    )
    credit = models.ForeignKey(
        InvestorFundCredit, on_delete=models.PROTECT, related_name="use_adjustments"
    )
    purchase_correction = models.ForeignKey(
        "vehicles.VehiclePurchaseCorrection",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fund_use_adjustments",
    )
    expense_correction = models.ForeignKey(
        "vehicles.VehicleExpenseCorrection",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="fund_use_adjustments",
    )
    amount_delta = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investor_fund_use_adjustments_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="investor_fund_use_adjustments",
    )
    effective_at = models.DateTimeField()
    reason = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(purchase_correction__isnull=False, expense_correction__isnull=True)
                    | Q(purchase_correction__isnull=True, expense_correction__isnull=False)
                ),
                name="invest_use_adj_source_ck",
            ),
            models.CheckConstraint(
                condition=~Q(amount_delta=Decimal("0.00")),
                name="invest_use_adj_nonzero_ck",
            ),
            models.CheckConstraint(condition=Q(reason__gt=""), name="invest_use_adj_reason_ck"),
            models.UniqueConstraint(
                fields=("purchase_correction", "credit"),
                condition=Q(purchase_correction__isnull=False),
                name="invest_use_adj_purchase_credit_uq",
            ),
            models.UniqueConstraint(
                fields=("expense_correction", "credit"),
                condition=Q(expense_correction__isnull=False),
                name="invest_use_adj_expense_credit_uq",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "credit", "effective_at", "id"), name="invest_use_adj_credit_idx")
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Fund use adjustments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Fund use adjustments are retained.")


class InvestmentIdempotencyRecord(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investment_idempotency"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="investment_idempotency_records",
    )
    key = models.CharField(max_length=128)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=240)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    completed_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "actor", "key"), name="invest_idem_scope_key_uq"
            ),
            models.CheckConstraint(
                condition=Q(method__in=("POST", "PATCH")), name="invest_idem_method_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "actor", "created_at"), name="invest_idem_actor_idx"
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investment idempotency results are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investment idempotency results are retained.")
