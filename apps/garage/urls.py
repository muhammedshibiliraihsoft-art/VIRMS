from django.urls import path
from apps.garage.views import GarageReceiptCorrectionView, JobCustomerChargeView, JobCustomerCostCorrectionView, JobCustomerCostPaymentCorrectionView, JobCustomerCostPaymentView, JobCustomerCostRefundPreviewView, JobCustomerCostRefundView, JobCustomerCostView, JobCustomerReceiptView, JobDetailView, JobListCreateView, JobStatusHistoryView, JobStatusView, JobStockCostCreateView, JobStockCostView, JobWorkView

urlpatterns = [
    path("jobs/", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/<uuid:job_id>/", JobDetailView.as_view(), name="job-detail"),
    path("jobs/<uuid:job_id>/work/", JobWorkView.as_view(), name="job-work"),
    path("jobs/<uuid:job_id>/charges/", JobCustomerChargeView.as_view(), name="job-customer-charge"),
    path("jobs/<uuid:job_id>/customer-costs/", JobCustomerCostView.as_view(), name="job-customer-costs"),
    path("jobs/<uuid:job_id>/customer-costs/<uuid:cost_id>/corrections/", JobCustomerCostCorrectionView.as_view(), name="job-customer-cost-correction"),
    path("jobs/<uuid:job_id>/customer-costs/<uuid:cost_id>/payments/", JobCustomerCostPaymentView.as_view(), name="job-customer-cost-payments"),
    path("jobs/<uuid:job_id>/customer-costs/<uuid:cost_id>/refund-preview/", JobCustomerCostRefundPreviewView.as_view(), name="job-customer-cost-refund-preview"),
    path("jobs/<uuid:job_id>/customer-costs/<uuid:cost_id>/refunds/", JobCustomerCostRefundView.as_view(), name="job-customer-cost-refunds"),
    path("jobs/<uuid:job_id>/customer-costs/<uuid:cost_id>/payments/<uuid:payment_id>/corrections/", JobCustomerCostPaymentCorrectionView.as_view(), name="job-customer-cost-payment-corrections"),
    path("jobs/<uuid:job_id>/receipts/", JobCustomerReceiptView.as_view(), name="job-customer-receipt"),
    path("jobs/<uuid:job_id>/receipts/<uuid:receipt_id>/corrections/", GarageReceiptCorrectionView.as_view(), name="job-receipt-corrections"),
    path("jobs/<uuid:job_id>/stock-costs/", JobStockCostView.as_view(), name="job-stock-costs"),
    path("jobs/<uuid:job_id>/stock-costs/create/", JobStockCostCreateView.as_view(), name="job-stock-cost-create"),
    path("jobs/<uuid:job_id>/status-history/", JobStatusHistoryView.as_view(), name="job-status-history"),
    path("jobs/<uuid:job_id>/status/", JobStatusView.as_view(), name="job-status"),
]
