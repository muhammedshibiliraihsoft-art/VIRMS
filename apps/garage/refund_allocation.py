"""Arithmetic shared by the future Customer Job refund posting contract.

This module does not post money, choose an excess destination or authorize a
refund. Callers must obtain the current figures under the Job transaction lock.
"""

from decimal import Decimal, localcontext


def split_customer_cost_refund(amount: Decimal, paid: Decimal, applied_refunds: Decimal) -> tuple[Decimal, Decimal]:
    """Return the cost-applied and separately allocated parts of actual cash."""
    values = (amount, paid, applied_refunds)
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in values):
        raise ValueError("Refund amounts must be finite Decimal values.")
    with localcontext() as context:
        context.prec = max(40, *(len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 2 for value in values))
        if any(value != value.quantize(Decimal('0.01')) for value in values):
            raise ValueError("Refund amounts must have at most two decimal places.")
        if amount <= 0 or paid < 0 or applied_refunds < 0 or applied_refunds > paid:
            raise ValueError("Refund or prior payment amounts are invalid.")
        applied = min(amount, paid - applied_refunds)
        return applied, amount - applied
