import json
import uuid

from django.http import JsonResponse


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        raw = request.headers.get("X-Request-ID", "")
        try:
            request.request_id = str(uuid.UUID(raw))
        except (ValueError, TypeError, AttributeError):
            request.request_id = str(uuid.uuid4())
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if request.path.startswith("/api/v1/") and response.status_code >= 400:
            content_type = response.get("Content-Type", "")
            if "application/json" in content_type:
                try:
                    payload = json.loads(response.content)
                except (ValueError, UnicodeDecodeError):
                    payload = None
            else:
                payload = None
            if not isinstance(payload, dict):
                payload = {
                    "detail": {
                        400: "Invalid request",
                        401: "Authentication required",
                        403: "Not authorized",
                        404: "Not found",
                        405: "Method not allowed",
                        409: "Conflict",
                        429: "Too many requests",
                    }.get(
                        response.status_code,
                        (
                            "Service unavailable"
                            if response.status_code == 503
                            else "Request failed"
                        ),
                    ),
                    "code": f"http_{response.status_code}",
                }
            else:
                payload.setdefault("code", f"http_{response.status_code}")
            payload["request_id"] = request.request_id
            normalized = JsonResponse(payload, status=response.status_code)
            # Keep security and protocol headers set by the view, including
            # no-store on one-time credentials and Retry-After on throttles.
            for name, value in response.items():
                if name.lower() not in {
                    "content-type",
                    "content-length",
                    "x-request-id",
                }:
                    normalized[name] = value
            normalized.cookies.update(response.cookies)
            response = normalized
            response["X-Request-ID"] = request.request_id
        return response


def api_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)
    if response is None:
        return None
    request = context.get("request")
    request_id = getattr(request, "request_id", None)
    if isinstance(response.data, dict):
        response.data.setdefault("request_id", request_id)
        response.data.setdefault("code", f"http_{response.status_code}")
    else:
        response.data = {
            "detail": "Request failed",
            "code": f"http_{response.status_code}",
            "request_id": request_id,
        }
    if request_id:
        response["X-Request-ID"] = request_id
    return response


def api_error(request, status, detail, code):
    request_id = getattr(request, "request_id", str(uuid.uuid4()))
    response = JsonResponse(
        {"detail": detail, "code": code, "request_id": request_id}, status=status
    )
    response["X-Request-ID"] = request_id
    return response


def handler404(request, exception):
    if request.path.startswith("/api/v1/"):
        return api_error(request, 404, "Not found", "http_404")
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)


def handler403(request, exception):
    if request.path.startswith("/api/v1/"):
        return api_error(request, 403, "Not authorized", "http_403")
    from django.views.defaults import permission_denied

    return permission_denied(request, exception)


def handler500(request):
    if request.path.startswith("/api/v1/"):
        return api_error(request, 500, "Request failed", "http_500")
    from django.views.defaults import server_error

    return server_error(request)
