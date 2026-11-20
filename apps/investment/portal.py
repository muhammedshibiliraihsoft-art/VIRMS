"""Company-scoped account binding and default-deny Investor self resolution."""

from decimal import Decimal
from datetime import timezone as datetime_timezone

from django.utils import timezone
from rest_framework.exceptions import NotFound
from django.db.models import (
    CharField, Count, DecimalField, ExpressionWrapper, F, Max, Q, Sum, Value,
)
from django.db.models.functions import Coalesce

from apps.accounts.audit import record_event
from apps.accounts.locks import locked_users
from apps.accounts.models import CompanyRoleGrant, User
from apps.accounts.login_id import canonical_login_id
from apps.accounts.policy import require_action
from apps.common.domain_mutations import (
    DomainConflict, DomainMutationResult, execute_domain_mutation,
)
from apps.investment.models import (
    InvestmentIdempotencyRecord, Investor, InvestorAccountBinding,
    InvestorExitRequest, InvestorExitRequestHistory, InvestorExitNoticeExtension, InvestorFundCredit,
    InvestorFundCreditCorrection, InvestorFundUseAllocation,
    InvestorFundUse, InvestorFundUseAdjustment, InvestorInterimConfiguration,
    InvestorPrincipalReturn, InvestorPrincipalReturnAllocation,
    InvestorProfitCalendarConfiguration,
    InvestorProfitLossOffset,
    InvestorInterimPayment,
    InvestorProfitPeriodReconciliation,
    InvestorVehicleProfitPayment,
    VehicleResultConfirmation,
)
from apps.investment.selectors import with_current_fund_credit_owner, with_fund_credit_available
from apps.tenants.models import CompanyModuleCode, CompanyModuleState, Tenant, TenantMembership
from apps.tenants.selectors import current_interval


EXIT_TERMS_VERSION = "investor-exit-request-v1"


def _binding_data(binding):
    return {
        "id": str(binding.pk),
        "investor_id": str(binding.investor_id),
        "account_id": str(binding.account_id),
        "login_id": binding.account.login_id,
        "effective_from": binding.effective_from.isoformat(),
        "effective_until": binding.effective_until.isoformat() if binding.effective_until else None,
    }


def _eligible_investor_account(*, account_id, company):
    account = User.objects.filter(
        pk=account_id, is_active=True, must_change_password=False,
        account_kind=User.AccountKind.COMPANY,
    ).first()
    if account is None:
        raise NotFound("Investor account not found.")
    membership = TenantMembership.objects.filter(
        user=account, tenant=company,
    ).filter(current_interval()).first()
    if membership is None or not CompanyRoleGrant.objects.filter(
        membership=membership, role=CompanyRoleGrant.Role.INVESTOR,
        branch__isnull=True,
    ).filter(current_interval()).exists():
        raise NotFound("Investor account not found.")
    return account


def bind_account(*, actor, company_id, investor_id, key, path, account_id=None, login_id=None):
    if bool(account_id) == bool(login_id):
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"account_id": "Provide exactly one account_id or login_id."})
    if login_id:
        login_id = canonical_login_id(login_id)
        account_id = User.objects.filter(login_id=login_id).values_list("pk", flat=True).first()
        if account_id is None:
            raise NotFound("Investor account not found.")
    body = {"investor_id": str(investor_id), "account_id": str(account_id)}

    def operation(company, _branch, _revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            pk=investor_id, tenant=company, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        account = _eligible_investor_account(account_id=account_id, company=company)
        if InvestorAccountBinding.objects.filter(
            effective_until__isnull=True,
        ).filter(tenant=company, account=account).exists() or InvestorAccountBinding.objects.filter(
            investor=investor, effective_until__isnull=True,
        ).exists():
            raise DomainConflict("An active Investor account binding already exists.", code="BINDING_EXISTS")
        binding = InvestorAccountBinding.objects.create(
            tenant=company, investor=investor, account=account, bound_by=locked_actor,
        )
        record_event(
            action="investor.portal.binding.create", actor=locked_actor, subject=account,
            company=company, resource=binding,
            metadata={"binding_id": str(binding.pk), "investor_id": str(investor.pk),
                      "account_id": str(account.pk)},
        )
        return DomainMutationResult(201, _binding_data(binding))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.portal.binding.manage",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def get_binding(*, actor, company_id, investor_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Investor not found.")
    with locked_users(actor.pk) as users:
        locked_actor = users[actor.pk]
        if actor.auth_epoch != locked_actor.auth_epoch or actor.password != locked_actor.password:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Authentication changed.")
        require_action(locked_actor, "investment.portal.binding.manage", company=company)
        investor = Investor.objects.filter(pk=investor_id, tenant=company).first()
        if investor is None:
            raise NotFound("Investor not found.")
        binding = InvestorAccountBinding.objects.select_related("account").filter(
            tenant=company, investor=investor, effective_from__lte=timezone.now(),
            effective_until__isnull=True,
        ).first()
        return _binding_data(binding) if binding else None


def revoke_binding(*, actor, company_id, binding_id, reason, key, path):
    reason = reason.strip()
    body = {"binding_id": str(binding_id), "reason": reason}

    def operation(company, _branch, _revisions, locked_actor):
        binding = InvestorAccountBinding.objects.select_for_update().filter(
            pk=binding_id, tenant=company, effective_until__isnull=True,
        ).first()
        if binding is None:
            raise NotFound("Active Investor account binding not found.")
        binding.effective_until = timezone.now()
        binding.ended_by = locked_actor
        binding.end_reason = reason
        binding.save(update_fields=("effective_until", "ended_by", "end_reason", "updated_at"))
        record_event(
            action="investor.portal.binding.revoke", actor=locked_actor,
            subject=binding.account, company=company, resource=binding, reason=reason,
            metadata={"binding_id": str(binding.pk), "investor_id": str(binding.investor_id),
                      "account_id": str(binding.account_id)},
        )
        return DomainMutationResult(200, _binding_data(binding))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.portal.binding.manage",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def self_profile(*, actor, company_id):
    """Return only the bound profile; never accept a client-selected Investor ID."""
    company, binding = _self_portal_context(actor=actor, company_id=company_id)
    return _investor_portal_snapshot(company=company, binding=binding)


def self_fund_history(*, actor, company_id):
    """Return a paginatable, private activity query for the server-bound Investor."""
    company, binding = _self_portal_context(actor=actor, company_id=company_id)
    investor = binding.investor
    current_credits = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    ).filter(current_investor_id=investor.pk)
    credit_ids = current_credits.values("id")

    credits = current_credits.annotate(
        branch_name=F("branch__name"),
        activity_type=Value("FUND_CREDIT", output_field=CharField(max_length=32)),
        vehicle_registration=Value("", output_field=CharField()),
    ).values("id", "effective_at", "amount", "branch_name", "activity_type", "vehicle_registration")

    returns = InvestorPrincipalReturn.objects.filter(
        tenant=company, investor=investor,
    ).annotate(
        branch_name=F("branch__name"),
        activity_type=Value("PRINCIPAL_RETURN", output_field=CharField(max_length=32)),
        vehicle_registration=Value("", output_field=CharField()),
    ).values("id", "effective_at", "amount", "branch_name", "activity_type", "vehicle_registration")

    uses = InvestorFundUse.objects.filter(
        tenant=company, investor=investor,
    ).annotate(
        activity_amount=ExpressionWrapper(
            -F("amount"), output_field=DecimalField(max_digits=38, decimal_places=2),
        ),
        branch_name=F("branch__name"),
        activity_type=Value("VEHICLE_COMMITMENT", output_field=CharField(max_length=32)),
        vehicle_registration=Coalesce(
            F("purchase__vehicle__registration"),
            F("expense__vehicle__registration"),
            Value("", output_field=CharField()),
        ),
    ).values(
        "id", "effective_at", "activity_amount", "branch_name", "activity_type", "vehicle_registration",
    )

    adjustments = InvestorFundUseAdjustment.objects.filter(
        tenant=company, credit_id__in=credit_ids,
    ).annotate(
        branch_name=F("credit__branch__name"),
        activity_type=Value("COMMITMENT_ADJUSTMENT", output_field=CharField(max_length=32)),
        vehicle_registration=Coalesce(
            F("purchase_correction__purchase__vehicle__registration"),
            F("expense_correction__expense__vehicle__registration"),
            Value("", output_field=CharField()),
        ),
    ).values(
        "id", "effective_at", "amount_delta", "branch_name", "activity_type", "vehicle_registration",
    )

    # The first queryset defines the common output column names. Values are
    # source-owned records; the union stays in PostgreSQL and is paginated there.
    return credits.union(returns, uses, adjustments, all=True).order_by(
        "-effective_at", "-activity_type", "-id",
    )


def self_interim_payment_history(*, actor, company_id):
    """Return only the bound Investor's actual Interim payments."""
    company, binding = _self_portal_context(actor=actor, company_id=company_id)
    return InvestorInterimPayment.objects.filter(
        tenant=company, investor=binding.investor,
    ).order_by("-effective_at", "-id")


def interim_payment_activity_data(payment):
    return {
        "id": str(payment.pk),
        "period_month": payment.period_month.isoformat(),
        "effective_at": payment.effective_at.isoformat(),
        "amount": format(payment.amount, ".2f"),
    }


def _self_portal_context(*, actor, company_id):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Investor profile not found.")
    for module_code in (CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL):
        revision = CompanyModuleState.objects.filter(
            tenant=company, module_code=module_code,
        ).order_by("-version", "-id").first()
        if revision is None or revision.state != CompanyModuleState.State.ENABLED:
            raise NotFound("Investor profile not found.")
    return company, _self_binding(actor=actor, company=company)


def fund_history_activity_data(row):
    return {
        "id": str(row["id"]),
        "effective_at": row["effective_at"].isoformat(),
        "amount": format(row["amount"], ".2f"),
        "activity_type": row["activity_type"],
        "branch_name": row["branch_name"],
        "vehicle_registration": row["vehicle_registration"] or None,
    }


def _self_binding(*, actor, company):
    account = _eligible_investor_account(account_id=actor.pk, company=company)
    binding = InvestorAccountBinding.objects.select_related("investor").filter(
        tenant=company, account=account, effective_from__lte=timezone.now(),
        effective_until__isnull=True, investor__tenant=company, investor__is_active=True,
    ).first()
    if binding is None:
        raise NotFound("Investor profile not found.")
    return binding


def _investor_portal_snapshot(*, company, binding):
    from apps.investment.finance import exact_money_difference, summarize_investor_profit_periods
    from apps.vehicles.models import VehiclePurchase
    from apps.vehicles.services import get_vehicle_financial_position

    investor = binding.investor
    credit_rows = with_fund_credit_available(with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    )).filter(current_investor_id=investor.pk)
    credit_ids = credit_rows.values("id")
    credit_totals = credit_rows.aggregate(
        total=Sum("amount"), available=Sum("fund_available"),
        review_count=Count("id", filter=Q(fund_available__isnull=True)),
    )
    credit_total = credit_totals["total"] or 0
    first_credit_at = credit_rows.order_by("effective_at", "id").values_list(
        "effective_at", flat=True
    ).first()
    return_total = InvestorPrincipalReturn.objects.filter(
        tenant=company, investor=investor,
    ).aggregate(total=Sum("amount"))["total"] or 0
    use_allocations = InvestorFundUseAllocation.objects.filter(
        tenant=company, credit_id__in=credit_ids,
    )
    use_adjustments = InvestorFundUseAdjustment.objects.filter(
        tenant=company, credit_id__in=credit_ids,
    )
    used_total = use_allocations.aggregate(total=Sum("amount"))["total"] or 0
    use_adjustment_total = use_adjustments.aggregate(total=Sum("amount_delta"))["total"] or 0
    has_manual_review = InvestorFundCreditCorrection.objects.filter(
        tenant=company,
    ).filter(
        Q(from_investor=investor) | Q(to_investor=investor),
    ).filter(
        # Q133-Q134: never silently move historical use/return rows with a corrected credit.
        Q(credit__use_allocations__isnull=False)
        | Q(credit__return_allocations__isnull=False)
    ).exists() or bool(credit_totals["review_count"])

    vehicles = []
    latest_results = []
    purchases = VehiclePurchase.objects.filter(
        tenant=company, investor=investor, investor_fund_amount__gt=0,
    ).select_related("vehicle", "vehicle__current_branch", "vehicle__confirmed_sale").order_by("purchased_at", "id")
    for purchase in purchases:
        position = get_vehicle_financial_position(
            actor=binding.account, company_id=company.pk,
            vehicle_id=purchase.vehicle_id, authorized_investor_id=investor.pk,
        )
        confirmed = position["confirmed_result"]
        portal_vehicle = {
            "vehicle_id": str(purchase.vehicle_id),
            "registration": purchase.vehicle.registration,
            "model": purchase.vehicle.model,
            "branch_name": purchase.vehicle.current_branch.name,
            # The Investor may see their own Vehicle and confirmed result, but
            # internal cost, Buyer balances, sale price, and protected agreement
            # configuration are not part of the private portal projection.
            "sale_status": position["status"],
            "confirmed_result_status": (
                "CURRENT" if confirmed and confirmed["is_current"]
                else "STALE_REVIEW_REQUIRED" if confirmed else "NOT_CONFIRMED"
            ),
        }
        if confirmed:
            portal_vehicle["confirmed_result"] = {
                "result_kind": confirmed["result_kind"],
                "investor_share_amount": confirmed["investor_share_amount"],
                "deal_profit_paid": confirmed["investor_profit_paid"],
                "loss_offset_applied": confirmed["investor_loss_offset_applied"],
                "confirmed_at": confirmed["confirmed_at"],
                "current": confirmed["is_current"],
            }
            latest_results.append({
                "id": str(confirmed["id"]),
                "vehicle_id": str(purchase.vehicle_id),
                "source_version": confirmed["source_version"],
                "sale_id": position["sale_id"],
                "investor_id": str(investor.pk),
                "effective_sale_date": position["sale_effective_date"],
                "status": "CURRENT" if confirmed["is_current"] else "STALE_REVIEW_REQUIRED",
                "deal_profit_paid": confirmed["investor_profit_paid"],
                "loss_offset_applied": confirmed["investor_loss_offset_applied"],
                **portal_vehicle["confirmed_result"],
            })
        vehicles.append(portal_vehicle)

    configurations = list(InvestorInterimConfiguration.objects.filter(
        tenant=company, investor=investor,
    ).order_by("effective_date", "id"))
    today = timezone.localdate()
    current_month_start = today.replace(day=1)
    active_interim = next((row for row in reversed(configurations)
                           if row.effective_date <= current_month_start), None)
    exit_requests = InvestorExitRequest.objects.filter(
        tenant=company, investor=investor,
    ).order_by("-created_at", "-id")[:20]

    available_ledger = credit_totals["available"] or Decimal("0.00")
    configured_calendars = list(
        InvestorProfitCalendarConfiguration.objects.filter(
            tenant=company, investor=investor,
        ).order_by("effective_start", "version", "id")
    )
    today = timezone.localdate()
    active_calendars = [row for row in configured_calendars if row.effective_start <= today]
    if configured_calendars:
        calendar_versions = [
            {"effective_start": row.effective_start.isoformat(),
             "duration_months": row.duration_months, "version": row.version}
            for row in configured_calendars
        ]
        active_calendar = active_calendars[-1] if active_calendars else configured_calendars[0]
        calendar_start = active_calendar.effective_start.isoformat()
        calendar_duration = active_calendar.duration_months
        calendar_status = "CONFIGURED" if active_calendars else "SCHEDULED"
        calendar_source = "ACCOUNTANT_CONFIGURED"
    else:
        calendar_start = timezone.localdate(first_credit_at).isoformat() if first_credit_at else None
        calendar_versions = (
            [{"effective_start": calendar_start, "duration_months": 6, "version": 1}]
            if calendar_start else []
        )
        calendar_duration = 6 if calendar_start else None
        calendar_status = "DEFAULT_FROM_FIRST_FUND_CREDIT" if calendar_start else "NOT_AVAILABLE"
        calendar_source = "DEFAULT_SIX_MONTHS" if calendar_start else None
    current_results_by_sale = {
        row["sale_id"]: row for row in latest_results
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
            "vehicle_result_id": (
                current["id"] if matching_current_profit
                else str(payment.result_confirmation_id)
            ),
            "effective_sale_date": (
                current["effective_sale_date"] if matching_current_profit else None
            ),
            "amount": format(payment.amount, ".2f"),
            "effective_at": payment.effective_at.isoformat(),
        })
    interim_payments = [
        {
            "id": str(row.pk),
            "effective_payment_date": timezone.localdate(row.effective_at).isoformat(),
            "amount": format(row.amount, ".2f"),
        }
        for row in InvestorInterimPayment.objects.filter(
            tenant=company, investor=investor,
        ).order_by("effective_at", "id")
    ]
    current_results_by_sale = {
        row["sale_id"]: row for row in latest_results
        if row.get("sale_id") and row.get("id")
    }
    loss_offsets = []
    for offset in InvestorProfitLossOffset.objects.filter(
        tenant=company, investor=investor,
    ).select_related("loss_result__sale", "profit_result__sale").order_by("effective_at", "id"):
        loss_result = current_results_by_sale.get(str(offset.loss_result.sale_id))
        profit_result = current_results_by_sale.get(str(offset.profit_result.sale_id))
        valid_link = bool(
            loss_result and profit_result
            and loss_result["status"] == "CURRENT"
            and profit_result["status"] == "CURRENT"
            and loss_result["id"] == str(offset.loss_result_id)
            and profit_result["id"] == str(offset.profit_result_id)
            and loss_result["result_kind"] == VehicleResultConfirmation.ResultKind.LOSS
            and profit_result["result_kind"] == VehicleResultConfirmation.ResultKind.PROFIT
        )
        loss_offsets.append({
            "id": str(offset.pk),
            "loss_result_id": str(offset.loss_result_id),
            "profit_result_id": str(offset.profit_result_id),
            "valid_link": valid_link,
            "effective_sale_date": profit_result["effective_sale_date"] if valid_link else None,
            "amount": format(offset.amount, ".2f"),
        })
    profit_periods, unassigned_result_count = summarize_investor_profit_periods(
        latest_results, calendar_versions,
        deal_profit_payments=deal_profit_payments,
        interim_payments=interim_payments,
        loss_offsets=loss_offsets,
    )
    if has_manual_review:
        profit_periods = []
        unassigned_result_count = len(latest_results)
        profit_period_status = "MANUAL_REVIEW_REQUIRED"
    elif not calendar_start:
        profit_period_status = "CALENDAR_NOT_AVAILABLE"
    elif not active_calendars and configured_calendars:
        profit_period_status = "CALENDAR_NOT_ACTIVE"
    elif unassigned_result_count:
        profit_period_status = "REVIEW_REQUIRED"
    else:
        profit_period_status = "CALCULATED_NOT_RECONCILED"
    reconciliations = list(
        InvestorProfitPeriodReconciliation.objects.filter(
            tenant=company, investor=investor,
        ).order_by("period_start", "period_end", "version", "id")
    ) if not has_manual_review else []
    latest_by_period = {}
    for reconciliation in reconciliations:
        latest_by_period[(
            reconciliation.period_start.isoformat(),
            reconciliation.period_end.isoformat(),
        )] = reconciliation

    def confirmed_snapshot(reconciliation, *, current_position=None):
        pending_adjustment = None
        if current_position is not None:
            pending_adjustment = format(
                exact_money_difference(current_position, reconciliation.net_position), ".2f",
            )
        return {
            "version": reconciliation.version,
            "confirmed_at": reconciliation.confirmed_at.isoformat(),
            "gross_investor_profit": format(reconciliation.gross_investor_profit, ".2f"),
            "investor_loss_share": format(reconciliation.investor_loss_share, ".2f"),
            "deal_profit_paid": format(reconciliation.deal_profit_paid, ".2f"),
            "interim_paid": format(reconciliation.interim_paid, ".2f"),
            "loss_offset_applied": format(reconciliation.loss_offset_applied, ".2f"),
            "net_position": format(reconciliation.net_position, ".2f"),
            "restatement_adjustment": format(reconciliation.restatement_adjustment, ".2f"),
            "pending_restatement_adjustment": pending_adjustment,
            "notice": "Confirmed calculation snapshot only; not a payable, payment, or final settlement.",
        }

    display_profit_periods = []
    for row in profit_periods:
        key = (row["period_start"], row["period_end"])
        current_position = exact_money_difference(
            row["gross_investor_profit"], row["deal_profit_paid"],
            row["interim_paid"], row["loss_offset_applied"],
        )
        latest = latest_by_period.get(key)
        source_matches = bool(latest and latest.source_version == row["source_version"])
        display_profit_periods.append({
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "duration_months": row["duration_months"],
            "gross_investor_profit": row["gross_investor_profit"],
            "investor_loss_share": row["investor_loss_share"],
            "deal_profit_paid": row["deal_profit_paid"],
            "interim_paid": row["interim_paid"],
            "loss_offset_applied": row["loss_offset_applied"],
            "result_count": row["result_count"],
            "status": "CALCULATED_NOT_RECONCILED",
            "paid_status": "NOT_RECONCILED",
            "reconciliation_status": (
                "RECONCILED" if source_matches
                else "RESTATEMENT_REQUIRED" if latest
                else "NOT_RECONCILED"
            ),
            "confirmed_snapshot": (
                confirmed_snapshot(
                    latest,
                    current_position=current_position if not source_matches else None,
                ) if latest else None
            ),
        })
    current_period_keys = {
        (row["period_start"], row["period_end"]) for row in display_profit_periods
    }
    for key, latest in latest_by_period.items():
        if key in current_period_keys:
            continue
        display_profit_periods.append({
            "period_start": key[0],
            "period_end": key[1],
            "duration_months": latest.duration_months,
            "gross_investor_profit": format(latest.gross_investor_profit, ".2f"),
            "investor_loss_share": format(latest.investor_loss_share, ".2f"),
            "deal_profit_paid": format(latest.deal_profit_paid, ".2f"),
            "interim_paid": format(latest.interim_paid, ".2f"),
            "loss_offset_applied": format(latest.loss_offset_applied, ".2f"),
            "result_count": latest.result_count,
            "status": "SOURCE_REVIEW_REQUIRED",
            "paid_status": "NOT_RECONCILED",
            "reconciliation_status": "SOURCE_REVIEW_REQUIRED",
            "confirmed_snapshot": confirmed_snapshot(latest),
        })
    display_profit_periods.sort(key=lambda row: (row["period_start"], row["period_end"]))
    if has_manual_review:
        profit_period_status = "MANUAL_REVIEW_REQUIRED"
    elif not calendar_start:
        profit_period_status = "CALENDAR_NOT_AVAILABLE"
    elif not active_calendars and configured_calendars:
        profit_period_status = "CALENDAR_NOT_ACTIVE"
    elif unassigned_result_count or any(
        row["reconciliation_status"] == "SOURCE_REVIEW_REQUIRED"
        for row in display_profit_periods
    ):
        profit_period_status = "REVIEW_REQUIRED"
    elif any(row["reconciliation_status"] == "RESTATEMENT_REQUIRED" for row in display_profit_periods):
        profit_period_status = "RESTATEMENT_REQUIRED"
    elif display_profit_periods and all(
        row["reconciliation_status"] == "RECONCILED" for row in display_profit_periods
    ):
        profit_period_status = "RECONCILED"
    else:
        profit_period_status = "CALCULATED_NOT_RECONCILED"
    return {
        "investor_id": str(investor.pk),
        "name": investor.name,
        "binding_id": str(binding.pk),
        "fund_position": {
            "credit_total": None if has_manual_review else format(credit_total, ".2f"),
            "principal_return_total": None if has_manual_review else format(return_total, ".2f"),
            "committed_vehicle_total": None if has_manual_review else format(used_total, ".2f"),
            "use_adjustment_total": None if has_manual_review else format(use_adjustment_total, ".2f"),
            "ledger_available_amount": None if has_manual_review else format(available_ledger, ".2f"),
            "withdrawal_eligible": False,
            "status": "MANUAL_REVIEW_REQUIRED" if has_manual_review else "PHASE8_RECONCILIATION_REQUIRED",
        },
        "vehicles": vehicles,
        "interim": {
            "status": "CONFIGURED" if active_interim else "NOT_CONFIGURED",
            "monthly_amount": format(active_interim.amount, ".2f") if active_interim else None,
            "effective_date": active_interim.effective_date.isoformat() if active_interim else None,
            "payout_status": "NOT_RECONCILED",
        },
        "vehicle_results": latest_results,
        "profit_calendar": {
            "status": calendar_status,
            "start_date": calendar_start,
            "duration_months": calendar_duration,
            "source": calendar_source,
        },
        "profit_period_status": profit_period_status,
        "profit_periods": display_profit_periods,
        "unassigned_result_count": unassigned_result_count,
        "exit_requests": [_exit_request_data(row) for row in exit_requests],
    }


def _exit_request_data(row):
    from apps.investment.finance import _add_months

    # Exit requests are recorded in UTC; calendar-month arithmetic preserves
    # the original UTC time and clamps an unavailable month-end date.
    request_time = row.created_at.astimezone(datetime_timezone.utc)
    initial_date = _add_months(request_time.date(), 3)
    initial_deadline = request_time.replace(year=initial_date.year, month=initial_date.month, day=initial_date.day)
    extensions = list(row.notice_extensions.order_by("version", "id"))
    return {
        "id": str(row.pk),
        "status": row.status,
        "terms_version": row.terms_version,
        "terms_accepted_at": row.terms_accepted_at.isoformat(),
        "requested_at": row.created_at.isoformat(),
        "initial_notice_deadline": initial_deadline.isoformat(),
        "notice_deadline": (extensions[-1].deadline if extensions else initial_deadline).isoformat(),
        "notice_extensions": [{"id": str(item.pk), "version": item.version,
                               "previous_deadline": item.previous_deadline.isoformat(),
                               "deadline": item.deadline.isoformat(), "reason": item.reason,
                               "recorded_at": item.created_at.isoformat()} for item in extensions],
        "history": [
            {
                "version": event.version,
                "action": event.action,
                "previous_status": event.previous_status or None,
                "new_status": event.new_status,
                "reason": event.reason,
                "recorded_at": event.created_at.isoformat(),
            }
            for event in row.history.order_by("version", "id")
        ],
    }


def extend_exit_notice(*, actor, company_id, investor_id, exit_request_id, deadline, reason, key, path):
    reason = reason.strip()
    body = {"investor_id": str(investor_id), "exit_request_id": str(exit_request_id),
            "deadline": deadline.isoformat(), "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(tenant=company, pk=investor_id, is_active=True).first()
        if investor is None:
            raise NotFound("Investor Exit request not found.")
        request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, investor=investor, pk=exit_request_id,
            status__in=(InvestorExitRequest.Status.REQUESTED, InvestorExitRequest.Status.CANCELLATION_PENDING),
        ).first()
        if request is None:
            raise NotFound("Open Investor Exit request not found.")
        current = _exit_request_data(request)
        from django.utils.dateparse import parse_datetime
        previous = parse_datetime(current["notice_deadline"])
        if deadline <= previous:
            raise DomainConflict("The new deadline must be later than the current notice deadline.", code="EXIT_NOTICE_NOT_EXTENDED")
        extension = InvestorExitNoticeExtension.objects.create(
            tenant=company, exit_request=request, version=len(current["notice_extensions"]) + 1,
            previous_deadline=previous, deadline=deadline, reason=reason, actor=locked_actor,
            investment_module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(action="investment.exit.notice.extend", actor=locked_actor, subject=locked_actor,
                     company=company, resource=extension, reason=reason,
                     metadata={"exit_request_id": str(request.pk), "investor_id": str(investor.pk),
                               "extension_id": str(extension.pk), "version": extension.version,
                               "previous_deadline": previous.isoformat(), "deadline": deadline.isoformat()})
        return DomainMutationResult(201, {"id": str(extension.pk), "version": extension.version,
                                          "previous_deadline": previous.isoformat(),
                                          "deadline": extension.deadline.isoformat(), "reason": reason})

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.exit.notice.extend", module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def submit_exit_request(*, actor, company_id, key, path):
    body = {"terms_accepted": True, "terms_version": EXIT_TERMS_VERSION}

    def operation(company, _branch, _revisions, locked_actor):
        binding = _self_binding(actor=locked_actor, company=company)
        investor = Investor.objects.select_for_update().get(
            tenant=company, pk=binding.investor_id, is_active=True,
        )
        if InvestorExitRequest.objects.filter(
            tenant=company, investor=investor,
            status__in=(InvestorExitRequest.Status.REQUESTED,
                        InvestorExitRequest.Status.CANCELLATION_PENDING),
        ).exists():
            raise DomainConflict(
                "An open Exit request already exists for this Investor.",
                code="INVESTOR_EXIT_REQUEST_OPEN",
            )
        request = InvestorExitRequest.objects.create(
            tenant=company, investor=investor,
            status=InvestorExitRequest.Status.REQUESTED,
            terms_version=EXIT_TERMS_VERSION, requested_by=locked_actor,
            investment_module_revision=_revisions[CompanyModuleCode.INVESTMENT],
            portal_module_revision=_revisions[CompanyModuleCode.INVESTOR_PORTAL],
        )
        InvestorExitRequestHistory.objects.create(
            tenant=company, exit_request=request, version=1,
            action=InvestorExitRequestHistory.Action.SUBMITTED,
            new_status=request.status, actor=locked_actor,
        )
        record_event(
            action="investor.portal.exit.request", actor=locked_actor,
            subject=locked_actor, company=company, resource=request,
            metadata={"exit_request_id": str(request.pk),
                      "investor_id": str(investor.pk), "terms_version": EXIT_TERMS_VERSION,
                      "status": request.status},
        )
        return DomainMutationResult(201, _exit_request_data(request))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.portal.exit.request",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def request_exit_cancellation(*, actor, company_id, exit_request_id, reason="", key, path):
    reason = reason.strip()
    body = {"exit_request_id": str(exit_request_id), "reason": reason}

    def operation(company, _branch, _revisions, locked_actor):
        binding = _self_binding(actor=locked_actor, company=company)
        investor = Investor.objects.select_for_update().get(
            tenant=company, pk=binding.investor_id, is_active=True,
        )
        request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, pk=exit_request_id, investor=investor,
            status=InvestorExitRequest.Status.REQUESTED,
        ).first()
        if request is None:
            raise NotFound("Open Exit request not found.")
        version = request.history.aggregate(max_version=Max("version"))["max_version"] or 0
        InvestorExitRequest.objects.filter(pk=request.pk, tenant=company).update(
            status=InvestorExitRequest.Status.CANCELLATION_PENDING,
            updated_at=timezone.now(),
        )
        InvestorExitRequestHistory.objects.create(
            tenant=company, exit_request=request, version=version + 1,
            action=InvestorExitRequestHistory.Action.CANCELLATION_REQUESTED,
            previous_status=request.status,
            new_status=InvestorExitRequest.Status.CANCELLATION_PENDING,
            actor=locked_actor, reason=reason,
        )
        request.status = InvestorExitRequest.Status.CANCELLATION_PENDING
        record_event(
            action="investor.portal.exit.cancel_request", actor=locked_actor,
            subject=locked_actor, company=company, resource=request, reason=reason,
            metadata={"exit_request_id": str(request.pk),
                      "investor_id": str(investor.pk), "status": request.status},
        )
        return DomainMutationResult(200, _exit_request_data(request))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.portal.exit.request",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )


def review_exit_cancellation(
    *, actor, company_id, investor_id, exit_request_id, approve, reason="", key, path
):
    reason = reason.strip()
    body = {"investor_id": str(investor_id), "exit_request_id": str(exit_request_id),
            "approve": bool(approve), "reason": reason}

    def operation(company, _branch, _revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True,
        ).first()
        if investor is None:
            raise NotFound("Investor Exit request not found.")
        request = InvestorExitRequest.objects.select_for_update().filter(
            tenant=company, pk=exit_request_id, investor=investor,
            status=InvestorExitRequest.Status.CANCELLATION_PENDING,
        ).first()
        if request is None:
            raise NotFound("Pending cancellation request not found.")
        previous = request.status
        new_status = (
            InvestorExitRequest.Status.CANCELLED if approve
            else InvestorExitRequest.Status.REQUESTED
        )
        version = request.history.aggregate(max_version=Max("version"))["max_version"] or 0
        InvestorExitRequest.objects.filter(pk=request.pk, tenant=company).update(
            status=new_status, updated_at=timezone.now(),
        )
        InvestorExitRequestHistory.objects.create(
            tenant=company, exit_request=request, version=version + 1,
            action=(InvestorExitRequestHistory.Action.CANCELLATION_APPROVED if approve
                    else InvestorExitRequestHistory.Action.CANCELLATION_REJECTED),
            previous_status=previous, new_status=new_status,
            actor=locked_actor, reason=reason,
        )
        request.status = new_status
        record_event(
            action="investor.portal.exit.cancel_review", actor=locked_actor,
            subject=locked_actor, company=company, resource=request, reason=reason,
            metadata={"exit_request_id": str(request.pk),
                      "investor_id": str(investor.pk), "status": request.status},
        )
        return DomainMutationResult(200, _exit_request_data(request))

    return execute_domain_mutation(
        actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="investment.exit.cancel.review",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.INVESTOR_PORTAL),
        idempotency_model=InvestmentIdempotencyRecord, operation=operation,
    )
