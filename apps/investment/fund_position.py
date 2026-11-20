"""Internal source-derived Investor Fund position for recovery integration.

This is not yet an API or a write authorization. Callers must lock the Company
and Investor when using the result to authorize a financial mutation.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from django.db.models import Q, Sum

from apps.investment.finance import calculate_investor_only_refund_reserve
from apps.investment.models import (
    InvestorFundCredit, InvestorFundCreditCorrection, InvestorFundUseAllocation,
    InvestorFundUseAdjustment, InvestorPrincipalReturnAllocation,
    VehicleCapitalRecovery, VehicleCapitalRecoveryCreditAllocation, VehicleCapitalRecoveryReview,
    VehiclePrincipalRefundDebit,
    VehiclePrincipalRefundReview,
    VehicleRefundPrincipalClassification,
)
from apps.investment.selectors import with_current_fund_credit_owner
from apps.vehicles.models import VehicleExpense, VehiclePurchase, VehicleSaleReceipt, VehicleSaleRefund


class FundPositionReviewRequired(ValueError):
    """A source change requires manual reconciliation before using a balance."""


def prepare_principal_refund(*, company, sale, actor, refund_amount, principal_amount):
    """Plan allocations before creating cash rows, while the Company is locked.

    Recovery provenance and the Fund lot paying the Buyer are independent:
    recovered capital can already have been redeployed to another Vehicle.
    """
    from apps.accounts.policy import require_action
    from apps.common.domain_mutations import DomainConflict
    from apps.investment.models import Investor

    recoveries = VehicleCapitalRecovery.objects.filter(
        tenant=company, sale=sale, investor_principal__gt=0,
    )
    if not recoveries.exists():
        if principal_amount not in (None, Decimal("0")):
            raise DomainConflict("No recovered Investor principal backs this refund.",
                                 code="REFUND_PRINCIPAL_EXCEEDS_BALANCE")
        return None
    require_action(actor, "investment.capital.recovery.confirm", company=company)
    if principal_amount is None:
        raise DomainConflict("Specify the Investor principal portion, including zero.",
                             code="REFUND_PRINCIPAL_CLASSIFICATION_REQUIRED")
    investor_ids = set(recoveries.values_list("investor_id", flat=True))
    if len(investor_ids) != 1:
        raise DomainConflict("Recovery ownership requires review.", code="RECOVERY_FUND_LOT_REVIEW_REQUIRED")
    investor = Investor.objects.select_for_update().get(tenant=company, pk=investor_ids.pop())
    try:
        position = investor_fund_position(company=company, investor=investor)
    except FundPositionReviewRequired as exc:
        raise DomainConflict(str(exc), code="RECOVERY_REFUND_REVIEW_REQUIRED") from exc
    due = position.sale_principal_due.get(sale.pk, Decimal("0"))
    if principal_amount < 0 or principal_amount > min(refund_amount, due, position.reserve):
        raise DomainConflict("Principal refund exceeds the current backed and held amount.",
                             code="REFUND_PRINCIPAL_EXCEEDS_BALANCE")
    # Paying a non-principal portion must not leave less total payable than
    # the outstanding principal component.
    received = sale.receipts.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    refunded = sale.refunds.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    correction = sale.corrections.order_by("-version", "-id").first()
    price = correction.sale_price if correction else sale.sale_price
    if due - principal_amount > received - refunded - price - refund_amount:
        raise DomainConflict("Remaining refund cannot cover its principal component.",
                             code="REFUND_PRINCIPAL_REMAINDER_INVALID")
    sources = list(VehicleCapitalRecoveryCreditAllocation.objects.select_for_update().filter(
        tenant=company, recovery__sale=sale, recovery__investor=investor,
    ).order_by("recovery__created_at", "id"))
    spent = _totals(VehiclePrincipalRefundDebit.objects.filter(
        tenant=company, recovery_allocation__in=sources,
    ), "recovery_allocation_id", "amount")
    held = dict(position.lot_reserved)
    parts = []
    remaining = principal_amount
    for source in sources:
        source_left = source.amount - (spent.get(source.pk) or Decimal("0"))
        for credit_id, balance in held.items():
            part = min(source_left, balance, remaining)
            if part > 0:
                parts.append((source, credit_id, part))
                held[credit_id] -= part
                source_left -= part
                remaining -= part
            if not source_left or not remaining:
                break
        if not remaining:
            break
    if remaining:
        raise DomainConflict("Refund Fund lots require review.", code="RECOVERY_FUND_LOT_REVIEW_REQUIRED")
    return principal_amount, parts


def record_principal_refund(*, company, refund, actor, plan):
    if plan is None:
        return
    amount, parts = plan
    VehicleRefundPrincipalClassification.objects.create(
        tenant=company, refund=refund, actor=actor, principal_amount=amount,
    )
    for source, credit_id, part in parts:
        VehiclePrincipalRefundDebit.objects.create(
            tenant=company, refund=refund, recovery_allocation=source,
            fund_credit_id=credit_id, amount=part,
        )


@dataclass(frozen=True)
class InvestorFundPosition:
    gross_available: Decimal
    principal_refund_due: Decimal
    reserve: Decimal
    uncovered: Decimal
    available: Decimal
    lot_available: dict
    lot_reserved: dict
    sale_principal_due: dict


def _totals(queryset, key, amount):
    return {row[key]: row["total"] for row in queryset.values(key).annotate(total=Sum(amount))}


def investor_fund_position(*, company, investor):
    """Compute current credit-lot balances and Investor-only refund reserve.

    Unsupported corrections, mixed-funded refund cases and actual Buyer
    refunds fail closed pending the explicit refund allocation workflow.
    Historical rows are never silently reassigned after attribution changes.
    """
    if investor.tenant_id != company.pk:
        raise FundPositionReviewRequired("Investor is not in this Company.")
    credits = list(with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    ).filter(current_investor_id=investor.pk).order_by("effective_at", "id"))
    credit_ids = [row.pk for row in credits]
    if InvestorFundCreditCorrection.objects.filter(tenant=company).filter(
        Q(from_investor=investor) | Q(to_investor=investor),
    ).filter(Q(credit__use_allocations__isnull=False) | Q(credit__return_allocations__isnull=False)).exists():
        raise FundPositionReviewRequired("Fund attribution with historical allocations requires review.")
    allocations = VehicleCapitalRecoveryCreditAllocation.objects.filter(tenant=company)
    if allocations.filter(recovery__investor=investor).exclude(credit_id__in=credit_ids).exists() or allocations.filter(
        credit_id__in=credit_ids,
    ).exclude(recovery__investor=investor).exists():
        raise FundPositionReviewRequired("Recovered credit attribution requires review.")

    used = _totals(InvestorFundUseAllocation.objects.filter(tenant=company, credit_id__in=credit_ids), "credit_id", "amount")
    adjustments = _totals(InvestorFundUseAdjustment.objects.filter(tenant=company, credit_id__in=credit_ids), "credit_id", "amount_delta")
    returned = _totals(InvestorPrincipalReturnAllocation.objects.filter(tenant=company, credit_id__in=credit_ids), "credit_id", "amount")
    recovered = _totals(allocations.filter(credit_id__in=credit_ids), "credit_id", "amount")
    debited = _totals(VehiclePrincipalRefundDebit.objects.filter(
        tenant=company, fund_credit_id__in=credit_ids,
    ), "fund_credit_id", "amount")

    recoveries = list(VehicleCapitalRecovery.objects.filter(
        tenant=company, investor=investor,
    ).select_related("sale").prefetch_related("sale__corrections").order_by("created_at", "id"))
    sale_ids = {row.sale_id for row in recoveries}
    principal_reviews = {
        row.sale_correction_id: row for row in VehiclePrincipalRefundReview.objects.filter(
            tenant=company, recovery__sale_id__in=sale_ids,
        )
    }
    reviewed_sale_versions = set(VehicleCapitalRecoveryReview.objects.filter(
        tenant=company, recovery__sale_id__in=sale_ids,
    ).values_list("recovery__sale_id", "sale_correction_version"))
    vehicle_ids = {row.sale.vehicle_id for row in recoveries}
    receipts = _totals(VehicleSaleReceipt.objects.filter(tenant=company, sale_id__in=sale_ids), "sale_id", "amount")
    refunds = _totals(VehicleSaleRefund.objects.filter(tenant=company, sale_id__in=sale_ids), "sale_id", "amount")
    unclassified_refund_sales = set(VehicleSaleRefund.objects.filter(
        tenant=company, sale_id__in=sale_ids, principal_classification__isnull=True,
    ).values_list("sale_id", flat=True))
    purchases = {row.vehicle_id: row for row in VehiclePurchase.objects.filter(
        tenant=company, vehicle_id__in=vehicle_ids,
    ).prefetch_related("corrections")}
    expenses = list(VehicleExpense.objects.filter(
        tenant=company, vehicle_id__in=vehicle_ids,
    ).prefetch_related("corrections"))
    expenses_by_vehicle = {}
    for expense in expenses:
        expenses_by_vehicle.setdefault(expense.vehicle_id, []).append(expense)
    grouped = {}
    for row in recoveries:
        group = grouped.setdefault(row.sale_id, {"sale": row.sale, "rows": []})
        group["rows"].append(row)
    refund_debits = _totals(VehiclePrincipalRefundDebit.objects.filter(
        tenant=company, refund__sale_id__in=sale_ids,
    ), "refund__sale_id", "amount")

    with localcontext() as context:
        context.prec = 80
        balances = {}
        for credit in credits:
            balance = (credit.amount - (used.get(credit.pk) or 0) - (adjustments.get(credit.pk) or 0)
                       - (returned.get(credit.pk) or 0) + (recovered.get(credit.pk) or 0)
                       - (debited.get(credit.pk) or 0))
            if balance < 0:
                raise FundPositionReviewRequired("A Fund credit lot has a negative balance.")
            balances[credit.pk] = balance
        gross = sum(balances.values(), Decimal("0.00"))
        principal_due = Decimal("0.00")
        sale_principal_due = {}
        for sale_id, group in grouped.items():
            sale = group["sale"]
            purchase = purchases.get(sale.vehicle_id)
            if purchase is None or purchase.investor_id != investor.pk:
                raise FundPositionReviewRequired("Vehicle funding ownership requires review.")
            first_recovery = group["rows"][0].created_at
            purchase_corrections = list(purchase.corrections.all())
            vehicle_expenses = expenses_by_vehicle.get(sale.vehicle_id, [])
            if any(row.created_at > first_recovery for row in purchase_corrections) or any(
                expense.created_at > first_recovery or any(row.created_at > first_recovery for row in expense.corrections.all())
                for expense in vehicle_expenses
            ):
                raise FundPositionReviewRequired("Vehicle funding changed after recovery.")
            current_purchase = max(purchase_corrections, key=lambda row: (row.version, str(row.pk)), default=None)
            running = current_purchase.running_capital_amount if current_purchase else purchase.running_capital_amount
            for expense in vehicle_expenses:
                latest = max(expense.corrections.all(), key=lambda row: (row.version, str(row.pk)), default=None)
                running += latest.running_capital_amount if latest else expense.running_capital_amount
            sale_corrections = list(sale.corrections.all())
            current_sale = max(sale_corrections, key=lambda row: (row.version, str(row.pk)), default=None)
            price = current_sale.sale_price if current_sale else sale.sale_price
            if sale_id in unclassified_refund_sales:
                raise FundPositionReviewRequired("Actual Buyer refund allocation requires review.")
            received = receipts.get(sale_id) or Decimal("0.00")
            refunded = refunds.get(sale_id) or Decimal("0.00")
            if refunded > received:
                raise FundPositionReviewRequired("Buyer refunds exceed received money.")
            refund_due = max(Decimal("0.00"), received - refunded - price)
            sale_reviewed = (sale_id, current_sale.version if current_sale else 0) in reviewed_sale_versions
            principal_review = principal_reviews.get(current_sale.pk) if current_sale else None
            if running > 0 and principal_review:
                since_review = (refund_debits.get(sale_id) or Decimal("0")) - principal_review.principal_debited_before
                due = principal_review.principal_amount - since_review
                if due < 0 or due > refund_due:
                    raise FundPositionReviewRequired("Principal refund review no longer reconciles.")
                principal_due += due
                sale_principal_due[sale_id] = due
            elif running > 0 and (refund_due or (
                any(row.created_at > first_recovery for row in sale_corrections) and not sale_reviewed
            )):
                raise FundPositionReviewRequired("Mixed-funded Sale correction requires review.")
            if running == 0:
                result = calculate_investor_only_refund_reserve(
                    recovered_principal=sum((row.investor_principal for row in group["rows"]), Decimal("0.00")),
                    principal_refunded=refund_debits.get(sale_id) or Decimal("0.00"),
                    sale_applied=min(received - refunded, price), refund_payable=refund_due, fund_balance=gross,
                )
                principal_due += result.principal_refund_due
                sale_principal_due[sale_id] = result.principal_refund_due
        reserved = min(principal_due, gross)
        remaining_reserve = reserved
        reserved_by_credit = {}
        for credit in credits:
            held = min(balances[credit.pk], remaining_reserve)
            reserved_by_credit[credit.pk] = held
            balances[credit.pk] -= held
            remaining_reserve -= held
        return InvestorFundPosition(
            gross_available=gross, principal_refund_due=principal_due, reserve=reserved,
            uncovered=principal_due - reserved, available=gross - reserved, lot_available=balances,
            lot_reserved=reserved_by_credit, sale_principal_due=sale_principal_due,
        )
