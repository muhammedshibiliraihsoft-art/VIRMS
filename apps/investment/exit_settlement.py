"""Company-wide Exit review from authoritative financial sources."""
import hashlib
import json
from datetime import datetime
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import NotFound


def exit_settlement_position(*, actor, company_id, investor_id, exit_request_id):
    from apps.investment.models import Investor, InvestorExitRequest, InvestorProfitLossOffset, InvestorExitLossApplication
    from apps.investment.fund_position import investor_fund_position, FundPositionReviewRequired
    from apps.investment.services import list_investor_profit_period_projection, read_scope
    from apps.investment.portal import _exit_request_data
    from apps.vehicles.models import VehiclePurchase
    from apps.vehicles.services import get_vehicle_financial_position

    company, _scope, _branch = read_scope(actor=actor, company_id=company_id,
                                         action="investment.exit.settlement.read")
    investor = Investor.objects.filter(tenant=company, pk=investor_id).first()
    request = InvestorExitRequest.objects.filter(
        tenant=company, investor=investor, pk=exit_request_id,
    ).first() if investor else None
    if request is None:
        raise NotFound("Investor Exit request not found.")
    blockers = []
    if request.status != InvestorExitRequest.Status.REQUESTED:
        blockers.append("EXIT_REQUEST_NOT_ACTIVE")
    deadline = _exit_request_data(request)["notice_deadline"]
    if timezone.now() < datetime.fromisoformat(deadline):
        blockers.append("EXIT_NOTICE_NOT_EXPIRED")
    fund = None
    try:
        fund = investor_fund_position(company=company, investor=investor)
        if fund.principal_refund_due:
            blockers.append("BUYER_PRINCIPAL_REFUND_OPEN")
    except FundPositionReviewRequired:
        blockers.append("FUND_SOURCE_REVIEW_REQUIRED")
    vehicles, confirmed_losses, residual_loss = [], [], Decimal("0")
    offsets = {
        row["loss_result_id"]: row["total"] for row in InvestorProfitLossOffset.objects.filter(
            tenant=company, investor=investor,
        ).values("loss_result_id").annotate(total=Sum("amount"))
    }
    applied_losses = {
        row["loss_result_id"]: row["total"] for row in InvestorExitLossApplication.objects.filter(
            tenant=company, exit_request=request,
        ).values("loss_result_id").annotate(total=Sum("amount"))
    }
    purchases = VehiclePurchase.objects.filter(tenant=company).filter(
        Q(investor=investor) | Q(vehicle__direct_expenses__investor=investor),
    ).distinct().select_related("vehicle")
    for purchase in purchases:
        position = get_vehicle_financial_position(actor=actor, company_id=company.pk, vehicle_id=purchase.vehicle_id)
        if purchase.investor_id != investor.pk:
            blockers.append("VEHICLE_INVESTOR_ATTRIBUTION_REVIEW_REQUIRED")
        confirmed = position.get("confirmed_result")
        if not position["sale_id"]:
            blockers.append("OPEN_FUNDED_VEHICLE")
        elif Decimal(position["buyer_receivable"] or "0") or Decimal(position["buyer_refund_payable"] or "0"):
            blockers.append("BUYER_BALANCE_OPEN")
        if not confirmed or not confirmed["is_current"]:
            blockers.append("VEHICLE_RESULT_REVIEW_REQUIRED")
        elif confirmed["result_kind"] == "LOSS":
            from uuid import UUID
            result_id = UUID(confirmed["id"])
            outstanding_loss = max(Decimal("0"), abs(Decimal(confirmed["investor_share_amount"]))
                                  - offsets.get(result_id, Decimal("0")) - applied_losses.get(result_id, Decimal("0")))
            residual_loss += outstanding_loss
            if outstanding_loss:
                confirmed_losses.append({"loss_result_id": str(result_id), "vehicle_id": str(purchase.vehicle_id),
                                         "label": purchase.vehicle.registration,
                                         "amount": format(outstanding_loss, ".2f")})
        elif Decimal(position["investor_fund_cost"]) > 0 and not position["capital_recovery"]["is_complete"]:
            blockers.append("VEHICLE_CAPITAL_RECOVERY_REQUIRED")
        vehicles.append({"vehicle_id": str(purchase.vehicle_id), "label": purchase.vehicle.registration,
                         "source_version": position["source_version"], "status": position["status"]})
    periods = list_investor_profit_period_projection(actor=actor, company_id=company.pk, investor_id=investor.pk)
    obligations = []
    if periods["unassigned_result_count"]:
        blockers.append("PERIOD_SOURCE_REVIEW_REQUIRED")
    for period in periods["periods"]:
        confirmed = period["confirmed_position"]
        if not confirmed or not confirmed["is_current"]:
            blockers.append("PERIOD_POSITION_CONFIRMATION_REQUIRED")
        else:
            obligations.append({**confirmed, "period_start": period["period_start"], "period_end": period["period_end"]})
    from apps.investment.models import InvestorExitSettlementClosure
    closure = InvestorExitSettlementClosure.objects.filter(tenant=company, exit_request=request).first()
    result = {
        "investor_id": str(investor.pk), "exit_request_id": str(request.pk), "notice_deadline": deadline,
        "principal_available": format(fund.available, ".2f") if fund else None,
        "residual_confirmed_loss": format(residual_loss, ".2f"), "vehicles": vehicles,
        "confirmed_positions": obligations, "confirmed_losses": confirmed_losses, "blockers": sorted(set(blockers)),
        "settlement_order": ["PRINCIPAL", "RESIDUAL_LOSS", "REMAINING_PROFIT", "CLOSE"],
        "closure_implemented": closure is not None,
        "settlement_status": request.status,
    }
    result["source_version"] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


def record_exit_principal_payment(*, actor, company_id, investor_id, exit_request_id,
                                  branch_id, account_id, amount, reference, effective_at,
                                  expected_source_version, reason, key, path):
    """Record a Company-approved partial Exit principal payment from one source Branch."""
    from apps.accounts.audit import record_event
    from apps.accounting.models import AccountingAccount
    from apps.accounting.services import record_capital_movement
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.investment.models import (
        InvestmentIdempotencyRecord, Investor, InvestorExitRequest, InvestorFundCredit,
        InvestorPrincipalReturn, InvestorPrincipalReturnAllocation,
    )
    from apps.investment.selectors import with_current_fund_credit_owner, with_fund_credit_available
    from apps.investment.services import _available_credit, _return_data
    from apps.tenants.models import Branch, CompanyModuleCode

    amount = Decimal(amount)
    reason, reference = reason.strip(), reference.strip()
    if amount <= 0 or len(reason) < 3 or len(reference) < 3 or effective_at > timezone.now():
        raise DomainConflict("A positive current Exit payment, reference and reason are required.",
                             code="EXIT_PRINCIPAL_PAYMENT_INVALID")
    body = {
        "investor_id": str(investor_id), "exit_request_id": str(exit_request_id),
        "branch_id": str(branch_id), "account_id": str(account_id), "amount": format(amount, ".2f"),
        "reference": reference, "effective_at": effective_at.isoformat(),
        "expected_source_version": expected_source_version, "reason": reason,
    }

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        exit_request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, investor=investor, pk=exit_request_id,
            status=InvestorExitRequest.Status.REQUESTED,
        ).first()
        if exit_request is None:
            raise NotFound("Open Investor Exit request not found.")
        current = exit_settlement_position(
            actor=locked_actor, company_id=company.pk, investor_id=investor.pk,
            exit_request_id=exit_request.pk,
        )
        if current["source_version"] != expected_source_version:
            raise DomainConflict("Exit sources changed. Reload the settlement review.",
                                 code="EXIT_SETTLEMENT_SOURCE_STALE")
        blocking = [item for item in current["blockers"] if item != "EXIT_NOTICE_NOT_EXPIRED"]
        if blocking:
            raise DomainConflict(
                "Resolve current Exit source blockers before principal payment: " + ", ".join(blocking),
                code="EXIT_SETTLEMENT_BLOCKED",
            )
        branch = Branch.objects.filter(tenant=company, pk=branch_id).first()
        account = AccountingAccount.objects.select_for_update().filter(
            tenant=company, pk=account_id, is_active=True,
        ).first()
        if branch is None or account is None:
            raise NotFound("Payment Branch or Cash/Bank account not found.")
        credits = list(with_fund_credit_available(with_current_fund_credit_owner(
            InvestorFundCredit.objects.select_for_update().filter(tenant=company, branch=branch)
        )).filter(current_investor_id=investor.pk).order_by("effective_at", "id"))
        remaining_by_credit = {}
        available_total = Decimal("0.00")
        for credit in credits:
            available = _available_credit(credit)
            remaining_by_credit[credit.pk] = available
            available_total += available
        if amount > available_total:
            raise DomainConflict("Exit principal payment exceeds this Branch's unreserved Available Fund.",
                                 code="EXIT_PRINCIPAL_AVAILABLE_INSUFFICIENT")
        principal_return = InvestorPrincipalReturn.objects.create(
            tenant=company, investor=investor, exit_request=exit_request, branch=branch,
            amount=amount, effective_at=effective_at, reference=reference,
            actor=locked_actor, module_revision=exit_request.investment_module_revision,
        )
        unallocated = amount
        for credit in credits:
            lot_available = remaining_by_credit[credit.pk]
            allocation_amount = min(lot_available, unallocated)
            if allocation_amount > 0:
                InvestorPrincipalReturnAllocation.objects.create(
                    tenant=company, principal_return=principal_return, credit=credit,
                    amount=allocation_amount, actor=locked_actor,
                )
                unallocated -= allocation_amount
            if unallocated == 0:
                break
        event, movement, _data = record_capital_movement(
            tenant=company, branch=branch, account_id=account.pk, amount=amount,
            actor=locked_actor, accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type="CAPITAL_OUTFLOW", source_record=principal_return,
            description=f"Investor Exit principal return: {investor.name}",
            source_reference=reference, effective_at=effective_at,
        )
        record_event(
            action="investment.exit.settlement.principal", actor=locked_actor,
            subject=locked_actor, company=company, branch=branch, resource=principal_return,
            reason=reason, metadata={
                "investor_id": str(investor.pk), "exit_request_id": str(exit_request.pk),
                "amount": format(amount, ".2f"), "accounting_event_id": str(event.pk),
                "branch_id": str(branch.pk),
            },
        )
        data = _return_data(principal_return)
        data.update({"exit_request_id": str(exit_request.pk), "accounting_event_id": str(event.pk),
                     "movement_id": str(movement.pk)})
        return DomainMutationResult(201, data)

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key, body=body,
        action="investment.exit.settlement.principal",
        module_codes=(CompanyModuleCode.ACCOUNTING,),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def record_exit_loss_application(*, actor, company_id, investor_id, exit_request_id,
                                 loss_result_id, branch_id, account_id, source, amount,
                                 effective_at, expected_source_version, reason, key, path):
    """Apply one confirmed Investor Loss from Available Fund or actual receipt."""
    from apps.accounts.audit import record_event
    from apps.accounts.policy import require_action
    from apps.accounting.models import AccountingAccount
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.investment.models import (
        InvestmentIdempotencyRecord, Investor, InvestorExitRequest, InvestorExitLossApplication,
        InvestorExitLossAllocation, InvestorFundCredit, VehicleResultConfirmation,
    )
    from apps.investment.selectors import with_current_fund_credit_owner, with_fund_credit_available
    from apps.investment.services import _available_credit
    from apps.tenants.models import Branch, CompanyModuleCode

    amount, reason = Decimal(amount), reason.strip()
    if amount <= 0 or effective_at > timezone.now() or len(reason) < 3:
        raise DomainConflict("Enter a positive current Loss application and reason.", code="EXIT_LOSS_APPLICATION_INVALID")
    body = {"investor_id": str(investor_id), "exit_request_id": str(exit_request_id),
            "loss_result_id": str(loss_result_id), "branch_id": str(branch_id), "account_id": str(account_id) if account_id else None,
            "source": source, "amount": format(amount, ".2f"), "effective_at": effective_at.isoformat(),
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor not found.")
        exit_request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, pk=exit_request_id, investor=investor, status=InvestorExitRequest.Status.REQUESTED,
        ).first()
        if exit_request is None:
            raise NotFound("Open Investor Exit request not found.")
        current = exit_settlement_position(actor=locked_actor, company_id=company.pk,
                                           investor_id=investor.pk, exit_request_id=exit_request.pk)
        if current["source_version"] != expected_source_version:
            raise DomainConflict("Exit sources changed. Reload the settlement review.", code="EXIT_SETTLEMENT_SOURCE_STALE")
        blocking = [item for item in current["blockers"] if item != "EXIT_NOTICE_NOT_EXPIRED"]
        if blocking:
            raise DomainConflict("Resolve current Exit source blockers first: " + ", ".join(blocking), code="EXIT_SETTLEMENT_BLOCKED")
        loss_item = next((item for item in current["confirmed_losses"] if item["loss_result_id"] == str(loss_result_id)), None)
        if loss_item is None or amount > Decimal(loss_item["amount"]):
            raise DomainConflict("Loss application exceeds the current confirmed outstanding Loss.", code="EXIT_LOSS_EXCEEDS_BALANCE")
        result = VehicleResultConfirmation.objects.select_for_update().filter(
            tenant=company, investor=investor, pk=loss_result_id, result_kind=VehicleResultConfirmation.ResultKind.LOSS,
        ).first()
        if result is None:
            raise DomainConflict("The confirmed Vehicle Loss is no longer current.", code="EXIT_LOSS_SOURCE_STALE")
        branch = Branch.objects.filter(tenant=company, pk=branch_id).first()
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first() if account_id else None
        if branch is None or (source == InvestorExitLossApplication.Source.DIRECT_RECEIPT and account is None):
            raise NotFound("Payment Branch or Cash/Bank account not found.")
        if source == InvestorExitLossApplication.Source.DIRECT_RECEIPT:
            from apps.investment.fund_position import FundPositionReviewRequired, investor_fund_position
            try:
                fund = investor_fund_position(company=company, investor=investor)
            except FundPositionReviewRequired as exc:
                raise DomainConflict(str(exc), code="EXIT_LOSS_FUND_REVIEW_REQUIRED") from exc
            if fund.available > 0:
                raise DomainConflict(
                    "Use the Investor's eligible Available Fund before a direct Exit Loss receipt.",
                    code="EXIT_LOSS_FUND_FIRST_REQUIRED",
                )
            require_action(locked_actor, "accounting.receipt.create", company=company, branch=branch)
        application = InvestorExitLossApplication.objects.create(
            tenant=company, exit_request=exit_request, loss_result=result, branch=branch, account=account,
            source=source, amount=amount, effective_at=effective_at, reason=reason, actor=locked_actor,
            investment_revision=exit_request.investment_module_revision,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        if source == InvestorExitLossApplication.Source.AVAILABLE_FUND:
            credits = list(with_fund_credit_available(with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update().filter(tenant=company)
            )).filter(current_investor_id=investor.pk).order_by("effective_at", "id"))
            available_total = sum((_available_credit(credit) for credit in credits), Decimal("0.00"))
            if amount > available_total:
                raise DomainConflict("Loss application exceeds this Investor's unreserved Available Fund.", code="EXIT_LOSS_FUND_INSUFFICIENT")
            left = amount
            for credit in credits:
                take = min(left, _available_credit(credit))
                if take > 0:
                    InvestorExitLossAllocation.objects.create(tenant=company, application=application,
                                                              credit=credit, amount=take, actor=locked_actor)
                    left -= take
                if left == 0:
                    break
        else:
            from apps.accounting.services import record_investor_exit_loss_recovery
            event, movement = record_investor_exit_loss_recovery(
                tenant=company, application=application, actor=locked_actor,
                accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            )
        record_event(action="investment.exit.settlement.loss", actor=locked_actor, subject=locked_actor,
                     company=company, branch=branch, resource=application, reason=reason,
                     metadata={"investor_id": str(investor.pk), "exit_request_id": str(exit_request.pk),
                               "loss_result_id": str(result.pk), "source": source, "amount": format(amount, ".2f"),
                               "accounting_event_id": str(event.pk) if source == InvestorExitLossApplication.Source.DIRECT_RECEIPT else None})
        return DomainMutationResult(201, {"id": str(application.pk), "exit_request_id": str(exit_request.pk),
                                          "loss_result_id": str(result.pk), "source": source,
                                          "amount": format(amount, ".2f"),
                                          "accounting_event_id": str(event.pk) if source == InvestorExitLossApplication.Source.DIRECT_RECEIPT else None,
                                          "allocations": [{"credit_id": str(row.credit_id), "amount": format(row.amount, ".2f")}
                                                          for row in application.allocations.all()]})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
                                   body=body, action="investment.exit.settlement.loss",
                                   module_codes=(CompanyModuleCode.ACCOUNTING,),
                                   idempotency_model=InvestmentIdempotencyRecord, operation=operation)


def record_exit_profit_payment(*, actor, company_id, investor_id, exit_request_id,
                               position_id, branch_id, account_id, amount, effective_at,
                               expected_source_version, reason, key, path):
    """Pay a partial current Exit Profit payable through Accounting."""
    from apps.accounts.audit import record_event
    from apps.accounts.policy import require_action
    from apps.accounting.models import AccountingAccount
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.investment.models import InvestmentIdempotencyRecord, Investor, InvestorExitRequest, InvestorExitProfitPayment, InvestorProfitPeriodPosition
    from apps.investment.services import list_investor_profit_period_projection
    from apps.tenants.models import Branch, CompanyModuleCode

    amount, reason = Decimal(amount), reason.strip()
    if amount <= 0 or effective_at > timezone.now() or len(reason) < 3:
        raise DomainConflict("Enter a positive current Exit Profit payment and reason.", code="EXIT_PROFIT_PAYMENT_INVALID")
    body = {"investor_id": str(investor_id), "exit_request_id": str(exit_request_id), "position_id": str(position_id),
            "branch_id": str(branch_id), "account_id": str(account_id), "amount": format(amount, ".2f"),
            "effective_at": effective_at.isoformat(), "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor not found.")
        exit_request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, pk=exit_request_id, investor=investor, status=InvestorExitRequest.Status.REQUESTED,
        ).first()
        if exit_request is None:
            raise NotFound("Open Investor Exit request not found.")
        current_exit = exit_settlement_position(actor=locked_actor, company_id=company.pk,
                                                investor_id=investor.pk, exit_request_id=exit_request.pk)
        if current_exit["source_version"] != expected_source_version:
            raise DomainConflict("Exit sources changed. Reload the settlement review.", code="EXIT_SETTLEMENT_SOURCE_STALE")
        blocking = [item for item in current_exit["blockers"] if item != "EXIT_NOTICE_NOT_EXPIRED"]
        if blocking:
            raise DomainConflict("Resolve current Exit source blockers first: " + ", ".join(blocking), code="EXIT_SETTLEMENT_BLOCKED")
        if Decimal(current_exit["principal_available"] or "0") != 0 or Decimal(current_exit["residual_confirmed_loss"]) != 0:
            raise DomainConflict(
                "Settle returnable Principal and confirmed residual Loss before Exit Profit.",
                code="EXIT_PROFIT_SETTLEMENT_ORDER_REQUIRED",
            )
        projection = list_investor_profit_period_projection(actor=locked_actor, company_id=company.pk, investor_id=investor.pk)
        position_data_current = next((row["confirmed_position"] for row in projection["periods"]
                                      if row["confirmed_position"] and row["confirmed_position"]["id"] == str(position_id)), None)
        if (not position_data_current or not position_data_current["is_current"] or position_data_current["kind"] != "PAYABLE"
            or amount > Decimal(position_data_current["amount"])):
            raise DomainConflict("Payment exceeds the current confirmed Exit Profit payable.", code="EXIT_PROFIT_EXCEEDS_BALANCE")
        position = InvestorProfitPeriodPosition.objects.select_for_update(of=("self",)).filter(
            tenant=company, pk=position_id, reconciliation__investor=investor,
        ).select_related("reconciliation").first()
        branch = Branch.objects.filter(tenant=company, pk=branch_id).first()
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if position is None or branch is None or account is None:
            raise NotFound("Confirmed Profit position, Branch or Cash/Bank account not found.")
        require_action(locked_actor, "accounting.payment.create", company=company, branch=branch)
        payment = InvestorExitProfitPayment.objects.create(
            tenant=company, exit_request=exit_request, position=position, branch=branch, account=account,
            amount=amount, effective_at=effective_at, reason=reason, actor=locked_actor,
            investment_revision=exit_request.investment_module_revision,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        from apps.accounting.services import record_investor_exit_profit_payment
        event, movement = record_investor_exit_profit_payment(
            tenant=company, payment=payment, actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
        )
        record_event(action="investment.exit.settlement.profit", actor=locked_actor, subject=locked_actor,
                     company=company, branch=branch, resource=payment, reason=reason,
                     metadata={"investor_id": str(investor.pk), "exit_request_id": str(exit_request.pk),
                               "reconciliation_id": str(position.reconciliation_id), "amount": format(amount, ".2f"),
                               "accounting_event_id": str(event.pk), "branch_id": str(branch.pk)})
        return DomainMutationResult(201, {"id": str(payment.pk), "exit_request_id": str(exit_request.pk),
                                          "position_id": str(position.pk), "amount": format(amount, ".2f"),
                                          "accounting_event_id": str(event.pk), "movement_id": str(movement.pk)})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
                                   body=body, action="investment.exit.settlement.profit",
                                   module_codes=(CompanyModuleCode.ACCOUNTING,),
                                   idempotency_model=InvestmentIdempotencyRecord, operation=operation)


def close_exit_settlement(*, actor, company_id, investor_id, exit_request_id,
                          expected_source_version, reason, key, path):
    """Close a fully paid Exit; waivers and unresolved balances are never inferred."""
    from apps.accounts.audit import record_event
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.investment.models import (InvestmentIdempotencyRecord, Investor, InvestorExitRequest,
        InvestorExitRequestHistory, InvestorExitSettlementClosure)
    from apps.tenants.models import CompanyModuleCode
    reason = reason.strip()
    body = {"investor_id": str(investor_id), "exit_request_id": str(exit_request_id),
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, pk=exit_request_id, investor=investor,
            status=InvestorExitRequest.Status.REQUESTED,
        ).first() if investor else None
        if request is None:
            raise NotFound("Open Investor Exit request not found.")
        current = exit_settlement_position(actor=locked_actor, company_id=company.pk,
                                           investor_id=investor.pk, exit_request_id=request.pk)
        if current["source_version"] != expected_source_version:
            raise DomainConflict("Exit sources changed. Reload the settlement review.", code="EXIT_SETTLEMENT_SOURCE_STALE")
        if current["blockers"] or Decimal(current["principal_available"] or "0") != 0 or Decimal(current["residual_confirmed_loss"]) != 0 or any(
            row.get("kind") not in ("BALANCED", None) or Decimal(row.get("amount", "0")) != 0
            for row in current["confirmed_positions"]
        ):
            raise DomainConflict("Clear all confirmed Exit principal, loss and profit balances before closing.", code="EXIT_SETTLEMENT_BLOCKED")
        revision = revisions[CompanyModuleCode.ACCOUNTING]
        closure = InvestorExitSettlementClosure.objects.create(
            tenant=company, exit_request=request, source_version=expected_source_version,
            reason=reason, actor=locked_actor, accounting_revision=revision, closed_at=timezone.now(),
        )
        version = (request.history.order_by("-version").values_list("version", flat=True).first() or 0) + 1
        record_event(action="investment.exit.settlement.close", actor=locked_actor, subject=locked_actor,
                     company=company, resource=request, reason=reason,
                     metadata={"exit_request_id": str(request.pk), "status": "SETTLED",
                               "closure_id": str(closure.pk), "source_version": expected_source_version})
        InvestorExitRequestHistory.objects.create(
            tenant=company, exit_request=request, version=version,
            action=InvestorExitRequestHistory.Action.SETTLEMENT_CLOSED,
            previous_status=request.status, new_status=InvestorExitRequest.Status.SETTLED,
            actor=locked_actor, reason=reason,
        )
        InvestorExitRequest.objects.filter(pk=request.pk).update(status=InvestorExitRequest.Status.SETTLED)
        return DomainMutationResult(201, {"id": str(closure.pk), "status": "SETTLED", "source_version": expected_source_version})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.exit.settlement.close", module_codes=(CompanyModuleCode.ACCOUNTING,),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation)
