from django.contrib import admin
from django.urls import include, path

from apps.accounts.admin_password import VIRMSAdminPasswordChangeView
from core.health import live, ready

handler403 = "core.http.handler403"
handler404 = "core.http.handler404"
handler500 = "core.http.handler500"

urlpatterns = [
    path(
        "admin/password_change/",
        admin.site.admin_view(VIRMSAdminPasswordChangeView.as_view()),
    ),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/tenants/", include("apps.tenants.urls")),
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
]
