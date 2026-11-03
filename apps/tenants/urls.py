from django.urls import path

from .views import CompanyBranchDetail, CompanyBranchList, TenantDetail, TenantList
from .views.module_state import CompanyModuleStatesView

urlpatterns = [
    path("", TenantList.as_view(), name="tenant-list"),
    path("<uuid:pk>/", TenantDetail.as_view(), name="tenant-detail"),
    path(
        "<uuid:company_id>/module-state/",
        CompanyModuleStatesView.as_view(),
        name="company-module-state",
    ),
    path(
        "<uuid:company_id>/branches/",
        CompanyBranchList.as_view(),
        name="company-branch-list",
    ),
    path(
        "<uuid:company_id>/branches/<uuid:pk>/",
        CompanyBranchDetail.as_view(),
        name="company-branch-detail",
    ),
]
