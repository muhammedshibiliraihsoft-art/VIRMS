"""Session issuance/revocation: server-side state, never frontend role snapshots."""

import hashlib
import time

from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.dispatch import receiver

from .models import SessionActivity, User


@receiver(user_logged_in, dispatch_uid="virms.session.issue")
def stamp_session(sender, request, user, **kwargs):
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=user.pk)
        if (
            not current.is_active
            or current.password != user.password
            or current.auth_epoch != user.auth_epoch
        ):
            logout(request)
            raise PermissionDenied("Authentication changed; sign in again")
        now = int(time.time())
        # Django's test client and a first login may not have persisted the
        # newly cycled session key when the signal fires.
        if request.session.session_key is None:
            request.session.save()
        SessionActivity.objects.update_or_create(
            key_hash=session_digest(request.session.session_key),
            defaults={"issued_at": now, "last_activity": now},
        )
        request.session["auth_epoch"] = current.auth_epoch
        request.session["issued_at"] = now
        request.session["last_activity"] = now


def session_digest(key):
    return hashlib.sha256(key.encode()).hexdigest()


def touch_activity(digest, now):
    from django.db.models import F, Value
    from django.db.models.functions import Greatest

    return SessionActivity.objects.filter(
        key_hash=digest, last_activity__lte=now - 60
    ).update(last_activity=Greatest(F("last_activity"), Value(now)))
