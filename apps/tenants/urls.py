from django.urls import include, path

from apps.accounting.urls import urlpatterns as accounting_urlpatterns
from apps.investment.urls import urlpatterns as investment_urlpatterns
from apps.garage.urls import urlpatterns as garage_urlpatterns
from apps.garage.labour_urls import urlpatterns as labour_urlpatterns
from apps.vehicles.urls import urlpatterns as vehicle_management_urlpatterns

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

urlpatterns += [
    path("<uuid:company_id>/garage/", include((garage_urlpatterns, "garage"))),
    path("<uuid:company_id>/labour/", include((labour_urlpatterns, "labour"))),
    path(
        "<uuid:company_id>/accounting/",
        include((accounting_urlpatterns, "accounting")),
    ),
    path(
        "<uuid:company_id>/investment/",
        include((investment_urlpatterns, "investment")),
    ),
    path(
        "<uuid:company_id>/vehicle-management/",
        include((vehicle_management_urlpatterns, "vehicle-management")),
    ),
]
