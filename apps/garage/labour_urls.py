from django.urls import path
from apps.garage.views import LabourPaymentCorrectionView, LabourPaymentView, LabourPersonDetailView, LabourPersonListCreateView, LabourStatusView

urlpatterns = [
    path("people/", LabourPersonListCreateView.as_view(), name="person-list-create"),
    path("people/<uuid:person_id>/", LabourPersonDetailView.as_view(), name="person-detail"),
    path("people/<uuid:person_id>/status/", LabourStatusView.as_view(), name="person-status"),
    path("people/<uuid:person_id>/payments/", LabourPaymentView.as_view(), name="person-payments"),
    path("people/<uuid:person_id>/payments/<uuid:payment_id>/corrections/", LabourPaymentCorrectionView.as_view(), name="payment-corrections"),
]
