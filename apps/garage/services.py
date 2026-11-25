from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from rest_framework.exceptions import NotFound, ValidationError
from uuid import uuid4

from apps.accounts.audit import record_event
from apps.accounts.policy import require_action
from apps.common.business_scope import business_scope
from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
from apps.garage.models import GarageCustomerCharge, GarageCustomerCost, GarageCustomerCostCorrection, GarageCustomerCostPayment, GarageCustomerCostPaymentCorrection, GarageCustomerCostRefund, GarageCustomerReceipt, GarageReceiptCorrection, GarageJob, GarageJobStatusChange, GarageStockCostLink, GarageWorkEntry, LabourPayment, LabourPaymentCorrection, LabourPerson, LabourStatusChange
from apps.accounting.models import AccountingAccount, AccountingApplication, AccountingCategory, AccountingEvent, AccountMovement
from apps.accounting.services import _event_row, _reverse_event
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleCode, Tenant
from apps.tenants.selectors import current_interval
from apps.vehicles.models import Vehicle, VehicleExpense, VehicleIdempotencyRecord
from apps.vehicles.services import _vehicle_investor_ids, create_vehicle_expense


def _require_job_action(actor, action, company, branch, resource=None):
    require_action(actor, action, company=company, branch=branch, resource=resource)
    if not BranchAssignment.objects.filter(membership__user=actor, membership__tenant=company, branch=branch).filter(current_interval(), membership__in=actor.tenant_memberships.filter(current_interval())).exists():
        raise PermissionDenied("An active Branch assignment is required.")


def job_data(job):
    return {"id": str(job.pk), "vehicle_id": str(job.vehicle_id), "branch_id": str(job.branch_id), "vehicle_registration": job.vehicle.registration, "vehicle_model": job.vehicle.model, "branch_name": job.branch.name, "context": job.context, "contact_name": job.contact_name, "contact_phone": job.contact_phone, "status": job.status, "status_version": job.status_version, "created_at": job.created_at.isoformat()}


def labour_person_data(person):
    return {"id": str(person.pk), "branch_id": str(person.branch_id), "branch_name": person.branch.name, "name": person.name, "phone": person.phone,
            "is_active": person.is_active, "status_version": person.status_version, "created_at": person.created_at.isoformat(), "updated_at": person.updated_at.isoformat()}


def list_labour_people(*, actor, company_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    current = require_action(actor, "labour.person.read", company=company)
    scope = business_scope(actor=current, company=company)
    rows = LabourPerson.objects.filter(tenant=company).select_related("branch")
    if not scope.is_company_reader:
        rows = rows.filter(branch_id__in=scope.allowed_branch_ids)
    return rows.order_by("name", "id")


def create_labour_person(*, actor, company_id, branch_id, name, phone, key, path):
    body = {"branch_id": str(branch_id), "name": name, "phone": phone}
    def operation(company, branch, revisions, current):
        _require_job_action(current, "labour.person.create", company, branch)
        person = LabourPerson.objects.create(tenant=company, branch=branch, name=name.strip(), phone=phone.strip(), created_by=current, module_revision=revisions[CompanyModuleCode.LABOUR])
        record_event(action="labour.person.create", actor=current, subject=current, company=company, branch=branch, resource=person, metadata={"labour_person_id": str(person.pk)})
        return DomainMutationResult(201, labour_person_data(person))
    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="labour.person.create", module_codes=(CompanyModuleCode.LABOUR,), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "labour.person.create", company, branch))


def update_labour_person(*, actor, company_id, person_id, name, phone, expected_updated_at, key, path):
    preview = LabourPerson.objects.filter(tenant_id=company_id, pk=person_id).first()
    if preview is None:
        raise NotFound("Labour person not found.")
    body = {"name": name.strip(), "phone": phone.strip(), "expected_updated_at": expected_updated_at.isoformat()}

    def operation(company, branch, revisions, current):
        person = LabourPerson.objects.select_for_update().filter(tenant=company, branch=branch, pk=person_id).first()
        if person is None:
            raise NotFound("Labour person not found.")
        _require_job_action(current, "labour.person.update", company, branch, person)
        if person.updated_at != expected_updated_at:
            raise DomainConflict("Labour details changed; reload and retry.", code="LABOUR_DETAILS_CONFLICT")
        old_name = person.name
        phone_changed = person.phone != body["phone"]
        person.name = body["name"]
        person.phone = body["phone"]
        person.save(update_fields=("name", "phone", "updated_at"))
        record_event(action="labour.person.update", actor=current, subject=current, company=company, branch=branch, resource=person,
                     metadata={"labour_person_id": str(person.pk), "old_name": old_name, "new_name": person.name, "phone_changed": phone_changed})
        return DomainMutationResult(200, labour_person_data(person))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="PATCH", path=path, key=key, body=body,
        action="labour.person.update", module_codes=(CompanyModuleCode.LABOUR,), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "labour.person.update", company, branch))


def change_labour_status(*, actor, company_id, person_id, is_active, expected_version, key, path):
    preview = LabourPerson.objects.filter(tenant_id=company_id, pk=person_id).first()
    if preview is None:
        raise NotFound("Labour person not found.")
    def operation(company, branch, revisions, current):
        person = LabourPerson.objects.select_for_update().filter(tenant=company, branch=branch, pk=person_id).first()
        if person is None:
            raise NotFound("Labour person not found.")
        _require_job_action(current, "labour.person.status", company, branch, person)
        if person.status_version != expected_version or person.is_active == is_active:
            raise DomainConflict("Labour status changed; reload and retry.", code="LABOUR_STATUS_CONFLICT")
        previous = person.is_active
        LabourStatusChange.objects.create(person=person, version=person.status_version + 1, is_active=is_active, actor=current, module_revision=revisions[CompanyModuleCode.LABOUR])
        person.is_active = is_active
        person.status_version += 1
        person.save(update_fields=("is_active", "status_version", "updated_at"))
        record_event(action="labour.person.status", actor=current, subject=current, company=company, branch=branch, resource=person,
                     metadata={"labour_person_id": str(person.pk), "previous_state": str(previous), "new_state": str(is_active)})
        return DomainMutationResult(200, labour_person_data(person))
    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body={"is_active": is_active, "expected_version": expected_version}, action="labour.person.status",
        module_codes=(CompanyModuleCode.LABOUR,), idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "labour.person.status", company, branch))


def labour_payment_data(payment):
    corrections = getattr(payment, "ordered_corrections", None)
    correction = (corrections[0] if corrections else None) if corrections is not None else payment.corrections.select_related("replacement_event", "previous_event").order_by("-version").first()
    event = correction.replacement_event if correction and correction.replacement_event_id else (None if correction else payment.event)
    return {"id": str(payment.pk), "event_id": str(event.pk) if event else str(correction.previous_event_id), "amount": format(event.amount if event else Decimal("0.00"), ".2f"),
            "effective_at": (event.effective_at if event else correction.previous_event.effective_at).isoformat(), "note": payment.note, "actor_id": str(payment.actor_id), "is_void": event is None}


def correct_labour_payment(*, actor, company_id, person_id, payment_id, expected_event_id, outcome, reason, replacement, key, path):
    preview = LabourPerson.objects.filter(tenant_id=company_id, pk=person_id).first()
    if preview is None:
        raise NotFound("Labour person not found.")
    body = {"expected_event_id": str(expected_event_id), "outcome": outcome, "reason": reason.strip(), "replacement": replacement}

    def authorize(current, company, branch):
        _require_job_action(current, "labour.payment.correct", company, branch)
        require_action(current, "accounting.event.correct", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        person = LabourPerson.objects.select_for_update().filter(tenant=company, branch=branch, pk=person_id).first()
        if person is None:
            raise NotFound("Labour person not found.")
        authorize(current, company, branch)
        payment = LabourPayment.objects.select_for_update().select_related("event").filter(person=person, pk=payment_id).first()
        if payment is None:
            raise NotFound("Labour payment not found.")
        previous_correction = payment.corrections.select_related("replacement_event").order_by("-version").first()
        current_event = previous_correction.replacement_event if previous_correction else payment.event
        if current_event is None or current_event.pk != expected_event_id:
            raise DomainConflict("Labour payment changed; reload and retry.", code="LABOUR_PAYMENT_CONFLICT")
        reversal, old_movements = _reverse_event(current_event, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING], reason=reason.strip())
        if len(old_movements) != 1:
            raise DomainConflict("Labour payment movement is invalid.", code="LABOUR_PAYMENT_MOVEMENT_INVALID")
        replacement_event = None
        if outcome == "REVERSE_AND_REPLACE":
            account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=replacement["account_id"], is_active=True).first()
            if account is None:
                raise NotFound("Cash/Bank account not found.")
            when = replacement["effective_at"]
            if when > timezone.now():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"effective_at": "Payment date cannot be in the future."})
            replacement_event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.LABOUR_PAYMENT,
                amount=replacement["amount"], actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
                description=current_event.description, source_reference=current_event.source_reference, effective_at=when,
                replaces_event=current_event, correction_reason=reason.strip())
            AccountMovement.objects.create(tenant=company, event=replacement_event, account=account, delta=-replacement["amount"])
        correction = LabourPaymentCorrection.objects.create(payment=payment, version=(previous_correction.version + 1 if previous_correction else 1), previous_event=current_event, reversal_event=reversal,
            replacement_event=replacement_event, reason=reason.strip(), actor=current, module_revision=revisions[CompanyModuleCode.LABOUR])
        record_event(action="labour.payment.correct", actor=current, subject=current, company=company, branch=branch, resource=payment,
            reason=reason.strip(), metadata={"labour_person_id": str(person.pk), "payment_id": str(payment.pk), "correction_id": str(correction.pk),
            "previous_amount": format(current_event.amount, ".2f"), "amount": format(replacement_event.amount if replacement_event else Decimal("0.00"), ".2f")})
        return DomainMutationResult(201, {"id": str(correction.pk), "reversal_event_id": str(reversal.pk), "replacement_event_id": str(replacement_event.pk) if replacement_event else None})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="labour.payment.correct", module_codes=(CompanyModuleCode.LABOUR, CompanyModuleCode.ACCOUNTING), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def create_labour_payment(*, actor, company_id, person_id, account_id, amount, note, effective_at, key, path):
    preview = LabourPerson.objects.filter(tenant_id=company_id, pk=person_id).first()
    if preview is None:
        raise NotFound("Labour person not found.")
    body = {"account_id": str(account_id), "amount": str(amount), "note": note, "effective_at": effective_at.isoformat()}

    def authorize(current, company, branch):
        _require_job_action(current, "labour.payment.create", company, branch)
        require_action(current, "accounting.payment.create", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        person = LabourPerson.objects.select_for_update().filter(tenant=company, branch=branch, pk=person_id).first()
        if person is None:
            raise NotFound("Labour person not found.")
        _require_job_action(current, "labour.payment.create", company, branch, person)
        require_action(current, "accounting.payment.create", company=company, branch=branch, resource=person)
        if not person.is_active:
            raise DomainConflict("Labour person is inactive.", code="LABOUR_PERSON_INACTIVE")
        if effective_at > timezone.now():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"effective_at": "Payment date cannot be in the future."})
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.LABOUR_PAYMENT,
            amount=amount, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
            description="Labour payment", source_reference=f"LABOUR-{uuid4()}", effective_at=effective_at)
        AccountMovement.objects.create(tenant=company, event=event, account=account, delta=-amount)
        payment = LabourPayment.objects.create(person=person, event=event, note=note, actor=current, module_revision=revisions[CompanyModuleCode.LABOUR])
        record_event(action="labour.payment.create", actor=current, subject=current, company=company, branch=branch, resource=person,
            metadata={"labour_person_id": str(person.pk), "payment_id": str(payment.pk), "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")})
        return DomainMutationResult(201, labour_payment_data(payment))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="labour.payment.create", module_codes=(CompanyModuleCode.LABOUR, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def _garage_received(job):
    original = job.customer_receipts.aggregate(total=Sum("event__amount"))["total"] or Decimal("0.00")
    changes = GarageReceiptCorrection.objects.filter(receipt__job=job).aggregate(previous=Sum("previous_event__amount"), replacement=Sum("replacement_event__amount"))
    return original - (changes["previous"] or Decimal("0.00")) + (changes["replacement"] or Decimal("0.00"))


def job_detail(job):
    data = job_data(job)
    if job.context == GarageJob.Context.EXTERNAL_CUSTOMER:
        charge = job.customer_charges.order_by("-version").first()
        received = _garage_received(job)
        latest = GarageCustomerCostCorrection.objects.filter(cost_id=OuterRef("pk")).order_by("-version").values("amount")[:1]
        cost_total = job.customer_costs.annotate(current_amount=Coalesce(Subquery(latest), "amount")).aggregate(total=Sum("current_amount"))["total"] or Decimal("0.00")
        data["customer_cost_total"] = format(cost_total, ".2f")
        data["customer_charge"] = format(charge.amount, ".2f") if charge else None
        data["charge_version"] = charge.version if charge else 0
        data["received"] = format(received, ".2f")
        data["outstanding"] = format(charge.amount - received, ".2f") if charge else None
    return data


def list_jobs(*, actor, company_id, branch_id=None, context=None):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if not company:
        raise NotFound("Company not found.")
    current = require_action(actor, "garage.job.read", company=company)
    scope = business_scope(actor=current, company=company)
    rows = GarageJob.objects.filter(tenant=company).select_related("branch", "vehicle")
    if not scope.is_company_reader:
        rows = rows.filter(branch_id__in=scope.allowed_branch_ids)
    if branch_id is not None:
        from uuid import UUID
        branch_uuid = UUID(str(branch_id))
        branch_exists = Branch.objects.filter(pk=branch_uuid, tenant=company).exists()
        allowed_strs = {str(item) for item in scope.allowed_branch_ids}
        if not branch_exists or (not scope.is_company_reader and str(branch_uuid) not in allowed_strs):
            raise NotFound("Branch not found.")
        rows = rows.filter(branch_id=branch_uuid)
    if context is not None:
        rows = rows.filter(context=context)
    return rows.order_by("-created_at", "id")


def job_summary(*, actor, company_id, branch_id=None):
    """Return full, permission-scoped Garage Job counts without paging rows."""
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    current = require_action(actor, "garage.job.read", company=company)
    scope = business_scope(actor=current, company=company)
    rows = GarageJob.objects.filter(tenant=company)
    if not scope.is_company_reader:
        rows = rows.filter(branch_id__in=scope.allowed_branch_ids)
    if branch_id is not None:
        branch_exists = Branch.objects.filter(pk=branch_id, tenant=company).exists()
        if not branch_exists or (not scope.is_company_reader and branch_id not in scope.allowed_branch_ids):
            # Do not turn an unauthorized or cross-Company Branch into a successful zero.
            raise NotFound("Branch not found.")
        rows = rows.filter(branch_id=branch_id)
    totals = rows.aggregate(
        total=Count("id"),
        open=Count("id", filter=Q(status=GarageJob.Status.OPEN)),
        completed=Count("id", filter=Q(status=GarageJob.Status.COMPLETED)),
        external_customer=Count("id", filter=Q(context=GarageJob.Context.EXTERNAL_CUSTOMER)),
    )
    return {
        "company_id": str(company.pk),
        "branch_id": str(branch_id) if branch_id else None,
        "total_jobs": totals["total"] or 0,
        "open_jobs": totals["open"] or 0,
        "completed_jobs": totals["completed"] or 0,
        "external_customer_jobs": totals["external_customer"] or 0,
    }


def get_job(*, actor, company_id, job_id):
    job = list_jobs(actor=actor, company_id=company_id).filter(pk=job_id).first()
    if job is None:
        raise NotFound("Job not found.")
    return job


def work_data(entry):
    return {"id": str(entry.pk), "description": entry.description, "actor_id": str(entry.actor_id), "created_at": entry.created_at.isoformat()}


def charge_data(charge):
    return {"id": str(charge.pk), "version": charge.version, "amount": format(charge.amount, ".2f"), "reason": charge.reason, "actor_id": str(charge.actor_id), "created_at": charge.created_at.isoformat()}


def customer_cost_data(cost):
    correction = max(cost.corrections.all(), key=lambda row: row.version, default=None)
    amount = correction.amount if correction else cost.amount
    paid = _customer_cost_paid(cost)
    refunded = _customer_cost_refunded(cost)
    return {"id": str(cost.pk), "description": cost.description, "amount": format(amount, ".2f"),
            "paid": format(paid, ".2f"), "refunded": format(refunded, ".2f"),
            "payable": format(amount - paid + refunded, ".2f"),
            "version": correction.version if correction else 0, "actor_id": str(cost.actor_id), "created_at": cost.created_at.isoformat()}


def write_customer_cost(*, actor, company_id, job_id, amount, key, path, description=None, cost_id=None, expected_version=None, reason=""):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    action = "garage.customer_cost.correct" if cost_id else "garage.customer_cost.create"
    body = {"amount": str(amount), "description": description, "cost_id": str(cost_id) if cost_id else None,
            "expected_version": expected_version, "reason": reason}

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, action, company, branch, job)
        if job.status != GarageJob.Status.OPEN or job.context != GarageJob.Context.EXTERNAL_CUSTOMER:
            raise DomainConflict("An open external customer Job is required.", code="GARAGE_CUSTOMER_JOB_REQUIRED")
        if cost_id:
            cost = GarageCustomerCost.objects.select_for_update().filter(job=job, pk=cost_id).first()
            if cost is None:
                raise NotFound("Customer Job cost not found.")
            previous = cost.corrections.order_by("-version").first()
            version = previous.version if previous else 0
            if expected_version != version:
                raise DomainConflict("Cost changed; reload and retry.", code="GARAGE_COST_CONFLICT")
            net_paid = _customer_cost_net_paid(cost)
            if amount < net_paid:
                raise DomainConflict("Cost cannot be less than the net amount paid after refunds.", code="GARAGE_COST_BELOW_PAYMENTS")
            GarageCustomerCostCorrection.objects.create(cost=cost, version=version + 1, amount=amount, reason=reason, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
            metadata = {"job_id": str(job.pk), "expense_id": str(cost.pk), "amount": format(amount, ".2f"), "previous_amount": format(previous.amount if previous else cost.amount, ".2f")}
        else:
            cost = GarageCustomerCost.objects.create(job=job, description=description, amount=amount, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
            metadata = {"job_id": str(job.pk), "expense_id": str(cost.pk), "amount": format(amount, ".2f")}
        record_event(action=action, actor=current, subject=current, company=company, branch=branch, resource=job, reason=reason, metadata=metadata)
        return DomainMutationResult(201, customer_cost_data(cost))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action=action, module_codes=(CompanyModuleCode.GARAGE,), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, action, company, branch))


def customer_cost_payment_data(payment):
    corrections = getattr(payment, "ordered_corrections", None)
    correction = (corrections[0] if corrections else None) if corrections is not None else payment.corrections.select_related("replacement_event", "previous_event").order_by("-version").first()
    event = correction.replacement_event if correction and correction.replacement_event_id else (None if correction else payment.event)
    return {"id": str(payment.pk), "event_id": str(event.pk) if event else str(correction.previous_event_id),
            "amount": format(event.amount if event else Decimal("0.00"), ".2f"),
            "effective_at": (event.effective_at if event else correction.previous_event.effective_at).isoformat(),
            "actor_id": str(payment.actor_id), "is_void": event is None}


def _customer_cost_paid(cost):
    if hasattr(cost, "calculated_paid"):
        return cost.calculated_paid
    original = cost.payments.aggregate(total=Sum("event__amount"))["total"] or Decimal("0.00")
    changes = GarageCustomerCostPaymentCorrection.objects.filter(payment__cost=cost).aggregate(previous=Sum("previous_event__amount"), replacement=Sum("replacement_event__amount"))
    return original - (changes["previous"] or Decimal("0.00")) + (changes["replacement"] or Decimal("0.00"))


def _customer_cost_refunded(cost):
    if hasattr(cost, "calculated_refunded"):
        return cost.calculated_refunded
    return cost.refunds.aggregate(total=Sum("applied_amount"))["total"] or Decimal("0.00")


def _customer_cost_net_paid(cost):
    return _customer_cost_paid(cost) - _customer_cost_refunded(cost)


def preview_customer_cost_refund(*, actor, company_id, job_id, cost_id, amount):
    """Read a consistent preview; posting must reauthorize and recalculate."""
    from apps.garage.refund_allocation import split_customer_cost_refund

    job = get_job(actor=actor, company_id=company_id, job_id=job_id)
    with transaction.atomic():
        job = GarageJob.objects.select_for_update().get(pk=job.pk, tenant_id=company_id)
        cost = job.customer_costs.filter(pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        paid = _customer_cost_paid(cost)
        refunded = cost.refunds.aggregate(total=Sum("applied_amount"))["total"] or Decimal("0.00")
        applied, excess = split_customer_cost_refund(amount, paid, refunded)
        return {"paid": format(paid, ".2f"), "previous_refunds": format(refunded, ".2f"),
                "applied_amount": format(applied, ".2f"), "excess_amount": format(excess, ".2f")}


def pay_customer_cost(*, actor, company_id, job_id, cost_id, account_id, amount, effective_at, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    body = {"account_id": str(account_id), "amount": str(amount), "effective_at": effective_at.isoformat() if effective_at else None}

    def authorize(current, company, branch):
        _require_job_action(current, "garage.customer_cost.payment", company, branch)
        require_action(current, "accounting.payment.create", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, branch=branch, pk=job_id).first()
        if job is None:
            raise NotFound("Job not found.")
        authorize(current, company, branch)
        cost = GarageCustomerCost.objects.select_for_update().filter(job=job, pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        latest = cost.corrections.order_by("-version").first()
        cost_amount = latest.amount if latest else cost.amount
        net_paid = _customer_cost_net_paid(cost)
        if amount <= 0 or net_paid + amount > cost_amount:
            raise DomainConflict("Payment exceeds the remaining cost amount.", code="GARAGE_COST_PAYMENT_EXCEEDED")
        when = effective_at or timezone.now()
        if when > timezone.now():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"effective_at": "Payment date cannot be in the future."})
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.GARAGE_COST_PAYMENT,
            amount=amount, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING], description="Garage customer Job cost payment",
            source_reference=f"GARAGE-COST-{uuid4()}", effective_at=when)
        AccountMovement.objects.create(tenant=company, event=event, account=account, delta=-amount)
        payment = GarageCustomerCostPayment.objects.create(cost=cost, event=event, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.customer_cost.payment", actor=current, subject=current, company=company, branch=branch, resource=cost,
            metadata={"job_id": str(job.pk), "expense_id": str(cost.pk), "payment_id": str(payment.pk), "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")})
        return DomainMutationResult(201, customer_cost_payment_data(payment))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.customer_cost.payment", module_codes=(CompanyModuleCode.GARAGE, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def customer_cost_refund_data(refund, *, income_event=None):
    amount = refund.event.amount
    return {
        "id": str(refund.pk),
        "event_id": str(refund.event_id),
        "amount": format(amount, ".2f"),
        "applied_amount": format(refund.applied_amount, ".2f"),
        "excess_amount": format(amount - refund.applied_amount, ".2f"),
        "income_event_id": str(income_event.pk) if income_event else None,
        "effective_at": refund.event.effective_at.isoformat(),
        "actor_id": str(refund.actor_id),
    }


def create_customer_cost_refund(*, actor, company_id, job_id, cost_id, account_id, amount,
                                effective_at, excess_income_category_id=None,
                                excess_income_description="", key, path):
    from apps.garage.refund_allocation import split_customer_cost_refund

    description = (excess_income_description or "").strip()
    when = effective_at or timezone.now()
    body = {
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "effective_at": effective_at.isoformat() if effective_at else None,
        "excess_income_category_id": str(excess_income_category_id) if excess_income_category_id else None,
        "excess_income_description": description,
    }
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")

    def authorize(current, company, branch):
        _require_job_action(current, "garage.customer_cost.refund", company, branch)
        require_action(current, "accounting.receipt.create", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, branch=branch, pk=job_id).first()
        if job is None:
            raise NotFound("Job not found.")
        authorize(current, company, branch)
        cost = GarageCustomerCost.objects.select_for_update().filter(job=job, pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        if amount <= 0 or when > timezone.now():
            raise ValidationError({"amount": "Refund must be positive and cannot be future-dated."})

        paid = _customer_cost_paid(cost)
        refunded = _customer_cost_refunded(cost)
        applied, excess = split_customer_cost_refund(amount, paid, refunded)
        category = None
        if excess > 0:
            if not excess_income_category_id or not description:
                raise ValidationError({
                    "excess_income_category_id": "The excess needs an Accountant-selected Company Income category and note.",
                    "excess_income_description": "Explain why the excess is Company Income.",
                })
            require_action(current, "accounting.income.create", company=company, branch=branch, resource=job)
            category = AccountingCategory.objects.select_for_update().filter(
                tenant=company, pk=excess_income_category_id,
                kind=AccountingCategory.Kind.INCOME, is_active=True,
            ).first()
            if category is None:
                raise NotFound("Active Company Income category not found.")
        elif excess_income_category_id or description:
            raise ValidationError({
                "excess_income_category_id": "An Income category and note are only accepted when the refund exceeds the remaining paid amount."
            })

        account = AccountingAccount.objects.select_for_update().filter(
            tenant=company, pk=account_id, is_active=True,
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")

        refund_id = uuid4()
        income_event = None
        if excess > 0:
            income_event = _event_row(
                tenant=company, branch=branch, event_type=AccountingEvent.EventType.INCOME,
                amount=excess, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
                category=category, description=description,
                source_reference=f"GARAGE-COST-REFUND-EXCESS-{refund_id}", effective_at=when,
            )
        event = _event_row(
            tenant=company, branch=branch, event_type=AccountingEvent.EventType.GARAGE_COST_REFUND,
            amount=amount, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
            description=f"Garage customer Job cost refund: {cost.description}",
            source_reference=f"GARAGE-COST-REFUND-{refund_id}", effective_at=when,
        )
        AccountMovement.objects.create(tenant=company, event=event, account=account, delta=amount)
        refund = GarageCustomerCostRefund.objects.create(
            id=refund_id, cost=cost, event=event, applied_amount=applied, actor=current,
            module_revision=revisions[CompanyModuleCode.GARAGE],
        )
        if income_event is not None:
            AccountingApplication.objects.create(
                tenant=company, source_event=event, target_event=income_event,
                amount=excess, actor=current, module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            )
        record_event(action="garage.customer_cost.refund", actor=current, subject=current,
            company=company, branch=branch, resource=cost,
            metadata={"job_id": str(job.pk), "cost_id": str(cost.pk), "refund_id": str(refund.pk),
                      "accounting_event_id": str(event.pk), "amount": format(amount, ".2f"),
                      "applied_amount": format(applied, ".2f"),
                      "excess_income_event_id": str(income_event.pk) if income_event else None})
        return DomainMutationResult(201, customer_cost_refund_data(refund, income_event=income_event))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.customer_cost.refund", module_codes=(CompanyModuleCode.GARAGE, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id, authorize_replay=authorize,
    )


def correct_customer_cost_payment(*, actor, company_id, job_id, cost_id, payment_id, expected_event_id, outcome, reason, replacement, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    body = {"expected_event_id": str(expected_event_id), "outcome": outcome, "reason": reason.strip(), "replacement": replacement}

    def authorize(current, company, branch):
        _require_job_action(current, "garage.customer_cost.payment.correct", company, branch)
        require_action(current, "accounting.event.correct", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, branch=branch, pk=job_id).first()
        if job is None:
            raise NotFound("Job not found.")
        authorize(current, company, branch)
        cost = GarageCustomerCost.objects.select_for_update().filter(job=job, pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        payment = GarageCustomerCostPayment.objects.select_for_update().select_related("event").filter(cost=cost, pk=payment_id).first()
        if payment is None:
            raise NotFound("Customer Job cost payment not found.")
        previous = payment.corrections.select_related("replacement_event").order_by("-version").first()
        current_event = previous.replacement_event if previous else payment.event
        if current_event is None or current_event.pk != expected_event_id:
            raise DomainConflict("Cost payment changed; reload and retry.", code="GARAGE_COST_PAYMENT_CONFLICT")
        latest_cost = cost.corrections.order_by("-version").first()
        cost_amount = latest_cost.amount if latest_cost else cost.amount
        new_paid = _customer_cost_paid(cost) - current_event.amount + (replacement["amount"] if replacement else Decimal("0.00"))
        refunded = _customer_cost_refunded(cost)
        new_net_paid = new_paid - refunded
        if new_net_paid < 0:
            raise DomainConflict("Payment correction cannot reduce net payments below already applied refunds.", code="GARAGE_COST_PAYMENT_BELOW_REFUNDS")
        if new_net_paid > cost_amount:
            raise DomainConflict("Corrected payment exceeds the cost amount.", code="GARAGE_COST_PAYMENT_EXCEEDED")
        reversal, movements = _reverse_event(current_event, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING], reason=reason.strip())
        if len(movements) != 1:
            raise DomainConflict("Cost payment movement is invalid.", code="GARAGE_COST_PAYMENT_MOVEMENT_INVALID")
        replacement_event = None
        if outcome == "REVERSE_AND_REPLACE":
            account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=replacement["account_id"], is_active=True).first()
            if account is None:
                raise NotFound("Cash/Bank account not found.")
            when = replacement["effective_at"]
            if when > timezone.now():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"effective_at": "Payment date cannot be in the future."})
            replacement_event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.GARAGE_COST_PAYMENT,
                amount=replacement["amount"], actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING], description=current_event.description,
                source_reference=current_event.source_reference, effective_at=when, replaces_event=current_event, correction_reason=reason.strip())
            AccountMovement.objects.create(tenant=company, event=replacement_event, account=account, delta=-replacement["amount"])
        correction = GarageCustomerCostPaymentCorrection.objects.create(payment=payment, version=(previous.version + 1 if previous else 1),
            previous_event=current_event, reversal_event=reversal, replacement_event=replacement_event, reason=reason.strip(), actor=current,
            module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.customer_cost.payment.correct", actor=current, subject=current, company=company, branch=branch, resource=payment,
            reason=reason.strip(), metadata={"job_id": str(job.pk), "expense_id": str(cost.pk), "payment_id": str(payment.pk),
            "correction_id": str(correction.pk), "previous_amount": format(current_event.amount, ".2f"),
            "amount": format(replacement_event.amount if replacement_event else Decimal("0.00"), ".2f")})
        return DomainMutationResult(201, {"id": str(correction.pk), "reversal_event_id": str(reversal.pk), "replacement_event_id": str(replacement_event.pk) if replacement_event else None})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.customer_cost.payment.correct", module_codes=(CompanyModuleCode.GARAGE, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def record_charge(*, actor, company_id, job_id, amount, expected_version, reason, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    body = {"amount": str(amount), "expected_version": expected_version, "reason": reason}

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.charge.record", company, branch, job)
        if job.status != GarageJob.Status.OPEN or job.context != GarageJob.Context.EXTERNAL_CUSTOMER:
            raise DomainConflict("An open external customer Job is required.", code="GARAGE_CUSTOMER_JOB_REQUIRED")
        previous = job.customer_charges.order_by("-version").first()
        version = previous.version if previous else 0
        if version != expected_version:
            raise DomainConflict("Charge changed; reload and retry.", code="GARAGE_CHARGE_CONFLICT")
        if previous and not reason.strip():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"reason": "A reason is required for a charge correction."})
        collected = _garage_received(job)
        if amount < collected:
            raise DomainConflict("Charge cannot be less than the amount already collected.", code="GARAGE_CHARGE_BELOW_RECEIPTS")
        charge = GarageCustomerCharge.objects.create(job=job, version=version + 1, amount=amount, reason=reason, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.charge.record", actor=current, subject=current, company=company, branch=branch, resource=job, reason=reason, metadata={"job_id": str(job.pk), "amount": format(amount, ".2f"), "version": version + 1, "previous_amount": format(previous.amount, ".2f") if previous else None})
        return DomainMutationResult(201, charge_data(charge))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body, action="garage.charge.record", module_codes=(CompanyModuleCode.GARAGE,), idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "garage.charge.record", company, branch))


def receipt_data(receipt):
    corrections = getattr(receipt, "ordered_corrections", None)
    correction = (corrections[0] if corrections else None) if corrections is not None else receipt.corrections.select_related("replacement_event", "previous_event").order_by("-version").first()
    event = correction.replacement_event if correction and correction.replacement_event_id else (None if correction else receipt.event)
    return {"id": str(receipt.pk), "event_id": str(event.pk) if event else str(correction.previous_event_id), "amount": format(event.amount if event else Decimal("0.00"), ".2f"), "reference": receipt.reference, "effective_at": (event.effective_at if event else correction.previous_event.effective_at).isoformat(), "actor_id": str(receipt.actor_id), "is_void": event is None}


def record_receipt(*, actor, company_id, job_id, account_id, amount, reference, key, path, effective_at=None):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    reference = reference.strip()
    body = {"account_id": str(account_id), "amount": str(amount), "reference": reference,
            "effective_at": effective_at.isoformat() if effective_at else None}

    def authorize(current, company, branch):
        _require_job_action(current, "garage.receipt.record", company, branch)
        require_action(current, "accounting.receipt.create", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.receipt.record", company, branch, job)
        require_action(current, "accounting.receipt.create", company=company, branch=branch, resource=job)
        if job.context != GarageJob.Context.EXTERNAL_CUSTOMER:
            raise DomainConflict("An external customer Job is required.", code="GARAGE_CUSTOMER_JOB_REQUIRED")
        charge = job.customer_charges.order_by("-version").first()
        collected = _garage_received(job)
        if charge is None or amount <= 0 or collected + amount > charge.amount:
            raise DomainConflict("Receipt exceeds the current outstanding Job charge.", code="GARAGE_RECEIVABLE_EXCEEDED")
        when = effective_at or timezone.now()
        if when > timezone.now():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"effective_at": "Receipt date cannot be in the future."})
        if GarageCustomerReceipt.objects.filter(tenant=company, reference=reference).exists():
            raise DomainConflict("This Garage receipt reference already exists in this Company.", code="GARAGE_RECEIPT_REFERENCE_DUPLICATE")
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.GARAGE_RECEIPT,
            amount=amount, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
            description="Garage customer receipt", source_reference=reference, effective_at=when)
        AccountMovement.objects.create(tenant=company, event=event, account=account, delta=amount)
        receipt = GarageCustomerReceipt.objects.create(tenant=company, job=job, event=event, reference=reference, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.receipt.record", actor=current, subject=current, company=company, branch=branch, resource=job,
            metadata={"job_id": str(job.pk), "receipt_id": str(receipt.pk), "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")})
        return DomainMutationResult(201, receipt_data(receipt))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.receipt.record", module_codes=(CompanyModuleCode.GARAGE, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def correct_receipt(*, actor, company_id, job_id, receipt_id, expected_event_id, outcome, reason, replacement, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    body = {"expected_event_id": str(expected_event_id), "outcome": outcome, "reason": reason.strip(), "replacement": replacement}

    def authorize(current, company, branch):
        _require_job_action(current, "garage.receipt.correct", company, branch)
        require_action(current, "accounting.event.correct", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, branch=branch, pk=job_id).first()
        if job is None:
            raise NotFound("Job not found.")
        authorize(current, company, branch)
        receipt = GarageCustomerReceipt.objects.select_for_update().select_related("event").filter(tenant=company, job=job, pk=receipt_id).first()
        if receipt is None:
            raise NotFound("Garage receipt not found.")
        previous_correction = receipt.corrections.select_related("replacement_event").order_by("-version").first()
        current_event = previous_correction.replacement_event if previous_correction else receipt.event
        if current_event is None or current_event.pk != expected_event_id:
            raise DomainConflict("Garage receipt changed; reload and retry.", code="GARAGE_RECEIPT_CONFLICT")
        charge = job.customer_charges.order_by("-version").first()
        new_total = _garage_received(job) - current_event.amount + (replacement["amount"] if replacement else Decimal("0.00"))
        if charge is None or new_total < 0 or new_total > charge.amount:
            raise DomainConflict("Corrected receipt exceeds the current Job charge.", code="GARAGE_RECEIVABLE_EXCEEDED")
        reversal, old_movements = _reverse_event(current_event, actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING], reason=reason.strip())
        if len(old_movements) != 1:
            raise DomainConflict("Garage receipt movement is invalid.", code="GARAGE_RECEIPT_MOVEMENT_INVALID")
        replacement_event = None
        if outcome == "REVERSE_AND_REPLACE":
            account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=replacement["account_id"], is_active=True).first()
            if account is None:
                raise NotFound("Cash/Bank account not found.")
            when = replacement["effective_at"]
            if when > timezone.now():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"effective_at": "Receipt date cannot be in the future."})
            replacement_event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.GARAGE_RECEIPT,
                amount=replacement["amount"], actor=current, revision=revisions[CompanyModuleCode.ACCOUNTING],
                description=current_event.description, source_reference=current_event.source_reference, effective_at=when,
                replaces_event=current_event, correction_reason=reason.strip())
            AccountMovement.objects.create(tenant=company, event=replacement_event, account=account, delta=replacement["amount"])
        correction = GarageReceiptCorrection.objects.create(receipt=receipt, version=(previous_correction.version + 1 if previous_correction else 1),
            previous_event=current_event, reversal_event=reversal, replacement_event=replacement_event, reason=reason.strip(), actor=current,
            module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.receipt.correct", actor=current, subject=current, company=company, branch=branch, resource=receipt,
            reason=reason.strip(), metadata={"job_id": str(job.pk), "receipt_id": str(receipt.pk), "correction_id": str(correction.pk),
            "previous_amount": format(current_event.amount, ".2f"), "amount": format(replacement_event.amount if replacement_event else Decimal("0.00"), ".2f")})
        return DomainMutationResult(201, {"id": str(correction.pk), "reversal_event_id": str(reversal.pk), "replacement_event_id": str(replacement_event.pk) if replacement_event else None})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.receipt.correct", module_codes=(CompanyModuleCode.GARAGE, CompanyModuleCode.ACCOUNTING), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def stock_cost_data(link):
    correction = max(link.expense.corrections.all(), key=lambda row: row.version, default=None)
    amount = correction.amount if correction else link.expense.amount
    return {"id": str(link.pk), "expense_id": str(link.expense_id), "amount": format(amount, ".2f"), "description": link.expense.description, "created_at": link.created_at.isoformat()}


def link_stock_cost(*, actor, company_id, job_id, expense_id, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    expense_preview = VehicleExpense.objects.filter(tenant_id=company_id, pk=expense_id).first()
    if expense_preview is None:
        raise NotFound("Vehicle Expense not found.")
    investor_linked = expense_preview.investor_id is not None
    modules = [CompanyModuleCode.GARAGE, CompanyModuleCode.VEHICLE_MANAGEMENT]
    if investor_linked:
        modules.append(CompanyModuleCode.INVESTMENT)

    def authorize(current, company, branch):
        _require_job_action(current, "garage.cost.link", company, branch)
        expense = VehicleExpense.objects.filter(tenant=company, pk=expense_id, branch=branch).first()
        if expense is None:
            raise NotFound("Vehicle Expense not found.")
        require_action(current, "vehicle.expense.create", company=company, branch=branch, resource=expense)
        if expense.investor_id is not None:
            require_action(current, "vehicle.expense.fund", company=company, branch=branch, resource=expense)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.cost.link", company, branch, job)
        expense = VehicleExpense.objects.select_for_update().filter(tenant=company, pk=expense_id).first()
        if expense is None:
            raise NotFound("Vehicle Expense not found.")
        require_action(current, "vehicle.expense.create", company=company, branch=branch, resource=expense)
        if (expense.investor_id is not None) != investor_linked:
            raise DomainConflict("Expense funding changed; reload.", code="GARAGE_COST_SOURCE_CHANGED")
        if investor_linked:
            require_action(current, "vehicle.expense.fund", company=company, branch=branch, resource=expense)
        if job.status != GarageJob.Status.OPEN or job.context != GarageJob.Context.STOCK:
            raise DomainConflict("An open Stock Job is required.", code="GARAGE_STOCK_JOB_REQUIRED")
        if expense.vehicle_id != job.vehicle_id or expense.branch_id != job.branch_id:
            raise DomainConflict("The expense must belong to this Job's Vehicle and Branch.", code="GARAGE_COST_SCOPE_MISMATCH")
        if GarageStockCostLink.objects.filter(expense=expense).exists():
            raise DomainConflict("The Vehicle Expense is already linked to a Job.", code="GARAGE_COST_ALREADY_LINKED")
        link = GarageStockCostLink.objects.create(job=job, expense=expense, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.cost.link", actor=current, subject=current, company=company, branch=branch, resource=job, metadata={"job_id": str(job.pk), "expense_id": str(expense.pk)})
        return DomainMutationResult(201, stock_cost_data(link))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body={"expense_id": str(expense_id)}, action="garage.cost.link", module_codes=tuple(modules), idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def create_stock_cost(*, actor, company_id, job_id, key, path, amount, description,
                      investor_id=None, investor_fund_amount=None,
                      running_capital_amount=None, effective_at=None):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if preview is None:
        raise NotFound("Job not found.")
    investor_linked = investor_id is not None or (investor_fund_amount is not None and investor_fund_amount > 0)
    modules = [CompanyModuleCode.GARAGE, CompanyModuleCode.VEHICLE_MANAGEMENT]
    if investor_linked:
        modules.append(CompanyModuleCode.INVESTMENT)
    body = {"amount": str(amount), "description": description, "investor_id": str(investor_id) if investor_id else None,
            "investor_fund_amount": str(investor_fund_amount) if investor_fund_amount is not None else None,
            "running_capital_amount": str(running_capital_amount) if running_capital_amount is not None else None,
            "effective_at": effective_at.isoformat() if effective_at else None}

    def authorize(current, company, branch):
        _require_job_action(current, "garage.cost.link", company, branch)
        require_action(current, "vehicle.expense.create", company=company, branch=branch)
        if investor_linked:
            require_action(current, "vehicle.expense.fund", company=company, branch=branch)

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.cost.link", company, branch, job)
        if job.status != GarageJob.Status.OPEN or job.context != GarageJob.Context.STOCK:
            raise DomainConflict("An open Stock Job is required.", code="GARAGE_STOCK_JOB_REQUIRED")
        vehicle = Vehicle.objects.select_for_update().filter(tenant=company, pk=job.vehicle_id, is_active=True).first()
        if vehicle is None or vehicle.current_branch_id != branch.pk:
            raise DomainConflict("Vehicle has moved; create the cost at its current Branch.", code="GARAGE_VEHICLE_BRANCH_CHANGED")
        result = create_vehicle_expense(actor=current, company_id=company.pk, vehicle_id=vehicle.pk,
            key=f"garage-internal-{uuid4()}", path=path + "#vehicle-cost", amount=amount, description=description,
            investor_id=investor_id, investor_fund_amount=investor_fund_amount,
            running_capital_amount=running_capital_amount, effective_at=effective_at)
        expense = VehicleExpense.objects.get(tenant=company, pk=result.body["id"])
        link = GarageStockCostLink.objects.create(job=job, expense=expense, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.cost.link", actor=current, subject=current, company=company, branch=branch, resource=job, metadata={"job_id": str(job.pk), "expense_id": str(expense.pk)})
        return DomainMutationResult(201, stock_cost_data(link))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="garage.cost.link", module_codes=tuple(modules), idempotency_model=VehicleIdempotencyRecord,
        operation=operation, branch_id=preview.branch_id, authorize_replay=authorize)


def add_work(*, actor, company_id, job_id, description, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if not preview:
        raise NotFound("Job not found.")
    description = description.strip()
    body = {"description": description}

    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.work.create", company, branch, job)
        if job.status != GarageJob.Status.OPEN:
            raise DomainConflict("Reopen the Job before adding work.", code="GARAGE_JOB_COMPLETED")
        entry = GarageWorkEntry.objects.create(job=job, description=description, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.work.create", actor=current, subject=current, company=company, branch=branch, resource=job, metadata={"job_id": str(job.pk), "description": description})
        return DomainMutationResult(201, work_data(entry))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body, action="garage.work.create", module_codes=(CompanyModuleCode.GARAGE,), idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "garage.work.create", company, branch))


def create_job(*, actor, company_id, branch_id, vehicle_id, context, contact_name, contact_phone, key, path):
    body = {"branch_id": str(branch_id), "vehicle_id": str(vehicle_id), "context": context, "contact_name": contact_name, "contact_phone": contact_phone}
    def operation(company, branch, revisions, current):
        _require_job_action(current, "garage.job.create", company, branch)
        vehicle = Vehicle.objects.select_for_update().filter(tenant=company, pk=vehicle_id, is_active=True).first()
        if vehicle is None:
            raise NotFound("Vehicle not found.")
        if vehicle.current_branch_id != branch.pk:
            raise DomainConflict("Vehicle Branch changed. Reload and try again.", code="GARAGE_VEHICLE_BRANCH_CHANGED")
        if context == GarageJob.Context.EXTERNAL_CUSTOMER and _vehicle_investor_ids(company=company, vehicle=vehicle):
            raise DomainConflict("Investor responsibility must be resolved before an external customer Job can be created.", code="GARAGE_INVESTOR_RESPONSIBILITY_UNKNOWN")
        job = GarageJob.objects.create(tenant=company, branch=branch, vehicle=vehicle, context=context, contact_name=contact_name, contact_phone=contact_phone, created_by=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        record_event(action="garage.job.create", actor=current, subject=current, company=company, branch=branch, resource=job, metadata={"job_id": str(job.pk), "vehicle_id": str(vehicle.pk)})
        return DomainMutationResult(201, job_data(job))
    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body, action="garage.job.create", module_codes=(CompanyModuleCode.GARAGE,), idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "garage.job.create", company, branch))


def change_status(*, actor, company_id, job_id, status, expected_version, key, path):
    preview = GarageJob.objects.filter(tenant_id=company_id, pk=job_id).first()
    if not preview:
        raise NotFound("Job not found.")
    body = {"status": status, "expected_version": expected_version}
    def operation(company, branch, revisions, current):
        job = GarageJob.objects.select_for_update().filter(tenant=company, pk=job_id, branch=branch).first()
        if job is None:
            raise NotFound("Job not found.")
        _require_job_action(current, "garage.job.status", company, branch, job)
        if job.status_version != expected_version or job.status == status:
            raise DomainConflict("Job status changed; reload and retry.", code="GARAGE_STATUS_CONFLICT")
        previous = job.status
        GarageJobStatusChange.objects.create(job=job, version=job.status_version + 1, from_status=previous, to_status=status, actor=current, module_revision=revisions[CompanyModuleCode.GARAGE])
        job.status = status
        job.status_version += 1
        job.save(update_fields=("status", "status_version", "updated_at"))
        record_event(action="garage.job.status", actor=current, subject=current, company=company, branch=branch, resource=job, metadata={"job_id": str(job.pk), "previous_state": previous, "new_state": status})
        return DomainMutationResult(200, job_data(job))
    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body, action="garage.job.status", module_codes=(CompanyModuleCode.GARAGE,), idempotency_model=VehicleIdempotencyRecord, operation=operation, branch_id=preview.branch_id, authorize_replay=lambda current, company, branch: _require_job_action(current, "garage.job.status", company, branch))
