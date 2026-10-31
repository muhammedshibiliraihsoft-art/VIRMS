"""PostgreSQL-backed login admission shared by identifier, source and service."""

import hashlib
import hmac
import ipaddress
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .login_id import canonical_login_id
from .models import LoginAttempt, User


def _key(kind, value):
    payload = f"{kind}:{value}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()


def _trusted(ip):
    try:
        address = ipaddress.ip_address(ip)
        return any(
            address in network for network in settings.VIRMS_TRUSTED_PROXY_NETWORKS
        )
    except ValueError:
        return False


def source_address(request):
    peer = request.META.get("REMOTE_ADDR", "")
    try:
        peer_ip = str(ipaddress.ip_address(peer))
    except ValueError:
        return "unknown"
    if not _trusted(peer_ip):
        return peer_ip
    chain = request.META.get(settings.VIRMS_FORWARDED_FOR_HEADER, "")
    if not chain:
        return peer_ip
    try:
        hops = [str(ipaddress.ip_address(part.strip())) for part in chain.split(",")]
    except ValueError:
        return peer_ip
    # Walk from the trusted immediate peer toward the client. Ignore any
    # attacker-supplied prefix to the left of the first untrusted hop.
    for hop in reversed(hops):
        if not _trusted(hop):
            return hop
    return hops[0] if hops else peer_ip


def admit_login(request, login_id):
    now = timezone.now()
    try:
        identity = canonical_login_id(login_id, allow_empty=True)
    except ValidationError:
        # Invalid Unicode and PostgreSQL's unsupported NUL character still
        # consume the shared source/global budget, without an identifier key.
        identity = ""
    buckets = [
        (
            _key("global", "all"),
            settings.VIRMS_LOGIN_GLOBAL_LIMIT,
            settings.VIRMS_LOGIN_GLOBAL_WINDOW_SECONDS,
        ),
        (
            _key("source", source_address(request)),
            settings.VIRMS_LOGIN_SOURCE_LIMIT,
            settings.VIRMS_LOGIN_SOURCE_WINDOW_SECONDS,
        ),
    ]
    if identity and User.objects.filter(login_id=identity).exists():
        buckets.append(
            (
                _key("identifier", identity),
                settings.VIRMS_LOGIN_IDENTIFIER_LIMIT,
                settings.VIRMS_LOGIN_IDENTIFIER_WINDOW_SECONDS,
            )
        )
    buckets.sort(key=lambda item: item[0])
    with transaction.atomic():
        rows_by_key = {}
        for key, _, _ in buckets:
            LoginAttempt.objects.get_or_create(key=key)
        rows_by_key = {
            row.key: row
            for row in LoginAttempt.objects.select_for_update()
            .filter(key__in=[item[0] for item in buckets])
            .order_by("key")
        }
        blocked_until = None
        for key, limit, window in buckets:
            row = rows_by_key[key]
            if row.failures >= limit and row.retry_after and row.retry_after > now:
                blocked_until = max(blocked_until or row.retry_after, row.retry_after)
            elif row.retry_after is None or row.retry_after <= now:
                if row.updated_at < now - timedelta(seconds=window):
                    row.failures = 0
                if row.failures >= limit:
                    row.retry_after = now + timedelta(seconds=window)
                    row.save(update_fields=["failures", "retry_after", "updated_at"])
                    blocked_until = max(
                        blocked_until or row.retry_after, row.retry_after
                    )
        if blocked_until:
            return False, max(1, int((blocked_until - now).total_seconds()))
        for key, _, window in buckets:
            row = rows_by_key[key]
            if row.updated_at < now - timedelta(seconds=window):
                row.failures = 0
            row.failures += 1
            row.retry_after = now + timedelta(seconds=window)
            row.save(update_fields=["failures", "retry_after", "updated_at"])
    return True, 0


def clear_identifier_budget(login_id):
    identity = canonical_login_id(login_id, allow_empty=True)
    if identity:
        LoginAttempt.objects.filter(key=_key("identifier", identity)).delete()
