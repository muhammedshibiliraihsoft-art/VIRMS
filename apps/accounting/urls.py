from django.urls import path

from .views import (
    AccountingBranchListView,
    AccountingMonthlyTrendView,
    AccountingResultView,
    AccountArchiveView,
    AccountListCreateView,
    ApplicationReallocationView,
    CategoryArchiveView,
    CategoryListCreateView,
    CompanyPeriodConfirmationView,
    OwnerDistributionConfigurationView,
    OwnerDistributionPaymentView,
    EventCorrectionView,
    EventDetailView,
    EventListView,
    ExpenseListCreateView,
    IncomeListCreateView,
    OpeningBalanceCorrectionView,
    OpeningBalanceView,
    PaymentCorrectionView,
    PaymentListCreateView,
    ReceiptCorrectionView,
    ReceiptListCreateView,
    TransferCorrectionView,
    TransferReversalView,
    TransferView,
)

app_name = "accounting"

urlpatterns = [
    path("reports/accounting-monthly-trend/", AccountingMonthlyTrendView.as_view(), name="accounting-monthly-trend"),
    path("branches/", AccountingBranchListView.as_view(), name="accounting-branch-list"),
    path("accounts/", AccountListCreateView.as_view(), name="account-list-create"),
    path(
        "accounts/<uuid:account_id>/",
        AccountArchiveView.as_view(),
        name="account-archive",
    ),
    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path(
        "categories/<uuid:category_id>/",
        CategoryArchiveView.as_view(),
        name="category-archive",
    ),
    path("events/", EventListView.as_view(), name="event-list"),
    path("events/<uuid:event_id>/", EventDetailView.as_view(), name="event-detail"),
    path(
        "events/<uuid:event_id>/corrections/",
        EventCorrectionView.as_view(),
        name="event-correct",
    ),
    path("incomes/", IncomeListCreateView.as_view(), name="income-create"),
    path("expenses/", ExpenseListCreateView.as_view(), name="expense-create"),
    path("receipts/", ReceiptListCreateView.as_view(), name="receipt-create"),
    path(
        "receipts/<uuid:event_id>/corrections/",
        ReceiptCorrectionView.as_view(),
        name="receipt-correct",
    ),
    path("payments/", PaymentListCreateView.as_view(), name="payment-create"),
    path(
        "payments/<uuid:event_id>/corrections/",
        PaymentCorrectionView.as_view(),
        name="payment-correct",
    ),
    path("opening-balances/", OpeningBalanceView.as_view(), name="opening-balance-create"),
    path(
        "opening-balances/<uuid:event_id>/corrections/",
        OpeningBalanceCorrectionView.as_view(),
        name="opening-balance-correct",
    ),
    path("transfers/", TransferView.as_view(), name="transfer-create"),
    path(
        "transfers/<uuid:event_id>/reversals/",
        TransferReversalView.as_view(),
        name="transfer-reverse",
    ),
    path(
        "transfers/<uuid:event_id>/corrections/",
        TransferCorrectionView.as_view(),
        name="transfer-correct",
    ),
    path(
        "applications/<uuid:application_id>/reallocations/",
        ApplicationReallocationView.as_view(),
        name="application-reallocate",
    ),
    path(
        "reports/accounting-result/",
        AccountingResultView.as_view(),
        name="accounting-result",
    ),
    path("company-period-confirmations/", CompanyPeriodConfirmationView.as_view(), name="company-period-confirmations"),
    path("owner-distribution-configurations/", OwnerDistributionConfigurationView.as_view(), name="owner-distribution-configurations"),
    path("company-period-confirmations/<uuid:confirmation_id>/owner-payments/", OwnerDistributionPaymentView.as_view(), name="company-period-owner-payment"),
]
