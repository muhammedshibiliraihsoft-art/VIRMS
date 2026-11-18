from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.common.models import TimestampedUUIDModel


class GarageJob(TimestampedUUIDModel):
    class Context(models.TextChoices):
        STOCK = "STOCK", "Stock Vehicle"
        EXTERNAL_CUSTOMER = "EXTERNAL_CUSTOMER", "External customer"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        COMPLETED = "COMPLETED", "Completed"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="garage_jobs")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="garage_jobs")
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.PROTECT, related_name="garage_jobs")
    context = models.CharField(max_length=24, choices=Context.choices)
    contact_name = models.CharField(max_length=160, blank=True, default="")
    contact_phone = models.CharField(max_length=40, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    status_version = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_jobs_created")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_jobs_created")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(context__in=("STOCK", "EXTERNAL_CUSTOMER")), name="garage_job_context_ck"),
            models.CheckConstraint(condition=Q(status__in=("OPEN", "COMPLETED")), name="garage_job_status_ck"),
            models.CheckConstraint(condition=~Q(context="EXTERNAL_CUSTOMER") | Q(contact_name__regex=r"\S"), name="garage_customer_name_ck"),
        ]
        indexes = [models.Index(fields=("tenant", "branch", "status", "id"), name="garage_job_scope_idx"), models.Index(fields=("tenant", "vehicle", "status"), name="garage_job_vehicle_idx")]

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage Job history is retained.")


class GarageJobStatusChange(TimestampedUUIDModel):
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="status_history")
    version = models.PositiveIntegerField()
    from_status = models.CharField(max_length=12, choices=GarageJob.Status.choices)
    to_status = models.CharField(max_length=12, choices=GarageJob.Status.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_status_changes")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_status_changes")

    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(from_status="OPEN", to_status="COMPLETED") | Q(from_status="COMPLETED", to_status="OPEN")), name="garage_status_transition_ck"), models.UniqueConstraint(fields=("job", "version"), name="garage_status_version_uq"), models.CheckConstraint(condition=Q(version__gt=0), name="garage_status_version_positive_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage Job status history is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage Job status history is retained.")


class GarageWorkEntry(TimestampedUUIDModel):
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="work_entries")
    description = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_work_entries")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_work_entries")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(description__regex=r"\S"), name="garage_work_description_ck")]
        indexes = [models.Index(fields=("job", "created_at", "id"), name="garage_work_job_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage work history is append-only.")
        self.description = self.description.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage work history is retained.")


class GarageStockCostLink(TimestampedUUIDModel):
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="stock_cost_links")
    expense = models.OneToOneField("vehicles.VehicleExpense", on_delete=models.PROTECT, related_name="garage_cost_link")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_stock_cost_links")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_stock_cost_links")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage Stock cost links are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage Stock cost links are retained.")


class GarageCustomerCharge(TimestampedUUIDModel):
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="customer_charges")
    version = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    reason = models.CharField(max_length=500, blank=True, default="")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_charges")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_charges")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("job", "version"), name="garage_charge_version_uq"),
            models.CheckConstraint(condition=Q(version__gt=0) & Q(amount__gte=0), name="garage_charge_values_ck"),
            models.CheckConstraint(condition=Q(version=1) | Q(reason__regex=r"\S"), name="garage_charge_reason_ck"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage customer charges are append-only.")
        self.reason = self.reason.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage customer charge history is retained.")


class GarageCustomerReceipt(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="garage_receipts")
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="customer_receipts")
    event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_customer_receipt")
    reference = models.CharField(max_length=200)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_receipts")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_receipts")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("tenant", "reference"), name="garage_receipt_reference_uq"), models.CheckConstraint(condition=Q(reference__regex=r"\S"), name="garage_receipt_reference_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage customer receipts are append-only.")
        self.reference = self.reference.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage customer receipts are retained.")


class GarageReceiptCorrection(TimestampedUUIDModel):
    receipt = models.ForeignKey(GarageCustomerReceipt, on_delete=models.PROTECT, related_name="corrections")
    version = models.PositiveIntegerField()
    previous_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_receipt_correction_previous")
    reversal_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_receipt_correction_reversal")
    replacement_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_receipt_correction_replacement", null=True, blank=True)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_receipt_corrections")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_receipt_corrections")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="garage_receipt_corr_reason_ck"), models.CheckConstraint(condition=Q(version__gt=0), name="garage_receipt_corr_version_ck"), models.UniqueConstraint(fields=("receipt", "version"), name="garage_receipt_corr_version_uq")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage receipt corrections are append-only.")
        self.reason = self.reason.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage receipt corrections are retained.")


class GarageCustomerCost(TimestampedUUIDModel):
    job = models.ForeignKey(GarageJob, on_delete=models.PROTECT, related_name="customer_costs")
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_costs")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_costs")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0) & Q(description__regex=r"\S"), name="garage_customer_cost_values_ck")]
        indexes = [models.Index(fields=("job", "created_at", "id"), name="garage_customer_cost_job_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage customer costs are append-only.")
        self.description = self.description.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage customer costs are retained.")


class GarageCustomerCostCorrection(TimestampedUUIDModel):
    cost = models.ForeignKey(GarageCustomerCost, on_delete=models.PROTECT, related_name="corrections")
    version = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=38, decimal_places=2)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_cost_corrections")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_cost_corrections")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("cost", "version"), name="garage_customer_cost_version_uq"), models.CheckConstraint(condition=Q(amount__gt=0) & Q(version__gt=0) & Q(reason__regex=r"\S"), name="garage_customer_correction_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage customer cost corrections are append-only.")
        self.reason = self.reason.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage customer cost corrections are retained.")


class GarageCustomerCostPayment(TimestampedUUIDModel):
    cost = models.ForeignKey(GarageCustomerCost, on_delete=models.PROTECT, related_name="payments")
    event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_customer_cost_payment")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_cost_payments")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_cost_payments")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage cost payments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage cost payments are retained.")


class GarageCustomerCostRefund(TimestampedUUIDModel):
    cost = models.ForeignKey(GarageCustomerCost, on_delete=models.PROTECT, related_name="refunds")
    event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_customer_cost_refund")
    applied_amount = models.DecimalField(max_digits=38, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_customer_cost_refunds")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_customer_cost_refunds")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(applied_amount__gte=0), name="garage_cost_refund_applied_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage cost refunds are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage cost refunds are retained.")


class GarageCustomerCostPaymentCorrection(TimestampedUUIDModel):
    payment = models.ForeignKey(GarageCustomerCostPayment, on_delete=models.PROTECT, related_name="corrections")
    version = models.PositiveIntegerField()
    previous_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_cost_correction_previous")
    reversal_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_cost_correction_reversal")
    replacement_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="garage_cost_correction_replacement", null=True, blank=True)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="garage_cost_payment_corrections")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="garage_cost_payment_corrections")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="garage_cost_pay_corr_reason_ck"), models.CheckConstraint(condition=Q(version__gt=0), name="garage_cost_pay_corr_version_ck"), models.UniqueConstraint(fields=("payment", "version"), name="garage_cost_pay_corr_version_uq")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Garage cost payment corrections are append-only.")
        self.reason = self.reason.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Garage cost payment corrections are retained.")


class LabourPerson(TimestampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="labour_people")
    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="labour_people")
    name = models.CharField(max_length=160)
    phone = models.CharField(max_length=40, blank=True, default="")
    is_active = models.BooleanField(default=True)
    status_version = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="labour_people_created")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="labour_people_created")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(name__regex=r"\S"), name="labour_person_name_ck")]
        indexes = [models.Index(fields=("tenant", "branch", "is_active", "id"), name="labour_person_scope_idx")]

    def delete(self, *args, **kwargs):
        raise ValidationError("Labour records are retained.")


class LabourStatusChange(TimestampedUUIDModel):
    person = models.ForeignKey(LabourPerson, on_delete=models.PROTECT, related_name="status_history")
    version = models.PositiveIntegerField()
    is_active = models.BooleanField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="labour_status_changes")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="labour_status_changes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("person", "version"), name="labour_status_version_uq"), models.CheckConstraint(condition=Q(version__gt=0), name="labour_status_version_ck")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Labour status history is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Labour status history is retained.")


class LabourPayment(TimestampedUUIDModel):
    person = models.ForeignKey(LabourPerson, on_delete=models.PROTECT, related_name="payments")
    event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="labour_payment")
    note = models.CharField(max_length=500, blank=True, default="")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="labour_payments")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="labour_payments")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Labour payments are append-only.")
        self.note = self.note.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Labour payments are retained.")


class LabourPaymentCorrection(TimestampedUUIDModel):
    payment = models.ForeignKey(LabourPayment, on_delete=models.PROTECT, related_name="corrections")
    version = models.PositiveIntegerField()
    previous_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="labour_correction_previous")
    reversal_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="labour_correction_reversal")
    replacement_event = models.OneToOneField("accounting.AccountingEvent", on_delete=models.PROTECT, related_name="labour_correction_replacement", null=True, blank=True)
    reason = models.CharField(max_length=500)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="labour_payment_corrections")
    module_revision = models.ForeignKey("tenants.CompanyModuleState", on_delete=models.PROTECT, related_name="labour_payment_corrections")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="labour_payment_correction_reason_ck"), models.CheckConstraint(condition=Q(version__gt=0), name="labour_payment_correction_version_ck"), models.UniqueConstraint(fields=("payment", "version"), name="labour_payment_correction_version_uq")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Labour payment corrections are append-only.")
        self.reason = self.reason.strip()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Labour payment corrections are retained.")
