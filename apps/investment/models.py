from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
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


class InvestorProfitShareAgreement(TimestampedUUIDModel):
    """Protected, effective-dated Investor share terms set by Platform Back Office."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_profit_share_agreements"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="profit_share_agreements"
    )
    share_percentage = models.DecimalField(max_digits=7, decimal_places=4)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_profit_share_agreements_recorded",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(share_percentage__gte=Decimal("0.0000"))
                & Q(share_percentage__lte=Decimal("100.0000")),
                name="invest_profit_share_range_ck",
            ),
            models.UniqueConstraint(
                fields=("investor", "effective_at"),
                name="invest_profit_share_effective_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_at", "id"),
                name="invest_profit_share_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Profit share agreements are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Profit share agreements are retained.")


class InvestorAccountBinding(TimestampedUUIDModel):
    """Audited temporal ownership link for the Investor self-service portal."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_account_bindings"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="account_bindings"
    )
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_bindings"
    )
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)
    bound_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_bindings_created"
    )
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="investor_bindings_ended",
    )
    end_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(effective_until__isnull=True) | Q(effective_until__gt=models.F("effective_from")),
                name="invest_binding_interval_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "account"), condition=Q(effective_until__isnull=True),
                name="invest_binding_open_account_uq",
            ),
            models.UniqueConstraint(
                fields=("investor",), condition=Q(effective_until__isnull=True),
                name="invest_binding_open_investor_uq",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "account", "effective_until"), name="invest_binding_self_idx")
        ]

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor account bindings are retained.")


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


class InvestorInterimPayment(TimestampedUUIDModel):
    """One immutable actual Monthly Interim payment and its Cash/Bank source."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT,
        related_name="investor_interim_payments",
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="interim_payments"
    )
    configuration = models.ForeignKey(
        InvestorInterimConfiguration, on_delete=models.PROTECT,
        related_name="payments",
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT,
        related_name="investor_interim_payments",
    )
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT,
        related_name="investor_interim_payments",
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    period_month = models.DateField()
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_interim_payments_recorded",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_interim_payments",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_interim_payment_accounting_revisions",
    )
    description = models.CharField(max_length=500)
    source_reference = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="invest_interim_payment_amount_ck",
            ),
            models.CheckConstraint(
                condition=Q(description__gt="") & Q(source_reference__gt=""),
                name="invest_interim_payment_source_ck",
            ),
            models.CheckConstraint(
                condition=Q(period_month__day=1),
                name="invest_interim_payment_month_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "period_month", "effective_at", "id"),
                name="invest_interim_month_idx",
            ),
            models.Index(
                fields=("tenant", "branch", "investor", "period_month", "effective_at"),
                name="invest_interim_branch_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.description = (self.description or "").strip()
        self.source_reference = (self.source_reference or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Interim payments are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Interim payments are retained.")


class InvestorProfitCalendarConfiguration(TimestampedUUIDModel):
    """Append-only Investor-specific Profit period calendar version."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT,
        related_name="investor_profit_calendars",
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="profit_calendars"
    )
    effective_start = models.DateField()
    duration_months = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_profit_calendars_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_calendars",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(duration_months__gt=0), name="invest_profit_cal_duration_ck"
            ),
            models.CheckConstraint(
                condition=Q(version__gt=0), name="invest_profit_cal_version_ck"
            ),
            models.UniqueConstraint(
                fields=("investor", "effective_start", "version"),
                name="invest_profit_cal_version_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_start", "version"),
                name="invest_profit_cal_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Profit calendar versions are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Profit calendar versions are retained.")


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


class VehicleCapitalRecovery(TimestampedUUIDModel):
    """Confirmed classification of existing Buyer cash, never a cash event."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_capital_recoveries")
    sale = models.ForeignKey("vehicles.VehicleSale", on_delete=models.PROTECT, related_name="capital_recoveries")
    investor = models.ForeignKey(Investor, null=True, blank=True, on_delete=models.PROTECT, related_name="vehicle_capital_recoveries")
    investor_principal = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital = models.DecimalField(max_digits=38, decimal_places=2)
    source_version = models.CharField(max_length=64)
    funding_version = models.CharField(max_length=64)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_capital_recoveries_recorded")
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="capital_recoveries_investment")
    vehicle_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="capital_recoveries_vehicle")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="capital_recoveries_accounting")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(investor_principal__gte=0, running_capital__gte=0), name="capital_recovery_nonnegative_ck"),
            models.CheckConstraint(condition=Q(investor_principal__gt=0) | Q(running_capital__gt=0), name="capital_recovery_nonzero_ck"),
            models.CheckConstraint(condition=Q(investor_principal=0) | Q(investor__isnull=False), name="capital_recovery_investor_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="capital_recovery_reason_ck"),
        ]
        indexes = [models.Index(fields=("tenant", "sale"), name="capital_recovery_sale_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Capital recoveries are append-only.")
        self.reason = (self.reason or "").strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Capital recovery history is retained.")


class VehicleCapitalRecoveryReview(TimestampedUUIDModel):
    """Revalidate recovered capital after a non-capital Sale correction."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="capital_recovery_reviews")
    recovery = models.ForeignKey(VehicleCapitalRecovery, on_delete=models.PROTECT, related_name="reviews")
    result_confirmation = models.ForeignKey("VehicleResultConfirmation", on_delete=models.PROTECT, related_name="capital_recovery_reviews")
    source_version = models.CharField(max_length=64)
    sale_correction_version = models.PositiveIntegerField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="capital_recovery_reviews")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("recovery", "source_version"), name="capital_recovery_review_uq"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="capital_recovery_review_reason"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Capital recovery reviews are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Capital recovery review history is retained.")


class VehicleCapitalRecoveryReceiptAllocation(TimestampedUUIDModel):
    """Provenance for capital classified against an actual Buyer receipt."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="capital_recovery_receipt_allocations")
    recovery = models.ForeignKey(VehicleCapitalRecovery, on_delete=models.PROTECT, related_name="receipt_allocations")
    receipt = models.ForeignKey("vehicles.VehicleSaleReceipt", on_delete=models.PROTECT, related_name="capital_recovery_allocations")
    investor_principal = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital = models.DecimalField(max_digits=38, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(investor_principal__gte=0, running_capital__gte=0), name="recovery_receipt_nonnegative_ck"),
            models.CheckConstraint(condition=Q(investor_principal__gt=0) | Q(running_capital__gt=0), name="recovery_receipt_nonzero_ck"),
            models.UniqueConstraint(fields=("recovery", "receipt"), name="recovery_receipt_uq"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Recovery receipt allocations are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Recovery receipt allocations are retained.")


class VehicleCapitalRecoveryCreditAllocation(TimestampedUUIDModel):
    """Links recovered Investor principal to the consumed credit lot."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="capital_recovery_credit_allocations")
    recovery = models.ForeignKey(VehicleCapitalRecovery, on_delete=models.PROTECT, related_name="credit_allocations")
    credit = models.ForeignKey(InvestorFundCredit, on_delete=models.PROTECT, related_name="capital_recovery_allocations")
    amount = models.DecimalField(max_digits=38, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="recovery_credit_amount_ck"),
            models.UniqueConstraint(fields=("recovery", "credit"), name="recovery_credit_uq"),
        ]
        indexes = [models.Index(fields=("tenant", "credit"), name="recovery_credit_scope_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Recovery credit allocations are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Recovery credit allocations are retained.")


class VehiclePrincipalRefundReview(TimestampedUUIDModel):
    """Accountant's principal refund obligation for one corrected Sale."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="principal_refund_reviews")
    recovery = models.ForeignKey(VehicleCapitalRecovery, on_delete=models.PROTECT, related_name="principal_refund_reviews")
    sale_correction = models.OneToOneField("vehicles.VehicleSaleCorrection", on_delete=models.PROTECT, related_name="principal_refund_review")
    principal_amount = models.DecimalField(max_digits=38, decimal_places=2)
    principal_debited_before = models.DecimalField(max_digits=38, decimal_places=2)
    source_version = models.CharField(max_length=64)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="principal_refund_reviews")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(principal_amount__gte=0, principal_debited_before__gte=0), name="principal_refund_review_amount_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="principal_refund_review_reason_ck"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Principal refund reviews are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Principal refund review history is retained.")


class VehicleRefundPrincipalClassification(TimestampedUUIDModel):
    """Accountant-confirmed principal component of one actual Buyer refund."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_refund_principal_classifications")
    refund = models.OneToOneField("vehicles.VehicleSaleRefund", on_delete=models.PROTECT, related_name="principal_classification")
    principal_amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_refund_classifications_recorded")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(principal_amount__gte=0), name="refund_class_principal_nonnegative_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Refund classifications are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Refund classification history is retained.")


class VehiclePrincipalRefundDebit(TimestampedUUIDModel):
    """Principal returned to a Buyer, linked to the actual refund and recovery lot."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_principal_refund_debits")
    refund = models.ForeignKey("vehicles.VehicleSaleRefund", on_delete=models.PROTECT, related_name="principal_debits")
    recovery_allocation = models.ForeignKey(VehicleCapitalRecoveryCreditAllocation, on_delete=models.PROTECT, related_name="refund_debits")
    fund_credit = models.ForeignKey(InvestorFundCredit, on_delete=models.PROTECT, related_name="principal_refund_debits")
    amount = models.DecimalField(max_digits=38, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="principal_refund_debit_amount_ck"),
            models.UniqueConstraint(fields=("refund", "recovery_allocation", "fund_credit"), name="principal_refund_debit_uq"),
        ]
        indexes = [models.Index(fields=("tenant", "recovery_allocation"), name="principal_refund_debit_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Principal refund debits are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Principal refund debit history is retained.")


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
    exit_request = models.ForeignKey(
        "InvestorExitRequest", null=True, blank=True, on_delete=models.PROTECT,
        related_name="principal_returns",
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


class VehicleResultConfirmation(TimestampedUUIDModel):
    """Immutable human confirmation of a versioned Vehicle economic result."""

    class ResultKind(models.TextChoices):
        PROFIT = "PROFIT", "Profit"
        LOSS = "LOSS", "Loss"
        BREAK_EVEN = "BREAK_EVEN", "Break even"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_result_confirmations"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.PROTECT, related_name="result_confirmations"
    )
    purchase = models.ForeignKey(
        "vehicles.VehiclePurchase", on_delete=models.PROTECT, related_name="result_confirmations"
    )
    sale = models.ForeignKey(
        "vehicles.VehicleSale", on_delete=models.PROTECT, related_name="result_confirmations"
    )
    investor = models.ForeignKey(
        Investor, null=True, blank=True, on_delete=models.PROTECT,
        related_name="vehicle_result_confirmations",
    )
    version = models.PositiveIntegerField()
    source_version = models.CharField(max_length=64)
    result_kind = models.CharField(max_length=12, choices=ResultKind.choices)
    purchase_cost = models.DecimalField(max_digits=38, decimal_places=2)
    expense_cost = models.DecimalField(max_digits=38, decimal_places=2)
    sale_price = models.DecimalField(max_digits=38, decimal_places=2)
    investor_share_percentage = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    result_amount = models.DecimalField(max_digits=38, decimal_places=2)
    investor_share_amount = models.DecimalField(max_digits=38, decimal_places=2)
    company_share_amount = models.DecimalField(max_digits=38, decimal_places=2)
    suggested_investor_loss = models.DecimalField(max_digits=38, decimal_places=2, null=True, blank=True)
    suggested_company_loss = models.DecimalField(max_digits=38, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=500)
    confirmed_at = models.DateTimeField(default=timezone.now, editable=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="vehicle_result_confirmations_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_result_confirmations",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", null=True, blank=True, on_delete=models.PROTECT,
        related_name="investor_vehicle_result_confirmations",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", null=True, blank=True, on_delete=models.PROTECT,
        related_name="vehicle_result_accounting_recognitions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="invest_result_version_ck"),
            models.CheckConstraint(condition=Q(source_version__gt=""), name="invest_result_source_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="invest_result_reason_ck"),
            models.CheckConstraint(
                condition=Q(investor_share_amount=F("result_amount") - F("company_share_amount")),
                name="invest_result_reconcile_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(result_kind="LOSS", result_amount__lt=0, investor_share_amount__lte=0, company_share_amount__lte=0)
                    | Q(result_kind="PROFIT", result_amount__gt=0, investor_share_amount__gte=0, company_share_amount__gte=0)
                    | Q(result_kind="BREAK_EVEN", result_amount=0, investor_share_amount=0, company_share_amount=0)
                ),
                name="invest_result_kind_sign_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(suggested_investor_loss__isnull=True, suggested_company_loss__isnull=True)
                    | Q(result_kind="LOSS", suggested_investor_loss__isnull=False, suggested_company_loss__isnull=False,
                        suggested_investor_loss__gte=0, suggested_company_loss__gte=0,
                        suggested_investor_loss=-F("result_amount") - F("suggested_company_loss"))
                ),
                name="invest_result_loss_suggest_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(investor__isnull=True, investor_share_percentage__isnull=True,
                      investment_module_revision__isnull=True, investor_share_amount=Decimal("0.00"))
                    | Q(investor__isnull=False, investor_share_percentage__isnull=False,
                        investment_module_revision__isnull=False)
                ),
                name="invest_result_investor_ck",
            ),
            models.CheckConstraint(
                condition=Q(investor_share_percentage__isnull=True)
                | Q(investor_share_percentage__gte=Decimal("0.0000"),
                    investor_share_percentage__lte=Decimal("100.0000")),
                name="invest_result_share_range_ck",
            ),
            models.UniqueConstraint(
                fields=("vehicle", "version"), name="invest_result_vehicle_version_uq"
            ),
            models.UniqueConstraint(
                fields=("vehicle", "source_version"), name="invest_result_source_version_uq"
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "investor", "confirmed_at", "id"),
                         name="invest_result_investor_idx"),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle result confirmations are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle result confirmations are retained.")


class InvestorVehicleProfitPayment(TimestampedUUIDModel):
    """One actual, partial-capable payment against a confirmed Vehicle share."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payments",
    )
    result_confirmation = models.ForeignKey(
        VehicleResultConfirmation, on_delete=models.PROTECT,
        related_name="profit_payments",
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT,
        related_name="vehicle_profit_payments",
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payments",
    )
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payments",
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payments_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payment_vehicle_revisions",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_vehicle_profit_payments",
    )
    description = models.CharField(max_length=500)
    source_reference = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="invest_profit_payment_amount_ck",
            ),
            models.CheckConstraint(
                condition=Q(description__gt="") & Q(source_reference__gt=""),
                name="invest_profit_payment_source_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_at", "id"),
                name="invest_profit_payment_idx",
            ),
            models.Index(
                fields=("result_confirmation", "effective_at", "id"),
                name="invest_profit_result_pay_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.description = (self.description or "").strip()
        self.source_reference = (self.source_reference or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Vehicle Profit payments are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Vehicle Profit payments are retained.")


class InvestorProfitLossOffset(TimestampedUUIDModel):
    """Manual, non-cash application of one confirmed Investor Loss to unpaid Profit."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT,
        related_name="investor_profit_loss_offsets",
    )
    loss_result = models.ForeignKey(
        VehicleResultConfirmation, on_delete=models.PROTECT,
        related_name="profit_loss_offsets_given",
    )
    profit_result = models.ForeignKey(
        VehicleResultConfirmation, on_delete=models.PROTECT,
        related_name="profit_loss_offsets_received",
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT,
        related_name="profit_loss_offsets",
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT,
        related_name="investor_profit_loss_offsets",
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField(default=timezone.now)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_profit_loss_offsets_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_loss_offset_vehicle_revisions",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_loss_offsets",
    )
    reason = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="invest_profit_loss_offset_amount_ck",
            ),
            models.CheckConstraint(
                condition=Q(reason__gt=""),
                name="invest_profit_loss_offset_reason_ck",
            ),
            models.CheckConstraint(
                condition=~Q(loss_result=F("profit_result")),
                name="invest_profit_loss_offset_distinct_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "effective_at", "id"),
                name="invest_loss_off_inv_idx",
            ),
            models.Index(
                fields=("loss_result", "effective_at", "id"),
                name="invest_loss_off_loss_idx",
            ),
            models.Index(
                fields=("profit_result", "effective_at", "id"),
                name="invest_loss_off_profit_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Profit/Loss offsets are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Profit/Loss offsets are retained.")


class InvestorExitRequest(TimestampedUUIDModel):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        CANCELLATION_PENDING = "CANCELLATION_PENDING", "Cancellation pending review"
        CANCELLED = "CANCELLED", "Cancelled"
        SETTLED = "SETTLED", "Settled"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_requests"
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT, related_name="exit_requests"
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REQUESTED)
    terms_version = models.CharField(max_length=80)
    terms_accepted_at = models.DateTimeField(default=timezone.now)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_exit_requests_submitted",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_exit_requests",
    )
    portal_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_portal_exit_requests",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=("REQUESTED", "CANCELLATION_PENDING", "CANCELLED", "SETTLED")),
                name="invest_exit_status_ck",
            ),
            models.CheckConstraint(condition=Q(terms_version__gt=""), name="invest_exit_terms_ck"),
            models.UniqueConstraint(
                fields=("tenant", "investor"),
                condition=Q(status__in=("REQUESTED", "CANCELLATION_PENDING")),
                name="invest_exit_active_uq",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "investor", "created_at", "id"),
                         name="invest_exit_portal_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Exit request state changes must be audited.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Exit requests are retained.")


class InvestorExitNoticeExtension(TimestampedUUIDModel):
    """Audited extension; does not settle or change the Exit lifecycle."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_notice_extensions")
    exit_request = models.ForeignKey(InvestorExitRequest, on_delete=models.PROTECT, related_name="notice_extensions")
    version = models.PositiveIntegerField()
    previous_deadline = models.DateTimeField()
    deadline = models.DateTimeField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_exit_notice_extensions")
    investment_module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_notice_extensions")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="invest_exit_ext_version_ck"),
            models.CheckConstraint(condition=Q(deadline__gt=F("previous_deadline")), name="invest_exit_ext_deadline_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="invest_exit_ext_reason_ck"),
            models.UniqueConstraint(fields=("exit_request", "version"), name="invest_exit_ext_version_uq"),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Exit notice extensions are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Exit notice extensions are retained.")


class InvestorExitLossApplication(TimestampedUUIDModel):
    """Accountant-confirmed application of an Investor's confirmed Vehicle Loss."""

    class Source(models.TextChoices):
        AVAILABLE_FUND = "AVAILABLE_FUND", "Available Fund"
        DIRECT_RECEIPT = "DIRECT_RECEIPT", "Direct receipt"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_loss_applications")
    exit_request = models.ForeignKey(InvestorExitRequest, on_delete=models.PROTECT, related_name="loss_applications")
    loss_result = models.ForeignKey(VehicleResultConfirmation, on_delete=models.PROTECT, related_name="exit_loss_applications")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="investor_exit_loss_applications")
    account = models.ForeignKey("accounting.AccountingAccount", null=True, blank=True, on_delete=models.PROTECT,
                                related_name="investor_exit_loss_applications")
    source = models.CharField(max_length=20, choices=Source.choices)
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_exit_loss_applications_recorded")
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_loss_applications")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_loss_accounting_revisions")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="exit_loss_apply_amount_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="exit_loss_apply_reason_ck"),
            models.CheckConstraint(condition=(Q(source="AVAILABLE_FUND", account__isnull=True) | Q(source="DIRECT_RECEIPT", account__isnull=False)), name="exit_loss_apply_source_ck"),
        ]
        indexes = [models.Index(fields=("tenant", "exit_request", "loss_result"), name="exit_loss_apply_scope_idx")]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Exit Loss applications are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Exit Loss application history is retained.")


class InvestorExitLossAllocation(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_loss_allocations")
    application = models.ForeignKey(InvestorExitLossApplication, on_delete=models.PROTECT, related_name="allocations")
    credit = models.ForeignKey(InvestorFundCredit, on_delete=models.PROTECT, related_name="exit_loss_allocations")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_exit_loss_allocations_recorded")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="exit_loss_alloc_amount_ck"),
                       models.UniqueConstraint(fields=("application", "credit"), name="exit_loss_alloc_credit_uq")]
        indexes = [models.Index(fields=("tenant", "credit"), name="exit_loss_alloc_credit_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Exit Loss allocations are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Exit Loss allocation history is retained.")


class InvestorExitProfitPayment(TimestampedUUIDModel):
    """One actual payment against a current confirmed Profit payable in Exit."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_profit_payments")
    exit_request = models.ForeignKey(InvestorExitRequest, on_delete=models.PROTECT, related_name="profit_payments")
    position = models.ForeignKey("InvestorProfitPeriodPosition", on_delete=models.PROTECT, related_name="exit_payments")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="investor_exit_profit_payments")
    account = models.ForeignKey("accounting.AccountingAccount", on_delete=models.PROTECT, related_name="investor_exit_profit_payments")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_exit_profit_payments_recorded")
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_profit_payments")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_profit_accounting_revisions")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="exit_profit_payment_amount_ck"),
                       models.CheckConstraint(condition=Q(reason__gt=""), name="exit_profit_payment_reason_ck")]
        indexes = [models.Index(fields=("tenant", "exit_request", "position"), name="exit_profit_pay_scope_idx")]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Exit Profit payments are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Exit Profit payment history is retained.")


class InvestorExitRequestHistory(TimestampedUUIDModel):
    class Action(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        CANCELLATION_REQUESTED = "CANCELLATION_REQUESTED", "Cancellation requested"
        CANCELLATION_APPROVED = "CANCELLATION_APPROVED", "Cancellation approved"
        CANCELLATION_REJECTED = "CANCELLATION_REJECTED", "Cancellation rejected"
        SETTLEMENT_CLOSED = "SETTLEMENT_CLOSED", "Settlement closed"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_request_history"
    )
    exit_request = models.ForeignKey(
        InvestorExitRequest, on_delete=models.PROTECT, related_name="history"
    )
    version = models.PositiveIntegerField()
    action = models.CharField(max_length=32, choices=Action.choices)
    previous_status = models.CharField(max_length=24, blank=True)
    new_status = models.CharField(max_length=24, choices=InvestorExitRequest.Status.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_exit_request_history",
    )
    reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="invest_exit_history_version_ck"),
            models.UniqueConstraint(fields=("exit_request", "version"), name="invest_exit_history_version_uq"),
        ]
        indexes = [models.Index(fields=("tenant", "exit_request", "version"), name="invest_exit_history_idx")]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Exit request history is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Exit request history is retained.")


class InvestorExitSettlementClosure(TimestampedUUIDModel):
    """Company Accountant's final all-balances-zero Exit closure."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_exit_closures")
    exit_request = models.OneToOneField(InvestorExitRequest, on_delete=models.PROTECT, related_name="settlement_closure")
    source_version = models.CharField(max_length=64)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_exit_closures_recorded")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="investor_exit_closures")
    closed_at = models.DateTimeField()

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(reason__gt=""), name="exit_closure_reason_ck")]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Exit closure is immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Exit closure is retained.")


class InvestorProfitPeriodPosition(TimestampedUUIDModel):
    """Human-confirmed obligation; its immutable calculation remains the source."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_period_positions")
    reconciliation = models.OneToOneField("InvestorProfitPeriodReconciliation", on_delete=models.PROTECT, related_name="confirmed_position")
    previous_position = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="restatements")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_period_positions_recorded")
    reason = models.CharField(max_length=500)
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="period_positions_investment")
    vehicle_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="period_positions_vehicle")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="period_positions_accounting")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(reason__gt=""), name="period_position_reason_ck"),
            models.UniqueConstraint(fields=("previous_position",), name="period_position_successor_uq"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Confirmed Investor period positions are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Confirmed Investor period position history is retained.")


class InvestorProfitFutureAdjustment(TimestampedUUIDModel):
    """Explicit non-cash transfer from future Profit to an earlier recoverable."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_profit_future_adjustments")
    recoverable_position = models.ForeignKey(InvestorProfitPeriodPosition, on_delete=models.PROTECT, related_name="future_profit_recoveries")
    profit_position = models.ForeignKey(InvestorProfitPeriodPosition, on_delete=models.PROTECT, related_name="recoverable_adjustments")
    profit_result = models.ForeignKey("VehicleResultConfirmation", on_delete=models.PROTECT, related_name="recoverable_adjustments")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_profit_future_adjustments")
    reason = models.CharField(max_length=500)
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="future_adjustments_investment")
    vehicle_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="future_adjustments_vehicle")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="future_adjustments_accounting")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="future_profit_adjustment_amount_ck"),
            models.CheckConstraint(condition=~Q(recoverable_position=F("profit_position")), name="future_profit_distinct_positions_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="future_profit_adjustment_reason_ck"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Future Profit adjustments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Future Profit adjustment history is retained.")


class InvestorProfitRecoveryReceipt(TimestampedUUIDModel):
    """One actual repayment against a confirmed period recoverable."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="investor_profit_recovery_receipts")
    position = models.ForeignKey(InvestorProfitPeriodPosition, on_delete=models.PROTECT, related_name="recovery_receipts")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="investor_profit_recovery_receipts")
    account = models.ForeignKey("accounting.AccountingAccount", on_delete=models.PROTECT, related_name="investor_profit_recovery_receipts")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="investor_profit_recovery_receipts")
    reason = models.CharField(max_length=500)
    investment_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="profit_receipts_investment")
    accounting_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="profit_receipts_accounting")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="profit_recovery_receipt_amount_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Investor Profit recovery receipts are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Profit recovery receipt history is retained.")


class InvestorProfitPeriodReconciliation(TimestampedUUIDModel):
    """Append-only Company Accountant confirmation of one Investor period snapshot."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT,
        related_name="investor_profit_period_reconciliations",
    )
    investor = models.ForeignKey(
        Investor, on_delete=models.PROTECT,
        related_name="profit_period_reconciliations",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    duration_months = models.PositiveSmallIntegerField()
    result_count = models.PositiveIntegerField()
    version = models.PositiveIntegerField()
    source_version = models.CharField(max_length=64)
    gross_investor_profit = models.DecimalField(max_digits=38, decimal_places=2)
    investor_loss_share = models.DecimalField(max_digits=38, decimal_places=2)
    deal_profit_paid = models.DecimalField(max_digits=38, decimal_places=2)
    interim_paid = models.DecimalField(max_digits=38, decimal_places=2)
    loss_offset_applied = models.DecimalField(max_digits=38, decimal_places=2)
    net_position = models.DecimalField(max_digits=38, decimal_places=2)
    restatement_adjustment = models.DecimalField(max_digits=38, decimal_places=2)
    previous_reconciliation = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="restatements",
    )
    reason = models.CharField(max_length=500)
    confirmed_at = models.DateTimeField(default=timezone.now, editable=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="investor_profit_period_reconciliations_recorded",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_period_investment_revisions",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_period_vehicle_revisions",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="investor_profit_period_accounting_revisions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="invest_recon_version_ck"),
            models.CheckConstraint(condition=Q(period_end__gte=F("period_start")), name="invest_recon_dates_ck"),
            models.CheckConstraint(condition=Q(duration_months__gt=0), name="invest_recon_duration_ck"),
            models.CheckConstraint(condition=Q(source_version__gt=""), name="invest_recon_source_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="invest_recon_reason_ck"),
            models.CheckConstraint(
                condition=(
                    Q(gross_investor_profit__gte=Decimal("0.00"))
                    & Q(investor_loss_share__gte=Decimal("0.00"))
                    & Q(deal_profit_paid__gte=Decimal("0.00"))
                    & Q(interim_paid__gte=Decimal("0.00"))
                    & Q(loss_offset_applied__gte=Decimal("0.00"))
                ),
                name="invest_recon_parts_ck",
            ),
            models.CheckConstraint(
                condition=Q(
                    net_position=(
                        F("gross_investor_profit") - F("deal_profit_paid")
                        - F("interim_paid") - F("loss_offset_applied")
                    )
                ),
                name="invest_recon_net_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "investor", "period_start", "period_end", "version"),
                name="invest_recon_version_uq",
            ),
            models.UniqueConstraint(
                fields=("tenant", "investor", "period_start", "period_end", "source_version"),
                name="invest_recon_source_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "investor", "period_start", "period_end", "version"),
                name="invest_recon_period_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Investor Profit period reconciliations are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Investor Profit period reconciliations are retained.")
