"""Accountant confirmation of mixed-funded Buyer principal refund obligations."""
from decimal import Decimal

from django.db.models import Sum
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.audit import record_event
from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
from apps.investment.models import (
    InvestmentIdempotencyRecord, VehicleCapitalRecovery, VehiclePrincipalRefundDebit,
    VehiclePrincipalRefundReview,
)
from apps.tenants.models import CompanyModuleCode


def confirm_principal_refund_review(*, actor, company_id, sale_id, principal_amount,
                                   expected_source_version, reason, key, path):
    from apps.vehicles.models import VehicleSale
    from apps.vehicles.services import get_vehicle_financial_position

    amount, reason = Decimal(principal_amount), reason.strip()
    if amount < 0 or len(reason) < 3:
        raise ValidationError("A nonnegative principal amount and confirmation reason are required.")
    body = {"sale_id": str(sale_id), "principal_amount": format(amount, ".2f"),
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        sale = VehicleSale.objects.select_for_update(of=("self",)).filter(tenant=company, pk=sale_id).first()
        if sale is None:
            raise NotFound("Vehicle Sale not found.")
        position = get_vehicle_financial_position(
            actor=locked_actor, company_id=company.pk, vehicle_id=sale.vehicle_id,
        )
        if position["source_version"] != expected_source_version:
            raise DomainConflict("Sale sources changed; reload the refund review.", code="VEHICLE_RESULT_STALE")
        correction = sale.corrections.order_by("-version", "-id").first()
        recoveries = VehicleCapitalRecovery.objects.filter(tenant=company, sale=sale)
        recovery = recoveries.filter(investor_principal__gt=0).order_by("created_at", "id").first()
        if correction is None or recovery is None or Decimal(position["running_capital_cost"]) <= 0:
            raise DomainConflict("A corrected mixed-funded recovered Sale is required.",
                                 code="REFUND_PRINCIPAL_REVIEW_NOT_AVAILABLE")
        total = recoveries.aggregate(total=Sum("investor_principal"))["total"] or Decimal("0")
        debited = VehiclePrincipalRefundDebit.objects.filter(tenant=company, refund__sale=sale).aggregate(
            total=Sum("amount"))["total"] or Decimal("0")
        if amount > min(total - debited, Decimal(position["buyer_refund_payable"] or "0")):
            raise DomainConflict("Principal obligation exceeds recovered principal or Buyer refund payable.",
                                 code="REFUND_PRINCIPAL_EXCEEDS_BALANCE")
        existing = VehiclePrincipalRefundReview.objects.filter(tenant=company, sale_correction=correction).first()
        if existing:
            if existing.principal_amount != amount:
                raise DomainConflict("This correction already has a confirmed principal obligation.",
                                     code="REFUND_PRINCIPAL_REVIEW_EXISTS")
            return DomainMutationResult(200, {"id": str(existing.pk), "principal_amount": format(amount, ".2f")})
        review = VehiclePrincipalRefundReview.objects.create(
            tenant=company, recovery=recovery, sale_correction=correction, principal_amount=amount,
            principal_debited_before=debited, source_version=expected_source_version,
            reason=reason, actor=locked_actor,
        )
        record_event(action="investment.capital.recovery.confirm", actor=locked_actor, subject=locked_actor,
                     company=company, branch=sale.branch, resource=recovery, reason=reason,
                     metadata={"sale_id": str(sale.pk), "operation_id": str(review.pk), "source_version": expected_source_version,
                               "amount": format(amount, ".2f"), "cash_movement_created": False})
        return DomainMutationResult(201, {"id": str(review.pk), "principal_amount": format(amount, ".2f")})

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.capital.recovery.confirm",
        module_codes=(CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )
