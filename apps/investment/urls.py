from django.urls import path

from apps.investment.views import (
    FundCreditListCreateView,
    FundCreditCorrectionCreateView,
    FundSummaryView,
    InvestorDetailView,
    InvestorInterimConfigurationView,
    InvestorListCreateView,
    PrincipalReturnListCreateView,
    Phase5BranchListView,
)

app_name = "investment"

urlpatterns = [
    path("branches/", Phase5BranchListView.as_view(), name="phase5-branch-list"),
    path("investors/", InvestorListCreateView.as_view(), name="investor-list-create"),
    path("investors/<uuid:investor_id>/", InvestorDetailView.as_view(), name="investor-detail"),
    path(
        "investors/<uuid:investor_id>/interim-configurations/",
        InvestorInterimConfigurationView.as_view(),
        name="investor-interim-configurations",
    ),
    path("fund/credits/", FundCreditListCreateView.as_view(), name="fund-credit-list-create"),
    path(
        "fund/credits/<uuid:credit_id>/corrections/",
        FundCreditCorrectionCreateView.as_view(),
        name="fund-credit-correction-create",
    ),
    path("fund/summary/", FundSummaryView.as_view(), name="fund-summary"),
    path(
        "fund/principal-returns/",
        PrincipalReturnListCreateView.as_view(),
        name="fund-principal-returns",
    ),
]
