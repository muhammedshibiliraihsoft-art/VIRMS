import hashlib
import json
from decimal import Decimal, localcontext
from datetime import date
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Count, DecimalField, Exists, F, Func, Max, OuterRef, Prefetch, Q, Sum
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

INVESTOR_PROFIT_TIME_ZONE = ZoneInfo("Asia/Kolkata")

from apps.accounts.audit import record_event
from apps.accounts.policy import require_action
from apps.accounting.models import AccountingAccount, AccountingEvent, AccountingSourceLink
from apps.accounting.services import (
    record_capital_movement,
    record_investor_interim_payment,
    record_investor_vehicle_profit_payment,
    record_vehicle_company_share_recognition,
)
from apps.common.business_scope import business_scope
from apps.common.domain_mutations import (
    DomainConflict,
    DomainMutationResult,
    execute_domain_mutation,
)
from apps.investment.models import (
    InvestmentIdempotencyRecord,
    Investor,
    InvestorExitRequest,
    InvestorFundCredit,
    InvestorFundCreditCorrection,
    InvestorFundUseAllocation,
    InvestorFundUseAdjustment,
    InvestorInterimConfiguration,
    InvestorInterimPayment,
    InvestorProfitCalendarConfiguration,
    InvestorProfitShareAgreement,
    InvestorPrincipalReturn,
    InvestorPrincipalReturnAllocation,
    InvestorProfitLossOffset,
    InvestorExitLossApplication,
    InvestorProfitPeriodReconciliation,
    InvestorVehicleProfitPayment,
    VehicleCapitalRecovery,
    VehicleCapitalRecoveryCreditAllocation,
    VehicleCapitalRecoveryReceiptAllocation,
    VehicleResultConfirmation,
)
from apps.investment.selectors import with_current_fund_credit_owner, with_fund_credit_available
from apps.tenants.models import Branch, CompanyModuleCode, Tenant


def _vehicle_result_data(row):
    return {
        "id": str(row.pk), "tenant_id": str(row.tenant_id),
        "vehicle_id": str(row.vehicle_id), "purchase_id": str(row.purchase_id),
        "sale_id": str(row.sale_id),
        "investor_id": str(row.investor_id) if row.investor_id else None,
        "version": row.version, "source_version": row.source_version,
        "result_kind": row.result_kind,
        "purchase_cost": format(Decimal(row.purchase_cost), ".2f"),
        "expense_cost": format(Decimal(row.expense_cost), ".2f"),
        "sale_price": format(Decimal(row.sale_price), ".2f"),
        "investor_share_percentage": (
            format(Decimal(row.investor_share_percentage), ".4f")
            if row.investor_share_percentage is not None else None
        ),
        "result_amount": format(Decimal(row.result_amount), ".2f"),
        "investor_share_amount": format(Decimal(row.investor_share_amount), ".2f"),
        "company_share_amount": format(Decimal(row.company_share_amount), ".2f"),
        "suggested_investor_loss": format(row.suggested_investor_loss, ".2f") if row.suggested_investor_loss is not None else None,
        "suggested_company_loss": format(row.suggested_company_loss, ".2f") if row.suggested_company_loss is not None else None,
        "reason": row.reason, "confirmed_at": row.confirmed_at.isoformat(),
        "confirmed_by_id": str(row.confirmed_by_id),
    }


def confirm_vehicle_result(
    *, actor, company_id, vehicle_id, expected_source_version, reason, key, path,
    investor_loss_amount=None, company_loss_amount=None,
):
    from apps.investment.finance import VehicleShareAmounts, calculate_vehicle_shares
    from apps.vehicles.models import VehiclePurchase
    from apps.vehicles.services import get_vehicle_financial_position

    for field, value in (("investor_loss_amount", investor_loss_amount), ("company_loss_amount", company_loss_amount)):
        if value is not None and (not isinstance(value, Decimal) or not value.is_finite() or value < 0):
            raise ValidationError({field: "A finite nonnegative amount is required."})

    purchase = VehiclePurchase.objects.filter(
        tenant_id=company_id, vehicle_id=vehicle_id
    ).only("investor_id").first()
    module_codes = [CompanyModuleCode.VEHICLE_MANAGEMENT]
    # Result confirmation and its Company Share recognition must commit as one
    # accounting-backed operation. Investor-funded Vehicles additionally need
    # the Investment module for the approved agreement snapshot.
    module_codes.append(CompanyModuleCode.ACCOUNTING)
    if purchase and purchase.investor_id:
        module_codes.append(CompanyModuleCode.INVESTMENT)
    body = {
        "vehicle_id": str(vehicle_id),
        "expected_source_version": expected_source_version,
        "reason": reason.strip(),
    }
    # Preserve the idempotency hash for previously submitted positive results.
    if investor_loss_amount is not None:
        body["investor_loss_amount"] = format(investor_loss_amount, ".2f")
    if company_loss_amount is not None:
        body["company_loss_amount"] = format(company_loss_amount, ".2f")

    def operation(company, _branch, revisions, locked_actor):
        position = get_vehicle_financial_position(
            actor=locked_actor, company_id=company.pk, vehicle_id=vehicle_id
        )
        if position["purchase_id"] is None or position["sale_id"] is None:
            raise DomainConflict(
                "A completed Vehicle Purchase and Sale are required before result confirmation.",
                code="VEHICLE_RESULT_SOURCES_INCOMPLETE",
            )
        if position["source_version"] != expected_source_version:
            raise DomainConflict(
                "Vehicle sources changed. Reload the current financial position before confirming.",
                code="VEHICLE_RESULT_STALE",
            )
        if position["status"] not in ("READY_FOR_REVIEW", "LOSS_REVIEW_REQUIRED"):
            raise DomainConflict(
                "Vehicle result is not ready: collection, refund, or source checks remain open.",
                code="VEHICLE_RESULT_NOT_READY",
            )
        if position["profit_share_status"] == "AGREEMENT_SNAPSHOT_MISSING":
            raise DomainConflict(
                "This Investor-funded Vehicle has no allocation-time agreement snapshot; manual review is required.",
                code="INVESTOR_AGREEMENT_SNAPSHOT_MISSING",
            )
        if VehicleResultConfirmation.objects.filter(
            tenant=company, vehicle_id=vehicle_id, source_version=expected_source_version
        ).exists():
            raise DomainConflict(
                "This exact source version was already confirmed.",
                code="VEHICLE_RESULT_ALREADY_CONFIRMED",
            )

        from apps.vehicles.models import Vehicle, VehicleSale
        vehicle = Vehicle.objects.select_for_update().get(pk=vehicle_id, tenant=company)
        purchase_row = VehiclePurchase.objects.select_related("investor").get(
            pk=position["purchase_id"], tenant=company, vehicle=vehicle
        )
        # An Investor can fund a later Vehicle expense even when the purchase
        # was Company-funded. That path has no purchase-time agreement
        # snapshot, so treating the Vehicle as Company-only would recognize
        # the Investor's share as Company income.
        from apps.vehicles.services import _vehicle_investor_ids
        vehicle_investors = _vehicle_investor_ids(company=company, vehicle=vehicle)
        if vehicle_investors and (
            purchase_row.investor_id is None
            or vehicle_investors != {purchase_row.investor_id}
        ):
            raise DomainConflict(
                "Vehicle Investor funding has no matching purchase agreement snapshot; manual review is required.",
                code="INVESTOR_AGREEMENT_SNAPSHOT_MISSING",
            )
        sale_row = VehicleSale.objects.get(
            pk=position["sale_id"], tenant=company, vehicle=vehicle
        )
        result = Decimal(position["calculated_result"])
        percentage = purchase_row.investor_share_percentage_snapshot
        suggested = calculate_vehicle_shares(result=result, investor_percentage=percentage) if result < 0 else None
        if result < 0:
            if investor_loss_amount is None or company_loss_amount is None:
                raise ValidationError({"loss_allocation": "Explicit Investor and Company Loss amounts are required."})
            with localcontext() as context:
                context.prec = 80
                if investor_loss_amount + company_loss_amount != result.copy_abs():
                    raise ValidationError({"loss_allocation": "Investor and Company Loss amounts must equal the Vehicle Loss."})
                if purchase_row.investor_id is None and investor_loss_amount != 0:
                    raise ValidationError({"investor_loss_amount": "This Vehicle has no Investor."})
                amounts = VehicleShareAmounts(-investor_loss_amount, -company_loss_amount)
        else:
            if investor_loss_amount is not None or company_loss_amount is not None:
                raise ValidationError({"loss_allocation": "Loss amounts apply only to a Vehicle Loss."})
            amounts = calculate_vehicle_shares(result=result, investor_percentage=percentage)
        kind = (
            VehicleResultConfirmation.ResultKind.PROFIT if result > 0
            else VehicleResultConfirmation.ResultKind.LOSS if result < 0
            else VehicleResultConfirmation.ResultKind.BREAK_EVEN
        )
        latest_version = VehicleResultConfirmation.objects.filter(
            tenant=company, vehicle=vehicle
        ).aggregate(max_version=Max("version"))["max_version"] or 0
        row = VehicleResultConfirmation.objects.create(
            tenant=company, vehicle=vehicle, purchase=purchase_row, sale=sale_row,
            investor=purchase_row.investor, version=latest_version + 1,
            source_version=expected_source_version, result_kind=kind,
            purchase_cost=position["purchase_cost"],
            expense_cost=position["vehicle_expense_cost"], sale_price=position["sale_price"],
            investor_share_percentage=percentage, result_amount=result,
            investor_share_amount=amounts.investor_share,
            company_share_amount=amounts.company_share, reason=reason.strip(),
            suggested_investor_loss=suggested.investor_share.copy_abs() if suggested else None,
            suggested_company_loss=suggested.company_share.copy_abs() if suggested else None,
            confirmed_by=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=(
                revisions.get(CompanyModuleCode.INVESTMENT) if purchase_row.investor_id else None
            ),
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        company_share_event, reversed_company_share_event_ids = (
            record_vehicle_company_share_recognition(
                tenant=company,
                result_confirmation=row,
                actor=locked_actor,
                accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            )
        )
        record_event(
            action="investment.vehicle_result.confirm", actor=locked_actor,
            subject=locked_actor, company=company, resource=row, reason=reason.strip(),
            metadata={
                "vehicle_id": str(vehicle.pk), "result_id": str(row.pk),
                "result_kind": kind, "result_amount": format(result, ".2f"),
                "investor_share_amount": format(amounts.investor_share, ".2f"),
                "company_share_amount": format(amounts.company_share, ".2f"),
                "suggested_investor_loss": format(row.suggested_investor_loss, ".2f") if suggested else None,
                "suggested_company_loss": format(row.suggested_company_loss, ".2f") if suggested else None,
                "source_version": expected_source_version,
                "company_share_accounting_event_id": (
                    str(company_share_event.pk) if company_share_event else None
                ),
                "reversed_company_share_accounting_event_id": (
                    reversed_company_share_event_ids[0]
                    if reversed_company_share_event_ids else None
                ),
            },
        )
        return DomainMutationResult(201, _vehicle_result_data(row))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.vehicle_result.confirm",
        module_codes=tuple(module_codes), idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def create_vehicle_capital_recovery(*, actor, company_id, sale_id, expected_source_version, reason, key, path):
    """Classify collected capital without creating another Accounting movement.

    The surrounding transaction serializes Company writers, checks module
    revisions and persists the idempotent response. Corrected funding and
    unresolved refunds remain subject to explicit review.
    """
    from apps.vehicles.models import Vehicle, VehicleExpense, VehiclePurchase, VehicleSale
    from apps.vehicles.services import get_vehicle_financial_position

    reason = (reason or "").strip()
    body = {"sale_id": str(sale_id), "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        sale = VehicleSale.objects.select_for_update(of=("self",)).filter(
            tenant=company, pk=sale_id,
        ).select_related("branch").first()
        if sale is None:
            raise NotFound("Vehicle Sale not found.")
        Vehicle.objects.select_for_update().get(tenant=company, pk=sale.vehicle_id)
        position = get_vehicle_financial_position(
            actor=locked_actor, company_id=company.pk, vehicle_id=sale.vehicle_id,
        )
        if len(reason) < 3:
            raise ValidationError({"reason": "A recovery confirmation reason is required."})
        if position["source_version"] != expected_source_version:
            raise DomainConflict("Vehicle sources changed; reload before confirming recovery.", code="VEHICLE_RESULT_STALE")
        if position["profit_share_status"] == "AGREEMENT_SNAPSHOT_MISSING":
            raise DomainConflict("Investor agreement requires review.", code="INVESTOR_AGREEMENT_SNAPSHOT_MISSING")
        if Decimal(position["buyer_refund_payable"] or "0") > 0 or sale.refunds.exists():
            raise DomainConflict("Buyer refund reconciliation is required.", code="RECOVERY_REFUND_REVIEW_REQUIRED")
        purchase = VehiclePurchase.objects.filter(tenant=company, vehicle_id=sale.vehicle_id).first()
        if purchase is None:
            raise DomainConflict("A Vehicle Purchase is required.", code="VEHICLE_RESULT_SOURCES_INCOMPLETE")
        investor_amount = Decimal(position["investor_fund_cost"])
        company_amount = Decimal(position["running_capital_cost"])
        if investor_amount and company_amount and Decimal(position["buyer_receivable"] or "0") > 0:
            raise DomainConflict("Mixed-funded recovery requires full collection.", code="RECOVERY_FULL_COLLECTION_REQUIRED")
        if Decimal(position["calculated_result"] or "0") < 0:
            raise DomainConflict("A Vehicle Loss requires Accountant review.", code="RECOVERY_LOSS_REVIEW_REQUIRED")
        investor = None
        if investor_amount:
            investor = Investor.objects.select_for_update().filter(tenant=company, pk=purchase.investor_id).first()
            if investor is None:
                raise DomainConflict("Investor funding requires agreement review.", code="INVESTOR_AGREEMENT_SNAPSHOT_MISSING")
        funding_snapshot = {
            "purchase_id": position["purchase_id"], "investor_id": position["investor_id"],
            "investor_fund_cost": position["investor_fund_cost"], "running_capital_cost": position["running_capital_cost"],
            "purchase_version": position["purchase_correction_version"],
            "expense_versions": sorted(position["expense_correction_versions"], key=lambda row: row["expense_id"]),
            "sale_version": position["sale_correction_version"], "sale_price": position["sale_price"],
        }
        funding_version = hashlib.sha256(json.dumps(funding_snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        prior = VehicleCapitalRecovery.objects.filter(tenant=company, sale=sale)
        if prior.exclude(funding_version=funding_version).exists():
            from apps.investment.models import VehicleCapitalRecoveryReview
            first = prior.order_by("created_at", "id").first()
            totals = prior.aggregate(investor=Sum("investor_principal"), running=Sum("running_capital"))
            confirmed = position.get("confirmed_result") or {}
            expenses = VehicleExpense.objects.filter(tenant=company, vehicle_id=sale.vehicle_id)
            funding_changed = purchase.corrections.filter(created_at__gt=first.created_at).exists() or expenses.filter(
                Q(created_at__gt=first.created_at) | Q(corrections__created_at__gt=first.created_at),
            ).exists()
            if (
                funding_changed or not confirmed.get("is_current")
                or confirmed.get("result_kind") not in ("PROFIT", "BREAK_EVEN")
                or Decimal(position["buyer_receivable"] or "0") != 0
                or (totals["investor"] or Decimal("0")) != investor_amount
                or (totals["running"] or Decimal("0")) != company_amount
            ):
                raise DomainConflict("Corrected capital sources require reconciliation.", code="RECOVERY_CORRECTION_REVIEW_REQUIRED")
            review, created = VehicleCapitalRecoveryReview.objects.get_or_create(
                tenant=company, recovery=first, source_version=expected_source_version,
                defaults={"result_confirmation_id": confirmed["id"],
                          "sale_correction_version": position["sale_correction_version"],
                          "reason": reason, "actor": locked_actor},
            )
            if created:
                record_event(action="investment.capital.recovery.confirm", actor=locked_actor, subject=locked_actor,
                             company=company, branch=sale.branch, resource=review, reason=reason,
                             metadata={"sale_id": str(sale.pk), "recovery_id": str(first.pk),
                                       "source_version": expected_source_version, "cash_movement_created": False})
            return DomainMutationResult(201 if created else 200, {
                "id": str(review.pk), "review_only": True,
                "investor_principal": format(totals["investor"] or Decimal("0"), ".2f"),
                "running_capital": format(totals["running"] or Decimal("0"), ".2f"),
            })
        totals = prior.aggregate(investor=Sum("investor_principal"), running=Sum("running_capital"))
        with localcontext() as context:
            context.prec = 80
            collected = Decimal(position["actual_net_collection"])
            prior_investor = totals["investor"] or Decimal("0.00")
            prior_company = totals["running"] or Decimal("0.00")
            if prior_investor > investor_amount or prior_company > company_amount or prior_investor + prior_company > collected:
                raise DomainConflict("Existing recoveries exceed current sources.", code="RECOVERY_CORRECTION_REVIEW_REQUIRED")
            available_collection = collected - prior_investor - prior_company
            investor_recovery = min(available_collection, investor_amount - prior_investor)
            company_recovery = min(available_collection - investor_recovery, company_amount - prior_company)
        if investor_recovery + company_recovery <= 0:
            raise DomainConflict("No collected capital is available to recover.", code="RECOVERY_NOT_AVAILABLE")

        receipt_totals = {
            row["receipt_id"]: row for row in VehicleCapitalRecoveryReceiptAllocation.objects.filter(
                tenant=company, receipt__sale=sale,
            ).values("receipt_id").annotate(investor=Sum("investor_principal"), running=Sum("running_capital"))
        }
        receipt_parts = []
        credit_parts = []
        with localcontext() as context:
            context.prec = 80
            investor_left, company_left = investor_recovery, company_recovery
            receipts = sale.receipts.select_for_update().order_by("effective_at", "id")
            for receipt in receipts:
                already = receipt_totals.get(receipt.pk, {})
                available = receipt.amount - (already.get("investor") or Decimal("0")) - (already.get("running") or Decimal("0"))
                if available < 0:
                    raise DomainConflict("Receipt allocations exceed the source.", code="RECOVERY_SOURCE_CHANGED")
                investor_part = min(available, investor_left)
                available -= investor_part
                company_part = min(available, company_left)
                investor_left -= investor_part
                company_left -= company_part
                if investor_part or company_part:
                    receipt_parts.append((receipt, investor_part, company_part))
            if investor_left or company_left:
                raise DomainConflict("Receipt allocations changed; reload.", code="RECOVERY_SOURCE_CHANGED")

            remaining = investor_recovery
            if investor is not None:
                vehicle_source = Q(fund_use__purchase__vehicle_id=sale.vehicle_id) | Q(fund_use__expense__vehicle_id=sale.vehicle_id)
                usage = {row["credit_id"]: row["total"] for row in InvestorFundUseAllocation.objects.filter(
                    vehicle_source, tenant=company,
                ).values("credit_id").annotate(total=Sum("amount"))}
                adjustment_source = Q(purchase_correction__purchase__vehicle_id=sale.vehicle_id) | Q(expense_correction__expense__vehicle_id=sale.vehicle_id)
                adjustments = {row["credit_id"]: row["total"] for row in InvestorFundUseAdjustment.objects.filter(
                    adjustment_source, tenant=company,
                ).values("credit_id").annotate(total=Sum("amount_delta"))}
                recovered_by_credit = {row["credit_id"]: row["total"] for row in VehicleCapitalRecoveryCreditAllocation.objects.filter(
                    tenant=company, recovery__sale=sale,
                ).values("credit_id").annotate(total=Sum("amount"))}
                credits = with_current_fund_credit_owner(
                    InvestorFundCredit.objects.select_for_update().filter(tenant=company)
                ).filter(current_investor_id=investor.pk).order_by("effective_at", "id")
                for credit in credits:
                    source_usage = (usage.get(credit.pk) or Decimal("0")) + (adjustments.get(credit.pk) or Decimal("0"))
                    recovered = recovered_by_credit.get(credit.pk) or Decimal("0")
                    part = min(max(Decimal("0.00"), source_usage - recovered), remaining)
                    if part:
                        credit_parts.append((credit, part))
                        remaining -= part
                    if remaining == 0:
                        break
            if remaining:
                raise DomainConflict("Fund lot provenance requires review.", code="RECOVERY_FUND_LOT_REVIEW_REQUIRED")
        recovery = VehicleCapitalRecovery.objects.create(
            tenant=company, sale=sale, investor=investor, investor_principal=investor_recovery,
            running_capital=company_recovery, source_version=expected_source_version, funding_version=funding_version,
            reason=reason, actor=locked_actor, investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            vehicle_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        for receipt, investor_part, company_part in receipt_parts:
            VehicleCapitalRecoveryReceiptAllocation.objects.create(
                tenant=company, recovery=recovery, receipt=receipt,
                investor_principal=investor_part, running_capital=company_part,
            )
        for credit, amount in credit_parts:
            VehicleCapitalRecoveryCreditAllocation.objects.create(tenant=company, recovery=recovery, credit=credit, amount=amount)
        record_event(action="investment.capital.recovery.confirm", actor=locked_actor, subject=locked_actor,
                     company=company, branch=sale.branch, resource=recovery, reason=reason,
                     metadata={"sale_id": str(sale.pk), "investor_principal": format(investor_recovery, ".2f"),
                               "running_capital": format(company_recovery, ".2f")})
        return DomainMutationResult(201, {"id": str(recovery.pk), "investor_principal": format(investor_recovery, ".2f"),
                                          "running_capital": format(company_recovery, ".2f")})

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.capital.recovery.confirm",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def create_vehicle_profit_payment(
    *, actor, company_id, result_confirmation_id, account_id, amount,
    effective_at=None, description="", key, path,
):
    from apps.vehicles.models import Vehicle
    from apps.vehicles.services import get_vehicle_financial_position
    from apps.accounting.services import AccountingConflict
    from django.utils import timezone

    preview = VehicleResultConfirmation.objects.select_related(
        "sale", "investor"
    ).filter(tenant_id=company_id, pk=result_confirmation_id).first()
    if preview is None or preview.investor_id is None:
        raise NotFound("Investor Vehicle result not found.")
    requested_amount = Decimal(amount)
    when = effective_at or timezone.now()
    if when > timezone.now():
        raise ValidationError({"effective_at": "An actual Investor Profit payment cannot be future-dated."})
    note = (description or "").strip() or f"Investor Vehicle Profit payment for Vehicle {preview.vehicle_id}"
    body = {
        "result_confirmation_id": str(result_confirmation_id),
        "account_id": str(account_id),
        "amount": format(requested_amount, ".2f"),
        "effective_at": effective_at.isoformat() if effective_at else None,
        "description": note,
    }

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=preview.investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        _assert_investor_offsets_current(
            actor=locked_actor, company=company, investor=investor,
        )
        vehicle = Vehicle.objects.select_for_update().filter(
            tenant=company, pk=preview.vehicle_id,
        ).first()
        if vehicle is None:
            raise NotFound("Vehicle not found.")
        result = VehicleResultConfirmation.objects.select_for_update(
            of=("self",)
        ).filter(tenant=company, pk=result_confirmation_id, vehicle=vehicle).first()
        latest = VehicleResultConfirmation.objects.filter(
            tenant=company, vehicle=vehicle,
        ).order_by("-version", "-id").first()
        if result is None or latest is None or latest.pk != result.pk:
            raise DomainConflict(
                "A newer Vehicle result exists; reload before recording a payment.",
                code="VEHICLE_RESULT_STALE",
            )
        position = get_vehicle_financial_position(
            actor=locked_actor, company_id=company.pk, vehicle_id=vehicle.pk,
        )
        current_result = position.get("confirmed_result") or {}
        if (
            result.result_kind != VehicleResultConfirmation.ResultKind.PROFIT
            or result.investor_id is None
            or result.source_version != position.get("source_version")
            or str(current_result.get("id")) != str(result.pk)
            or not current_result.get("is_current")
        ):
            raise DomainConflict(
                "Only the current verified positive Investor result can be paid.",
                code="VEHICLE_RESULT_NOT_CURRENT_PROFIT",
            )

        paid_total = InvestorVehicleProfitPayment.objects.select_for_update().filter(
            tenant=company,
            result_confirmation__sale_id=result.sale_id,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        offset_total = InvestorProfitLossOffset.objects.filter(
            tenant=company,
            investor=investor,
            profit_result=result,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        from apps.investment.models import InvestorProfitFutureAdjustment
        future_adjusted = InvestorProfitFutureAdjustment.objects.filter(
            tenant=company, profit_result__sale_id=result.sale_id,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        remaining = Decimal(result.investor_share_amount) - paid_total - offset_total - future_adjusted
        if requested_amount <= 0:
            raise ValidationError({"amount": "Payment amount must be greater than zero."})
        if requested_amount > remaining:
            raise AccountingConflict(
                "Payment exceeds the unpaid Investor share for this Vehicle Sale.",
                code="INVESTOR_PROFIT_PAYMENT_EXCEEDS_BALANCE",
            )
        recovery = position.get("capital_recovery") or {}
        if (
            Decimal(position["buyer_receivable"] or "0") != 0
            or Decimal(position["buyer_refund_payable"] or "0") != 0
            or not recovery.get("is_complete")
        ):
            raise DomainConflict(
                "Confirm the current source-linked Investor principal and Company Running Capital recovery, "
                "then resolve Buyer balances before Profit payment.",
                code="VEHICLE_CAPITAL_RECOVERY_REQUIRED",
            )
        from apps.investment.fund_position import FundPositionReviewRequired, investor_fund_position
        try:
            investor_fund_position(company=company, investor=investor)
        except FundPositionReviewRequired as exc:
            raise DomainConflict(str(exc), code="RECOVERY_REFUND_REVIEW_REQUIRED") from exc
        branch = result.sale.branch
        account = AccountingAccount.objects.filter(
            tenant=company, pk=account_id, is_active=True,
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        payment = InvestorVehicleProfitPayment(
            tenant=company,
            result_confirmation=result,
            investor=result.investor,
            branch=branch,
            account=account,
            amount=requested_amount,
            effective_at=when,
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            description=note,
            source_reference="",
        )
        payment.source_reference = f"INVESTOR-PROFIT-PAYMENT-{payment.pk}"
        payment.save()
        event, movement, accounting_data = record_investor_vehicle_profit_payment(
            tenant=company,
            payment=payment,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(
            action="investment.profit.payment.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=payment,
            reason=note,
            metadata={
                "payment_id": str(payment.pk),
                "result_id": str(result.pk),
                "investor_id": str(result.investor_id),
                "vehicle_id": str(vehicle.pk),
                "sale_id": str(result.sale_id),
                "account_id": str(account.pk),
                "branch_id": str(branch.pk),
                "amount": format(requested_amount, ".2f"),
                "accounting_event_id": str(event.pk),
            },
        )
        return DomainMutationResult(201, {
            "payment_id": str(payment.pk),
            "result_confirmation_id": str(result.pk),
            "investor_id": str(result.investor_id),
            "vehicle_id": str(vehicle.pk),
            "sale_id": str(result.sale_id),
            "branch_id": str(branch.pk),
            "account_id": str(account.pk),
            "amount": format(requested_amount, ".2f"),
            "paid_total": format(paid_total + requested_amount, ".2f"),
            "loss_offset_total": format(offset_total, ".2f"),
            "remaining_share": format(remaining - requested_amount, ".2f"),
            "effective_at": payment.effective_at.isoformat(),
            "accounting_event_id": str(event.pk),
            "movement_id": str(movement.pk),
            "accounting_event": accounting_data,
        })

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.profit.payment.create",
        module_codes=(
            CompanyModuleCode.VEHICLE_MANAGEMENT,
            CompanyModuleCode.INVESTMENT,
            CompanyModuleCode.ACCOUNTING,
        ),
        idempotency_model=InvestmentIdempotencyRecord,
        branch_id=preview.sale.branch_id,
        operation=operation,
    )


def _assert_investor_offsets_current(*, actor, company, investor):
    """Block new offsets/payouts while an affected confirmed result is stale."""
    from apps.vehicles.services import get_vehicle_financial_position

    offsets = list(
        InvestorProfitLossOffset.objects.filter(
            tenant=company, investor=investor,
        ).select_related("loss_result", "profit_result")
    )
    from apps.investment.models import InvestorExitLossApplication
    exit_loss_results = list(
        VehicleResultConfirmation.objects.filter(
            tenant=company,
            pk__in=InvestorExitLossApplication.objects.filter(
                tenant=company, exit_request__investor=investor,
            ).values("loss_result_id"),
        ).select_related("sale")
    )
    result_by_id = {}
    for offset in offsets:
        result_by_id[offset.loss_result_id] = offset.loss_result
        result_by_id[offset.profit_result_id] = offset.profit_result
    for result in exit_loss_results:
        result_by_id[result.pk] = result

    current_by_vehicle = {}
    for result in result_by_id.values():
        if result.vehicle_id not in current_by_vehicle:
            try:
                current_by_vehicle[result.vehicle_id] = get_vehicle_financial_position(
                    actor=actor,
                    company_id=company.pk,
                    vehicle_id=result.vehicle_id,
                    authorized_investor_id=investor.pk,
                ).get("confirmed_result")
            except NotFound:
                current_by_vehicle[result.vehicle_id] = None
        current = current_by_vehicle[result.vehicle_id]
        if not current or current.get("id") != str(result.pk) or not current.get("is_current"):
            raise DomainConflict(
                "An earlier Investor Loss/Profit offset needs review after a Vehicle correction.",
                code="INVESTOR_PROFIT_OFFSET_REVIEW_REQUIRED",
            )


def list_profit_loss_offset_targets(*, actor, company_id, loss_result_id):
    """List only authorized, current unpaid Profit results available for a Loss offset."""
    from apps.vehicles.services import get_vehicle_financial_position

    loss = VehicleResultConfirmation.objects.select_related(
        "sale", "vehicle", "investor",
    ).filter(tenant_id=company_id, pk=loss_result_id).first()
    if loss is None or loss.investor_id is None:
        raise NotFound("Investor Vehicle result not found.")
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.profit.loss_offset.read",
        branch_id=loss.sale.branch_id,
    )
    if (
        loss.result_kind != VehicleResultConfirmation.ResultKind.LOSS
        or Decimal(loss.investor_share_amount) >= 0
    ):
        raise ValidationError({"loss_result_id": "Choose a confirmed Investor Loss result."})

    loss_position = get_vehicle_financial_position(
        actor=actor,
        company_id=company.pk,
        vehicle_id=loss.vehicle_id,
        authorized_investor_id=loss.investor_id,
    )
    current_loss = loss_position.get("confirmed_result") or {}
    if current_loss.get("id") != str(loss.pk) or not current_loss.get("is_current"):
        raise DomainConflict(
            "The confirmed Loss no longer matches current Vehicle records.",
            code="VEHICLE_RESULT_STALE",
        )
    _assert_investor_offsets_current(
        actor=actor, company=company, investor=loss.investor,
    )

    loss_offset_total = InvestorProfitLossOffset.objects.filter(
        tenant=company, investor=loss.investor, loss_result=loss,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    exit_loss_total = InvestorExitLossApplication.objects.filter(
        tenant=company, loss_result=loss,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    loss_remaining = max(
        Decimal("0.00"), abs(Decimal(loss.investor_share_amount)) - loss_offset_total - exit_loss_total,
    )
    target_options = []
    if loss_remaining > 0:
        candidates = VehicleResultConfirmation.objects.filter(
            tenant=company,
            investor=loss.investor,
        ).select_related("sale", "vehicle").order_by("vehicle_id", "-version", "-id")
        seen_vehicle_ids = set()
        allowed_branch_ids = scope.allowed_branch_ids
        for candidate in candidates.iterator(chunk_size=100):
            if candidate.vehicle_id in seen_vehicle_ids:
                continue
            seen_vehicle_ids.add(candidate.vehicle_id)
            if (
                candidate.result_kind != VehicleResultConfirmation.ResultKind.PROFIT
                or Decimal(candidate.investor_share_amount) <= 0
            ):
                continue
            if candidate.vehicle_id == loss.vehicle_id:
                continue
            if not scope.is_company_reader and candidate.sale.branch_id not in allowed_branch_ids:
                continue
            try:
                position = get_vehicle_financial_position(
                    actor=actor,
                    company_id=company.pk,
                    vehicle_id=candidate.vehicle_id,
                    authorized_investor_id=loss.investor_id,
                )
            except NotFound:
                continue
            confirmed = position.get("confirmed_result") or {}
            sale_date = position.get("sale_effective_date")
            if (
                confirmed.get("id") != str(candidate.pk)
                or not confirmed.get("is_current")
                or confirmed.get("result_kind") != VehicleResultConfirmation.ResultKind.PROFIT
                or not sale_date
            ):
                continue
            remaining = Decimal(confirmed.get("investor_profit_remaining", "0.00"))
            if remaining <= 0:
                continue
            target_options.append({
                "result_id": str(candidate.pk),
                "vehicle_id": str(candidate.vehicle_id),
                "registration": candidate.vehicle.registration,
                "model": candidate.vehicle.model,
                "sale_branch_id": str(candidate.sale.branch_id),
                "sale_date": sale_date,
                "investor_share_amount": format(
                    Decimal(candidate.investor_share_amount), ".2f",
                ),
                "remaining_amount": format(remaining, ".2f"),
            })

    target_options.sort(key=lambda row: (row["sale_date"], row["registration"], row["result_id"]))
    return {
        "loss_result_id": str(loss.pk),
        "loss_remaining_amount": format(loss_remaining, ".2f"),
        "target_options": target_options,
    }


def create_profit_loss_offset(
    *, actor, company_id, loss_result_id, profit_result_id, amount, reason, key, path,
):
    """Apply an explicitly approved Investor loss against unpaid Vehicle Profit."""
    from apps.vehicles.models import Vehicle
    from apps.vehicles.services import get_vehicle_financial_position

    loss_preview = VehicleResultConfirmation.objects.select_related(
        "sale", "investor",
    ).filter(tenant_id=company_id, pk=loss_result_id).first()
    profit_preview = VehicleResultConfirmation.objects.select_related(
        "sale", "investor",
    ).filter(tenant_id=company_id, pk=profit_result_id).first()
    if (
        loss_preview is None
        or profit_preview is None
        or loss_preview.investor_id is None
        or loss_preview.investor_id != profit_preview.investor_id
    ):
        raise NotFound("Investor Vehicle result not found.")

    requested_amount = Decimal(amount)
    note = (reason or "").strip()
    body = {
        "loss_result_id": str(loss_result_id),
        "profit_result_id": str(profit_result_id),
        "amount": format(requested_amount, ".2f"),
        "reason": note,
    }
    loss_branch_id = loss_preview.sale.branch_id
    profit_branch_id = profit_preview.sale.branch_id
    cross_branch = loss_branch_id != profit_branch_id
    action = (
        "investment.profit.loss_offset.cross_branch"
        if cross_branch else "investment.profit.loss_offset.create"
    )
    audit_action = (
        "investment.profit.loss_offset.cross"
        if cross_branch else "investment.profit.loss_offset.create"
    )

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=loss_preview.investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")

        vehicle_ids = sorted({loss_preview.vehicle_id, profit_preview.vehicle_id}, key=str)
        locked_vehicles = list(
            Vehicle.objects.select_for_update().filter(
                tenant=company, pk__in=vehicle_ids,
            ).order_by("id")
        )
        if {row.pk for row in locked_vehicles} != set(vehicle_ids):
            raise NotFound("Vehicle not found.")
        results = {
            row.pk: row
            for row in VehicleResultConfirmation.objects.select_for_update(
                of=("self",)
            ).filter(
                tenant=company,
                pk__in=(loss_result_id, profit_result_id),
            ).select_related("sale", "investor").order_by("id")
        }
        loss = results.get(loss_result_id)
        profit = results.get(profit_result_id)
        if loss is None or profit is None:
            raise NotFound("Investor Vehicle result not found.")
        if (
            loss.investor_id != investor.pk
            or profit.investor_id != investor.pk
            or loss.result_kind != VehicleResultConfirmation.ResultKind.LOSS
            or profit.result_kind != VehicleResultConfirmation.ResultKind.PROFIT
            or Decimal(loss.investor_share_amount) >= 0
            or Decimal(profit.investor_share_amount) <= 0
        ):
            raise ValidationError({
                "profit_result_id": "Choose a later confirmed positive result for the same Investor."
            })

        _assert_investor_offsets_current(
            actor=locked_actor, company=company, investor=investor,
        )
        current_positions = {}
        for row in (loss, profit):
            current_positions[row.vehicle_id] = get_vehicle_financial_position(
                actor=locked_actor,
                company_id=company.pk,
                vehicle_id=row.vehicle_id,
                authorized_investor_id=investor.pk,
            )
        loss_position = current_positions[loss.vehicle_id]
        profit_position = current_positions[profit.vehicle_id]
        loss_current = loss_position.get("confirmed_result") or {}
        profit_current = profit_position.get("confirmed_result") or {}
        if (
            loss_current.get("id") != str(loss.pk)
            or not loss_current.get("is_current")
            or loss_position.get("source_version") != loss.source_version
            or profit_current.get("id") != str(profit.pk)
            or not profit_current.get("is_current")
            or profit_position.get("source_version") != profit.source_version
        ):
            raise DomainConflict(
                "Both Vehicle results must still match their current source records.",
                code="VEHICLE_RESULT_STALE",
            )
        loss_sale_date = loss_position.get("sale_effective_date")
        profit_sale_date = profit_position.get("sale_effective_date")
        if not loss_sale_date or not profit_sale_date:
            raise ValidationError({
                "profit_result_id": "Both Vehicle results must have a Sale date."
            })

        loss_offset_total = InvestorProfitLossOffset.objects.filter(
            tenant=company, investor=investor, loss_result=loss,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        exit_loss_total = InvestorExitLossApplication.objects.filter(
            tenant=company, loss_result=loss,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        target_offset_total = InvestorProfitLossOffset.objects.filter(
            tenant=company, investor=investor, profit_result=profit,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        paid_total = InvestorVehicleProfitPayment.objects.filter(
            tenant=company, investor=investor,
            result_confirmation__sale_id=profit.sale_id,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        loss_remaining = abs(Decimal(loss.investor_share_amount)) - loss_offset_total - exit_loss_total
        from apps.investment.models import InvestorProfitFutureAdjustment
        future_adjusted = InvestorProfitFutureAdjustment.objects.filter(
            tenant=company, profit_result__sale_id=profit.sale_id,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        profit_remaining = Decimal(profit.investor_share_amount) - paid_total - target_offset_total - future_adjusted
        if requested_amount <= 0:
            raise ValidationError({"amount": "Offset amount must be greater than zero."})
        if loss_remaining < 0:
            raise DomainConflict(
                "Existing Loss settlements exceed the current confirmed Loss and require review.",
                code="INVESTOR_LOSS_SETTLEMENT_REVIEW_REQUIRED",
            )
        if requested_amount > loss_remaining:
            raise DomainConflict(
                "Offset exceeds the Investor's remaining confirmed Loss.",
                code="INVESTOR_LOSS_OFFSET_EXCEEDS_LOSS",
            )
        if requested_amount > profit_remaining:
            raise DomainConflict(
                "Offset exceeds the unpaid Investor Profit for this Vehicle Sale.",
                code="INVESTOR_LOSS_OFFSET_EXCEEDS_PROFIT",
            )

        offset = InvestorProfitLossOffset.objects.create(
            tenant=company,
            loss_result=loss,
            profit_result=profit,
            investor=investor,
            branch=profit.sale.branch,
            amount=requested_amount,
            effective_at=timezone.now(),
            actor=locked_actor,
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            reason=note,
        )
        record_event(
            action=audit_action,
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=profit.sale.branch,
            resource=offset,
            reason=note,
            metadata={
                "offset_id": str(offset.pk),
                "investor_id": str(investor.pk),
                "loss_result_id": str(loss.pk),
                "profit_result_id": str(profit.pk),
                "loss_vehicle_id": str(loss.vehicle_id),
                "profit_vehicle_id": str(profit.vehicle_id),
                "loss_branch_id": str(loss.sale.branch_id),
                "profit_branch_id": str(profit.sale.branch_id),
                "amount": format(requested_amount, ".2f"),
                "cash_movement_created": False,
            },
        )
        return DomainMutationResult(201, {
            "offset_id": str(offset.pk),
            "investor_id": str(investor.pk),
            "loss_result_id": str(loss.pk),
            "profit_result_id": str(profit.pk),
            "branch_id": str(profit.sale.branch_id),
            "amount": format(requested_amount, ".2f"),
            "loss_remaining": format(loss_remaining - requested_amount, ".2f"),
            "profit_remaining": format(profit_remaining - requested_amount, ".2f"),
            "cash_movement_created": False,
        })

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action=action,
        module_codes=(
            CompanyModuleCode.VEHICLE_MANAGEMENT,
            CompanyModuleCode.INVESTMENT,
        ),
        idempotency_model=InvestmentIdempotencyRecord,
        branch_id=profit_branch_id,
        operation=operation,
    )


def _date_value(value):
    if value is None:
        value = timezone.now()
    if timezone.is_naive(value):
        raise ValidationError({"effective_at": "An aware timestamp is required."})
    if value > timezone.now():
        raise ValidationError(
            {"effective_at": "An actual Fund cash movement cannot be future-dated."}
        )
    return value


def _investor_data(investor):
    return {
        "id": str(investor.pk),
        "company_id": str(investor.tenant_id),
        "name": investor.name,
        "is_active": investor.is_active,
        "created_at": investor.created_at.isoformat(),
        "updated_at": investor.updated_at.isoformat(),
    }


def _profit_share_agreement_data(row):
    return {
        "id": str(row.pk),
        "company_id": str(row.tenant_id),
        "investor_id": str(row.investor_id),
        "share_percentage": format(row.share_percentage, ".4f"),
        "effective_at": row.effective_at.isoformat(),
        "recorded_at": row.created_at.isoformat(),
        "actor_id": str(row.actor_id),
    }


def list_profit_share_agreements(*, actor, company_id, investor_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    investor = Investor.objects.filter(tenant=company, pk=investor_id).first()
    if investor is None:
        raise NotFound("Investor not found.")
    require_action(
        actor, "investor.agreement.configure", company=company, resource=investor
    )
    rows = InvestorProfitShareAgreement.objects.filter(
        tenant=company, investor=investor
    ).order_by("effective_at", "id")
    return [_profit_share_agreement_data(row) for row in rows]


def create_profit_share_agreement(
    *, actor, company_id, investor_id, share_percentage, effective_at, key, path
):
    share_percentage = Decimal(share_percentage)
    if timezone.is_naive(effective_at):
        raise ValidationError({"effective_at": "An aware timestamp is required."})
    if not Decimal("0.0000") <= share_percentage <= Decimal("100.0000"):
        raise ValidationError({"share_percentage": "Share must be between 0 and 100 percent."})
    body = {
        "investor_id": str(investor_id),
        "share_percentage": format(share_percentage, ".4f"),
        "effective_at": effective_at.isoformat(),
    }

    def operation(company, _branch, _revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        if InvestorProfitShareAgreement.objects.filter(
            tenant=company, investor=investor, effective_at=effective_at
        ).exists():
            raise DomainConflict(
                "An agreement already exists for this effective time.",
                code="AGREEMENT_EFFECTIVE_TIME_EXISTS",
            )
        row = InvestorProfitShareAgreement.objects.create(
            tenant=company, investor=investor,
            share_percentage=share_percentage, effective_at=effective_at,
            actor=locked_actor,
        )
        record_event(
            action="investor.agreement.configure", actor=locked_actor,
            subject=locked_actor, company=company, resource=row,
            metadata={
                "investor_share_agreement_id": str(row.pk),
                "investor_id": str(investor.pk),
                "investor_share_percentage_snapshot": format(share_percentage, ".4f"),
                "effective_from": effective_at.isoformat(),
            },
        )
        return DomainMutationResult(201, _profit_share_agreement_data(row))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investor.agreement.configure", module_codes=(),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def _credit_data(credit):
    link = AccountingSourceLink.objects.filter(investor_fund_credit=credit).select_related("event").first()
    corrections = list(credit.attribution_corrections.all())
    corrections.sort(key=lambda row: (row.version, str(row.pk)))
    current_investor_id = corrections[-1].to_investor_id if corrections else credit.investor_id
    manual_review_required = getattr(credit, "has_fund_use", None)
    if manual_review_required is None:
        manual_review_required = InvestorFundUseAllocation.objects.filter(
            tenant_id=credit.tenant_id, credit=credit
        ).exists()
    has_principal_return = getattr(credit, "has_principal_return", None)
    if has_principal_return is None:
        has_principal_return = InvestorPrincipalReturnAllocation.objects.filter(
            tenant_id=credit.tenant_id, credit=credit
        ).exists()
    return {
        "id": str(credit.pk),
        "investor_id": str(current_investor_id),
        "original_investor_id": str(credit.investor_id),
        "branch_id": str(credit.branch_id),
        "amount": format(credit.amount, ".2f"),
        "reference": credit.reference,
        "effective_at": credit.effective_at.isoformat(),
        "recorded_at": credit.created_at.isoformat(),
        "accounting_event_id": str(link.event_id) if link else None,
        "correction_version": corrections[-1].version if corrections else 0,
        "manual_review_required": bool(
            corrections and (manual_review_required or has_principal_return)
        ),
        "attribution_corrections": [
            {
                "id": str(row.pk),
                "from_investor_id": str(row.from_investor_id),
                "to_investor_id": str(row.to_investor_id),
                "amount": format(row.amount, ".2f"),
                "effective_at": row.effective_at.isoformat(),
                "recorded_at": row.created_at.isoformat(),
                "reason": row.reason,
            }
            for row in corrections
        ],
    }


def _return_data(principal_return):
    link = AccountingSourceLink.objects.filter(
        investor_principal_return=principal_return
    ).select_related("event").first()
    return {
        "id": str(principal_return.pk),
        "investor_id": str(principal_return.investor_id),
        "branch_id": str(principal_return.branch_id),
        "amount": format(principal_return.amount, ".2f"),
        "reference": principal_return.reference,
        "effective_at": principal_return.effective_at.isoformat(),
        "recorded_at": principal_return.created_at.isoformat(),
        "accounting_event_id": str(link.event_id) if link else None,
        "allocations": [
            {
                "credit_id": str(row.credit_id),
                "amount": format(row.amount, ".2f"),
            }
            for row in principal_return.allocations.select_related("credit").order_by("credit__effective_at", "credit_id")
        ],
    }


def _available_credit(credit):
    if not hasattr(credit, "fund_available"):
        raise RuntimeError("Fund credit availability must be selected under the transaction lock.")
    if credit.fund_available is None:
        raise DomainConflict("Fund recovery sources require review.", code="FUND_RECOVERY_REVIEW_REQUIRED")
    return credit.fund_available


def assert_investor_accepts_new_funding(*, company, investor):
    """Caller must hold the Investor row lock through the enclosing transaction."""
    if InvestorExitRequest.objects.filter(
        tenant=company, investor=investor,
        status__in=(InvestorExitRequest.Status.REQUESTED, InvestorExitRequest.Status.CANCELLATION_PENDING),
    ).exists():
        raise DomainConflict(
            "New Fund credit or Vehicle funding is unavailable while Investor Exit is open.",
            code="INVESTOR_EXIT_OPEN",
        )


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


def _filter_branch_records(queryset, *, scope, branch_id, field="branch_id"):
    if branch_id is not None:
        if not scope.is_company_reader and branch_id not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        return queryset.filter(**{field: branch_id})
    if scope.is_company_reader:
        return queryset
    return queryset.filter(**{f"{field}__in": scope.allowed_branch_ids})


def list_investors(*, actor, company_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.profile.read"
    )
    return Investor.objects.filter(tenant=company, is_active=True).order_by("name", "id")


def get_investor(*, actor, company_id, investor_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.profile.read"
    )
    investor = Investor.objects.filter(
        tenant=company, pk=investor_id, is_active=True
    ).first()
    if investor is None:
        raise NotFound("Investor not found.")
    return investor


def create_investor(*, actor, company_id, key, path, name):
    body = {"name": name.strip()}

    def operation(company, _branch, revisions, locked_actor):
        if not body["name"]:
            raise ValidationError({"name": "A name is required."})
        investor = Investor.objects.create(
            tenant=company,
            name=body["name"],
            created_by=locked_actor,
            updated_by=locked_actor,
        )
        record_event(
            action="investor.profile.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=investor,
            metadata={"investor_id": str(investor.pk), "new_name": investor.name},
        )
        return DomainMutationResult(201, _investor_data(investor))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.profile.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def update_investor(*, actor, company_id, investor_id, key, path, values):
    body = {"name": values["name"].strip()}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        old_name = investor.name
        if not body["name"]:
            raise ValidationError({"name": "A name is required."})
        investor.name = body["name"]
        investor.updated_by = locked_actor
        investor.save(update_fields=("name", "updated_by", "updated_at"))
        record_event(
            action="investor.profile.update",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=investor,
            metadata={
                "investor_id": str(investor.pk),
                "old_name": old_name,
                "new_name": investor.name,
            },
        )
        return DomainMutationResult(200, _investor_data(investor))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="PATCH",
        path=path,
        key=key,
        body=body,
        action="investment.profile.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def list_interim_configurations(*, actor, company_id, investor_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.interim.read"
    )
    investor = Investor.objects.filter(tenant=company, pk=investor_id, is_active=True).first()
    if investor is None:
        raise NotFound("Investor not found.")
    return investor.interim_configurations.order_by("effective_date", "id")


def create_interim_configuration(
    *, actor, company_id, investor_id, key, path, amount, effective_date
):
    body = {
        "investor_id": str(investor_id),
        "amount": format(Decimal(amount), ".2f"),
        "effective_date": effective_date.isoformat(),
    }

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        config = InvestorInterimConfiguration.objects.create(
            tenant=company,
            investor=investor,
            amount=Decimal(amount),
            effective_date=effective_date,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(
            action="investor.interim.configure",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=config,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(config.amount, ".2f"),
            },
        )
        return DomainMutationResult(
            201,
            {
                "id": str(config.pk),
                "investor_id": str(investor.pk),
                "amount": format(config.amount, ".2f"),
                "effective_date": config.effective_date.isoformat(),
                "recorded_at": config.created_at.isoformat(),
                "actor_id": str(config.actor_id),
            },
        )

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.interim.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def _interim_payment_data(payment, *, accounting_event_id=None):
    data = {
        "payment_id": str(payment.pk),
        "investor_id": str(payment.investor_id),
        "configuration_id": str(payment.configuration_id),
        "branch_id": str(payment.branch_id),
        "account_id": str(payment.account_id),
        "amount": format(Decimal(payment.amount), ".2f"),
        "period_month": payment.period_month.isoformat(),
        "effective_at": payment.effective_at.isoformat(),
        "recorded_at": payment.created_at.isoformat(),
        "actor_id": str(payment.actor_id),
        "description": payment.description,
    }
    if accounting_event_id:
        data["accounting_event_id"] = str(accounting_event_id)
    return data


def list_interim_payments(
    *, actor, company_id, investor_id, period_month, branch_id=None,
):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.interim.read",
        branch_id=branch_id,
    )
    investor = Investor.objects.filter(
        tenant=company, pk=investor_id, is_active=True,
    ).first()
    if investor is None:
        raise NotFound("Investor not found.")
    queryset = InvestorInterimPayment.objects.filter(
        tenant=company, investor=investor, period_month=period_month,
    ).select_related("branch", "account")
    queryset = _filter_branch_records(queryset, scope=scope, branch_id=branch_id)
    return queryset.order_by("effective_at", "id")


def create_interim_payment(
    *, actor, company_id, investor_id, branch_id, account_id, amount,
    effective_at, key, path,
):
    when = _date_value(effective_at)
    requested_amount = Decimal(amount)
    period_month = timezone.localtime(when).date().replace(day=1)
    body = {
        "investor_id": str(investor_id),
        "branch_id": str(branch_id),
        "account_id": str(account_id),
        "amount": format(requested_amount, ".2f"),
        "effective_at": when.isoformat(),
        "period_month": period_month.isoformat(),
    }

    def operation(company, branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        configuration = InvestorInterimConfiguration.objects.filter(
            tenant=company,
            investor=investor,
            effective_date__lte=period_month,
        ).order_by("-effective_date", "-id").first()
        if configuration is None or configuration.amount <= 0:
            raise DomainConflict(
                "No positive Monthly Interim amount is configured for this payment month.",
                code="INTERIM_NOT_CONFIGURED",
            )
        already_paid = InvestorInterimPayment.objects.filter(
            tenant=company, investor=investor, period_month=period_month,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        remaining = Decimal(configuration.amount) - already_paid
        if requested_amount <= 0:
            raise ValidationError({"amount": "Payment amount must be greater than zero."})
        if requested_amount > remaining:
            raise DomainConflict(
                "This payment would exceed the configured Monthly Interim amount for the month.",
                code="INTERIM_MONTHLY_LIMIT_EXCEEDED",
            )
        account = AccountingAccount.objects.filter(
            tenant=company, pk=account_id, is_active=True,
        ).first()
        if account is None:
            raise NotFound("Cash/Bank account not found.")
        description = f"Monthly Interim payment for {period_month:%Y-%m}"
        payment = InvestorInterimPayment(
            tenant=company,
            investor=investor,
            configuration=configuration,
            branch=branch,
            account=account,
            amount=requested_amount,
            period_month=period_month,
            effective_at=when,
            actor=locked_actor,
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
            description=description,
            source_reference="",
        )
        payment.source_reference = f"INVESTOR-INTERIM-PAYMENT-{payment.pk}"
        payment.save()
        event, _movement, _event_data = record_investor_interim_payment(
            tenant=company,
            payment=payment,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(
            action="investment.interim.payment.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=payment,
            reason=description,
            metadata={
                "payment_id": str(payment.pk),
                "investor_id": str(investor.pk),
                "configuration_id": str(configuration.pk),
                "branch_id": str(branch.pk),
                "account_id": str(account.pk),
                "amount": format(requested_amount, ".2f"),
                "period_month": period_month.isoformat(),
                "accounting_event_id": str(event.pk),
                "cash_movement_created": "true",
            },
        )
        return DomainMutationResult(
            201,
            _interim_payment_data(payment, accounting_event_id=event.pk),
        )

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.interim.payment.create",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )


def _profit_calendar_data(row):
    return {
        "id": str(row.pk),
        "investor_id": str(row.investor_id),
        "effective_start": row.effective_start.isoformat(),
        "duration_months": row.duration_months,
        "version": row.version,
        "recorded_at": row.created_at.isoformat(),
        "actor_id": str(row.actor_id),
    }


def list_profit_calendar_configurations(*, actor, company_id, investor_id):
    company, scope, _ = read_scope(
        actor=actor, company_id=company_id,
        action="investment.profit.calendar.read",
    )
    investor = Investor.objects.filter(
        tenant=company, pk=investor_id, is_active=True,
    ).first()
    if investor is None:
        raise NotFound("Investor not found.")
    return [
        _profit_calendar_data(row)
        for row in InvestorProfitCalendarConfiguration.objects.filter(
            tenant=company, investor=investor,
        ).order_by("effective_start", "version", "id")
    ]


def list_investor_profit_period_projection(*, actor, company_id, investor_id):
    """Return a Company Accountant-only calculation projection, never a payable."""
    from apps.investment.finance import exact_money_difference, summarize_investor_profit_periods
    from apps.vehicles.models import VehiclePurchase
    from apps.vehicles.services import get_vehicle_financial_position

    company, _scope, _branch = read_scope(
        actor=actor, company_id=company_id,
        action="investment.profit.calendar.read",
    )
    investor = Investor.objects.filter(
        tenant=company, pk=investor_id, is_active=True,
    ).first()
    if investor is None:
        raise NotFound("Investor not found.")

    credit_rows = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    ).filter(current_investor_id=investor.pk)
    first_credit_at = credit_rows.order_by("effective_at", "id").values_list(
        "effective_at", flat=True
    ).first()
    configured = list(InvestorProfitCalendarConfiguration.objects.filter(
        tenant=company, investor=investor,
    ).order_by("effective_start", "version", "id"))
    if configured:
        calendar_versions = [
            {"effective_start": row.effective_start.isoformat(),
             "duration_months": row.duration_months, "version": row.version}
            for row in configured
        ]
        active = [row for row in configured if row.effective_start <= timezone.localdate(timezone=INVESTOR_PROFIT_TIME_ZONE)]
        calendar = {
            "status": "CONFIGURED" if active else "SCHEDULED",
            "start_date": active[-1].effective_start.isoformat() if active else configured[0].effective_start.isoformat(),
            "duration_months": active[-1].duration_months if active else configured[0].duration_months,
            "versions": [_profit_calendar_data(row) for row in configured],
        }
    elif first_credit_at:
        first_credit_date = timezone.localdate(first_credit_at, INVESTOR_PROFIT_TIME_ZONE)
        calendar_versions = [{
            "effective_start": first_credit_date.isoformat(),
            "duration_months": 6,
            "version": 1,
        }]
        calendar = {
            "status": "DEFAULT_FROM_FIRST_FUND_CREDIT",
            "start_date": first_credit_date.isoformat(),
            "duration_months": 6,
            "versions": [],
        }
    else:
        calendar_versions = []
        calendar = {
            "status": "NOT_AVAILABLE", "start_date": None,
            "duration_months": None, "versions": [],
        }

    vehicle_results = []
    purchases = VehiclePurchase.objects.filter(
        tenant=company, investor=investor, investor_fund_amount__gt=0,
    ).select_related("vehicle").order_by("purchased_at", "id")
    for purchase in purchases.iterator(chunk_size=100):
        position = get_vehicle_financial_position(
            actor=actor, company_id=company.pk, vehicle_id=purchase.vehicle_id,
        )
        sale_date = position["sale_effective_date"]
        confirmed = position["confirmed_result"]
        if not sale_date:
            continue
        if not confirmed:
            vehicle_results.append({
                "id": None, "vehicle_id": str(purchase.vehicle_id),
                "effective_sale_date": sale_date, "status": "NOT_CONFIRMED",
            })
            continue
        vehicle_results.append({
            "id": confirmed["id"], "vehicle_id": str(purchase.vehicle_id),
            "source_version": confirmed["source_version"],
            "sale_id": position["sale_id"],
            "investor_id": str(investor.pk),
            "effective_sale_date": sale_date,
            "status": "CURRENT" if confirmed["is_current"] else "STALE_REVIEW_REQUIRED",
            "result_kind": confirmed["result_kind"],
            "investor_share_amount": confirmed["investor_share_amount"],
            "unpaid_profit": confirmed["investor_profit_remaining"],
            "vehicle_label": purchase.vehicle.registration,
        })

    current_results_by_sale = {
        row["sale_id"]: row for row in vehicle_results
        if row.get("sale_id") and row.get("id")
    }
    deal_profit_payments = []
    for payment in InvestorVehicleProfitPayment.objects.filter(
        tenant=company, investor=investor,
    ).select_related("result_confirmation__sale").order_by("effective_at", "id"):
        current = current_results_by_sale.get(str(payment.result_confirmation.sale_id))
        matching_current_profit = bool(
            current
            and current["status"] == "CURRENT"
            and current["result_kind"] == VehicleResultConfirmation.ResultKind.PROFIT
            and current["investor_id"] == str(payment.investor_id)
        )
        deal_profit_payments.append({
            "id": str(payment.pk),
            "vehicle_result_id": current["id"] if matching_current_profit else str(payment.result_confirmation_id),
            "effective_sale_date": current["effective_sale_date"] if matching_current_profit else None,
            "amount": format(payment.amount, ".2f"),
            "effective_at": payment.effective_at.isoformat(),
        })

    loss_offsets = []
    for offset in InvestorProfitLossOffset.objects.filter(
        tenant=company, investor=investor,
    ).select_related(
        "loss_result__sale", "profit_result__sale",
    ).order_by("effective_at", "id"):
        current_loss = current_results_by_sale.get(str(offset.loss_result.sale_id))
        current_profit = current_results_by_sale.get(str(offset.profit_result.sale_id))
        valid_link = bool(
            current_loss and current_profit
            and current_loss["status"] == "CURRENT"
            and current_profit["status"] == "CURRENT"
            and current_loss["result_kind"] == VehicleResultConfirmation.ResultKind.LOSS
            and current_profit["result_kind"] == VehicleResultConfirmation.ResultKind.PROFIT
            and current_loss["id"] == str(offset.loss_result_id)
            and current_profit["id"] == str(offset.profit_result_id)
            and current_loss["investor_id"] == str(investor.pk)
            and current_profit["investor_id"] == str(investor.pk)
        )
        loss_offsets.append({
            "id": str(offset.pk),
            "loss_result_id": str(offset.loss_result_id),
            "profit_result_id": str(offset.profit_result_id),
            "valid_link": valid_link,
            "effective_sale_date": current_profit["effective_sale_date"] if valid_link else None,
            "amount": format(offset.amount, ".2f"),
        })
    interim_payments = [
        {
            "id": str(payment.pk),
            "effective_payment_date": timezone.localdate(payment.effective_at, INVESTOR_PROFIT_TIME_ZONE).isoformat(),
            "amount": format(payment.amount, ".2f"),
            "effective_at": payment.effective_at.isoformat(),
        }
        for payment in InvestorInterimPayment.objects.filter(
            tenant=company, investor=investor,
        ).order_by("effective_at", "id")
    ]

    periods, unassigned_count = summarize_investor_profit_periods(
        vehicle_results, calendar_versions,
        deal_profit_payments=deal_profit_payments,
        interim_payments=interim_payments,
        loss_offsets=loss_offsets,
    )
    if not calendar_versions:
        status = "CALENDAR_NOT_AVAILABLE"
    elif unassigned_count:
        status = "REVIEW_REQUIRED"
    else:
        status = "CALCULATED_NOT_RECONCILED"
    # Deal payments, Interim advances and offsets are verified facts, but this
    # route has no persisted period-reconciliation record. Expose each paid
    # source separately while withholding any provisional period net.
    reconciliations = list(
        InvestorProfitPeriodReconciliation.objects.filter(
            tenant=company, investor=investor,
        ).order_by("period_start", "period_end", "version", "id")
    )
    latest_by_period = {}
    for reconciliation in reconciliations:
        latest_by_period[(reconciliation.period_start, reconciliation.period_end)] = reconciliation
    current_period_keys = set()
    gross_periods = []
    for row in periods:
        period_key = (date.fromisoformat(row["period_start"]), date.fromisoformat(row["period_end"]))
        current_period_keys.add(period_key)
        latest = latest_by_period.get(period_key)
        source_matches = bool(latest and latest.source_version == row["source_version"])
        pending_restatement_adjustment = None
        if latest and not source_matches:
            current_net_position = exact_money_difference(
                row["gross_investor_profit"], row["deal_profit_paid"],
                row["interim_paid"], row["loss_offset_applied"],
            )
            pending_restatement_adjustment = format(
                exact_money_difference(current_net_position, latest.net_position), ".2f",
            )
        gross_periods.append({
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "duration_months": row["duration_months"],
            "gross_investor_profit": row["gross_investor_profit"],
            "investor_loss_share": row["investor_loss_share"],
            "deal_profit_paid": row["deal_profit_paid"],
            "interim_paid": row["interim_paid"],
            "loss_offset_applied": row["loss_offset_applied"],
            "result_count": row["result_count"],
            "status": row["status"],
            "source_version": row["source_version"],
            "paid_status": "NOT_RECONCILED",
            "reconciliation_status": (
                "RECONCILED" if source_matches
                else "RESTATEMENT_REQUIRED" if latest
                else "NOT_RECONCILED"
            ),
            "reconciliation_id": str(latest.pk) if latest else None,
            "reconciliation_version": latest.version if latest else None,
            "last_reconciled_net_position": (
                format(latest.net_position, ".2f") if latest else None
            ),
            "last_restatement_adjustment": (
                format(latest.restatement_adjustment, ".2f") if latest else None
            ),
            "pending_restatement_adjustment": pending_restatement_adjustment,
        })
    for key, latest in latest_by_period.items():
        if key in current_period_keys:
            continue
        gross_periods.append({
            "period_start": latest.period_start.isoformat(),
            "period_end": latest.period_end.isoformat(),
            "duration_months": latest.duration_months,
            "gross_investor_profit": format(latest.gross_investor_profit, ".2f"),
            "investor_loss_share": format(latest.investor_loss_share, ".2f"),
            "deal_profit_paid": format(latest.deal_profit_paid, ".2f"),
            "interim_paid": format(latest.interim_paid, ".2f"),
            "loss_offset_applied": format(latest.loss_offset_applied, ".2f"),
            "result_count": latest.result_count,
            "status": "SOURCE_REVIEW_REQUIRED",
            "source_version": None,
            "paid_status": "NOT_RECONCILED",
            "reconciliation_status": "SOURCE_REVIEW_REQUIRED",
            "reconciliation_id": str(latest.pk),
            "reconciliation_version": latest.version,
            "last_reconciled_net_position": format(latest.net_position, ".2f"),
            "last_restatement_adjustment": format(latest.restatement_adjustment, ".2f"),
            "pending_restatement_adjustment": None,
        })
    gross_periods.sort(key=lambda row: (row["period_start"], row["period_end"]))
    from apps.investment.models import InvestorProfitPeriodPosition, InvestorProfitRecoveryReceipt, InvestorProfitFutureAdjustment, InvestorExitProfitPayment
    from apps.investment.period_positions import position_data
    recovery_received_by_period = {
        (row["position__reconciliation__period_start"].isoformat(), row["position__reconciliation__period_end"].isoformat()): row["total"]
        for row in InvestorProfitRecoveryReceipt.objects.filter(
            tenant=company, position__reconciliation__investor=investor,
        ).values("position__reconciliation__period_start", "position__reconciliation__period_end").annotate(total=Sum("amount"))
    }
    profit_paid_by_period = {}
    for row in InvestorExitProfitPayment.objects.filter(
        tenant=company, exit_request__investor=investor,
    ).values("position__reconciliation__period_start", "position__reconciliation__period_end").annotate(total=Sum("amount")):
        key = (row["position__reconciliation__period_start"].isoformat(), row["position__reconciliation__period_end"].isoformat())
        profit_paid_by_period[key] = profit_paid_by_period.get(key, Decimal("0")) + row["total"]
    future_recovered, future_applied = {}, {}
    from apps.investment.finance import exact_money_difference
    for adjustment in InvestorProfitFutureAdjustment.objects.filter(
        tenant=company, recoverable_position__reconciliation__investor=investor,
    ).select_related("recoverable_position__reconciliation", "profit_position__reconciliation"):
        source = adjustment.recoverable_position.reconciliation
        target = adjustment.profit_position.reconciliation
        source_key = (source.period_start.isoformat(), source.period_end.isoformat())
        target_key = (target.period_start.isoformat(), target.period_end.isoformat())
        future_recovered[source_key] = future_recovered.get(source_key, Decimal("0")) + adjustment.amount
        future_applied[target_key] = future_applied.get(target_key, Decimal("0")) + adjustment.amount
    confirmed_positions = {}
    for confirmed_position in InvestorProfitPeriodPosition.objects.filter(
        tenant=company, reconciliation__investor=investor,
    ).select_related("reconciliation").order_by("reconciliation__version"):
        calculation = confirmed_position.reconciliation
        confirmed_positions[(calculation.period_start.isoformat(), calculation.period_end.isoformat())] = confirmed_position
    for period in gross_periods:
        confirmed_position = confirmed_positions.get((period["period_start"], period["period_end"]))
        period["confirmed_position"] = position_data(
            confirmed_position,
            is_current=bool(not unassigned_count and period["reconciliation_status"] == "RECONCILED"
                            and period["reconciliation_id"] == str(confirmed_position.reconciliation_id)),
            recovery_received=recovery_received_by_period.get((period["period_start"], period["period_end"]), Decimal("0")),
            profit_paid=profit_paid_by_period.get((period["period_start"], period["period_end"]), Decimal("0")),
            future_recovered=future_recovered.get((period["period_start"], period["period_end"]), Decimal("0")),
            future_applied=future_applied.get((period["period_start"], period["period_end"]), Decimal("0")),
        ) if confirmed_position else None
        period["future_profit_targets"] = []
        current_position = period["confirmed_position"]
        if current_position and current_position["is_current"] and current_position["kind"] == "PAYABLE":
            for result in vehicle_results:
                if (
                    result.get("status") == "CURRENT" and result.get("result_kind") == "PROFIT"
                    and period["period_start"] <= result["effective_sale_date"] <= period["period_end"]
                ):
                    available = min(Decimal(current_position["amount"]), Decimal(result["unpaid_profit"]))
                    if available > 0:
                        period["future_profit_targets"].append({
                            "profit_position_id": current_position["id"], "profit_result_id": result["id"],
                            "source_version": current_position["source_version"],
                            "amount": format(available, ".2f"), "label": result["vehicle_label"],
                        })
    projection_status = status
    if calendar_versions and not unassigned_count:
        if any(row["reconciliation_status"] == "SOURCE_REVIEW_REQUIRED" for row in gross_periods):
            projection_status = "REVIEW_REQUIRED"
        elif gross_periods and all(row["reconciliation_status"] == "RECONCILED" for row in gross_periods):
            projection_status = "RECONCILED"
        else:
            projection_status = "CALCULATED_NOT_RECONCILED"
    return {
        "company_id": str(company.pk),
        "investor_id": str(investor.pk),
        "calendar": calendar,
        "status": projection_status,
        "periods": gross_periods,
        "unassigned_result_count": unassigned_count,
        "settlement_status": "NOT_IMPLEMENTED",
        "notice": "Reconciliation stores a calculation snapshot. A separately confirmed position identifies payable or recoverable. Actual payments, repayments and final Exit settlement remain separate workflows.",
    }


def _profit_period_reconciliation_data(row):
    return {
        "id": str(row.pk),
        "investor_id": str(row.investor_id),
        "period_start": row.period_start.isoformat(),
        "period_end": row.period_end.isoformat(),
        "duration_months": row.duration_months,
        "result_count": row.result_count,
        "version": row.version,
        "source_version": row.source_version,
        "gross_investor_profit": format(row.gross_investor_profit, ".2f"),
        "investor_loss_share": format(row.investor_loss_share, ".2f"),
        "deal_profit_paid": format(row.deal_profit_paid, ".2f"),
        "interim_paid": format(row.interim_paid, ".2f"),
        "loss_offset_applied": format(row.loss_offset_applied, ".2f"),
        "net_position": format(row.net_position, ".2f"),
        "restatement_adjustment": format(row.restatement_adjustment, ".2f"),
        "previous_reconciliation_id": (
            str(row.previous_reconciliation_id) if row.previous_reconciliation_id else None
        ),
        "reason": row.reason,
        "confirmed_at": row.confirmed_at.isoformat(),
        "confirmed_by_id": str(row.confirmed_by_id),
    }


def reconcile_investor_profit_period(
    *, actor, company_id, investor_id, period_start, expected_source_version,
    reason, key, path,
):
    from apps.investment.finance import exact_money_difference
    reason = (reason or "").strip()
    body = {
        "investor_id": str(investor_id),
        "period_start": period_start.isoformat(),
        "expected_source_version": expected_source_version,
        "reason": reason,
    }

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")

        projection = list_investor_profit_period_projection(
            actor=locked_actor, company_id=company.pk, investor_id=investor.pk,
        )
        if projection["unassigned_result_count"]:
            raise DomainConflict(
                "Review all unassigned or stale Investor results before confirming a period.",
                code="INVESTOR_PERIOD_SOURCES_REVIEW_REQUIRED",
            )
        period = next((
            row for row in projection["periods"]
            if row["period_start"] == period_start.isoformat()
            and row["source_version"] is not None
            and row["status"] != "SOURCE_REVIEW_REQUIRED"
        ), None)
        if period is None:
            raise DomainConflict(
                "No current calculated Investor period matches this start date.",
                code="INVESTOR_PERIOD_NOT_AVAILABLE",
            )
        if period["source_version"] != expected_source_version:
            raise DomainConflict(
                "Investor period sources changed. Reload before confirming.",
                code="INVESTOR_PERIOD_SOURCE_STALE",
            )

        period_end = date.fromisoformat(period["period_end"])
        latest_same_start = InvestorProfitPeriodReconciliation.objects.filter(
            tenant=company, investor=investor, period_start=period_start,
        ).order_by("-version", "-id").first()
        if latest_same_start and latest_same_start.period_end != period_end:
            raise DomainConflict(
                "The period boundary differs from a saved reconciliation; review the calendar history.",
                code="INVESTOR_PERIOD_BOUNDARY_REVIEW_REQUIRED",
            )
        previous = latest_same_start
        if previous and previous.source_version == expected_source_version:
            return DomainMutationResult(200, _profit_period_reconciliation_data(previous))

        gross = Decimal(period["gross_investor_profit"])
        loss_share = Decimal(period["investor_loss_share"])
        deal_paid = Decimal(period["deal_profit_paid"])
        interim_paid = Decimal(period["interim_paid"])
        loss_offset = Decimal(period["loss_offset_applied"])
        net_position = exact_money_difference(gross, deal_paid, interim_paid, loss_offset)
        adjustment = exact_money_difference(net_position, previous.net_position) if previous else Decimal("0.00")
        # The DB enforces non-future confirmations. Use its clock for this
        # server-generated timestamp so host/DB clock skew cannot reject it.
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT clock_timestamp()")
            confirmed_at = cursor.fetchone()[0]
        reconciliation = InvestorProfitPeriodReconciliation.objects.create(
            tenant=company,
            investor=investor,
            period_start=period_start,
            period_end=period_end,
            duration_months=period["duration_months"],
            result_count=period["result_count"],
            version=(previous.version + 1) if previous else 1,
            source_version=expected_source_version,
            gross_investor_profit=gross,
            investor_loss_share=loss_share,
            deal_profit_paid=deal_paid,
            interim_paid=interim_paid,
            loss_offset_applied=loss_offset,
            net_position=net_position,
            restatement_adjustment=adjustment,
            previous_reconciliation=previous,
            reason=reason,
            confirmed_by=locked_actor,
            confirmed_at=confirmed_at,
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
            vehicle_module_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_module_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(
            action="investment.profit.period.reconcile",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            # The global audit resource-type column is capped at 40 chars;
            # retain the Investor identity there and carry the exact snapshot
            # UUID in allowlisted metadata.
            resource=investor,
            reason=reason,
            metadata={
                "investor_id": str(investor.pk),
                "period_start": period["period_start"],
                "period_end": period["period_end"],
                "reconciliation_id": str(reconciliation.pk),
                "version": reconciliation.version,
                "source_version": reconciliation.source_version,
                "net_position": format(net_position, ".2f"),
                "restatement_adjustment": format(adjustment, ".2f"),
                "cash_movement_created": False,
            },
        )
        return DomainMutationResult(201, _profit_period_reconciliation_data(reconciliation))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.profit.period.reconcile",
        module_codes=(
            CompanyModuleCode.INVESTMENT,
            CompanyModuleCode.VEHICLE_MANAGEMENT,
            CompanyModuleCode.ACCOUNTING,
        ),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def configure_profit_calendar(
    *, actor, company_id, investor_id, effective_start, duration_months, key, path,
):
    effective_start = effective_start
    duration_months = int(duration_months)
    body = {
        "investor_id": str(investor_id),
        "effective_start": effective_start.isoformat(),
        "duration_months": duration_months,
    }

    def operation(company, _branch, revisions, locked_actor):
        from apps.investment.finance import investor_profit_period_for_date

        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        rows = list(
            InvestorProfitCalendarConfiguration.objects.select_for_update().filter(
                tenant=company, investor=investor,
            ).order_by("effective_start", "version", "id")
        )
        if rows:
            versions = [
                {"effective_start": row.effective_start,
                 "duration_months": row.duration_months, "version": row.version}
                for row in rows
            ]
            current_period = investor_profit_period_for_date(
                timezone.localdate(timezone=INVESTOR_PROFIT_TIME_ZONE), versions,
            )
            if current_period is None:
                raise DomainConflict(
                    "The current Investor calendar is not active; review its scheduled start before changing it.",
                    code="PROFIT_CALENDAR_NOT_ACTIVE",
                )
            expected_start = date.fromisoformat(current_period.start)
            if effective_start != expected_start:
                raise DomainConflict(
                    f"A calendar change must begin at the current incomplete period boundary: {current_period.start}.",
                    code="PROFIT_CALENDAR_BOUNDARY_REQUIRED",
                )
            same_boundary = [row for row in rows if row.effective_start == effective_start]
            latest = same_boundary[-1] if same_boundary else None
            if latest and latest.duration_months == duration_months:
                return DomainMutationResult(200, _profit_calendar_data(latest))
            version = (latest.version + 1) if latest else 1
        else:
            version = 1

        row = InvestorProfitCalendarConfiguration.objects.create(
            tenant=company,
            investor=investor,
            effective_start=effective_start,
            duration_months=duration_months,
            version=version,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(
            action="investor.profit_calendar.configure",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=investor,
            metadata={
                "calendar_id": str(row.pk),
                "investor_id": str(investor.pk),
                "effective_start": row.effective_start.isoformat(),
                "duration_months": row.duration_months,
                "version": row.version,
            },
        )
        return DomainMutationResult(201, _profit_calendar_data(row))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.profit.calendar.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def list_fund_credits(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    queryset = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
        .select_related("investor", "branch")
        .annotate(
            has_fund_use=Exists(
                InvestorFundUseAllocation.objects.filter(
                    tenant_id=company.pk, credit_id=OuterRef("pk")
                )
            ),
            has_principal_return=Exists(
                InvestorPrincipalReturnAllocation.objects.filter(
                    tenant_id=company.pk, credit_id=OuterRef("pk")
                )
            ),
        )
        .prefetch_related(
            Prefetch(
                "attribution_corrections",
                queryset=InvestorFundCreditCorrection.objects.select_related(
                    "from_investor", "to_investor"
                ).order_by("version", "id"),
            )
        )
    )
    if investor_id is not None:
        queryset = queryset.filter(current_investor_id=investor_id)
    queryset = _filter_branch_records(queryset, scope=scope, branch_id=branch_id)
    return queryset.order_by("effective_at", "id")


def correct_fund_credit_investor(
    *, actor, company_id, credit_id, to_investor_id, reason, key, path
):
    reason = (reason or "").strip()
    body = {
        "credit_id": str(credit_id),
        "to_investor_id": str(to_investor_id),
        "reason": reason,
    }
    source_branch_id = InvestorFundCredit.objects.filter(
        tenant_id=company_id, pk=credit_id
    ).values_list("branch_id", flat=True).first()
    if source_branch_id is None:
        raise NotFound("Fund Credit not found.")

    def operation(company, branch, revisions, locked_actor):
        credit = InvestorFundCredit.objects.select_for_update().filter(
            tenant=company, pk=credit_id, branch=branch
        ).first()
        if credit is None:
            raise NotFound("Fund Credit not found.")
        prior = credit.attribution_corrections.order_by("-version", "-id").first()
        from_investor_id = prior.to_investor_id if prior else credit.investor_id
        if str(from_investor_id) == str(to_investor_id):
            raise ValidationError({"to_investor_id": "Choose a different Investor."})
        to_investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=to_investor_id, is_active=True
        ).first()
        if to_investor is None:
            raise NotFound("Investor not found.")
        if not reason:
            raise ValidationError({"reason": "A correction reason is required."})
        correction = InvestorFundCreditCorrection.objects.create(
            tenant=company,
            credit=credit,
            version=(prior.version + 1 if prior else 1),
            from_investor_id=from_investor_id,
            to_investor=to_investor,
            amount=credit.amount,
            effective_at=credit.effective_at,
            reason=reason,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(
            action="investment.fund.credit.correct",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=correction,
            reason=reason,
            metadata={
                "credit_id": str(credit.pk),
                "correction_id": str(correction.pk),
                "old_investor_id": str(from_investor_id),
                "new_investor_id": str(to_investor.pk),
                "amount": format(credit.amount, ".2f"),
                "version": correction.version,
            },
        )
        return DomainMutationResult(201, _credit_data(credit))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.credit.correct",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=source_branch_id,
    )


def fund_summary(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    credits = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    )
    returns = InvestorPrincipalReturn.objects.filter(tenant=company)
    if investor_id is not None:
        investor_exists = Investor.objects.filter(
            tenant=company, pk=investor_id, is_active=True
        ).exists()
        if not investor_exists:
            raise NotFound("Investor not found.")
        credits = credits.filter(current_investor_id=investor_id)
        returns = returns.filter(investor_id=investor_id)
    if branch_id is not None:
        if not scope.is_company_reader and branch_id not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        credits = credits.filter(branch_id=branch_id)
        returns = returns.filter(branch_id=branch_id)
    elif not scope.is_company_reader:
        credits = credits.filter(branch_id__in=scope.allowed_branch_ids)
        returns = returns.filter(branch_id__in=scope.allowed_branch_ids)

    credits = with_fund_credit_available(credits)
    credits = credits.annotate(fund_gross=Func(F("pk"), function="investment_credit_gross_available", output_field=DecimalField(max_digits=38, decimal_places=2)))
    credit_totals = credits.aggregate(
        total=Sum("amount"), available=Sum("fund_available"),
        gross=Sum("fund_gross"),
        review_count=Count("id", filter=Q(fund_available__isnull=True)),
    )
    if credit_totals["review_count"]:
        raise DomainConflict("Fund recovery sources require review.", code="FUND_RECOVERY_REVIEW_REQUIRED")
    credit_total = credit_totals["total"] or Decimal("0.00")
    return_total = returns.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    use_credit_ids = credits.order_by().values("id")
    from apps.investment.models import VehiclePrincipalRefundDebit
    with localcontext() as context:
        context.prec = 80
        used_total = (
            (InvestorFundUseAllocation.objects.filter(credit_id__in=use_credit_ids).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"))
            + (InvestorFundUseAdjustment.objects.filter(credit_id__in=use_credit_ids).aggregate(total=Sum("amount_delta"))["total"] or Decimal("0.00"))
            - (VehicleCapitalRecoveryCreditAllocation.objects.filter(credit_id__in=use_credit_ids).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"))
            + (VehiclePrincipalRefundDebit.objects.filter(fund_credit_id__in=use_credit_ids).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"))
        )
        reserved_amount = (credit_totals["gross"] or Decimal("0.00")) - (credit_totals["available"] or Decimal("0.00"))
    result = {
        "company_id": str(company.pk),
        "investor_id": str(investor_id) if investor_id else None,
        "branch_id": str(branch_id) if branch_id else None,
        "credit_total": format(credit_total, ".2f"),
        "principal_return_total": format(return_total, ".2f"),
        "used_total": format(used_total, ".2f"),
        "reserved_amount": format(reserved_amount, ".2f"),
        "available_amount": format(credit_totals["available"] or Decimal("0.00"), ".2f"),
    }
    # The Branch Accountant receives only the sum inside their authorized
    # source-Branch filter; it is never the pooled Company balance.
    return result


def create_fund_credit(
    *, actor, company_id, key, path, investor_id, branch_id, account_id,
    amount, reference, effective_at,
):
    effective_at = _date_value(effective_at)
    body = {
        "investor_id": str(investor_id),
        "branch_id": str(branch_id),
        "account_id": str(account_id),
        "amount": format(Decimal(amount), ".2f"),
        "reference": reference.strip(),
        "effective_at": effective_at.isoformat(),
    }

    def operation(company, branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        assert_investor_accepts_new_funding(company=company, investor=investor)
        credit = InvestorFundCredit.objects.create(
            tenant=company,
            investor=investor,
            branch=branch,
            amount=Decimal(amount),
            effective_at=effective_at,
            reference=body["reference"],
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        event, _movement, event_data = record_capital_movement(
            tenant=company,
            branch=branch,
            account_id=account_id,
            amount=credit.amount,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.CAPITAL_INFLOW,
            source_record=credit,
            description=f"Investor Fund credit: {investor.name}",
            source_reference=credit.reference,
            effective_at=effective_at,
        )
        record_event(
            action="investment.fund.credit",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=credit,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(credit.amount, ".2f"),
                "accounting_event_id": str(event.pk),
                "branch_id": str(branch.pk),
            },
        )
        result = _credit_data(credit)
        result["accounting_event_id"] = event_data["id"]
        return DomainMutationResult(201, result)

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.credit",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )


def list_principal_returns(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    queryset = InvestorPrincipalReturn.objects.filter(tenant=company).select_related(
        "investor", "branch"
    )
    if investor_id is not None:
        queryset = queryset.filter(investor_id=investor_id)
    queryset = _filter_branch_records(queryset, scope=scope, branch_id=branch_id)
    return queryset.order_by("effective_at", "id").prefetch_related("allocations")


def create_principal_return(
    *, actor, company_id, key, path, investor_id, branch_id, account_id,
    amount, reference, effective_at,
):
    effective_at = _date_value(effective_at)
    amount = Decimal(amount)
    body = {
        "investor_id": str(investor_id),
        "branch_id": str(branch_id),
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "reference": reference.strip(),
        "effective_at": effective_at.isoformat(),
    }

    def operation(company, branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        credits = list(
            with_fund_credit_available(with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update().filter(
                    tenant=company, branch=branch
                )
            ))
            .filter(current_investor_id=investor.pk)
            .order_by("effective_at", "id")
        )
        if not credits:
            raise DomainConflict(
                "No returnable Fund credit exists in this source Branch.",
                code="FUND_AVAILABLE_INSUFFICIENT",
            )
        remaining_by_credit = {}
        available_total = Decimal("0.00")
        for credit in credits:
            remaining = _available_credit(credit)
            remaining_by_credit[credit.pk] = remaining
            available_total += remaining
        if amount <= 0 or amount > available_total:
            raise DomainConflict(
                "Return exceeds the Investor's available Fund in this source Branch.",
                code="FUND_AVAILABLE_INSUFFICIENT",
            )
        principal_return = InvestorPrincipalReturn.objects.create(
            tenant=company,
            investor=investor,
            branch=branch,
            amount=amount,
            effective_at=effective_at,
            reference=body["reference"],
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        unallocated = amount
        for credit in credits:
            available = remaining_by_credit[credit.pk]
            if available <= 0:
                continue
            allocation_amount = min(available, unallocated)
            if allocation_amount > 0:
                InvestorPrincipalReturnAllocation.objects.create(
                    tenant=company,
                    principal_return=principal_return,
                    credit=credit,
                    amount=allocation_amount,
                    actor=locked_actor,
                )
                unallocated -= allocation_amount
            if unallocated == 0:
                break
        event, _movement, _event_data = record_capital_movement(
            tenant=company,
            branch=branch,
            account_id=account_id,
            amount=principal_return.amount,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.CAPITAL_OUTFLOW,
            source_record=principal_return,
            description=f"Investor principal return: {investor.name}",
            source_reference=principal_return.reference,
            effective_at=effective_at,
        )
        record_event(
            action="investment.fund.principal_return",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=principal_return,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(amount, ".2f"),
                "accounting_event_id": str(event.pk),
                "branch_id": str(branch.pk),
            },
        )
        return DomainMutationResult(201, _return_data(principal_return))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.return",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )
