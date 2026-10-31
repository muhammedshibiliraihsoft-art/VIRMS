from django.http import JsonResponse


class ActiveAccountMiddleware:
    """Enforce first-login credential replacement across current and future APIs."""

    ALLOWED_PATHS = {
        "/api/v1/auth/csrf/",
        "/api/v1/auth/login/",
        "/api/v1/auth/logout/",
        "/api/v1/auth/password/change/",
        "/api/v1/auth/me/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if request.path.startswith("/api/") and user.is_authenticated:
            if not user.is_active:
                return JsonResponse({"detail": "Authentication required"}, status=401)
            if user.must_change_password and request.path not in self.ALLOWED_PATHS:
                return JsonResponse({"detail": "Password change required"}, status=403)
        return self.get_response(request)
