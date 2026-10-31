import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse

from .models import SessionActivity
from .session_security import session_digest, touch_activity


class ActiveAccountMiddleware:
    """Current account, epoch and bounded lifetime on API and operational Admin."""

    ALLOWED_PATHS = {
        "/api/v1/auth/csrf/",
        "/api/v1/auth/logout/",
        "/api/v1/auth/password/change/",
        "/api/v1/auth/me/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            now = int(time.time())
            issued = request.session.get("issued_at")
            key = request.session.session_key
            digest = session_digest(key) if key else ""
            lease = SessionActivity.objects.filter(key_hash=digest).first()
            last = lease.last_activity if lease else None
            valid = (
                lease is not None
                and user.is_active
                and request.session.get("auth_epoch") == user.auth_epoch
                and isinstance(issued, int)
                and isinstance(last, int)
                and 0 <= now - issued < settings.VIRMS_SESSION_ABSOLUTE_SECONDS
                and 0 <= now - lease.issued_at < settings.VIRMS_SESSION_ABSOLUTE_SECONDS
                and 0 <= now - last < settings.VIRMS_SESSION_IDLE_SECONDS
            )
            if not valid:
                logout(request)
                return JsonResponse({"detail": "Authentication required"}, status=401)
            if user.must_change_password and request.path not in self.ALLOWED_PATHS:
                return JsonResponse({"detail": "Password change required"}, status=403)
            if now - last >= 60:
                touch_activity(digest, now)
        return self.get_response(request)
