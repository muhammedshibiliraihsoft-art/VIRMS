import json
import logging

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from apps.tenants.selectors import company_context, current_interval

from .login_admission import admit_login, clear_identifier_budget
from .login_id import canonical_login_id
from .models import RoleAssignment, User

logger = logging.getLogger(__name__)


def body_data(request, *, max_bytes=None):
    try:
        body = request.body
        if max_bytes is not None and len(body) > max_bytes:
            return None
        value = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def login_content_length_is_bounded(request):
    try:
        length = int(request.META.get("CONTENT_LENGTH", ""))
    except (TypeError, ValueError):
        return False
    return 0 < length <= 8192


@never_cache
@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


@never_cache
@csrf_protect
@require_POST
def login_view(request):
    if not login_content_length_is_bounded(request):
        return JsonResponse({"detail": "Invalid request"}, status=400)
    data = body_data(request, max_bytes=8192)
    if data is None:
        return JsonResponse({"detail": "Invalid request"}, status=400)
    login_id = data.get("login_id")
    password = data.get("password")
    if not isinstance(login_id, str) or not isinstance(password, str):
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    admitted, retry_after = admit_login(request, login_id)
    if not admitted:
        response = JsonResponse({"detail": "Too many attempts. Try later"}, status=429)
        response["Retry-After"] = str(retry_after)
        return response
    try:
        login_id = canonical_login_id(login_id, allow_empty=True)
    except ValidationError:
        login_id = ""
    if not login_id:
        logger.warning("Login failed")
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    user = authenticate(request, username=login_id, password=password)
    if user is None or not user.is_active:
        logger.warning("Login failed")
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    clear_identifier_budget(login_id)
    login(request, user)
    return JsonResponse({"must_change_password": user.must_change_password})


@never_cache
@csrf_protect
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Signed out"})


@never_cache
@require_GET
def me_view(request):
    user = request.user
    if not user.is_authenticated or not user.is_active:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    companies, truncated = company_context(user)
    roles = {role for company in companies for role in company["roles"]}
    if (
        user.account_kind == User.AccountKind.PLATFORM
        and RoleAssignment.objects.filter(user=user, role="back_office")
        .filter(current_interval())
        .exists()
    ):
        roles.add(RoleAssignment.Role.BACK_OFFICE)
    return JsonResponse(
        {
            "id": str(user.pk),
            "login_id": user.login_id,
            "must_change_password": user.must_change_password,
            "roles": sorted(roles),
            "tenant_ids": sorted(company["id"] for company in companies),
            "companies": companies,
            "company_context_truncated": truncated,
        }
    )


@never_cache
@csrf_protect
@require_POST
def change_password_view(request):
    user = request.user
    if not user.is_authenticated or not user.is_active:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    data = body_data(request)
    if data is None:
        return JsonResponse({"detail": "Invalid request"}, status=400)
    from django.core.exceptions import PermissionDenied

    from .passwords import change_private_password

    try:
        change_private_password(
            request,
            current_password=data.get("current_password"),
            new_password=data.get("new_password"),
            confirmation=data.get("confirm_password"),
        )
    except PermissionDenied:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    except ValidationError as error:
        return JsonResponse({"errors": error.messages}, status=400)
    return JsonResponse({"detail": "Password changed"})
