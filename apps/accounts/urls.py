from django.urls import path

from .auth_views import change_password_view, csrf, login_view, logout_view, me_view
from .views import (
    provision_account,
    reset_account_password,
    revoke_account_sessions_view,
    set_account_active,
)

urlpatterns = [
    path("csrf/", csrf, name="auth-csrf"),
    path("login/", login_view, name="auth-login"),
    path("logout/", logout_view, name="auth-logout"),
    path("me/", me_view, name="auth-me"),
    path("password/change/", change_password_view, name="auth-password-change"),
    path("accounts/provision/", provision_account, name="account-provision"),
    path(
        "accounts/<uuid:user_id>/reset/", reset_account_password, name="account-reset"
    ),
    path("accounts/<uuid:user_id>/status/", set_account_active, name="account-status"),
    path(
        "accounts/<uuid:user_id>/revoke/",
        revoke_account_sessions_view,
        name="account-revoke",
    ),
]
