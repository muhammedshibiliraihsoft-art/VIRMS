import hashlib
import hmac
import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .access import active_roles, active_tenant_ids
from .models import AccountSecurityEvent, LoginAttempt

logger = logging.getLogger(__name__)


def body_data(request):
    try:
        value = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def attempt_key(login_id):
    identifier = login_id.casefold()
    return hmac.new(
        settings.SECRET_KEY.encode(), identifier.encode(), hashlib.sha256
    ).hexdigest()


def is_throttled(key):
    attempt = LoginAttempt.objects.filter(key=key).first()
    return bool(
        attempt and attempt.retry_after and attempt.retry_after > timezone.now()
    )


def note_failure(key):
    with transaction.atomic():
        attempt, _ = LoginAttempt.objects.get_or_create(key=key)
        attempt = LoginAttempt.objects.select_for_update().get(pk=attempt.pk)
        attempt.failures += 1
        if attempt.failures >= 3:
            seconds = min(300, 2 ** min(attempt.failures - 2, 8))
            attempt.retry_after = timezone.now() + timedelta(seconds=seconds)
        attempt.save(update_fields=["failures", "retry_after", "updated_at"])


@ensure_csrf_cookie
@require_GET
def csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


@csrf_protect
@require_POST
def login_view(request):
    data = body_data(request)
    if data is None:
        return JsonResponse({"detail": "Invalid request"}, status=400)
    login_id = data.get("login_id")
    password = data.get("password")
    if not isinstance(login_id, str) or not isinstance(password, str):
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    key = attempt_key(login_id)
    if is_throttled(key):
        return JsonResponse({"detail": "Too many attempts. Try later"}, status=429)
    user = authenticate(request, username=login_id, password=password)
    if user is None or not user.is_active:
        note_failure(key)
        logger.warning("Login failed for hashed attempt key %s", key)
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
    LoginAttempt.objects.filter(key=key).delete()
    login(request, user)
    return JsonResponse({"must_change_password": user.must_change_password})


@csrf_protect
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Signed out"})


@require_GET
def me_view(request):
    user = request.user
    if not user.is_authenticated or not user.is_active:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    return JsonResponse(
        {
            "id": str(user.pk),
            "login_id": user.login_id,
            "must_change_password": user.must_change_password,
            "roles": sorted(active_roles(user)),
            "tenant_ids": sorted(str(value) for value in active_tenant_ids(user)),
        }
    )


@csrf_protect
@require_POST
def change_password_view(request):
    user = request.user
    if not user.is_authenticated or not user.is_active:
        return JsonResponse({"detail": "Authentication required"}, status=401)
    data = body_data(request)
    if data is None:
        return JsonResponse({"detail": "Invalid request"}, status=400)
    current = data.get("current_password")
    new = data.get("new_password")
    confirmation = data.get("confirm_password")
    if not isinstance(current, str) or not user.check_password(current):
        return JsonResponse({"detail": "Current password is incorrect"}, status=400)
    if not isinstance(new, str) or new != confirmation:
        return JsonResponse({"detail": "New passwords do not match"}, status=400)
    try:
        validate_password(new, user)
    except ValidationError as error:
        return JsonResponse({"errors": error.messages}, status=400)
    user.set_password(new)
    user.must_change_password = False
    with transaction.atomic():
        user.save(update_fields=["password", "must_change_password", "updated_at"])
        AccountSecurityEvent.objects.create(
            actor=user, subject=user, action="change_password", tenant_ids=[]
        )
    update_session_auth_hash(request, user)
    return JsonResponse({"detail": "Password changed"})
