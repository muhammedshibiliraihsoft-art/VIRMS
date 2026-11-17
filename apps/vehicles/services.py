from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError
from django.db.models import OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.audit import record_event
from apps.accounts.policy import require_action
from apps.common.business_scope import business_scope
from apps.common.domain_mutations import (
    DomainConflict,
    DomainMutationResult,
    execute_domain_mutation,
)
from apps.accounting.models import (
    AccountMovement,
    AccountingApplication,
    AccountingAccount,
    AccountingCategory,
    AccountingEvent,
    AccountingSourceLink,
)
from apps.accounting.services import _event_row, event_data
from apps.investment.models import (
    Investor,
    InvestorFundCredit,
    InvestorFundUse,
    InvestorFundUseAllocation,
    InvestorFundUseAdjustment,
    InvestorPrincipalReturnAllocation,
)
from apps.investment.selectors import with_current_fund_credit_owner
from apps.tenants.models import Branch, CompanyModuleCode, Tenant
from apps.vehicles.models import (
    Vehicle,
    VehicleBranchMovement,
    VehicleIdempotencyRecord,
    VehiclePurchase,
    VehiclePurchaseCorrection,
    VehiclePurchasePayment,
    VehiclePurchaseRefund,
    VehicleSale,
    VehicleSaleCorrection,
    VehicleSaleReceipt,
    VehicleSaleRefund,
    VehiclePaymentAccountPreference,
    VehicleExpense,
    VehicleExpenseCorrection,
    VehicleExpensePayment,
    VehicleExpenseRefund,
    normalize_registration,
)


def _money(value):
    return Decimal(value).quantize(Decimal("0.01"))


def _purchase_source_values(purchase):
    correction = purchase.corrections.order_by("-version", "-id").first()
    return (
        correction.purchase_cost if correction else purchase.purchase_cost,
        correction.investor_fund_amount if correction else purchase.investor_fund_amount,
        correction.running_capital_amount if correction else purchase.running_capital_amount,
    )


def _purchase_payable(purchase, *, paid=None, refunded=None):
    if paid is None:
        paid = purchase.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    if refunded is None:
        refunded = purchase.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    current_cost = _purchase_source_values(purchase)[0]
    return max(Decimal("0.00"), current_cost - paid + refunded)


def _vehicle_investor_ids(*, company, vehicle):
    purchase_investors = VehiclePurchase.objects.filter(
        tenant=company, vehicle=vehicle, investor_id__isnull=False
    ).values_list("investor_id", flat=True)
    expense_investors = VehicleExpense.objects.filter(
        tenant=company, vehicle=vehicle, investor_id__isnull=False
    ).values_list("investor_id", flat=True)
    return set(purchase_investors) | set(expense_investors)


def _vehicle_uses_investor_fund(vehicle):
    purchase = getattr(vehicle, "purchase", None)
    if purchase is None:
        purchase = VehiclePurchase.objects.filter(
            tenant_id=vehicle.tenant_id, vehicle_id=vehicle.pk
        ).first()
    if purchase and _purchase_source_values(purchase)[1] > 0:
        return True

    latest_correction = VehicleExpenseCorrection.objects.filter(
        expense_id=OuterRef("pk")
    ).order_by("-version", "-id")
    return VehicleExpense.objects.filter(
        tenant_id=vehicle.tenant_id,
        vehicle_id=vehicle.pk,
    ).annotate(
        current_fund_amount=Coalesce(
            Subquery(latest_correction.values("investor_fund_amount")[:1]),
            "investor_fund_amount",
        )
    ).filter(current_fund_amount__gt=0).exists()


def _purchase_data(purchase):
    paid = purchase.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    refunded = purchase.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    correction = purchase.corrections.order_by("-version", "-id").first()
    cost, investor_fund_amount, running_capital_amount = _purchase_source_values(purchase)
    payable = _purchase_payable(purchase, paid=paid, refunded=refunded)
    return {
        "id": str(purchase.pk),
        "vehicle_id": str(purchase.vehicle_id),
        "company_id": str(purchase.tenant_id),
        "branch_id": str(purchase.branch_id),
        "purchase_cost": format(cost, ".2f"),
        "seller_name": purchase.seller_name,
        "seller_phone": purchase.seller_phone,
        "investor_id": str(purchase.investor_id) if purchase.investor_id else None,
        "investor_fund_amount": format(investor_fund_amount, ".2f"),
        "running_capital_amount": format(running_capital_amount, ".2f"),
        "seller_paid": format(paid - refunded, ".2f"),
        "seller_payable": format(max(Decimal("0.00"), payable), ".2f"),
        "no_advance_warning": paid == 0,
        "purchased_at": purchase.purchased_at.isoformat(),
        "created_at": purchase.created_at.isoformat(),
        "payments": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "account_id": str(row.account_id),
                "reference": row.reference,
                "effective_at": row.effective_at.isoformat(),
            }
            for row in purchase.payments.select_related("account").order_by("effective_at", "id")
        ],
        "refunds": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "account_id": str(row.account_id),
                "effective_at": row.effective_at.isoformat(),
            }
            for row in purchase.refunds.select_related("account").order_by("effective_at", "id")
        ],
        "correction_version": correction.version if correction else 0,
    }


def _expense_totals(expense):
    cache = getattr(expense, "_prefetched_objects_cache", {})
    if "payments" in cache:
        paid = sum((row.amount for row in cache["payments"]), Decimal("0.00"))
    else:
        paid = expense.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    if "refunds" in cache:
        applied_refunds = sum((row.applied_amount for row in cache["refunds"]), Decimal("0.00"))
    else:
        applied_refunds = expense.refunds.aggregate(total=Sum("applied_amount"))["total"] or Decimal("0.00")
    net_paid = max(Decimal("0.00"), paid - applied_refunds)
    correction = expense.corrections.order_by("-version", "-id").first()
    amount = correction.amount if correction else expense.amount
    return paid, applied_refunds, net_paid, max(Decimal("0.00"), amount - net_paid)


def _expense_data(expense):
    paid, applied_refunds, net_paid, payable = _expense_totals(expense)
    correction = expense.corrections.order_by("-version", "-id").first()
    amount = correction.amount if correction else expense.amount
    fund_amount = correction.investor_fund_amount if correction else expense.investor_fund_amount
    running_amount = correction.running_capital_amount if correction else expense.running_capital_amount
    cache = getattr(expense, "_prefetched_objects_cache", {})
    payments = list(cache["payments"]) if "payments" in cache else list(expense.payments.all())
    refunds = list(cache["refunds"]) if "refunds" in cache else list(expense.refunds.all())
    payments.sort(key=lambda row: (row.effective_at, row.pk))
    refunds.sort(key=lambda row: (row.effective_at, row.pk))
    return {
        "id": str(expense.pk),
        "vehicle_id": str(expense.vehicle_id),
        "company_id": str(expense.tenant_id),
        "branch_id": str(expense.branch_id),
        "amount": format(amount, ".2f"),
        "description": expense.description,
        "investor_id": str(expense.investor_id) if expense.investor_id else None,
        "investor_fund_amount": format(fund_amount, ".2f"),
        "running_capital_amount": format(running_amount, ".2f"),
        "paid_total": format(paid, ".2f"),
        "applied_refund_total": format(applied_refunds, ".2f"),
        "net_paid": format(net_paid, ".2f"),
        "payable": format(payable, ".2f"),
        "effective_at": expense.effective_at.isoformat(),
        "created_at": expense.created_at.isoformat(),
        "payments": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "reference": row.reference,
                "account_id": str(row.account_id),
                "effective_at": row.effective_at.isoformat(),
            }
            for row in payments
        ],
        "refunds": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "applied_amount": format(row.applied_amount, ".2f"),
                "excess_amount": format(row.amount - row.applied_amount, ".2f"),
                "account_id": str(row.account_id),
                "effective_at": row.effective_at.isoformat(),
                "excess_income_event_id": str(row.excess_income_event_id) if row.excess_income_event_id else None,
            }
            for row in refunds
        ],
    }


def _record_purchase_payment(*, company, branch, purchase, actor, account_id, amount, effective_at, reference, accounting_revision):
    amount = _money(amount)
    if amount <= 0:
        raise ValidationError({"amount": "Payment must be greater than zero."})
    if effective_at > timezone.now():
        raise ValidationError({"effective_at": "Actual seller payment cannot be future-dated."})
    account = AccountingAccount.objects.filter(
        tenant=company, pk=account_id, is_active=True
    ).first()
    if account is None:
        raise NotFound("Cash/Bank account not found.")
    payment = VehiclePurchasePayment.objects.create(
        tenant=company,
        purchase=purchase,
        branch=branch,
        amount=amount,
        account=account,
        reference=(reference or "").strip(),
        effective_at=effective_at,
        actor=actor,
        accounting_module_revision=accounting_revision,
    )
    event = _event_row(
        tenant=company,
        branch=branch,
        event_type=AccountingEvent.EventType.VEHICLE_PAYMENT,
        amount=amount,
        actor=actor,
        revision=accounting_revision,
        description=f"Vehicle purchase payment: {purchase.seller_name}",
        source_reference=(payment.reference or f"VEHICLE-PURCHASE-PAYMENT-{payment.pk}"),
        effective_at=effective_at,
    )
    movement = AccountMovement.objects.create(
        tenant=company, event=event, account=account, delta=-amount
    )
    AccountingSourceLink.objects.create(
        tenant=company, event=event, vehicle_purchase_payment=payment
    )
    _save_payment_account_preference(company=company, actor=actor, account=account)
    record_event(
        action="vehicle.purchase.payment",
        actor=actor,
        subject=actor,
        company=company,
        branch=branch,
        resource=purchase,
        metadata={
            "purchase_id": str(purchase.pk),
            "payment_id": str(payment.pk),
            "accounting_event_id": str(event.pk),
            "account_id": str(account.pk),
            "amount": format(amount, ".2f"),
        },
    )
    return payment, event, movement


def _available_credit(credit):
    returned = InvestorPrincipalReturnAllocation.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    used = InvestorFundUseAllocation.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    adjustment = InvestorFundUseAdjustment.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount_delta"))["total"] or Decimal("0.00")
    return credit.amount - returned - used - adjustment


def _allocate_fund_use(
    *, company, investor, branch, amount, actor, revision, effective_at,
    purchase=None, expense=None,
):
    if (purchase is None) == (expense is None):
        raise ValidationError("Investor Fund use must have exactly one Vehicle source.")
    credits = list(
        with_current_fund_credit_owner(
            InvestorFundCredit.objects.select_for_update().filter(tenant=company)
        )
        .filter(current_investor_id=investor.pk)
        .order_by("effective_at", "id")
    )
    available = {credit.pk: _available_credit(credit) for credit in credits}
    total = sum(available.values(), Decimal("0.00"))
    amount = _money(amount)
    if amount <= 0 or amount > total:
        raise DomainConflict(
            "The Investor does not have enough available Fund for this Vehicle Purchase.",
            code="FUND_AVAILABLE_INSUFFICIENT",
        )
    fund_use = InvestorFundUse.objects.create(
        tenant=company,
        investor=investor,
        branch=branch,
        purchase=purchase,
        expense=expense,
        amount=amount,
        effective_at=effective_at,
        actor=actor,
        module_revision=revision,
    )
    remaining = amount
    for credit in credits:
        part = min(max(available[credit.pk], Decimal("0.00")), remaining)
        if part > 0:
            InvestorFundUseAllocation.objects.create(
                tenant=company,
                fund_use=fund_use,
                credit=credit,
                amount=part,
                actor=actor,
            )
            remaining -= part
        if remaining == 0:
            break
    if remaining:
        raise DomainConflict(
            "The Investor's available Fund changed while allocating the Purchase.",
            code="FUND_AVAILABLE_INSUFFICIENT",
        )


def _vehicle_data(vehicle):
    sale = getattr(vehicle, "confirmed_sale", None)
    return {
        "id": str(vehicle.pk),
        "company_id": str(vehicle.tenant_id),
        "branch_id": str(vehicle.current_branch_id),
        "branch_name": vehicle.current_branch.name,
        "registration": vehicle.registration,
        "model": vehicle.model,
        "is_active": vehicle.is_active,
        "is_sold": sale is not None,
        "sale_id": str(sale.pk) if sale else None,
        "created_at": vehicle.created_at.isoformat(),
        "updated_at": vehicle.updated_at.isoformat(),
    }


def _sale_data(sale):
    corrections = list(sale.corrections.all())
    correction = max(corrections, key=lambda row: (row.version, str(row.pk)), default=None)
    price = correction.sale_price if correction else sale.sale_price
    receipts = sorted(sale.receipts.all(), key=lambda row: (row.effective_at, str(row.pk)))
    refunds = sorted(sale.refunds.all(), key=lambda row: (row.effective_at, str(row.pk)))
    received = sum((row.amount for row in receipts), Decimal("0.00"))
    refunded = sum((row.amount for row in refunds), Decimal("0.00"))
    net_received = received - refunded
    receivable = max(Decimal("0.00"), price - net_received)
    refund_payable = max(Decimal("0.00"), net_received - price)
    return {
        "id": str(sale.pk),
        "company_id": str(sale.tenant_id),
        "vehicle_id": str(sale.vehicle_id),
        "vehicle_registration": sale.vehicle.registration,
        "vehicle_model": sale.vehicle.model,
        "branch_id": str(sale.branch_id),
        "branch_name": sale.branch.name,
        "sale_price": format(price, ".2f"),
        "investor_funded": _vehicle_uses_investor_fund(sale.vehicle),
        "buyer_name": sale.buyer_name,
        "buyer_phone": sale.buyer_phone,
        "sold_at": sale.sold_at.isoformat(),
        "received_total": format(received, ".2f"),
        "refunded_total": format(refunded, ".2f"),
        "net_received": format(net_received, ".2f"),
        "receivable": format(receivable, ".2f"),
        "refund_payable": format(refund_payable, ".2f"),
        # Keep the legacy field while correcting its meaning to the actual
        # Buyer refund liability, rather than all net money received.
        "refund_available": format(refund_payable, ".2f"),
        "correction_version": correction.version if correction else 0,
        "created_at": sale.created_at.isoformat(),
        "receipts": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "account_id": str(row.account_id),
                "reference": row.reference,
                "effective_at": row.effective_at.isoformat(),
            }
            for row in receipts
        ],
        "refunds": [
            {
                "id": str(row.pk),
                "amount": format(row.amount, ".2f"),
                "account_id": str(row.account_id),
                "effective_at": row.effective_at.isoformat(),
            }
            for row in refunds
        ],
    }


def read_scope(*, actor, company_id, action, branch_id=None):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    branch = None
    if branch_id is not None:
        branch = Branch.objects.filter(pk=branch_id, tenant=company).first()
        if branch is None:
            raise NotFound("Branch not found.")
    current_actor = require_action(actor, action, company=company, branch=branch)
    return company, business_scope(actor=current_actor, company=company), branch


def _queryset_for_scope(queryset, *, scope, branch_id):
    if branch_id is not None:
        if not scope.is_company_reader and branch_id not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        return queryset.filter(current_branch_id=branch_id)
    if scope.is_company_reader:
        return queryset
    return queryset.filter(current_branch_id__in=scope.allowed_branch_ids)


def list_vehicles(*, actor, company_id, branch_id=None, search=""):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="vehicle.read",
        branch_id=branch_id,
    )
    queryset = Vehicle.objects.filter(tenant=company, is_active=True).select_related(
        "current_branch", "confirmed_sale"
    )
    queryset = _queryset_for_scope(queryset, scope=scope, branch_id=branch_id)
    if search:
        queryset = queryset.filter(
            Q(normalized_registration__icontains=normalize_registration(search))
            | Q(model__icontains=search.strip())
        )
    return queryset.order_by("normalized_registration", "id")


def get_vehicle(*, actor, company_id, vehicle_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    vehicle = Vehicle.objects.filter(tenant=company, pk=vehicle_id, is_active=True).select_related(
        "current_branch", "confirmed_sale"
    ).first()
    if vehicle is None:
        raise NotFound("Vehicle not found.")
    require_action(
        actor,
        "vehicle.read",
        company=company,
        branch=vehicle.current_branch,
        resource=vehicle,
    )
    return _vehicle_data(vehicle)


def create_vehicle(*, actor, company_id, key, path, branch_id, registration, model):
    body = {
        "branch_id": str(branch_id),
        "registration": registration.strip(),
        "model": model.strip(),
    }

    def operation(company, branch, revisions, locked_actor):
        if not body["registration"] or not normalize_registration(body["registration"]):
            raise ValidationError({"registration": "A registration number is required."})
        if not body["model"]:
            raise ValidationError({"model": "A vehicle model/description is required."})
        normalized = normalize_registration(body["registration"])
        if Vehicle.objects.filter(
            tenant=company, normalized_registration=normalized, is_active=True
        ).exists():
            raise DomainConflict(
                "An active Vehicle with this registration already exists in this Company.",
                code="VEHICLE_REGISTRATION_DUPLICATE",
            )
        vehicle = Vehicle.objects.create(
            tenant=company,
            current_branch=branch,
            registration=body["registration"],
            model=body["model"],
            created_by=locked_actor,
            updated_by=locked_actor,
        )
        record_event(
            action="vehicle.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=vehicle,
            metadata={
                "vehicle_id": str(vehicle.pk),
                "new_registration": vehicle.registration,
                "new_model": vehicle.model,
                "branch_id": str(branch.pk),
            },
        )
        return DomainMutationResult(201, _vehicle_data(vehicle))

    try:
        return execute_domain_mutation(
            actor=actor,
            company_id=company_id,
            method="POST",
            path=path,
            key=key,
            body=body,
            action="vehicle.create",
            module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT,),
            idempotency_model=VehicleIdempotencyRecord,
            operation=operation,
            branch_id=branch_id,
        )
    except IntegrityError as exc:
        constraint = getattr(
            getattr(getattr(exc, "__cause__", None), "diag", None),
            "constraint_name",
            None,
        )
        if constraint == "vehicle_active_registration_uq":
            raise DomainConflict(
                "An active Vehicle with this registration already exists in this Company.",
                code="VEHICLE_REGISTRATION_DUPLICATE",
            ) from exc
        raise


def update_vehicle(*, actor, company_id, vehicle_id, key, path, values):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    preview = Vehicle.objects.filter(
        tenant=company, pk=vehicle_id, is_active=True
    ).select_related("current_branch").first()
    if preview is None:
        raise NotFound("Vehicle not found.")
    body = {key: value.strip() for key, value in values.items()}

    def operation(company, _branch, revisions, locked_actor):
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=vehicle_id, is_active=True
        ).select_related("current_branch").first()
        if vehicle is None:
            raise NotFound("Vehicle not found.")
        require_action(
            locked_actor,
            "vehicle.edit",
            company=company,
            branch=vehicle.current_branch,
            resource=vehicle,
        )
        old_registration = vehicle.registration
        old_model = vehicle.model
        new_registration = body.get("registration", vehicle.registration)
        new_model = body.get("model", vehicle.model)
        if not new_registration or not normalize_registration(new_registration):
            raise ValidationError({"registration": "A registration number is required."})
        if not new_model:
            raise ValidationError({"model": "A vehicle model/description is required."})
        if Vehicle.objects.filter(
            tenant=company,
            normalized_registration=normalize_registration(new_registration),
            is_active=True,
        ).exclude(pk=vehicle.pk).exists():
            raise DomainConflict(
                "An active Vehicle with this registration already exists in this Company.",
                code="VEHICLE_REGISTRATION_DUPLICATE",
            )
        vehicle.registration = new_registration
        vehicle.model = new_model
        vehicle.updated_by = locked_actor
        vehicle.save(update_fields=("registration", "normalized_registration", "model", "updated_by", "updated_at"))
        record_event(
            action="vehicle.update",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=vehicle.current_branch,
            resource=vehicle,
            metadata={
                "vehicle_id": str(vehicle.pk),
                "old_registration": old_registration,
                "new_registration": vehicle.registration,
                "old_model": old_model,
                "new_model": vehicle.model,
                "branch_id": str(vehicle.current_branch_id),
            },
        )
        return DomainMutationResult(200, _vehicle_data(vehicle))

    try:
        return execute_domain_mutation(
            actor=actor,
            company_id=company_id,
            method="PATCH",
            path=path,
            key=key,
            body=body,
            action="vehicle.edit",
            module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT,),
            idempotency_model=VehicleIdempotencyRecord,
            operation=operation,
            branch_id=preview.current_branch_id,
        )
    except IntegrityError as exc:
        constraint = getattr(
            getattr(getattr(exc, "__cause__", None), "diag", None),
            "constraint_name",
            None,
        )
        if constraint == "vehicle_active_registration_uq":
            raise DomainConflict(
                "An active Vehicle with this registration already exists in this Company.",
                code="VEHICLE_REGISTRATION_DUPLICATE",
            ) from exc
        raise


def move_vehicle(*, actor, company_id, vehicle_id, key, path, to_branch_id, reason):
    body = {"to_branch_id": str(to_branch_id), "reason": reason.strip()}

    def operation(company, _branch, revisions, locked_actor):
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=vehicle_id, is_active=True
        ).select_related("current_branch").first()
        if vehicle is None:
            raise NotFound("Vehicle not found.")
        to_branch = Branch.objects.filter(pk=to_branch_id, tenant=company).first()
        if to_branch is None:
            raise NotFound("Branch not found.")
        if vehicle.current_branch_id == to_branch.pk:
            raise ValidationError({"to_branch_id": "Vehicle is already assigned to this Branch."})
        if not body["reason"]:
            raise ValidationError({"reason": "A reason is required."})
        movement = VehicleBranchMovement.objects.create(
            tenant=company,
            vehicle=vehicle,
            from_branch=vehicle.current_branch,
            to_branch=to_branch,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            moved_at=timezone.now(),
            reason=body["reason"],
        )
        from_branch = vehicle.current_branch
        vehicle.current_branch = to_branch
        vehicle.updated_by = locked_actor
        vehicle.save(update_fields=("current_branch", "updated_by", "updated_at"))
        record_event(
            action="vehicle.branch.move",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=to_branch,
            resource=vehicle,
            reason=body["reason"],
            metadata={
                "vehicle_id": str(vehicle.pk),
                "from_branch_id": str(from_branch.pk),
                "to_branch_id": str(to_branch.pk),
            },
        )
        return DomainMutationResult(
            201,
            {
                "id": str(movement.pk),
                "vehicle_id": str(vehicle.pk),
                "from_branch_id": str(from_branch.pk),
                "to_branch_id": str(to_branch.pk),
                "reason": movement.reason,
                "moved_at": movement.moved_at.isoformat(),
            },
        )

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="vehicle.branch.move",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT,),
        idempotency_model=VehicleIdempotencyRecord,
        operation=operation,
    )


def list_purchases(*, actor, company_id, branch_id=None, vehicle_id=None):
    company, scope, branch = read_scope(
        actor=actor,
        company_id=company_id,
        action="vehicle.read",
        branch_id=branch_id,
    )
    queryset = VehiclePurchase.objects.filter(tenant=company).select_related(
        "vehicle", "branch", "investor"
    )
    if vehicle_id is not None:
        queryset = queryset.filter(vehicle_id=vehicle_id)
    if branch is not None:
        if not scope.is_company_reader and branch.pk not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        queryset = queryset.filter(branch=branch)
    elif not scope.is_company_reader:
        queryset = queryset.filter(branch_id__in=scope.allowed_branch_ids)
    return queryset.order_by("-purchased_at", "-id")


def get_purchase(*, actor, company_id, purchase_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    purchase = VehiclePurchase.objects.filter(
        tenant=company, pk=purchase_id
    ).select_related("vehicle", "branch", "investor").first()
    if purchase is None:
        raise NotFound("Vehicle Purchase not found.")
    require_action(
        actor,
        "vehicle.read",
        company=company,
        branch=purchase.branch,
        resource=purchase,
    )
    return _purchase_data(purchase)


def create_purchase(
    *, actor, company_id, key, path, vehicle_id, branch_id, purchase_cost,
    seller_name, seller_phone="", investor_id=None, investor_fund_amount="0.00",
    running_capital_amount="0.00", purchased_at=None, initial_payment_amount="0.00",
    initial_payment_account_id=None, initial_payment_effective_at=None,
):
    purchase_cost = _money(purchase_cost)
    investor_fund_amount = _money(investor_fund_amount)
    running_capital_amount = _money(running_capital_amount)
    initial_payment_amount = _money(initial_payment_amount)
    purchased_at_was_supplied = purchased_at is not None
    initial_payment_date_was_supplied = initial_payment_effective_at is not None
    purchased_at = purchased_at or timezone.now()
    initial_payment_effective_at = initial_payment_effective_at or timezone.now()
    if purchased_at > timezone.now():
        raise ValidationError({"purchased_at": "Purchase date cannot be in the future."})
    if initial_payment_amount < 0 or initial_payment_amount > purchase_cost:
        raise ValidationError({"initial_payment_amount": "Initial payment must be between zero and the purchase cost."})
    if purchase_cost <= 0:
        raise ValidationError({"purchase_cost": "Purchase cost must be greater than zero."})
    if investor_fund_amount < 0 or running_capital_amount < 0:
        raise ValidationError("Funding allocations cannot be negative.")
    if investor_fund_amount + running_capital_amount != purchase_cost:
        raise ValidationError({"funding": "Investor Fund and Company Running Capital must total the Purchase cost."})
    if (investor_fund_amount > 0) != bool(investor_id):
        raise ValidationError({"investor_id": "Select one Investor exactly when Investor Fund is used."})
    if initial_payment_amount and not initial_payment_account_id:
        raise ValidationError({"initial_payment_account_id": "Choose the Cash/Bank account used for the actual payment."})
    if not initial_payment_amount and initial_payment_account_id:
        raise ValidationError({"initial_payment_account_id": "An account is only allowed when an initial payment is recorded."})

    modules = [CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING]
    if investor_fund_amount > 0:
        modules.append(CompanyModuleCode.INVESTMENT)
    body = {
        "vehicle_id": str(vehicle_id),
        "branch_id": str(branch_id),
        "purchase_cost": format(purchase_cost, ".2f"),
        "seller_name": seller_name.strip(),
        "seller_phone": seller_phone.strip(),
        "investor_id": str(investor_id) if investor_id else None,
        "investor_fund_amount": format(investor_fund_amount, ".2f"),
        "running_capital_amount": format(running_capital_amount, ".2f"),
        "purchased_at": purchased_at.isoformat() if purchased_at_was_supplied else None,
        "initial_payment_amount": format(initial_payment_amount, ".2f"),
        "initial_payment_account_id": str(initial_payment_account_id) if initial_payment_account_id else None,
        "initial_payment_effective_at": (
            initial_payment_effective_at.isoformat()
            if initial_payment_date_was_supplied
            else None
        ),
    }

    def operation(company, branch, revisions, locked_actor):
        if not body["seller_name"]:
            raise ValidationError({"seller_name": "Seller name is required."})
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=vehicle_id, current_branch=branch, is_active=True
        ).first()
        if vehicle is None:
            raise NotFound("Active Vehicle not found in this Branch.")
        if VehiclePurchase.objects.filter(tenant=company, vehicle=vehicle).exists():
            raise DomainConflict("This Vehicle already has a Purchase record.", code="VEHICLE_PURCHASE_EXISTS")

        investor = None
        if investor_fund_amount > 0:
            require_action(
                locked_actor,
                "investment.fund.use",
                company=company,
                branch=branch,
            )
            investor = Investor.objects.select_for_update().filter(
                tenant=company, pk=investor_id, is_active=True
            ).first()
            if investor is None:
                raise NotFound("Active Investor not found.")
            existing_investors = _vehicle_investor_ids(company=company, vehicle=vehicle)
            if existing_investors and existing_investors != {investor.pk}:
                raise DomainConflict(
                    "A Stock Vehicle may use Investor Fund from only one Investor.",
                    code="VEHICLE_INVESTOR_MISMATCH",
                )

        purchase = VehiclePurchase.objects.create(
            tenant=company,
            vehicle=vehicle,
            branch=branch,
            purchase_cost=purchase_cost,
            seller_name=body["seller_name"],
            seller_phone=body["seller_phone"],
            investor=investor,
            investor_fund_amount=investor_fund_amount,
            running_capital_amount=running_capital_amount,
            purchased_at=purchased_at,
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=(
                revisions[CompanyModuleCode.INVESTMENT] if investor else None
            ),
        )
        if investor is not None:
            _allocate_fund_use(
                company=company,
                investor=investor,
                branch=branch,
                purchase=purchase,
                amount=investor_fund_amount,
                actor=locked_actor,
                revision=revisions[CompanyModuleCode.INVESTMENT],
                effective_at=purchased_at,
            )

        record_event(
            action="vehicle.purchase.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=purchase,
            metadata={
                "purchase_id": str(purchase.pk),
                "vehicle_id": str(vehicle.pk),
                "purchase_cost": format(purchase_cost, ".2f"),
                "investor_id": str(investor.pk) if investor else None,
                "investor_fund_amount": format(investor_fund_amount, ".2f"),
                "running_capital_amount": format(running_capital_amount, ".2f"),
            },
        )
        if initial_payment_amount:
            require_action(
                locked_actor,
                "accounting.payment.create",
                company=company,
                branch=branch,
            )
            _record_purchase_payment(
                company=company,
                branch=branch,
                purchase=purchase,
                actor=locked_actor,
                account_id=initial_payment_account_id,
                amount=initial_payment_amount,
                effective_at=initial_payment_effective_at,
                reference="",
                accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            )
        return DomainMutationResult(201, _purchase_data(purchase))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="vehicle.purchase.create",
        module_codes=tuple(modules),
        idempotency_model=VehicleIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )


def create_purchase_installment(
    *, actor, company_id, purchase_id, key, path, account_id, amount,
    effective_at=None, reference="",
):
    amount = _money(amount)
    effective_at_was_supplied = effective_at is not None
    effective_at = effective_at or timezone.now()
    preview = VehiclePurchase.objects.filter(
        tenant_id=company_id, pk=purchase_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Purchase not found.")
    body = {
        "purchase_id": str(purchase_id),
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "effective_at": effective_at.isoformat() if effective_at_was_supplied else None,
        "reference": reference.strip(),
    }

    def operation(company, branch, revisions, locked_actor):
        purchase = VehiclePurchase.objects.select_for_update().filter(
            tenant=company, pk=purchase_id
        ).select_related("branch").first()
        if purchase is None:
            raise NotFound("Vehicle Purchase not found.")
        # Purchase Branch, not the Vehicle's current Branch, owns the payable.
        require_action(
            locked_actor,
            "accounting.payment.create",
            company=company,
            branch=purchase.branch,
            resource=purchase,
        )
        if not _pre_off_obligation_is_settleable(
            company=company, purchase=purchase
        ):
            raise DomainConflict(
                "A pre-existing payable can be paid only while Accounting is ON and any disabled source module was OFF after the Purchase was recorded.",
                code="PRE_OFF_OBLIGATION_NOT_ELIGIBLE",
            )
        payable = _purchase_payable(purchase)
        if amount <= 0 or amount > payable:
            raise DomainConflict(
                "Seller installment must be positive and no greater than the remaining payable.",
                code="PURCHASE_PAYABLE_EXCEEDED",
            )
        payment, _event, _movement = _record_purchase_payment(
            company=company,
            branch=purchase.branch,
            purchase=purchase,
            actor=locked_actor,
            account_id=account_id,
            amount=amount,
            effective_at=effective_at,
            reference=reference,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        response = _purchase_data(purchase)
        response.update(
            {
                "payment_id": str(payment.pk),
                "paid_now": format(amount, ".2f"),
            }
        )
        return DomainMutationResult(201, response)

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="vehicle.purchase.pay",
        module_codes=(CompanyModuleCode.ACCOUNTING,),
        idempotency_model=VehicleIdempotencyRecord,
        operation=operation,
        branch_id=preview.branch_id,
    )


def _pre_off_obligation_is_settleable(*, company, purchase):
    from apps.tenants.models import CompanyModuleState

    tracked = [(CompanyModuleCode.VEHICLE_MANAGEMENT, purchase.vehicle_module_revision_id)]
    if purchase.investor_fund_amount > 0:
        tracked.append((CompanyModuleCode.INVESTMENT, purchase.investment_module_revision_id))
    for module_code, source_revision_id in tracked:
        latest = CompanyModuleState.objects.filter(
            tenant=company, module_code=module_code
        ).order_by("-version", "-id").first()
        if latest is None or latest.state == CompanyModuleState.State.ENABLED:
            continue
        if source_revision_id is None or purchase.created_at >= latest.effective_from:
            return False
        source_revision = CompanyModuleState.objects.filter(
            pk=source_revision_id,
            tenant=company,
            module_code=module_code,
            state=CompanyModuleState.State.ENABLED,
            version__lt=latest.version,
        ).first()
        if source_revision is None:
            return False
    return True


def list_expenses(*, actor, company_id, vehicle_id, branch_id=None):
    company, scope, branch = read_scope(
        actor=actor, company_id=company_id, action="vehicle.read", branch_id=branch_id
    )
    vehicle = Vehicle.objects.filter(tenant=company, pk=vehicle_id, is_active=True).first()
    if vehicle is None:
        raise NotFound("Vehicle not found.")
    require_action(
        actor, "vehicle.read", company=company, branch=vehicle.current_branch, resource=vehicle
    )
    queryset = VehicleExpense.objects.filter(tenant=company, vehicle=vehicle).select_related(
        "branch", "investor"
    ).prefetch_related("payments", "refunds")
    if branch is not None:
        if not scope.is_company_reader and branch.pk not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        queryset = queryset.filter(branch=branch)
    elif not scope.is_company_reader:
        queryset = queryset.filter(branch_id__in=scope.allowed_branch_ids)
    return queryset.order_by("effective_at", "id")


def get_expense(*, actor, company_id, expense_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    expense = VehicleExpense.objects.filter(tenant=company, pk=expense_id).select_related(
        "branch", "vehicle", "investor"
    ).prefetch_related("payments", "refunds").first()
    if expense is None:
        raise NotFound("Vehicle Expense not found.")
    require_action(
        actor, "vehicle.read", company=company, branch=expense.branch, resource=expense
    )
    return _expense_data(expense)


def create_vehicle_expense(
    *, actor, company_id, vehicle_id, key, path, amount, description,
    investor_id=None, investor_fund_amount=None,
    running_capital_amount=None, effective_at=None,
):
    amount = _money(amount)
    requested_fund = _money(investor_fund_amount) if investor_fund_amount is not None else None
    requested_running = _money(running_capital_amount) if running_capital_amount is not None else None
    preview = Vehicle.objects.filter(
        tenant_id=company_id, pk=vehicle_id, is_active=True
    ).select_related("current_branch").first()
    if preview is None:
        raise NotFound("Vehicle not found.")
    body = {
        "vehicle_id": str(vehicle_id),
        "amount": format(amount, ".2f"),
        "description": description.strip(),
        "investor_id": str(investor_id) if investor_id else None,
        "investor_fund_amount": format(requested_fund, ".2f") if requested_fund is not None else None,
        "running_capital_amount": format(requested_running, ".2f") if requested_running is not None else None,
        "effective_at": effective_at.isoformat() if effective_at else None,
    }
    modules = [CompanyModuleCode.VEHICLE_MANAGEMENT]
    if investor_id or (requested_fund is not None and requested_fund > 0):
        modules.append(CompanyModuleCode.INVESTMENT)

    def operation(company, _branch, revisions, locked_actor):
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=vehicle_id, is_active=True
        ).select_related("current_branch").first()
        if vehicle is None:
            raise NotFound("Vehicle not found.")
        branch = vehicle.current_branch
        require_action(
            locked_actor, "vehicle.expense.create", company=company,
            branch=branch, resource=vehicle,
        )
        if amount <= 0:
            raise ValidationError({"amount": "Vehicle Expense must be positive."})
        if not body["description"]:
            raise ValidationError({"description": "A description is required."})
        when = effective_at or timezone.now()
        if when > timezone.now():
            raise ValidationError({"effective_at": "An actual Vehicle Expense cannot be future-dated."})
        investor = None
        investment_revision = None
        existing_investors = _vehicle_investor_ids(company=company, vehicle=vehicle)
        if existing_investors and not investor_id:
            raise DomainConflict("Select the Vehicle's Investor for Fund-first allocation.", code="VEHICLE_INVESTOR_REQUIRED")
        if investor_id:
            require_action(
                locked_actor, "vehicle.expense.fund", company=company,
                branch=branch, resource=vehicle,
            )
            investor = Investor.objects.filter(
                tenant=company, pk=investor_id, is_active=True
            ).first()
            if investor is None:
                raise NotFound("Investor not found.")
            investment_revision = revisions[CompanyModuleCode.INVESTMENT]
            if existing_investors and existing_investors != {investor.pk}:
                raise DomainConflict(
                    "A Stock Vehicle may use Investor Fund from only one Investor.",
                    code="VEHICLE_INVESTOR_MISMATCH",
                )
            credits = list(with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update(of=("self",)).filter(tenant=company)
            ).filter(current_investor_id=investor.pk).order_by("effective_at", "id"))
            available = sum((max(Decimal("0.00"), _available_credit(row)) for row in credits), Decimal("0.00"))
            fund_amount = min(amount, available)
        else:
            fund_amount = Decimal("0.00")
        running_amount = amount - fund_amount
        if (requested_fund is not None and requested_fund != fund_amount) or (requested_running is not None and requested_running != running_amount):
            raise DomainConflict("The available Investor Fund changed. Reload and review the source allocation.", code="VEHICLE_EXPENSE_FUND_SPLIT_CHANGED")

        expense = VehicleExpense.objects.create(
            tenant=company,
            vehicle=vehicle,
            branch=branch,
            amount=amount,
            description=body["description"],
            investor=investor,
            investor_fund_amount=fund_amount,
            running_capital_amount=running_amount,
            effective_at=when,
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=investment_revision,
        )
        record_event(
            action="vehicle.expense.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=expense,
            metadata={
                "expense_id": str(expense.pk),
                "vehicle_id": str(vehicle.pk),
                "amount": format(amount, ".2f"),
                "investor_fund_amount": format(fund_amount, ".2f"),
                "running_capital_amount": format(running_amount, ".2f"),
            },
        )
        if fund_amount > 0:
            _allocate_fund_use(
                company=company,
                investor=investor,
                branch=branch,
                expense=expense,
                amount=fund_amount,
                actor=locked_actor,
                revision=investment_revision,
                effective_at=when,
            )
        return DomainMutationResult(201, _expense_data(expense))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="vehicle.expense.create",
        module_codes=tuple(modules),
        idempotency_model=VehicleIdempotencyRecord,
        operation=operation,
        branch_id=preview.current_branch_id,
    )


def create_expense_installment(
    *, actor, company_id, expense_id, key, path, account_id, amount,
    reference, effective_at=None,
):
    amount = _money(amount)
    reference = (reference or "").strip()
    effective_at_value = effective_at
    preview = VehicleExpense.objects.filter(
        tenant_id=company_id, pk=expense_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Expense not found.")
    body = {
        "expense_id": str(expense_id),
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "reference": reference,
        "effective_at": effective_at_value.isoformat() if effective_at_value else None,
    }

    def operation(company, _branch, revisions, locked_actor):
        expense = VehicleExpense.objects.select_for_update().filter(
            tenant=company, pk=expense_id
        ).select_related("branch").first()
        if expense is None:
            raise NotFound("Vehicle Expense not found.")
        require_action(
            locked_actor, "vehicle.expense.pay", company=company,
            branch=expense.branch, resource=expense,
        )
        require_action(
            locked_actor, "accounting.payment.create", company=company,
            branch=expense.branch, resource=expense,
        )
        if not reference:
            raise ValidationError({"reference": "A bank transaction ID or cash voucher number is required."})
        when = effective_at_value or timezone.now()
        if when > timezone.now():
            raise ValidationError({"effective_at": "An actual payment cannot be future-dated."})
        _paid, _refunds, _net_paid, payable = _expense_totals(expense)
        if amount <= 0 or amount > payable:
            raise DomainConflict(
                "Payment must be positive and no greater than the remaining Vehicle Expense payable.",
                code="VEHICLE_EXPENSE_PAYABLE_EXCEEDED",
            )
        account = AccountingAccount.objects.select_for_update().filter(
            tenant=company, pk=account_id, is_active=True
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        payment = VehicleExpensePayment.objects.create(
            tenant=company,
            expense=expense,
            branch=expense.branch,
            amount=amount,
            account=account,
            reference=reference,
            normalized_reference=reference.lower(),
            effective_at=when,
            actor=locked_actor,
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
        )
        event = _event_row(
            tenant=company,
            branch=expense.branch,
            event_type=AccountingEvent.EventType.VEHICLE_PAYMENT,
            amount=amount,
            actor=locked_actor,
            revision=revisions[CompanyModuleCode.ACCOUNTING],
            description=f"Vehicle expense payment: {expense.description}",
            source_reference=reference,
            effective_at=when,
        )
        AccountMovement.objects.create(
            tenant=company, event=event, account=account, delta=-amount
        )
        AccountingSourceLink.objects.create(
            tenant=company, event=event, vehicle_expense_payment=payment
        )
        _save_payment_account_preference(company=company, actor=locked_actor, account=account)
        record_event(
            action="vehicle.expense.payment",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=expense.branch,
            resource=expense,
            metadata={
                "expense_id": str(expense.pk),
                "payment_id": str(payment.pk),
                "accounting_event_id": str(event.pk),
                "account_id": str(account.pk),
                "amount": format(amount, ".2f"),
            },
        )
        return DomainMutationResult(201, {
            **_expense_data(expense),
            "payment_id": str(payment.pk),
            "accounting_event_id": str(event.pk),
        })

    try:
        return execute_domain_mutation(
            actor=actor,
            company_id=company_id,
            method="POST",
            path=path,
            key=key,
            body=body,
            action="vehicle.expense.pay",
            module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
            idempotency_model=VehicleIdempotencyRecord,
            operation=operation,
            branch_id=preview.branch_id,
        )
    except IntegrityError as exc:
        constraint = getattr(
            getattr(getattr(exc, "__cause__", None), "diag", None),
            "constraint_name",
            None,
        )
        if constraint == "vehicle_expense_payment_ref_uq":
            raise DomainConflict(
                "This Cash/Bank reference already exists for this Company account.",
                code="VEHICLE_EXPENSE_PAYMENT_REFERENCE_DUPLICATE",
            ) from exc
        raise


def create_expense_refund(
    *, actor, company_id, expense_id, key, path, account_id, amount,
    excess_income_category_id=None,
    excess_income_description="", effective_at=None,
):
    amount = _money(amount)
    description = (excess_income_description or "").strip()
    effective_at_value = effective_at
    preview = VehicleExpense.objects.filter(
        tenant_id=company_id, pk=expense_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Expense not found.")
    body = {
        "expense_id": str(expense_id),
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "excess_income_category_id": str(excess_income_category_id) if excess_income_category_id else None,
        "excess_income_description": description,
        "effective_at": effective_at_value.isoformat() if effective_at_value else None,
    }

    def operation(company, _branch, revisions, locked_actor):
        expense = VehicleExpense.objects.select_for_update().filter(
            tenant=company, pk=expense_id
        ).select_related("branch").first()
        if expense is None:
            raise NotFound("Vehicle Expense not found.")
        require_action(
            locked_actor, "vehicle.expense.refund", company=company,
            branch=expense.branch, resource=expense,
        )
        require_action(
            locked_actor, "accounting.receipt.create", company=company,
            branch=expense.branch, resource=expense,
        )
        when = effective_at_value or timezone.now()
        if amount <= 0 or when > timezone.now():
            raise ValidationError({"amount": "Refund must be positive and cannot be future-dated."})
        paid = expense.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        prior_applied = expense.refunds.aggregate(total=Sum("applied_amount"))["total"] or Decimal("0.00")
        applied = min(amount, max(Decimal("0.00"), paid - prior_applied))
        excess = amount - applied
        category = None
        income_event = None
        if excess > 0:
            if not excess_income_category_id or not description:
                raise ValidationError({
                    "excess_income_category_id": "The excess needs an Accountant-selected Company Income category and note.",
                    "excess_income_description": "Explain why the excess is Company Income.",
                })
            require_action(
                locked_actor, "accounting.income.create", company=company,
                branch=expense.branch, resource=expense,
            )
            category = AccountingCategory.objects.filter(
                tenant=company, pk=excess_income_category_id,
                kind=AccountingCategory.Kind.INCOME, is_active=True,
            ).first()
            if category is None:
                raise NotFound("Active Company Income category not found.")
        elif excess_income_category_id or description:
            raise ValidationError({
                "excess_income_category_id": "An excess Income category is only accepted when the refund exceeds the remaining paid amount."
            })
        account = AccountingAccount.objects.select_for_update().filter(
            tenant=company, pk=account_id, is_active=True
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")

        from uuid import uuid4

        refund_id = uuid4()
        if excess > 0:
            income_event = _event_row(
                tenant=company,
                branch=expense.branch,
                event_type=AccountingEvent.EventType.INCOME,
                amount=excess,
                actor=locked_actor,
                revision=revisions[CompanyModuleCode.ACCOUNTING],
                category=category,
                description=description,
                source_reference=f"VEHICLE-EXPENSE-REFUND-EXCESS-{refund_id}",
                effective_at=when,
            )
        refund = VehicleExpenseRefund.objects.create(
            id=refund_id,
            tenant=company,
            expense=expense,
            branch=expense.branch,
            amount=amount,
            applied_amount=applied,
            excess_income_category=category,
            excess_income_description=description,
            excess_income_event=income_event,
            account=account,
            effective_at=when,
            actor=locked_actor,
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        event = _event_row(
            tenant=company,
            branch=expense.branch,
            event_type=AccountingEvent.EventType.VEHICLE_REFUND_IN,
            amount=amount,
            actor=locked_actor,
            revision=revisions[CompanyModuleCode.ACCOUNTING],
            description=f"Vehicle expense refund: {expense.description}",
            source_reference=f"VEHICLE-EXPENSE-REFUND-{refund.pk}",
            effective_at=when,
        )
        AccountMovement.objects.create(
            tenant=company, event=event, account=account, delta=amount
        )
        AccountingSourceLink.objects.create(
            tenant=company, event=event, vehicle_expense_refund=refund
        )
        if income_event is not None:
            AccountingApplication.objects.create(
                tenant=company,
                source_event=event,
                target_event=income_event,
                amount=excess,
                actor=locked_actor,
                module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            )
        record_event(
            action="vehicle.expense.refund",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=expense.branch,
            resource=expense,
            metadata={
                "expense_id": str(expense.pk),
                "refund_id": str(refund.pk),
                "accounting_event_id": str(event.pk),
                "amount": format(amount, ".2f"),
                "applied_amount": format(applied, ".2f"),
                "excess_income_event_id": str(income_event.pk) if income_event else None,
            },
        )
        return DomainMutationResult(201, {
            **_expense_data(expense),
            "refund_id": str(refund.pk),
            "accounting_event_id": str(event.pk),
            "refunded_amount": format(amount, ".2f"),
            "applied_amount": format(applied, ".2f"),
            "excess_income_amount": format(excess, ".2f"),
            "excess_income_event_id": str(income_event.pk) if income_event else None,
        })

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="vehicle.expense.refund",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord,
        operation=operation,
        branch_id=preview.branch_id,
    )


def _source_fund_usage(*, purchase=None, expense=None, credit=None):
    if (purchase is None) == (expense is None):
        raise ValueError("Exactly one Vehicle source is required.")
    allocations = InvestorFundUseAllocation.objects.filter(tenant_id=(purchase or expense).tenant_id)
    adjustments = InvestorFundUseAdjustment.objects.filter(tenant_id=(purchase or expense).tenant_id)
    if purchase is not None:
        allocations = allocations.filter(fund_use__purchase=purchase)
        adjustments = adjustments.filter(purchase_correction__purchase=purchase)
    else:
        allocations = allocations.filter(fund_use__expense=expense)
        adjustments = adjustments.filter(expense_correction__expense=expense)
    if credit is not None:
        allocations = allocations.filter(credit=credit)
        adjustments = adjustments.filter(credit=credit)
    used = allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    adjusted = adjustments.aggregate(total=Sum("amount_delta"))["total"] or Decimal("0.00")
    return used + adjusted


def _apply_fund_use_correction(
    *, company, correction, purchase=None, expense=None, investor, old_amount,
    new_amount, actor, investment_revision, effective_at,
):
    old_amount = _money(old_amount)
    new_amount = _money(new_amount)
    delta = new_amount - old_amount
    if delta == 0:
        return
    source = purchase or expense
    if investor is None:
        if new_amount != 0:
            raise ValidationError({"investor_id": "A source without an Investor cannot receive Investor Fund allocation."})
        return
    credits = list(
        with_current_fund_credit_owner(
            InvestorFundCredit.objects.select_for_update().filter(tenant=company)
        )
        .filter(current_investor_id=investor.pk)
        .order_by("effective_at", "id")
    )
    if delta > 0:
        remaining = delta
        for credit in credits:
            available = max(Decimal("0.00"), _available_credit(credit))
            part = min(available, remaining)
            if part > 0:
                InvestorFundUseAdjustment.objects.create(
                    tenant=company,
                    credit=credit,
                    purchase_correction=correction if purchase else None,
                    expense_correction=correction if expense else None,
                    amount_delta=part,
                    actor=actor,
                    module_revision=investment_revision,
                    effective_at=effective_at,
                    reason=correction.reason,
                )
                remaining -= part
            if remaining == 0:
                break
        if remaining > 0:
            raise DomainConflict(
                "Investor Fund availability changed while applying the Vehicle cost correction.",
                code="FUND_AVAILABLE_INSUFFICIENT",
            )
        return

    remaining = -delta
    current_by_credit = [
        (credit, _source_fund_usage(purchase=purchase, expense=expense, credit=credit))
        for credit in credits
    ]
    # Reverse the original FIFO consumption order when releasing source allocation.
    for credit, used in reversed(current_by_credit):
        releasable = max(Decimal("0.00"), used)
        part = min(releasable, remaining)
        if part > 0:
            InvestorFundUseAdjustment.objects.create(
                tenant=company,
                credit=credit,
                purchase_correction=correction if purchase else None,
                expense_correction=correction if expense else None,
                amount_delta=-part,
                actor=actor,
                module_revision=investment_revision,
                effective_at=effective_at,
                reason=correction.reason,
            )
            remaining -= part
        if remaining == 0:
            break
    if remaining > 0:
        raise DomainConflict(
            "The current Investor Fund-use ledger does not match the correction's previous allocation.",
            code="FUND_USE_LEDGER_MISMATCH",
        )


def _save_payment_account_preference(*, company, actor, account):
    preference, _created = VehiclePaymentAccountPreference.objects.get_or_create(
        tenant=company, actor=actor, defaults={"account": account}
    )
    if preference.account_id != account.pk:
        preference.account = account
        preference.save(update_fields=("account", "updated_at"))


def get_payment_account_preference(*, actor, company_id):
    company, _scope, _branch = read_scope(
        actor=actor, company_id=company_id, action="vehicle.read"
    )
    preference = VehiclePaymentAccountPreference.objects.filter(
        tenant=company, actor=actor, account__is_active=True
    ).select_related("account").first()
    return {
        "company_id": str(company.pk),
        "account_id": str(preference.account_id) if preference else None,
        "account_label": preference.account.label if preference else None,
    }


def create_purchase_refund(
    *, actor, company_id, purchase_id, key, path, account_id, amount, effective_at=None,
):
    amount = _money(amount)
    effective_at_was_supplied = effective_at is not None
    effective_at = effective_at or timezone.now()
    preview = VehiclePurchase.objects.filter(
        tenant_id=company_id, pk=purchase_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Purchase not found.")
    body = {
        "purchase_id": str(purchase_id), "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "effective_at": effective_at.isoformat() if effective_at_was_supplied else None,
    }

    def operation(company, _branch, revisions, locked_actor):
        purchase = VehiclePurchase.objects.select_for_update().filter(
            tenant=company, pk=purchase_id
        ).select_related("branch").first()
        if purchase is None:
            raise NotFound("Vehicle Purchase not found.")
        require_action(
            locked_actor, "vehicle.purchase.refund", company=company,
            branch=purchase.branch, resource=purchase,
        )
        require_action(
            locked_actor, "accounting.receipt.create", company=company,
            branch=purchase.branch, resource=purchase,
        )
        if effective_at > timezone.now():
            raise ValidationError({"effective_at": "An actual Seller refund cannot be future-dated."})
        paid = purchase.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        already_refunded = purchase.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if amount <= 0 or amount > max(Decimal("0.00"), paid - already_refunded):
            raise DomainConflict(
                "Seller refund cannot exceed the Purchase's net actual payments.",
                code="PURCHASE_REFUND_EXCEEDS_NET_PAID",
            )
        account = AccountingAccount.objects.select_for_update().filter(
            tenant=company, pk=account_id, is_active=True
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        refund = VehiclePurchaseRefund.objects.create(
            tenant=company, purchase=purchase, branch=purchase.branch,
            amount=amount, account=account, effective_at=effective_at,
            actor=locked_actor,
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
        )
        event = _event_row(
            tenant=company, branch=purchase.branch,
            event_type=AccountingEvent.EventType.PURCHASE_REFUND_IN,
            amount=amount, actor=locked_actor,
            revision=revisions[CompanyModuleCode.ACCOUNTING],
            description=f"Seller refund: {purchase.seller_name}",
            source_reference=f"PURCHASE-REFUND-{refund.pk}", effective_at=effective_at,
        )
        AccountMovement.objects.create(tenant=company, event=event, account=account, delta=amount)
        AccountingSourceLink.objects.create(
            tenant=company, event=event, vehicle_purchase_refund=refund
        )
        record_event(
            action="vehicle.purchase.refund", actor=locked_actor, subject=locked_actor,
            company=company, branch=purchase.branch, resource=purchase,
            metadata={"purchase_id": str(purchase.pk), "refund_id": str(refund.pk),
                      "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")},
        )
        return DomainMutationResult(201, {
            **_purchase_data(purchase), "refund_id": str(refund.pk),
            "accounting_event_id": str(event.pk), "refunded_now": format(amount, ".2f"),
        })

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="vehicle.purchase.refund",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id,
    )


def correct_purchase(*, actor, company_id, purchase_id, key, path, purchase_cost, reason):
    purchase_cost = _money(purchase_cost)
    reason = (reason or "").strip()
    preview = VehiclePurchase.objects.filter(
        tenant_id=company_id, pk=purchase_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Purchase not found.")
    body = {
        "purchase_id": str(purchase_id), "purchase_cost": format(purchase_cost, ".2f"),
        "reason": reason,
    }

    def operation(company, _branch, revisions, locked_actor):
        purchase = VehiclePurchase.objects.select_for_update(of=("self",)).filter(
            tenant=company, pk=purchase_id
        ).select_related("branch", "investor").first()
        if purchase is None:
            raise NotFound("Vehicle Purchase not found.")
        require_action(
            locked_actor, "vehicle.purchase.correct", company=company,
            branch=purchase.branch, resource=purchase,
        )
        if purchase_cost <= 0 or not reason:
            raise ValidationError({"purchase_cost": "A positive corrected Purchase cost and reason are required."})
        prior = purchase.corrections.order_by("-version", "-id").first()
        old_cost = prior.purchase_cost if prior else purchase.purchase_cost
        old_fund = prior.investor_fund_amount if prior else purchase.investor_fund_amount
        old_running = prior.running_capital_amount if prior else purchase.running_capital_amount
        if purchase_cost == old_cost:
            raise ValidationError({"purchase_cost": "The corrected Purchase cost must differ from the current cost."})
        paid = purchase.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        refunded = purchase.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        net_paid = paid - refunded
        if purchase_cost < net_paid:
            raise DomainConflict(
                "Record the actual Seller refund before correcting cost below the net amount paid.",
                code="PURCHASE_CORRECTION_REQUIRES_SELLER_REFUND",
            )
        if purchase.investor_id:
            raw_fund = purchase_cost * purchase.investor_fund_amount / purchase.purchase_cost
            desired_fund = raw_fund.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            credits = list(with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update().filter(tenant=company)
            ).filter(current_investor_id=purchase.investor_id).order_by("effective_at", "id"))
            available = sum((max(Decimal("0.00"), _available_credit(row)) for row in credits), Decimal("0.00"))
            new_fund = min(desired_fund, old_fund + available)
        else:
            new_fund = Decimal("0.00")
        new_running = purchase_cost - new_fund
        correction = VehiclePurchaseCorrection.objects.create(
            tenant=company, purchase=purchase, branch=purchase.branch,
            version=(prior.version + 1 if prior else 1),
            previous_purchase_cost=old_cost, purchase_cost=purchase_cost,
            previous_investor_fund_amount=old_fund, investor_fund_amount=new_fund,
            previous_running_capital_amount=old_running, running_capital_amount=new_running,
            reason=reason, effective_at=purchase.purchased_at, actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        _apply_fund_use_correction(
            company=company, correction=correction, purchase=purchase,
            investor=purchase.investor, old_amount=old_fund, new_amount=new_fund,
            actor=locked_actor, investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            effective_at=purchase.purchased_at,
        )
        record_event(
            action="vehicle.purchase.correct", actor=locked_actor, subject=locked_actor,
            company=company, branch=purchase.branch, resource=purchase,
            metadata={"purchase_id": str(purchase.pk), "correction_id": str(correction.pk),
                      "previous_cost": format(old_cost, ".2f"),
                      "purchase_cost": format(purchase_cost, ".2f"),
                      "investor_fund_amount": format(new_fund, ".2f"),
                      "running_capital_amount": format(new_running, ".2f")},
        )
        return DomainMutationResult(201, {
            **_purchase_data(purchase), "correction_id": str(correction.pk),
            "correction_version": correction.version,
        })

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="vehicle.purchase.correct",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id,
    )


def correct_vehicle_expense(*, actor, company_id, expense_id, key, path, amount, reason):
    amount = _money(amount)
    reason = (reason or "").strip()
    preview = VehicleExpense.objects.filter(
        tenant_id=company_id, pk=expense_id
    ).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Expense not found.")
    body = {"expense_id": str(expense_id), "amount": format(amount, ".2f"), "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        expense = VehicleExpense.objects.select_for_update(of=("self",)).filter(
            tenant=company, pk=expense_id
        ).select_related("branch", "investor").first()
        if expense is None:
            raise NotFound("Vehicle Expense not found.")
        require_action(
            locked_actor, "vehicle.expense.correct", company=company,
            branch=expense.branch, resource=expense,
        )
        if amount <= 0 or not reason:
            raise ValidationError({"amount": "A positive corrected amount and reason are required."})
        prior = expense.corrections.order_by("-version", "-id").first()
        old_amount = prior.amount if prior else expense.amount
        old_fund = prior.investor_fund_amount if prior else expense.investor_fund_amount
        old_running = prior.running_capital_amount if prior else expense.running_capital_amount
        if amount == old_amount:
            raise ValidationError({"amount": "The corrected Vehicle Expense must differ from the current amount."})
        _paid, _refunds, net_paid, _payable = _expense_totals(expense)
        if amount < net_paid:
            raise DomainConflict(
                "Record the actual Vendor refund before correcting cost below the net amount paid.",
                code="VEHICLE_EXPENSE_CORRECTION_REQUIRES_REFUND",
            )
        if expense.investor_id:
            credits = list(with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update().filter(tenant=company)
            ).filter(current_investor_id=expense.investor_id).order_by("effective_at", "id"))
            available = sum((max(Decimal("0.00"), _available_credit(row)) for row in credits), Decimal("0.00"))
            new_fund = min(amount, old_fund + available)
        else:
            new_fund = Decimal("0.00")
        if new_fund > old_fund:
            require_action(
                locked_actor, "vehicle.expense.fund", company=company,
                branch=expense.branch, resource=expense,
            )
        new_running = amount - new_fund
        correction = VehicleExpenseCorrection.objects.create(
            tenant=company, expense=expense, branch=expense.branch,
            version=(prior.version + 1 if prior else 1),
            previous_amount=old_amount, amount=amount,
            previous_investor_fund_amount=old_fund, investor_fund_amount=new_fund,
            previous_running_capital_amount=old_running, running_capital_amount=new_running,
            reason=reason, effective_at=expense.effective_at, actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        _apply_fund_use_correction(
            company=company, correction=correction, expense=expense,
            investor=expense.investor, old_amount=old_fund, new_amount=new_fund,
            actor=locked_actor, investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            effective_at=expense.effective_at,
        )
        record_event(
            action="vehicle.expense.correct", actor=locked_actor, subject=locked_actor,
            company=company, branch=expense.branch, resource=expense,
            metadata={"expense_id": str(expense.pk), "correction_id": str(correction.pk),
                      "previous_amount": format(old_amount, ".2f"),
                      "amount": format(amount, ".2f"),
                      "investor_fund_amount": format(new_fund, ".2f"),
                      "running_capital_amount": format(new_running, ".2f")},
        )
        return DomainMutationResult(201, {
            **_expense_data(expense), "correction_id": str(correction.pk),
            "correction_version": correction.version,
        })

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="vehicle.expense.correct",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id,
    )


def list_sales(*, actor, company_id, branch_id=None):
    company, scope, branch = read_scope(
        actor=actor, company_id=company_id, action="vehicle.read", branch_id=branch_id
    )
    queryset = VehicleSale.objects.filter(tenant=company).select_related("vehicle", "branch", "vehicle__purchase").prefetch_related(
        "receipts", "refunds", "corrections"
    )
    if branch is not None:
        if not scope.is_company_reader and branch.pk not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        queryset = queryset.filter(branch=branch)
    elif not scope.is_company_reader:
        queryset = queryset.filter(branch_id__in=scope.allowed_branch_ids)
    return queryset.order_by("-sold_at", "id")


def get_sale(*, actor, company_id, sale_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    sale = VehicleSale.objects.filter(tenant=company, pk=sale_id).select_related(
        "vehicle", "branch", "vehicle__purchase", "vehicle__purchase__investor"
    ).prefetch_related("receipts", "refunds", "corrections").first()
    if sale is None:
        raise NotFound("Vehicle Sale not found.")
    require_action(actor, "vehicle.read", company=company, branch=sale.branch, resource=sale)
    return _sale_data(sale)


def create_sale(*, actor, company_id, key, path, vehicle_id, branch_id, sale_price,
                buyer_name, buyer_phone, sold_at=None):
    sale_price = _money(sale_price)
    buyer_name = (buyer_name or "").strip()
    buyer_phone = (buyer_phone or "").strip()
    sold_at_was_supplied = sold_at is not None
    sold_at = sold_at or timezone.now()
    body = {
        "vehicle_id": str(vehicle_id), "branch_id": str(branch_id),
        "sale_price": format(sale_price, ".2f"), "buyer_name": buyer_name,
        "buyer_phone": buyer_phone,
        "sold_at": sold_at.isoformat() if sold_at_was_supplied else None,
    }

    def operation(company, branch, revisions, locked_actor):
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=vehicle_id, current_branch=branch, is_active=True
        ).first()
        if vehicle is None:
            raise NotFound("Active Vehicle not found in this Branch.")
        if not VehiclePurchase.objects.filter(tenant=company, vehicle=vehicle).exists():
            raise DomainConflict("Only a recorded Stock Vehicle Purchase can be sold.", code="VEHICLE_PURCHASE_REQUIRED")
        if VehicleSale.objects.filter(tenant=company, vehicle=vehicle).exists():
            raise DomainConflict("This Vehicle already has a confirmed Sale.", code="VEHICLE_SALE_EXISTS")
        require_action(locked_actor, "vehicle.sale.create", company=company, branch=branch, resource=vehicle)
        if sale_price <= 0 or not buyer_name or not buyer_phone:
            raise ValidationError({"sale": "A positive Sale price, Buyer name and Buyer phone are required."})
        if sold_at > timezone.now():
            raise ValidationError({"sold_at": "Sale date cannot be in the future."})
        sale = VehicleSale.objects.create(
            tenant=company, vehicle=vehicle, branch=branch, sale_price=sale_price,
            buyer_name=buyer_name, buyer_phone=buyer_phone, sold_at=sold_at,
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
        )
        record_event(
            action="vehicle.sale.create", actor=locked_actor, subject=locked_actor,
            company=company, branch=branch, resource=sale,
            metadata={"sale_id": str(sale.pk), "vehicle_id": str(vehicle.pk),
                      "sale_price": format(sale_price, ".2f")},
        )
        return DomainMutationResult(201, _sale_data(sale))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="vehicle.sale.create",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT,),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=branch_id,
    )


def _save_sale_cash_event(*, company, branch, actor, account, amount, effective_at,
                          accounting_revision, event_type, description, source_reference, source_field, source):
    event = _event_row(
        tenant=company, branch=branch, event_type=event_type, amount=amount, actor=actor,
        revision=accounting_revision, description=description,
        source_reference=source_reference, effective_at=effective_at,
    )
    delta = amount if event_type != AccountingEvent.EventType.VEHICLE_SALE_REFUND else -amount
    AccountMovement.objects.create(tenant=company, event=event, account=account, delta=delta)
    AccountingSourceLink.objects.create(
        tenant=company, event=event, **{source_field: source}
    )
    return event


def create_sale_receipt(*, actor, company_id, sale_id, key, path, account_id, amount,
                        reference, effective_at=None):
    amount = _money(amount)
    reference = (reference or "").strip()
    effective_at_was_supplied = effective_at is not None
    effective_at = effective_at or timezone.now()
    preview = VehicleSale.objects.filter(tenant_id=company_id, pk=sale_id).select_related(
        "branch", "vehicle__purchase"
    ).first()
    if preview is None:
        raise NotFound("Vehicle Sale not found.")
    investor_funded = _vehicle_uses_investor_fund(preview.vehicle)
    body = {"sale_id": str(sale_id), "account_id": str(account_id), "amount": format(amount, ".2f"),
            "reference": reference,
            "effective_at": effective_at.isoformat() if effective_at_was_supplied else None}
    modules = [CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING]
    if investor_funded:
        modules.append(CompanyModuleCode.INVESTMENT)

    def operation(company, _branch, revisions, locked_actor):
        sale = VehicleSale.objects.select_for_update(of=("self",)).filter(tenant=company, pk=sale_id).select_related(
            "branch", "vehicle__purchase"
        ).first()
        if sale is None:
            raise NotFound("Vehicle Sale not found.")
        require_action(locked_actor, "vehicle.sale.receipt", company=company,
                       branch=sale.branch, resource=sale)
        require_action(locked_actor, "accounting.receipt.create", company=company,
                       branch=sale.branch, resource=sale)
        current_investor_funded = _vehicle_uses_investor_fund(sale.vehicle)
        if current_investor_funded != investor_funded:
            raise DomainConflict("Sale funding changed; reload before recording the Buyer Receipt.", code="SALE_SOURCE_CHANGED")
        if not reference or effective_at > timezone.now():
            raise ValidationError({"reference": "A required reference and actual past/equal receipt date are needed."})
        current_price = sale.corrections.order_by("-version", "-id").values_list("sale_price", flat=True).first() or sale.sale_price
        received = sale.receipts.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        refunded = sale.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        outstanding = current_price - received + refunded
        if amount <= 0 or amount > outstanding:
            raise DomainConflict("Buyer Receipt must not exceed the current Sale receivable.", code="SALE_RECEIVABLE_EXCEEDED")
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        receipt = VehicleSaleReceipt.objects.create(
            tenant=company, sale=sale, branch=sale.branch, amount=amount, account=account,
            reference=reference, effective_at=effective_at, actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            investment_module_revision=(
                revisions[CompanyModuleCode.INVESTMENT] if current_investor_funded else None
            ),
        )
        event = _save_sale_cash_event(
            company=company, branch=sale.branch, actor=locked_actor, account=account,
            amount=amount, effective_at=effective_at,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.VEHICLE_SALE_RECEIPT,
            description=f"Vehicle Sale receipt: {sale.buyer_name}", source_reference=reference,
            source_field="vehicle_sale_receipt", source=receipt,
        )
        record_event(action="vehicle.sale.receipt", actor=locked_actor, subject=locked_actor,
                     company=company, branch=sale.branch, resource=sale,
                     metadata={"sale_id": str(sale.pk), "receipt_id": str(receipt.pk),
                               "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")})
        return DomainMutationResult(201, {**_sale_data(sale), "receipt_id": str(receipt.pk),
                                          "accounting_event_id": str(event.pk),
                                          "received_now": format(amount, ".2f")})

    try:
        return execute_domain_mutation(
            actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
            action="vehicle.sale.receipt", module_codes=tuple(modules),
            idempotency_model=VehicleIdempotencyRecord, operation=operation,
            branch_id=preview.branch_id,
        )
    except IntegrityError as exc:
        constraint = getattr(getattr(getattr(exc, "__cause__", None), "diag", None), "constraint_name", None)
        if constraint == "vehicle_sale_receipt_ref_uq":
            raise DomainConflict("This Buyer Receipt reference already exists for this Company account.",
                                 code="VEHICLE_SALE_RECEIPT_REFERENCE_DUPLICATE") from exc
        raise


def create_sale_refund(*, actor, company_id, sale_id, key, path, account_id, amount, effective_at=None):
    amount = _money(amount)
    effective_at_was_supplied = effective_at is not None
    effective_at = effective_at or timezone.now()
    preview = VehicleSale.objects.filter(tenant_id=company_id, pk=sale_id).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Sale not found.")
    body = {"sale_id": str(sale_id), "account_id": str(account_id), "amount": format(amount, ".2f"),
            "effective_at": effective_at.isoformat() if effective_at_was_supplied else None}

    def operation(company, _branch, revisions, locked_actor):
        sale = VehicleSale.objects.select_for_update().filter(tenant=company, pk=sale_id).select_related("branch").first()
        if sale is None:
            raise NotFound("Vehicle Sale not found.")
        require_action(locked_actor, "vehicle.sale.refund", company=company, branch=sale.branch, resource=sale)
        require_action(locked_actor, "accounting.payment.create", company=company, branch=sale.branch, resource=sale)
        if effective_at > timezone.now():
            raise ValidationError({"effective_at": "An actual Buyer refund cannot be future-dated."})
        received = sale.receipts.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        refunded = sale.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        current_price = sale.corrections.order_by("-version", "-id").values_list(
            "sale_price", flat=True
        ).first() or sale.sale_price
        refund_payable = max(Decimal("0.00"), received - refunded - current_price)
        if amount <= 0 or amount > refund_payable:
            raise DomainConflict(
                "Buyer refund cannot exceed the current Sale refund payable.",
                code="SALE_REFUND_EXCEEDS_NET_RECEIVED",
            )
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        refund = VehicleSaleRefund.objects.create(
            tenant=company, sale=sale, branch=sale.branch, amount=amount, account=account,
            effective_at=effective_at, actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        event = _save_sale_cash_event(
            company=company, branch=sale.branch, actor=locked_actor, account=account,
            amount=amount, effective_at=effective_at,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.VEHICLE_SALE_REFUND,
            description=f"Vehicle Sale refund: {sale.buyer_name}",
            source_reference=f"SALE-REFUND-{refund.pk}",
            source_field="vehicle_sale_refund", source=refund,
        )
        record_event(action="vehicle.sale.refund", actor=locked_actor, subject=locked_actor,
                     company=company, branch=sale.branch, resource=sale,
                     metadata={"sale_id": str(sale.pk), "refund_id": str(refund.pk),
                               "accounting_event_id": str(event.pk), "amount": format(amount, ".2f")})
        return DomainMutationResult(201, {**_sale_data(sale), "refund_id": str(refund.pk),
                                          "accounting_event_id": str(event.pk),
                                          "refunded_now": format(amount, ".2f")})

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="vehicle.sale.refund",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id,
    )


def correct_sale(*, actor, company_id, sale_id, key, path, sale_price, reason):
    sale_price = _money(sale_price)
    reason = (reason or "").strip()
    preview = VehicleSale.objects.filter(tenant_id=company_id, pk=sale_id).select_related("branch").first()
    if preview is None:
        raise NotFound("Vehicle Sale not found.")
    body = {"sale_id": str(sale_id), "sale_price": format(sale_price, ".2f"), "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        sale = VehicleSale.objects.select_for_update().filter(tenant=company, pk=sale_id).select_related("branch").first()
        if sale is None:
            raise NotFound("Vehicle Sale not found.")
        require_action(locked_actor, "vehicle.sale.correct", company=company, branch=sale.branch, resource=sale)
        prior = sale.corrections.order_by("-version", "-id").first()
        old_price = prior.sale_price if prior else sale.sale_price
        if sale_price <= 0 or not reason or sale_price == old_price:
            raise ValidationError({"sale_price": "A different positive Sale price and correction reason are required."})
        correction = VehicleSaleCorrection.objects.create(
            tenant=company, sale=sale, branch=sale.branch,
            version=(prior.version + 1 if prior else 1), previous_sale_price=old_price,
            sale_price=sale_price, reason=reason, effective_at=sale.sold_at,
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(action="vehicle.sale.correct", actor=locked_actor, subject=locked_actor,
                     company=company, branch=sale.branch, resource=sale,
                     metadata={"sale_id": str(sale.pk), "correction_id": str(correction.pk),
                               "previous_price": format(old_price, ".2f"),
                               "sale_price": format(sale_price, ".2f")})
        return DomainMutationResult(201, {**_sale_data(sale), "correction_id": str(correction.pk),
                                          "correction_version": correction.version})

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="vehicle.sale.correct",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=VehicleIdempotencyRecord, operation=operation,
        branch_id=preview.branch_id,
    )
