"""Pure Company finance calculations; these functions do not post records."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


@dataclass(frozen=True)
class CompanyPeriodCarryforward:
    loss_carried_forward: Decimal
    positive_after_loss: Decimal


def calculate_company_period_carryforward(*, period_result, prior_loss):
    """Calculate a provisional balance, not a confirmed distributable pool.

    ``prior_loss`` is the nonnegative magnitude of the prior carried Loss.
    An Accountant must separately review liabilities and confirm any amount.
    """
    def money(value):
        if isinstance(value, float):
            raise ValueError("Money must not use a binary float.")
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Money must be a finite decimal amount.") from exc
        if not amount.is_finite():
            raise ValueError("Money must be a finite decimal amount.")
        return amount

    result = money(period_result)
    loss = money(prior_loss)
    if loss < 0:
        raise ValueError("Prior Loss must be a nonnegative amount.")
    with localcontext() as context:
        context.prec = max(80, len(result.as_tuple().digits) + 4, len(loss.as_tuple().digits) + 4)
        result = result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        loss = loss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net = result - loss
        return CompanyPeriodCarryforward(
            loss_carried_forward=max(Decimal("0.00"), -net),
            positive_after_loss=max(Decimal("0.00"), net),
        )
