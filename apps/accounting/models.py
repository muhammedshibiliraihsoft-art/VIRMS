from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel


class AccountingAccount(TimestampedUUIDModel):
    class AccountType(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK = "BANK", "Bank"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="accounting_accounts"
    )
    account_type = models.CharField(max_length=8, choices=AccountType.choices)
    label = models.CharField(max_length=100)
    normalized_label = models.CharField(max_length=100, editable=False)
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="archived_accounting_accounts",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_accounting_accounts",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(account_type__in=("CASH", "BANK")),
                name="acct_account_type_ck",
            ),
            models.CheckConstraint(
                condition=Q(label__gt="") & Q(normalized_label__gt=""),
                name="acct_account_label_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_active=True, archived_at__isnull=True, archived_by__isnull=True)
                    | Q(is_active=False, archived_at__isnull=False, archived_by__isnull=False)
                ),
                name="acct_account_archive_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "account_type", "normalized_label"),
                condition=Q(is_active=True),
                name="acct_account_active_label_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "is_active", "account_type", "id"),
                name="acct_account_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        self.normalized_label = normalize_label(self.label)
        if self.pk and not self._state.adding:
            prior = type(self).objects.get(pk=self.pk)
            if (
                prior.tenant_id != self.tenant_id
                or prior.account_type != self.account_type
                or prior.label != self.label
                or prior.normalized_label != self.normalized_label
                or prior.created_by_id != self.created_by_id
                or not prior.is_active
                or self.is_active
                or prior.archived_at is not None
                or prior.archived_by_id is not None
                or self.archived_at is None
                or self.archived_by_id is None
            ):
                raise ValueError("Accounting accounts may only be archived once.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Accounting accounts cannot be deleted.")


class AccountingCategory(TimestampedUUIDModel):
    class Kind(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="accounting_categories"
    )
    kind = models.CharField(max_length=8, choices=Kind.choices)
    label = models.CharField(max_length=100)
    normalized_label = models.CharField(max_length=100, editable=False)
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="archived_accounting_categories",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_accounting_categories",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=("INCOME", "EXPENSE")),
                name="acct_category_kind_ck",
            ),
            models.CheckConstraint(
                condition=Q(label__gt="") & Q(normalized_label__gt=""),
                name="acct_category_label_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_active=True, archived_at__isnull=True, archived_by__isnull=True)
                    | Q(is_active=False, archived_at__isnull=False, archived_by__isnull=False)
                ),
                name="acct_category_archive_ck",
            ),
            models.UniqueConstraint(
                fields=("tenant", "kind", "normalized_label"),
                condition=Q(is_active=True),
                name="acct_category_active_label_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "kind", "is_active", "id"),
                name="acct_category_scope_idx",
            )
        ]

    def save(self, *args, **kwargs):
        self.normalized_label = normalize_label(self.label)
        if self.pk and not self._state.adding:
            prior = type(self).objects.get(pk=self.pk)
            if (
                prior.tenant_id != self.tenant_id
                or prior.kind != self.kind
                or prior.label != self.label
                or prior.normalized_label != self.normalized_label
                or prior.created_by_id != self.created_by_id
                or not prior.is_active
                or self.is_active
                or prior.archived_at is not None
                or prior.archived_by_id is not None
                or self.archived_at is None
                or self.archived_by_id is None
            ):
                raise ValueError("Accounting categories may only be archived once.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Accounting categories cannot be deleted.")


class AccountingEvent(TimestampedUUIDModel):
    class EventType(models.TextChoices):
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"
        RECEIPT = "RECEIPT", "Receipt"
        PAYMENT = "PAYMENT", "Payment"
        OPENING_BALANCE = "OPENING_BALANCE", "Opening Balance"
        TRANSFER = "TRANSFER", "Transfer"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="accounting_events"
    )
    branch = models.ForeignKey(
        "tenants.Branch",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="accounting_events",
    )
    event_type = models.CharField(max_length=16, choices=EventType.choices)
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    effect_sign = models.SmallIntegerField(default=1)
    reversal_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversal_rows",
    )
    replaces_event = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="replacement_rows",
    )
    correction_reason = models.CharField(max_length=500, blank=True)
    effective_at = models.DateTimeField()
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accounting_events_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="accounting_events",
    )
    category = models.ForeignKey(
        AccountingCategory,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
    )
    description = models.CharField(max_length=500)
    source_reference = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    event_type__in=(
                        "INCOME",
                        "EXPENSE",
                        "RECEIPT",
                        "PAYMENT",
                        "OPENING_BALANCE",
                        "TRANSFER",
                    )
                ),
                name="acct_event_type_ck",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="acct_event_amount_ck",
            ),
            models.CheckConstraint(
                condition=Q(currency="INR"),
                name="acct_event_currency_ck",
            ),
            models.CheckConstraint(
                condition=Q(effect_sign__in=(-1, 1)),
                name="acct_event_sign_ck",
            ),
            models.CheckConstraint(
                condition=Q(description__gt="") & Q(source_reference__gt=""),
                name="acct_event_source_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(event_type__in=("INCOME", "EXPENSE"), category__isnull=False)
                    | Q(
                        event_type__in=("RECEIPT", "PAYMENT", "OPENING_BALANCE", "TRANSFER"),
                        category__isnull=True,
                    )
                ),
                name="acct_event_category_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(effect_sign=1, reversal_of__isnull=True)
                    | Q(effect_sign=-1, reversal_of__isnull=False, replaces_event__isnull=True)
                ),
                name="acct_event_correction_ck",
            ),
            models.CheckConstraint(
                condition=~Q(id=F("reversal_of")) & ~Q(id=F("replaces_event")),
                name="acct_event_not_self_ck",
            ),
            models.UniqueConstraint(
                fields=("reversal_of",),
                condition=Q(reversal_of__isnull=False),
                name="acct_event_one_reverse_uq",
            ),
            models.UniqueConstraint(
                fields=("replaces_event",),
                condition=Q(replaces_event__isnull=False),
                name="acct_event_one_replace_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "effective_at", "id"),
                name="acct_event_scope_time_idx",
            ),
            models.Index(
                fields=("tenant", "branch", "effective_at", "id"),
                name="acct_event_branch_time_idx",
            ),
            models.Index(
                fields=("tenant", "event_type", "effective_at"),
                name="acct_event_type_time_idx",
            ),
            models.Index(
                fields=("tenant", "category", "effective_at"),
                name="acct_event_category_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValueError("Accounting events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Accounting events are append-only.")


class AccountMovement(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="account_movements"
    )
    event = models.ForeignKey(
        AccountingEvent, on_delete=models.PROTECT, related_name="movements"
    )
    account = models.ForeignKey(
        AccountingAccount, on_delete=models.PROTECT, related_name="movements"
    )
    delta = models.DecimalField(max_digits=38, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(delta=Decimal("0.00")), name="acct_move_nonzero_ck"
            ),
            models.UniqueConstraint(
                fields=("event", "account"), name="acct_move_event_account_uq"
            ),
        ]
        indexes = [
            models.Index(fields=("account", "event"), name="acct_move_account_idx")
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValueError("Account movements are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Account movements are append-only.")


class AccountingApplication(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="accounting_applications"
    )
    source_event = models.ForeignKey(
        AccountingEvent,
        on_delete=models.PROTECT,
        related_name="source_applications",
    )
    target_event = models.ForeignKey(
        AccountingEvent,
        on_delete=models.PROTECT,
        related_name="target_applications",
    )
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    effect_sign = models.SmallIntegerField(default=1)
    reversal_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversal_rows",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accounting_applications_recorded",
    )
    module_revision = models.ForeignKey(
        "tenants.CompanyModuleState",
        on_delete=models.PROTECT,
        related_name="accounting_applications",
    )
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)
    reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal("0.00")),
                name="acct_application_amount_ck",
            ),
            models.CheckConstraint(
                condition=Q(effect_sign__in=(-1, 1)),
                name="acct_application_sign_ck",
            ),
            models.CheckConstraint(
                condition=~Q(source_event=F("target_event")),
                name="acct_application_not_self_ck",
            ),
            models.CheckConstraint(
                condition=(
                    Q(effect_sign=1, reversal_of__isnull=True)
                    | Q(effect_sign=-1, reversal_of__isnull=False)
                ),
                name="acct_application_correction_ck",
            ),
            models.UniqueConstraint(
                fields=("reversal_of",),
                condition=Q(reversal_of__isnull=False),
                name="acct_app_one_reverse_uq",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "target_event", "id"), name="acct_app_target_idx"
            ),
            models.Index(
                fields=("tenant", "source_event", "id"), name="acct_app_source_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValueError("Accounting applications are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Accounting applications are append-only.")


class AccountingIdempotencyRecord(TimestampedUUIDModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="accounting_idempotency"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accounting_idempotency_records",
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
                fields=("tenant", "actor", "key"), name="acct_idem_scope_key_uq"
            ),
            models.CheckConstraint(
                condition=Q(method__in=("POST", "PATCH")),
                name="acct_idem_method_ck",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "actor", "created_at"), name="acct_idem_actor_idx"
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            raise ValueError("Accounting idempotency results are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Accounting idempotency results are retained.")


def normalize_label(value):
    return " ".join((value or "").split()).casefold()
