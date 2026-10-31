"""Private self-password operation; no account provisioning/reset implementation."""

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.crypto import constant_time_compare

from .audit import record_event
from .locks import locked_users
from .models import SessionActivity
from .session_security import session_digest


def change_private_password(request, *, current_password, new_password, confirmation):
    with locked_users(request.user.pk) as users:
        user = users[request.user.pk]
        old_key = request.session.session_key
        lease = (
            SessionActivity.objects.select_for_update()
            .filter(key_hash=session_digest(old_key))
            .first()
            if old_key
            else None
        )
        import time

        from django.conf import settings

        now = int(time.time())
        if lease is None or not (
            0 <= now - lease.issued_at < settings.VIRMS_SESSION_ABSOLUTE_SECONDS
            and 0 <= now - lease.last_activity < settings.VIRMS_SESSION_IDLE_SECONDS
        ):
            raise PermissionDenied("Session expired")
        if (
            not user.is_active
            or request.session.get("auth_epoch") != user.auth_epoch
            or not constant_time_compare(
                request.session.get("_auth_user_hash", ""), user.get_session_auth_hash()
            )
        ):
            raise PermissionDenied("Authentication changed; sign in again")
        if not isinstance(current_password, str) or not user.check_password(
            current_password
        ):
            raise ValidationError("Current password is incorrect")
        if not isinstance(new_password, str) or new_password != confirmation:
            raise ValidationError("New passwords do not match")
        if new_password == current_password:
            raise ValidationError("Choose a different private password")
        validate_password(new_password, user)
        user.set_password(new_password)
        user.must_change_password = False
        user.auth_epoch += 1
        user.updated_by = user
        user.save(
            update_fields=[
                "password",
                "must_change_password",
                "auth_epoch",
                "updated_by",
                "updated_at",
            ]
        )
        record_event(action="change_password", actor=user, subject=user)
        # Hold the User lock through current-session refresh. Other commands cannot
        # reset between validation and this operation's linearization point.
        update_session_auth_hash(request, user)
        SessionActivity.objects.create(
            key_hash=session_digest(request.session.session_key),
            issued_at=lease.issued_at,
            last_activity=max(lease.last_activity, now),
        )
        lease.delete()
        request.session["auth_epoch"] = user.auth_epoch
        request.user = user
    return user
