import re
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


def normalize_registration(value):
    """Ignore case and whitespace while preserving punctuation in a plate."""
    return re.sub(r"\s+", "", (value or "").strip()).upper()


def normalize_external_reference(value):
    return (value or "").strip().lower()


class Vehicle(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicles"
    )
    current_branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="current_vehicles"
    )
    registration = models.CharField(max_length=40)
    normalized_registration = models.CharField(max_length=40, editable=False)
    model = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicles_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicles_updated",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(registration__gt="")
                & Q(normalized_registration__gt="")
                & Q(model__gt=""),
                name="vehicle_identity_fields_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "normalized_registration"),
                condition=Q(is_active=True),
                name="vehicle_active_registration_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "current_branch", "is_active", "id"),
                name="vehicle_branch_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        self.registration = (self.registration or "").strip()
        self.model = (self.model or "").strip()
        self.normalized_registration = normalize_registration(self.registration)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle identity is retained; archive/deactivation is a separate workflow.")


class VehicleBranchMovement(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_branch_movements"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="branch_movements"
    )
    from_branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_moves_from"
    )
    to_branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_moves_to"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_branch_moves_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_branch_movements",
    )
    moved_at = models.DateTimeField(default=timezone.now, editable=False)
    reason = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(from_branch_id=F("to_branch_id")),
                name="vehicle_move_branch_diff_ck",
            ),
            models.CheckConstraint(
                condition=Q(reason__gt=""), name="vehicle_move_reason_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "vehicle", "moved_at", "id"),
                name="vehicle_move_history_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Vehicle branch movements are append-only.")
        self.reason = (self.reason or "").strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle branch movements are retained.")


class VehiclePurchase(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_purchases"
    )
    vehicle = models.OneToOneField(
        Vehicle, on_delete=models.PROTECT, related_name="purchase"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_purchases"
    )
    purchase_cost = models.DecimalField(max_digits=38, decimal_places=2)
    seller_name = models.CharField(max_length=160)
    seller_phone = models.CharField(max_length=40, blank=True)
    investor = models.ForeignKey(
        "investment.Investor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="vehicle_purchases",
    )
    investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    investor_share_agreement = models.ForeignKey(
        "investment.InvestorProfitShareAgreement",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="vehicle_purchase_snapshots",
    )
    investor_share_percentage_snapshot = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    purchased_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_purchases_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_purchases",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="funded_vehicle_purchases",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(purchase_cost__gt=0)
                & Q(investor_fund_amount__gte=0)
                & Q(running_capital_amount__gte=0)
                & Q(purchase_cost=F("investor_fund_amount") + F("running_capital_amount")),
                name="vehicle_purchase_sources_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(investor_fund_amount=0, investor__isnull=True, investment_module_revision__isnull=True)
                    | Q(investor_fund_amount__gt=0, investor__isnull=False, investment_module_revision__isnull=False)
                ),
                name="vehicle_purchase_investor_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(investor_share_agreement__isnull=True, investor_share_percentage_snapshot__isnull=True)
                    | Q(investor_share_agreement__isnull=False, investor_share_percentage_snapshot__isnull=False)
                ),
                name="vehicle_purchase_share_snapshot_ck",
            ),
            models.CheckConstraint(
                condition=Q(investor_share_percentage_snapshot__isnull=True)
                | Q(investor_share_percentage_snapshot__gte=Decimal("0.0000"), investor_share_percentage_snapshot__lte=Decimal("100.0000")),
                name="vehicle_purchase_share_range_ck",
            ),
            models.CheckConstraint(
                condition=Q(seller_name__gt=""), name="vehicle_purchase_seller_ck"
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "branch", "purchased_at", "id"),
                name="vehicle_purchase_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        self.seller_name = (self.seller_name or "").strip()
        self.seller_phone = (self.seller_phone or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Purchases are immutable; use an audited correction.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Purchases are retained.")


class VehiclePurchasePayment(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_purchase_payments"
    )
    purchase = models.ForeignKey(
        VehiclePurchase, on_delete=models.PROTECT, related_name="payments"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_purchase_payments"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_purchase_payments"
    )
    reference = models.CharField(max_length=200, blank=True)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_purchase_payments_recorded",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_purchase_payments",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="vehicle_purchase_payment_amount_ck")
        ]
        indexes = [
            models.Index(fields=("tenant", "purchase", "effective_at", "id"), name="vehicle_purchase_payment_idx")
        ]

    def save(self, *args, **kwargs):
        self.reference = (self.reference or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Purchase payments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Purchase payments are retained.")


class VehicleExpense(TimestampedUUIDModel):
    """Approved direct Stock Vehicle cost, separate from Company P&L expense."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_expenses"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="direct_expenses"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_expenses"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    description = models.CharField(max_length=500)
    investor = models.ForeignKey(
        "investment.Investor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="vehicle_expenses",
    )
    investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_expenses_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expenses",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="funded_vehicle_expenses",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0)
                & Q(investor_fund_amount__gte=0)
                & Q(running_capital_amount__gte=0)
                & Q(amount=F("investor_fund_amount") + F("running_capital_amount")),
                name="vehicle_expense_sources_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(investor_fund_amount=0, investor__isnull=True, investment_module_revision__isnull=True)
                    | Q(investor_fund_amount__gte=0, investor__isnull=False, investment_module_revision__isnull=False)
                ),
                name="vehicle_expense_investor_ck",
            ),
            models.CheckConstraint(
                condition=Q(description__gt=""), name="vehicle_expense_description_ck"
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "branch", "vehicle", "effective_at", "id"), name="vehicle_expense_scope_idx")
        ]

    def save(self, *args, **kwargs):
        self.description = (self.description or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Expenses are immutable; use an audited correction.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Expenses are retained.")


class VehicleExpensePayment(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_expense_payments"
    )
    expense = models.ForeignKey(
        VehicleExpense, on_delete=models.PROTECT, related_name="payments"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_expense_payments"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_expense_payments"
    )
    reference = models.CharField(max_length=200)
    normalized_reference = models.CharField(max_length=200, editable=False)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_expense_payments_recorded",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expense_payments",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expense_payment_vehicle_revisions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="vehicle_expense_payment_amount_ck"),
            models.CheckConstraint(
                condition=Q(reference__gt="") & Q(normalized_reference__gt=""),
                name="vehicle_expense_payment_reference_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "account", "normalized_reference"),
                name="vehicle_expense_payment_ref_uq",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "expense", "effective_at", "id"), name="vehicle_expense_payment_idx")
        ]

    def save(self, *args, **kwargs):
        self.reference = (self.reference or "").strip()
        self.normalized_reference = normalize_external_reference(self.reference)
        if not self._state.adding:
            raise ValidationError("Vehicle Expense payments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Expense payments are retained.")


class VehicleExpenseRefund(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_expense_refunds"
    )
    expense = models.ForeignKey(
        VehicleExpense, on_delete=models.PROTECT, related_name="refunds"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_expense_refunds"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    applied_amount = models.DecimalField(max_digits=38, decimal_places=2)
    excess_income_category = models.ForeignKey(
        "accounting.AccountingCategory",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refund_income",
    )
    excess_income_description = models.CharField(max_length=500, blank=True)
    excess_income_event = models.OneToOneField(
        "accounting.AccountingEvent",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refund_source",
    )
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_expense_refunds"
    )
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refunds_recorded",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refunds",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refund_vehicle_revisions",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="vehicle_expense_refund_investment_revisions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0)
                & Q(applied_amount__gte=0)
                & Q(applied_amount__lte=F("amount")),
                name="vehicle_expense_refund_amount_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(applied_amount=F("amount"), excess_income_category__isnull=True,
                      excess_income_description="", excess_income_event__isnull=True)
                    | Q(applied_amount__lt=F("amount"), excess_income_category__isnull=False,
                        excess_income_description__gt="", excess_income_event__isnull=False)
                ),
                name="vehicle_expense_refund_excess_ck",
            ),
        ]
        indexes = [
            models.Index(fields=("tenant", "expense", "effective_at", "id"), name="vehicle_expense_refund_idx")
        ]

    def save(self, *args, **kwargs):
        self.excess_income_description = (self.excess_income_description or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Expense refunds are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Expense refunds are retained.")


class VehicleExpenseCorrection(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_expense_corrections")
    expense = models.ForeignKey(VehicleExpense, on_delete=models.PROTECT, related_name="corrections")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_expense_corrections")
    version = models.PositiveIntegerField()
    previous_amount = models.DecimalField(max_digits=38, decimal_places=2)
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    previous_investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    previous_running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    reason = models.CharField(max_length=500)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_expense_corrections_recorded"
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_expense_corrections"
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_expense_correction_investment_revisions"
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_expense_correction_accounting_revisions"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="vehicle_expense_correction_version_ck"),
            models.CheckConstraint(
                condition=Q(amount__gt=0) & Q(investor_fund_amount__gte=0) & Q(running_capital_amount__gte=0)
                & Q(amount=F("investor_fund_amount") + F("running_capital_amount")),
                name="vehicle_expense_correction_sources_ck",
            ),
            models.CheckConstraint(
                condition=Q(previous_amount__gt=0) & Q(previous_investor_fund_amount__gte=0)
                & Q(previous_running_capital_amount__gte=0)
                & Q(previous_amount=F("previous_investor_fund_amount") + F("previous_running_capital_amount")),
                name="vehicle_expense_correction_previous_ck",
            ),
            models.CheckConstraint(condition=Q(reason__gt=""), name="vehicle_expense_correction_reason_ck"),
            models.UniqueConstraint(fields=("expense", "version"), name="vehicle_expense_correction_version_uq"),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Expense corrections are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Expense corrections are retained.")


class VehiclePurchaseRefund(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_purchase_refunds"
    )
    purchase = models.ForeignKey(
        VehiclePurchase, on_delete=models.PROTECT, related_name="refunds"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_purchase_refunds"
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_purchase_refunds"
    )
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="vehicle_purchase_refunds_recorded",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_purchase_refunds",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_purchase_refund_vehicle_revisions",
    )

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="vehicle_purchase_refund_amount_ck")]
        indexes = [models.Index(fields=("tenant", "purchase", "effective_at", "id"), name="vehicle_purchase_refund_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Vehicle Purchase refunds are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Purchase refunds are retained.")


class VehiclePurchaseCorrection(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_purchase_corrections"
    )
    purchase = models.ForeignKey(
        VehiclePurchase, on_delete=models.PROTECT, related_name="corrections"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_purchase_corrections"
    )
    version = models.PositiveIntegerField()
    previous_purchase_cost = models.DecimalField(max_digits=38, decimal_places=2)
    purchase_cost = models.DecimalField(max_digits=38, decimal_places=2)
    previous_investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    investor_fund_amount = models.DecimalField(max_digits=38, decimal_places=2)
    previous_running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    running_capital_amount = models.DecimalField(max_digits=38, decimal_places=2)
    reason = models.CharField(max_length=500)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="vehicle_purchase_corrections_recorded",
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_purchase_corrections",
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_purchase_correction_investment_revisions",
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT,
        related_name="vehicle_purchase_correction_accounting_revisions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="vehicle_purchase_correction_version_ck"),
            models.CheckConstraint(
                condition=Q(purchase_cost__gt=0)
                & Q(investor_fund_amount__gte=0)
                & Q(running_capital_amount__gte=0)
                & Q(purchase_cost=F("investor_fund_amount") + F("running_capital_amount")),
                name="vehicle_purchase_correction_sources_ck",
            ),
            models.CheckConstraint(
                condition=Q(previous_purchase_cost__gt=0)
                & Q(previous_investor_fund_amount__gte=0)
                & Q(previous_running_capital_amount__gte=0)
                & Q(previous_purchase_cost=F("previous_investor_fund_amount") + F("previous_running_capital_amount")),
                name="vehicle_purchase_correction_previous_ck",
            ),
            models.CheckConstraint(condition=Q(reason__gt=""), name="vehicle_purchase_correction_reason_ck"),
            models.UniqueConstraint(fields=("purchase", "version"), name="vehicle_purchase_correction_version_uq"),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Purchase corrections are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Purchase corrections are retained.")


class VehicleSale(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_sales")
    vehicle = models.OneToOneField(Vehicle, on_delete=models.PROTECT, related_name="confirmed_sale")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_sales")
    sale_price = models.DecimalField(max_digits=38, decimal_places=2)
    buyer_name = models.CharField(max_length=160)
    buyer_phone = models.CharField(max_length=40)
    sold_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_sales_recorded"
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sales"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(sale_price__gt=0), name="vehicle_sale_price_ck"),
            models.CheckConstraint(condition=Q(buyer_name__gt="") & Q(buyer_phone__gt=""), name="vehicle_sale_buyer_ck"),
        ]
        indexes = [models.Index(fields=("tenant", "branch", "sold_at", "id"), name="vehicle_sale_scope_idx")]

    def save(self, *args, **kwargs):
        self.buyer_name = (self.buyer_name or "").strip()
        self.buyer_phone = (self.buyer_phone or "").strip()
        if not self._state.adding:
            raise ValidationError("Confirmed Vehicle Sales are append-only; use an audited correction.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Confirmed Vehicle Sales are retained.")


class VehicleSaleCorrection(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_sale_corrections")
    sale = models.ForeignKey(VehicleSale, on_delete=models.PROTECT, related_name="corrections")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_sale_corrections")
    version = models.PositiveIntegerField()
    previous_sale_price = models.DecimalField(max_digits=38, decimal_places=2)
    sale_price = models.DecimalField(max_digits=38, decimal_places=2)
    reason = models.CharField(max_length=500)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_sale_corrections_recorded"
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_corrections"
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_correction_accounting_revisions"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gt=0), name="vehicle_sale_correction_version_ck"),
            models.CheckConstraint(condition=Q(previous_sale_price__gt=0) & Q(sale_price__gt=0), name="vehicle_sale_correction_price_ck"),
            models.CheckConstraint(condition=Q(reason__gt=""), name="vehicle_sale_correction_reason_ck"),
            models.UniqueConstraint(fields=("sale", "version"), name="vehicle_sale_correction_version_uq"),
        ]

    def save(self, *args, **kwargs):
        self.reason = (self.reason or "").strip()
        if not self._state.adding:
            raise ValidationError("Vehicle Sale corrections are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle Sale corrections are retained.")


class VehicleSaleReceipt(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_sale_receipts")
    sale = models.ForeignKey(VehicleSale, on_delete=models.PROTECT, related_name="receipts")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_sale_receipts")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    account = models.ForeignKey("accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_sale_receipts")
    reference = models.CharField(max_length=200)
    normalized_reference = models.CharField(max_length=200, editable=False)
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_sale_receipts_recorded"
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_receipt_vehicle_revisions"
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_receipts"
    )
    investment_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", null=True, blank=True, on_delete=models.PROTECT,
        related_name="vehicle_sale_receipt_investment_revisions",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="vehicle_sale_receipt_amount_ck"),
            models.CheckConstraint(condition=Q(reference__gt="") & Q(normalized_reference__gt=""), name="vehicle_sale_receipt_reference_ck"),
            models.UniqueConstraint(fields=("tenant", "account", "normalized_reference"), name="vehicle_sale_receipt_ref_uq"),
        ]
        indexes = [models.Index(fields=("tenant", "sale", "effective_at", "id"), name="vehicle_sale_receipt_idx")]

    def save(self, *args, **kwargs):
        self.reference = (self.reference or "").strip()
        self.normalized_reference = normalize_external_reference(self.reference)
        if not self._state.adding:
            raise ValidationError("Buyer receipts are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Buyer receipts are retained.")


class VehicleSaleRefund(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_sale_refunds")
    sale = models.ForeignKey(VehicleSale, on_delete=models.PROTECT, related_name="refunds")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="vehicle_sale_refunds")
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    account = models.ForeignKey("accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_sale_refunds")
    effective_at = models.DateTimeField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_sale_refunds_recorded"
    )
    vehicle_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_refund_vehicle_revisions"
    )
    accounting_module_revision = models.ForeignKey(
        "tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="vehicle_sale_refunds"
    )

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="vehicle_sale_refund_amount_ck")]
        indexes = [models.Index(fields=("tenant", "sale", "effective_at", "id"), name="vehicle_sale_refund_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Buyer refunds are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Buyer refunds are retained.")


class VehiclePaymentAccountPreference(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_payment_preferences")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vehicle_payment_preferences"
    )
    account = models.ForeignKey(
        "accounting.AccountingAccount", on_delete=models.PROTECT, related_name="vehicle_payment_preferences"
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=("tenant", "actor"), name="vehicle_payment_pref_actor_uq")]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding and (
            self.tenant_id != type(self).objects.get(pk=self.pk).tenant_id
            or self.actor_id != type(self).objects.get(pk=self.pk).actor_id
        ):
            raise ValidationError("Vehicle payment preferences keep their Company and Accountant identity.")
        return super().save(*args, **kwargs)


class VehicleIdempotencyRecord(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="vehicle_idempotency"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehicle_idempotency_records",
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
                fields=("tenant", "actor", "key"), name="vehicle_idem_scope_key_uq"
            ),
            models.CheckConstraint(
                condition=Q(method__in=("POST", "PATCH")),
                name="vehicle_idem_method_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "actor", "created_at"),
                name="vehicle_idem_actor_idx",
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Vehicle idempotency results are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Vehicle idempotency results are retained.")
