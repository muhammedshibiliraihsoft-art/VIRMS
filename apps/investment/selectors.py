from django.db.models import F, OuterRef, Subquery, UUIDField
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
