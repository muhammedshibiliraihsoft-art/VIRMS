"""Confirmed Investor obligations, separate from calculation and actual cash."""

from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.audit import record_event
from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
from apps.investment.models import (
    InvestmentIdempotencyRecord, Investor, InvestorProfitPeriodPosition,
    InvestorProfitPeriodReconciliation,
)
from apps.tenants.models import CompanyModuleCode


def position_data(position, *, is_current, repaid=None, profit_paid=None, recovery_received=None,
                  future_recovered=None, future_applied=None):
    calculation = position.reconciliation
    from apps.investment.models import InvestorProfitRecoveryReceipt
    from apps.investment.models import InvestorExitProfitPayment
    from apps.investment.models import InvestorProfitFutureAdjustment
    from apps.investment.finance import exact_money_difference
    if recovery_received is None:
        recovery_received = InvestorProfitRecoveryReceipt.objects.filter(
            tenant_id=position.tenant_id, position__reconciliation__investor_id=calculation.investor_id,
            position__reconciliation__period_start=calculation.period_start,
            position__reconciliation__period_end=calculation.period_end,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if profit_paid is None:
        profit_paid = InvestorExitProfitPayment.objects.filter(
            tenant_id=position.tenant_id, position__reconciliation__investor_id=calculation.investor_id,
            position__reconciliation__period_start=calculation.period_start,
            position__reconciliation__period_end=calculation.period_end,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if repaid is None:
        repaid = exact_money_difference(recovery_received, -profit_paid)
    period_filter = {
        "reconciliation__investor_id": calculation.investor_id,
        "reconciliation__period_start": calculation.period_start,
        "reconciliation__period_end": calculation.period_end,
    }
    if future_recovered is None:
        future_recovered = InvestorProfitFutureAdjustment.objects.filter(
            tenant_id=position.tenant_id, **{"recoverable_position__" + key: value for key, value in period_filter.items()},
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if future_applied is None:
        future_applied = InvestorProfitFutureAdjustment.objects.filter(
            tenant_id=position.tenant_id, **{"profit_position__" + key: value for key, value in period_filter.items()},
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    # Keep Investor-to-company receipts and company-to-Investor payments signed.
    # A payment reduces a payable and increases a recoverable; a receipt does
    # the opposite. Future adjustments move the signed position in their named
    # direction and may cross zero after a restatement.
    net = exact_money_difference(
        calculation.net_position, profit_paid, future_applied,
        -recovery_received, -future_recovered,
    )
    return {
        "id": str(position.pk), "reconciliation_id": str(calculation.pk),
        "previous_position_id": str(position.previous_position_id) if position.previous_position_id else None,
        "kind": "PAYABLE" if net > 0 else "RECOVERABLE" if net < 0 else "BALANCED",
        "amount": format(net.copy_abs(), ".2f"),
        "repaid": format(repaid, ".2f"),
        "profit_paid": format(profit_paid, ".2f"),
        "recovery_received": format(recovery_received, ".2f"),
        "future_profit_recovered": format(future_recovered, ".2f"),
        "future_profit_applied": format(future_applied, ".2f"),
        "is_current": is_current, "source_version": calculation.source_version,
        "confirmed_at": position.created_at.isoformat(), "reason": position.reason,
    }


def adjust_against_future_profit(*, actor, company_id, investor_id, position_id, profit_position_id,
                                 profit_result_id, expected_source_version, expected_profit_source_version,
                                 amount, reason, key, path):
    from apps.investment.models import InvestorProfitFutureAdjustment, VehicleResultConfirmation
    from apps.investment.services import list_investor_profit_period_projection
    from apps.vehicles.services import get_vehicle_financial_position
    from apps.investment.finance import exact_money_difference

    amount, reason = Decimal(amount), reason.strip()
    if amount <= 0 or len(reason) < 3:
        raise ValidationError("A positive adjustment and reason are required.")
    body = {"investor_id": str(investor_id), "position_id": str(position_id),
            "profit_position_id": str(profit_position_id), "profit_result_id": str(profit_result_id),
            "expected_source_version": expected_source_version, "expected_profit_source_version": expected_profit_source_version,
            "amount": format(amount, ".2f"), "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor not found.")
        positions = {str(row.pk): row for row in InvestorProfitPeriodPosition.objects.select_for_update(of=("self",)).filter(
            tenant=company, reconciliation__investor=investor, pk__in=(position_id, profit_position_id),
        ).select_related("reconciliation")}
        debt, profit = positions.get(str(position_id)), positions.get(str(profit_position_id))
        if debt is None or profit is None:
            raise NotFound("Confirmed Investor position not found.")
        projection = list_investor_profit_period_projection(actor=locked_actor, company_id=company.pk, investor_id=investor.pk)
        current = {row["confirmed_position"]["id"]: row["confirmed_position"] for row in projection["periods"] if row["confirmed_position"]}
        debt_now, profit_now = current.get(str(debt.pk)), current.get(str(profit.pk))
        if (
            not debt_now or not profit_now or not debt_now["is_current"] or not profit_now["is_current"]
            or debt_now["source_version"] != expected_source_version or profit_now["source_version"] != expected_profit_source_version
        ):
            raise DomainConflict("Confirm both current positions before adjustment.", code="INVESTOR_POSITION_SOURCE_STALE")
        if (
            debt_now["kind"] != "RECOVERABLE" or profit_now["kind"] != "PAYABLE"
            or profit.reconciliation.period_start <= debt.reconciliation.period_end
            or amount > min(Decimal(debt_now["amount"]), Decimal(profit_now["amount"]))
        ):
            raise DomainConflict("Adjustment exceeds the recoverable or future Profit.", code="INVESTOR_ADJUSTMENT_EXCEEDS_BALANCE")
        result = VehicleResultConfirmation.objects.select_for_update(of=("self",)).filter(
            tenant=company, investor=investor, pk=profit_result_id,
        ).select_related("sale").first()
        if result is None:
            raise NotFound("Future Profit result not found.")
        financial = get_vehicle_financial_position(actor=locked_actor, company_id=company.pk, vehicle_id=result.vehicle_id)
        confirmed = financial.get("confirmed_result") or {}
        sale_date = financial.get("sale_effective_date")
        if (
            confirmed.get("id") != str(result.pk) or not confirmed.get("is_current") or result.result_kind != "PROFIT"
            or not sale_date or not (profit.reconciliation.period_start.isoformat() <= sale_date <= profit.reconciliation.period_end.isoformat())
            or amount > Decimal(confirmed.get("investor_profit_remaining") or "0")
        ):
            raise DomainConflict("Choose current unpaid Profit from the selected future period.",
                                 code="INVESTOR_ADJUSTMENT_PROFIT_NOT_AVAILABLE")
        adjustment = InvestorProfitFutureAdjustment.objects.create(
            tenant=company, recoverable_position=debt, profit_position=profit, profit_result=result,
            amount=amount, reason=reason, actor=locked_actor,
            investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            vehicle_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(action="investment.profit.future_adjust", actor=locked_actor, subject=locked_actor,
                     company=company, branch=result.sale.branch, resource=investor, reason=reason,
                     metadata={"investor_id": str(investor.pk), "operation_id": str(adjustment.pk), "profit_result_id": str(result.pk),
                               "amount": format(amount, ".2f"), "cash_movement_created": False})
        return DomainMutationResult(201, {
            "id": str(adjustment.pk), "recoverable_position": position_data(debt, is_current=True),
            "profit_position": position_data(profit, is_current=True),
        })

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.profit.future_adjust",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def confirm_period_position(*, actor, company_id, investor_id, reconciliation_id,
                            expected_source_version, reason, key, path):
    from apps.investment.services import list_investor_profit_period_projection

    reason = reason.strip()
    if len(reason) < 3:
        raise ValidationError({"reason": "A position confirmation reason is required."})
    body = {"investor_id": str(investor_id), "reconciliation_id": str(reconciliation_id),
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor not found.")
        calculation = InvestorProfitPeriodReconciliation.objects.select_for_update().filter(
            tenant=company, investor=investor, pk=reconciliation_id,
        ).first()
        if calculation is None:
            raise NotFound("Investor period reconciliation not found.")
        projection = list_investor_profit_period_projection(
            actor=locked_actor, company_id=company.pk, investor_id=investor.pk,
        )
        period = next((row for row in projection["periods"]
                       if row["period_start"] == calculation.period_start.isoformat()
                       and row["period_end"] == calculation.period_end.isoformat()), None)
        if (
            projection["unassigned_result_count"] or period is None
            or period["reconciliation_status"] != "RECONCILED"
            or period["reconciliation_id"] != str(calculation.pk)
            or period["source_version"] != expected_source_version
            or calculation.source_version != expected_source_version
        ):
            raise DomainConflict("Reconcile current sources before confirming a position.",
                                 code="INVESTOR_POSITION_SOURCE_STALE")
        existing = InvestorProfitPeriodPosition.objects.select_related("reconciliation").filter(
            tenant=company, reconciliation=calculation,
        ).first()
        if existing:
            return DomainMutationResult(200, position_data(existing, is_current=True))
        previous = InvestorProfitPeriodPosition.objects.filter(
            tenant=company, reconciliation__investor=investor,
            reconciliation__period_start=calculation.period_start,
        ).select_related("reconciliation").order_by("-reconciliation__version").first()
        if previous and previous.reconciliation.period_end != calculation.period_end:
            raise DomainConflict("The confirmed period boundary requires review.",
                                 code="INVESTOR_PERIOD_BOUNDARY_REVIEW_REQUIRED")
        position = InvestorProfitPeriodPosition.objects.create(
            tenant=company, reconciliation=calculation, previous_position=previous,
            actor=locked_actor, reason=reason,
            investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            vehicle_revision=revisions[CompanyModuleCode.VEHICLE_MANAGEMENT],
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(
            action="investment.profit.position.confirm", actor=locked_actor, subject=locked_actor,
            company=company, resource=position, reason=reason,
            metadata={"investor_id": str(investor.pk), "reconciliation_id": str(calculation.pk),
                      "source_version": expected_source_version, "net_position": format(calculation.net_position, ".2f"),
                      "cash_movement_created": False},
        )
        return DomainMutationResult(201, position_data(position, is_current=True))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.profit.position.confirm",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.VEHICLE_MANAGEMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def receive_period_repayment(*, actor, company_id, investor_id, position_id,
                             expected_source_version, branch_id, account_id, amount,
                             reason, key, path, effective_at=None):
    from apps.accounts.policy import require_action
    from apps.accounting.models import AccountingAccount
    from apps.accounting.services import record_investor_profit_recovery
    from apps.investment.models import InvestorProfitRecoveryReceipt
    from apps.investment.services import list_investor_profit_period_projection
    from apps.tenants.models import Branch

    amount = Decimal(amount)
    when = effective_at or timezone.now()
    reason = reason.strip()
    if len(reason) < 3 or amount <= 0 or when > timezone.now():
        raise ValidationError("A positive actual repayment, current date and reason are required.")
    body = {"investor_id": str(investor_id), "position_id": str(position_id),
            "branch_id": str(branch_id), "account_id": str(account_id), "amount": format(amount, ".2f"),
            "effective_at": effective_at.isoformat() if effective_at else None,
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor not found.")
        position = InvestorProfitPeriodPosition.objects.select_for_update(of=("self",)).filter(
            tenant=company, pk=position_id, reconciliation__investor=investor,
        ).select_related("reconciliation").first()
        if position is None:
            raise NotFound("Confirmed Investor position not found.")
        projection = list_investor_profit_period_projection(
            actor=locked_actor, company_id=company.pk, investor_id=investor.pk,
        )
        current = next((row["confirmed_position"] for row in projection["periods"]
                        if row["confirmed_position"] and row["confirmed_position"]["id"] == str(position.pk)), None)
        if not current or not current["is_current"] or current["source_version"] != expected_source_version:
            raise DomainConflict("Confirm the current Investor position before repayment.",
                                 code="INVESTOR_POSITION_SOURCE_STALE")
        if current["kind"] != "RECOVERABLE" or amount > Decimal(current["amount"]):
            raise DomainConflict("Repayment exceeds the current confirmed recoverable.",
                                 code="INVESTOR_REPAYMENT_EXCEEDS_BALANCE")
        branch = Branch.objects.filter(tenant=company, pk=branch_id).first()
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if branch is None or account is None:
            raise NotFound("Repayment Branch or Cash/Bank account not found.")
        require_action(locked_actor, "accounting.receipt.create", company=company, branch=branch)
        receipt = InvestorProfitRecoveryReceipt.objects.create(
            tenant=company, position=position, branch=branch, account=account, amount=amount,
            effective_at=when, actor=locked_actor, reason=reason,
            investment_revision=revisions[CompanyModuleCode.INVESTMENT],
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        event, _movement = record_investor_profit_recovery(
            tenant=company, receipt=receipt, actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(
            action="investment.profit.repayment.create", actor=locked_actor, subject=locked_actor,
            company=company, branch=branch, resource=receipt, reason=reason,
            metadata={"investor_id": str(investor.pk), "amount": format(amount, ".2f"),
                      "accounting_event_id": str(event.pk), "cash_movement_created": True},
        )
        return DomainMutationResult(201, {
            "receipt_id": str(receipt.pk), "accounting_event_id": str(event.pk),
            "position": position_data(position, is_current=True),
        })

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.profit.repayment.create",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )
