import calendar
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext


PAISE = Decimal("0.01")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class VehicleShareAmounts:
    """Signed economic result split; this never represents a cash movement."""

    investor_share: Decimal
    company_share: Decimal


@dataclass(frozen=True)
class VehicleCapitalRecoverySuggestion:
    """Suggested classification of already-collected Sale cash, not a payment."""

    investor_principal: Decimal
    running_capital: Decimal
    remaining_after_capital: Decimal
    investor_principal_remaining: Decimal
    running_capital_remaining: Decimal


@dataclass(frozen=True)
class InvestorOnlyRefundReserve:
    principal_refund_due: Decimal
    reserve: Decimal
    uncovered: Decimal


def calculate_investor_only_refund_reserve(
    *, recovered_principal, principal_refunded, sale_applied, refund_payable, fund_balance,
):
    """Calculate a reserve from actual sources; creates no posting or allocation.

    This applies only when Investor principal is the Vehicle's sole capital
    source. The caller must separately resolve mixed funding and validate that
    all supplied figures are current and belong to the same Company/Investor.
    """
    values = []
    for raw in (recovered_principal, principal_refunded, sale_applied, refund_payable, fund_balance):
        if isinstance(raw, float):
            raise ValueError("Money must not use binary floating point.")
        try:
            value = Decimal(str(raw))
        except Exception as exc:
            raise ValueError("Money must be a finite nonnegative amount.") from exc
        if not value.is_finite() or value < 0:
            raise ValueError("Money must be a finite nonnegative amount.")
        values.append(value)
    with localcontext() as context:
        context.prec = max(80, *(len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 4 for value in values))
        recovered, refunded, applied, payable, held = (
            value.quantize(PAISE, rounding=ROUND_HALF_UP) for value in values
        )
        if refunded > recovered:
            raise ValueError("Principal already refunded cannot exceed recovered principal.")
        due = min(payable, max(Decimal("0.00"), recovered - refunded - applied))
        reserved = min(due, held)
        return InvestorOnlyRefundReserve(
            principal_refund_due=due, reserve=reserved, uncovered=due - reserved,
        )


@dataclass(frozen=True)
class OwnerDistributionAllocation:
    """Exact paise allocation in the protected recipient order."""

    recipient_id: str
    percentage: Decimal
    amount: Decimal


@dataclass(frozen=True)
class InvestorProfitPeriod:
    """Investor-specific inclusive date range for a Sale-date result."""

    start: str
    end: str
    duration_months: int


def _as_date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("Calendar dates must use ISO YYYY-MM-DD format.") from exc


def _add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def investor_profit_period_for_date(sale_date, calendar_versions):
    """Resolve a Sale date against append-only Investor calendar versions.

    Each calendar version becomes effective at a period boundary. Results
    before the first configured start date are deliberately left unassigned
    for Accountant review; this helper never invents a backdated calendar.
    """
    sale_date = _as_date(sale_date)
    by_start = {}
    for row in calendar_versions:
        effective_start = _as_date(row["effective_start"])
        duration_months = int(row["duration_months"])
        version = int(row.get("version", 1))
        if duration_months <= 0:
            raise ValueError("Profit period duration must be a positive number of months.")
        if version <= 0:
            raise ValueError("Profit calendar version must be positive.")
        existing = by_start.get(effective_start)
        if existing and existing[0] == version and existing[1] != duration_months:
            raise ValueError("A Profit calendar version cannot have conflicting durations.")
        if existing is None or version > existing[0]:
            by_start[effective_start] = (version, duration_months)
    versions = [
        (start, values[1]) for start, values in sorted(by_start.items())
    ]
    if not versions:
        return None

    for (previous_start, previous_months), (effective_start, _) in zip(versions, versions[1:]):
        elapsed_months = (effective_start.year - previous_start.year) * 12 + (
            effective_start.month - previous_start.month
        )
        if elapsed_months <= 0 or elapsed_months % previous_months:
            raise ValueError("A changed Investor calendar must start at a prior period boundary.")
        if _add_months(previous_start, elapsed_months) != effective_start:
            raise ValueError("A changed Investor calendar must start at a prior period boundary.")

    effective = None
    for row in versions:
        if row[0] > sale_date:
            break
        effective = row
    if effective is None:
        return None

    calendar_start, duration_months = effective
    elapsed_months = (sale_date.year - calendar_start.year) * 12 + (
        sale_date.month - calendar_start.month
    )
    period_index = elapsed_months // duration_months
    period_start = _add_months(calendar_start, period_index * duration_months)
    if period_start > sale_date:
        period_index -= 1
        period_start = _add_months(calendar_start, period_index * duration_months)
    next_start = _add_months(calendar_start, (period_index + 1) * duration_months)
    return InvestorProfitPeriod(
        start=period_start.isoformat(),
        end=(next_start - timedelta(days=1)).isoformat(),
        duration_months=duration_months,
    )


def summarize_investor_profit_periods(
    vehicle_results, calendar_versions, *, deal_profit_payments=(), interim_payments=(),
    loss_offsets=(),
):
    # Financial source columns support 38 digits; the default Decimal context
    # (28 digits) cannot safely quantize or aggregate those values.
    with localcontext() as context:
        context.prec = 80
        return _summarize_investor_profit_periods(
            vehicle_results, calendar_versions, deal_profit_payments=deal_profit_payments,
            interim_payments=interim_payments, loss_offsets=loss_offsets,
        )


def exact_money_difference(initial, *deductions):
    """Subtract monetary positions without rounding at the default precision."""
    with localcontext() as context:
        context.prec = 80
        result = Decimal(initial)
        for deduction in deductions:
            result -= Decimal(deduction)
        return result


def _summarize_investor_profit_periods(
    vehicle_results, calendar_versions, *, deal_profit_payments=(), interim_payments=(),
    loss_offsets=(),
):
    """Group only current, human-confirmed Vehicle results by Sale date.

    Gross Profit and Loss share remain separate. Only supplied, explicit
    confirmed payment and loss-offset records reduce the calculated unpaid
    figure; this function never authorizes payout or creates a confirmed
    reconciliation balance. Stale, undated, and pre-calendar results are
    returned as unassigned count for review rather than silently included.
    """
    periods = {}
    unassigned_count = 0
    result_dates = {}
    seen_payment_ids = set()
    seen_interim_payment_ids = set()

    def period_group(period):
        key = (period.start, period.end)
        return periods.setdefault(
            key,
            {
                "period_start": period.start,
                "period_end": period.end,
                "duration_months": period.duration_months,
                "gross_investor_profit": Decimal("0.00"),
                "investor_loss_share": Decimal("0.00"),
                "deal_profit_paid": Decimal("0.00"),
                "interim_paid": Decimal("0.00"),
                "loss_offset_applied": Decimal("0.00"),
                "result_count": 0,
                "sources": [],
                "status": "CALCULATED_NOT_RECONCILED",
                "paid_status": "NOT_RECONCILED",
            },
        )

    for row in vehicle_results:
        result_id = str(row.get("id") or "")
        sale_date = row.get("effective_sale_date")
        if result_id and sale_date:
            result_dates[result_id] = sale_date
        if row.get("status") != "CURRENT" or not sale_date:
            unassigned_count += 1
            continue
        period = investor_profit_period_for_date(
            sale_date, calendar_versions
        )
        if period is None:
            unassigned_count += 1
            continue

        kind = row.get("result_kind")
        amount = Decimal(row["investor_share_amount"]).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        if kind == "PROFIT" and amount >= 0:
            bucket = "gross_investor_profit"
            contribution = amount
        elif kind == "LOSS" and amount <= 0:
            bucket = "investor_loss_share"
            contribution = abs(amount)
        elif kind == "BREAK_EVEN" and amount == 0:
            bucket = None
            contribution = Decimal("0.00")
        else:
            raise ValueError("Confirmed result kind and signed Investor share disagree.")

        group = period_group(period)
        group["sources"].append({
            "kind": "VEHICLE_RESULT",
            "id": result_id,
            "source_version": str(row.get("source_version") or ""),
            "sale_date": str(sale_date),
            "result_kind": str(kind),
            "investor_share_amount": format(amount, ".2f"),
        })
        if bucket is not None:
            group[bucket] += contribution
        group["result_count"] += 1

    for payment in deal_profit_payments:
        payment_id = str(payment.get("id") or "")
        if payment_id and payment_id in seen_payment_ids:
            continue
        if payment_id:
            seen_payment_ids.add(payment_id)
        result_id = str(payment.get("vehicle_result_id") or "")
        sale_date = payment.get("effective_sale_date") or result_dates.get(result_id)
        if not sale_date:
            unassigned_count += 1
            continue
        period = investor_profit_period_for_date(sale_date, calendar_versions)
        if period is None:
            unassigned_count += 1
            continue
        amount = Decimal(payment["amount"]).quantize(PAISE, rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise ValueError("A confirmed Investor Profit payment must be positive.")
        group = period_group(period)
        group["sources"].append({
            "kind": "DEAL_PROFIT_PAYMENT",
            "id": payment_id,
            "result_id": result_id,
            "amount": format(amount, ".2f"),
            "effective_at": str(payment.get("effective_at") or ""),
        })
        group["deal_profit_paid"] += amount

    for payment in interim_payments:
        payment_id = str(payment.get("id") or "")
        if payment_id and payment_id in seen_interim_payment_ids:
            continue
        if payment_id:
            seen_interim_payment_ids.add(payment_id)
        paid_date = payment.get("effective_payment_date")
        if not paid_date:
            raw_effective_at = payment.get("effective_at")
            paid_date = str(raw_effective_at)[:10] if raw_effective_at else None
        if not paid_date:
            unassigned_count += 1
            continue
        period = investor_profit_period_for_date(paid_date, calendar_versions)
        if period is None:
            unassigned_count += 1
            continue
        amount = Decimal(payment["amount"]).quantize(PAISE, rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise ValueError("A confirmed Monthly Interim payment must be positive.")
        group = period_group(period)
        group["sources"].append({
            "kind": "INTERIM_PAYMENT",
            "id": payment_id,
            "amount": format(amount, ".2f"),
            "effective_payment_date": str(paid_date),
        })
        group["interim_paid"] += amount

    for offset in loss_offsets:
        if offset.get("valid_link") is False:
            unassigned_count += 1
            continue
        profit_result_id = str(offset.get("profit_result_id") or "")
        sale_date = offset.get("effective_sale_date") or result_dates.get(profit_result_id)
        if not sale_date:
            unassigned_count += 1
            continue
        period = investor_profit_period_for_date(sale_date, calendar_versions)
        if period is None:
            unassigned_count += 1
            continue
        amount = Decimal(offset["amount"]).quantize(PAISE, rounding=ROUND_HALF_UP)
        if amount <= 0:
            raise ValueError("A confirmed Investor Loss offset must be positive.")
        group = period_group(period)
        group["sources"].append({
            "kind": "LOSS_OFFSET",
            "id": str(offset.get("id") or ""),
            "loss_result_id": str(offset.get("loss_result_id") or ""),
            "profit_result_id": profit_result_id,
            "amount": format(amount, ".2f"),
        })
        group["loss_offset_applied"] += amount

    result = []
    for group in sorted(periods.values(), key=lambda row: row["period_start"]):
        gross = group["gross_investor_profit"]
        actual_paid = group["deal_profit_paid"]
        interim_paid = group["interim_paid"]
        total_paid = actual_paid + interim_paid
        settled = total_paid + group["loss_offset_applied"]
        source_payload = {
            "period_start": group["period_start"],
            "period_end": group["period_end"],
            "duration_months": group["duration_months"],
            "sources": sorted(
                group["sources"],
                key=lambda item: (item["kind"], item["id"], json.dumps(item, sort_keys=True)),
            ),
        }
        group["source_version"] = hashlib.sha256(
            json.dumps(source_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        group["calculated_unpaid_profit"] = max(Decimal("0.00"), gross - settled)
        group["historical_overpayment"] = max(Decimal("0.00"), settled - gross)
        if total_paid <= 0:
            group["paid_status"] = "NO_PAYMENT"
        elif total_paid < gross:
            group["paid_status"] = "PARTIALLY_PAID"
        elif total_paid == gross:
            group["paid_status"] = "PAID"
        else:
            group["paid_status"] = "OVERPAID_REVIEW_REQUIRED"
        result.append(
            {
                **group,
                "gross_investor_profit": format(group["gross_investor_profit"], ".2f"),
                "investor_loss_share": format(group["investor_loss_share"], ".2f"),
                "deal_profit_paid": format(group["deal_profit_paid"], ".2f"),
                "interim_paid": format(group["interim_paid"], ".2f"),
                "total_paid": format(total_paid, ".2f"),
                "loss_offset_applied": format(group["loss_offset_applied"], ".2f"),
                "calculated_unpaid_profit": format(group["calculated_unpaid_profit"], ".2f"),
                "historical_overpayment": format(group["historical_overpayment"], ".2f"),
                "source_version": group["source_version"],
            }
        )
    return result, unassigned_count


def calculate_vehicle_shares(*, result, investor_percentage):
    """Split a confirmed Vehicle result without losing or creating a paise.

    Positive result is an entitlement suggestion. Negative result is a loss
    allocation suggestion and still requires the separately approved manual
    confirmation workflow.
    """
    raw_result = Decimal(result)
    if not raw_result.is_finite():
        raise ValueError("Vehicle result must be finite.")
    percentage = Decimal(investor_percentage) if investor_percentage is not None else None
    if percentage is not None and (not percentage.is_finite() or percentage < 0 or percentage > HUNDRED):
        raise ValueError("Investor share percentage must be between 0 and 100.")
    with localcontext() as context:
        context.prec = max(60, len(raw_result.as_tuple().digits) + (len(percentage.as_tuple().digits) if percentage is not None else 0) + 8)
        result = raw_result.quantize(PAISE, rounding=ROUND_HALF_UP)
        if percentage is None:
            return VehicleShareAmounts(Decimal("0.00"), result)
        magnitude = (abs(result) * percentage / HUNDRED).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        investor_share = magnitude if result >= 0 else -magnitude
        company_share = result - investor_share
        return VehicleShareAmounts(investor_share, company_share)


def suggest_vehicle_capital_recovery(
    *, receipt_amount, investor_principal_outstanding, running_capital_outstanding,
    mixed_funding, sale_fully_collected,
):
    """Apply actual Vehicle Sale cash to capital in the approved order.

    Mixed funding requires full collection before a recovery suggestion.
    Investor principal is suggested first, followed by the Vehicle-linked
    Company Running Capital. Any remaining receipt is deliberately left
    unclassified here; this helper creates no Fund, Accounting, Profit, or cash
    record and grants no permission to confirm a recovery.
    """

    def money(value, name):
        if isinstance(value, float):
            raise ValueError(f"{name} must not be supplied as a binary float.")
        try:
            raw = Decimal(str(value))
            if not raw.is_finite() or raw < 0:
                raise ValueError(f"{name} must be a finite nonnegative INR amount.")
            with localcontext() as context:
                context.prec = max(60, len(raw.as_tuple().digits) + abs(raw.as_tuple().exponent) + 4)
                amount = raw.quantize(PAISE, rounding=ROUND_HALF_UP)
        except Exception as exc:
            raise ValueError(f"{name} must be a valid INR amount.") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError(f"{name} must be a finite nonnegative INR amount.")
        return amount

    if not isinstance(mixed_funding, bool) or not isinstance(sale_fully_collected, bool):
        raise ValueError("Funding and collection status must be explicitly verified.")
    if mixed_funding and not sale_fully_collected:
        raise ValueError("Mixed-funded Vehicle recovery requires full Sale collection.")

    receipt = money(receipt_amount, "receipt_amount")
    investor_outstanding = money(
        investor_principal_outstanding, "investor_principal_outstanding"
    )
    running_outstanding = money(
        running_capital_outstanding, "running_capital_outstanding"
    )

    with localcontext() as context:
        context.prec = max(60, *(len(value.as_tuple().digits) + 4 for value in (
            receipt, investor_outstanding, running_outstanding
        )))
        investor_recovery = min(receipt, investor_outstanding)
        remaining_receipt = receipt - investor_recovery
        running_recovery = min(remaining_receipt, running_outstanding)
        remaining_after_capital = remaining_receipt - running_recovery

        return VehicleCapitalRecoverySuggestion(
            investor_principal=investor_recovery,
            running_capital=running_recovery,
            remaining_after_capital=remaining_after_capital,
            investor_principal_remaining=investor_outstanding - investor_recovery,
            running_capital_remaining=running_outstanding - running_recovery,
        )


def allocate_owner_distribution(*, amount, recipients):
    """Allocate a confirmed Company pool exactly to configured recipients.

    Provisional allocations use ROUND_HALF_UP. Any residual paisa is assigned
    one at a time to the most under/over-allocated recipient, with configured
    order as the stable tie-break. This is arithmetic only; it authorizes or
    records no distribution or payment.
    """

    def decimal_value(value, field):
        if isinstance(value, float):
            raise ValueError(f"{field} must not be supplied as a binary float.")
        try:
            result = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"{field} must be a valid decimal amount.") from exc
        if not result.is_finite():
            raise ValueError(f"{field} must be finite.")
        return result

    raw_total = decimal_value(amount, "amount")
    if raw_total < 0:
        raise ValueError("Owner distribution amount must not be negative.")
    with localcontext() as context:
        context.prec = max(60, len(raw_total.as_tuple().digits) + 4)
        total = raw_total.quantize(PAISE, rounding=ROUND_HALF_UP)
    if not isinstance(recipients, (list, tuple)) or not recipients:
        raise ValueError("At least one configured distribution recipient is required.")

    normalized = []
    seen = set()
    for row in recipients:
        if not isinstance(row, dict):
            raise ValueError("Each recipient must contain an ID and percentage.")
        recipient_id = str(row.get("id") or "").strip()
        if not recipient_id or recipient_id in seen:
            raise ValueError("Recipient IDs must be present and unique.")
        seen.add(recipient_id)
        percentage = decimal_value(row.get("percentage"), "percentage")
        if percentage < 0 or percentage > HUNDRED:
            raise ValueError("Recipient percentages must be between 0 and 100.")
        normalized.append((recipient_id, percentage))
    if sum((percentage for _, percentage in normalized), Decimal("0")) != HUNDRED:
        raise ValueError("Configured Owner percentages must sum to exactly 100.")

    with localcontext() as context:
        context.prec = max(60, len(total.as_tuple().digits) + 20)
        raw = [total * percentage / HUNDRED for _, percentage in normalized]
        allocations = [value.quantize(PAISE, rounding=ROUND_HALF_UP) for value in raw]
        residual = total - sum(allocations, Decimal("0.00"))

        while residual != 0:
            differences = [allocations[index] - raw[index] for index in range(len(raw))]
            if residual > 0:
                eligible = [index for index in range(len(raw))]
                chosen = min(eligible, key=lambda index: (differences[index], index))
                allocations[chosen] += PAISE
                residual -= PAISE
            else:
                eligible = [
                    index for index, allocation in enumerate(allocations)
                    if allocation >= PAISE
                ]
                if not eligible:
                    raise ValueError("Exact allocation would require a negative recipient amount.")
                chosen = max(eligible, key=lambda index: (differences[index], -index))
                allocations[chosen] -= PAISE
                residual += PAISE

    return [
        OwnerDistributionAllocation(
            recipient_id=recipient_id,
            percentage=percentage,
            amount=allocations[index],
        )
        for index, (recipient_id, percentage) in enumerate(normalized)
    ]
