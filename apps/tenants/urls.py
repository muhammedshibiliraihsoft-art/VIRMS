from django.urls import path

from .views import TenantDetail, TenantList

urlpatterns = [
    path("", TenantList.as_view(), name="tenant-list"),
    path("<uuid:pk>/", TenantDetail.as_view(), name="tenant-detail"),
]
