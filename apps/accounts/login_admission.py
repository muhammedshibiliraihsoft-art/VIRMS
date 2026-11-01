"""PostgreSQL-backed login admission shared by identifier, source and service."""

import hashlib
import hmac
import ipaddress
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .login_id import canonical_login_id
from .models import LoginAttempt


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


def prune_expired_attempts(batch_size=500):
    """Lock eligible rows through deletion; never delete refreshed/in-flight state."""
    from django.db.models import Q

    now = timezone.now()
    retention = max(
        settings.VIRMS_LOGIN_GLOBAL_WINDOW_SECONDS,
        settings.VIRMS_LOGIN_SOURCE_WINDOW_SECONDS,
        settings.VIRMS_LOGIN_IDENTIFIER_WINDOW_SECONDS,
    )
    with transaction.atomic():
        rows = list(
            LoginAttempt.objects.select_for_update(skip_locked=True)
            .filter(
                Q(retry_after__lt=now) | Q(retry_after__isnull=True),
                updated_at__lt=now - timedelta(seconds=retention),
            )
            .exclude(key=_key("global", "all"))
            .order_by("updated_at", "id")
            .values_list("pk", flat=True)[:batch_size]
        )
        return LoginAttempt.objects.filter(pk__in=rows).delete()[0]


def admit_login(request, login_id):
    """Admit all requests against source/global budgets before password hashing."""
    now = timezone.now()
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
    with transaction.atomic():
        # This short global lock also bounds new identifier/source key creation
        # when inputs or source addresses rotate. It is released before hashing.
        global_row, _ = LoginAttempt.objects.get_or_create(key=buckets[0][0])
        global_row = LoginAttempt.objects.select_for_update().get(pk=global_row.pk)
        if (
            global_row.retry_after
            and global_row.retry_after > now
            and global_row.failures >= buckets[0][1]
        ):
            return False, max(1, int((global_row.retry_after - now).total_seconds()))
        prune_expired_attempts()
        rows = []
        for key, limit, window in buckets:
            LoginAttempt.objects.get_or_create(key=key)
            row = LoginAttempt.objects.select_for_update().get(key=key)
            if not row.retry_after or row.retry_after <= now:
                row.failures = 0
            if row.failures >= limit:
                return False, max(1, int((row.retry_after - now).total_seconds()))
            rows.append((row, window))
        for row, window in rows:
            row.failures += 1
            if row.retry_after is None or row.retry_after <= now:
                row.retry_after = now + timedelta(seconds=window)
            row.save(update_fields=["failures", "retry_after", "updated_at"])
    return True, 0


@dataclass
class LoginOutcome:
    allowed: bool
    retry_after: int = 0
    authenticated: bool | None = None


@contextmanager
def login_attempt(request, login_id):
    allowed, retry = admit_login(request, login_id)
    if not allowed:
        yield LoginOutcome(False, retry)
        return
    try:
        identity = canonical_login_id(login_id, allow_empty=True)
    except ValidationError:
        identity = ""
    if not identity:
        yield LoginOutcome(True)
        return

    # Serialize exact-identifier outcomes, but release the shared source/global
    # admission locks before expensive password hashing.
    with transaction.atomic():
        key = _key("identifier", identity)
        LoginAttempt.objects.get_or_create(key=key)
        row = LoginAttempt.objects.select_for_update().get(key=key)
        now = timezone.now()
        if row.retry_after is None or row.retry_after <= now:
            row.failures = 0
        if row.failures >= settings.VIRMS_LOGIN_IDENTIFIER_LIMIT:
            yield LoginOutcome(
                False, max(1, int((row.retry_after - now).total_seconds()))
            )
            return
        outcome = LoginOutcome(True)
        yield outcome
        if outcome.authenticated is True:
            row.failures = 0
            row.retry_after = None
        elif outcome.authenticated is False:
            row.failures += 1
            row.retry_after = timezone.now() + timedelta(
                seconds=settings.VIRMS_LOGIN_IDENTIFIER_WINDOW_SECONDS
            )
        else:
            return  # Infrastructure errors are not failed credentials.
        row.save(update_fields=["failures", "retry_after", "updated_at"])


def clear_identifier_budget(login_id):
    """Reset only the exact canonical identifier; preserve source/global state."""
    identity = canonical_login_id(login_id, allow_empty=True)
    if identity:
        with transaction.atomic():
            rows = LoginAttempt.objects.select_for_update().filter(
                key=_key("identifier", identity)
            )
            for row in rows:
                row.failures = 0
                row.retry_after = None
                row.save(update_fields=["failures", "retry_after", "updated_at"])
