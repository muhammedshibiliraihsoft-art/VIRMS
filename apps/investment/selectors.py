from django.db.models import DecimalField, F, Func, OuterRef, Subquery, UUIDField
from django.db.models.functions import Coalesce

from apps.investment.models import InvestorFundCredit, InvestorFundCreditCorrection


def with_current_fund_credit_owner(queryset=None):
    """Annotate each immutable credit with its latest audited Investor attribution."""
    queryset = queryset if queryset is not None else InvestorFundCredit.objects.all()
    latest_owner = (
        InvestorFundCreditCorrection.objects.filter(credit_id=OuterRef("pk"))
        .order_by("-version", "-id")
        .values("to_investor_id")[:1]
    )
    return queryset.annotate(
        current_investor_id=Coalesce(
            Subquery(latest_owner), F("investor_id"), output_field=UUIDField()
        )
    )


def with_fund_credit_available(queryset):
    """Annotate each lot with its reserve-aware database position.

    A NULL position means reconciliation is required and must not be treated
    as an available zero or authorized for spending.
    """
    return queryset.annotate(
        fund_available=Func(
            F("pk"), function="investment_credit_available",
            output_field=DecimalField(max_digits=38, decimal_places=2),
        )
    )
