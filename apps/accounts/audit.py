"""Bounded, allowlisted administrative evidence. Not an access decision source."""

import json

from django.core.exceptions import ValidationError

from .models import AccountSecurityEvent

ACTIONS = {
    "provision",
    "reset_password",
    "change_password",
    "activate",
    "deactivate",
    "company.create",
    "company.rename",
    "company.suspend",
    "company.activate",
    "branch.create",
    "branch.rename",
    "membership.add",
    "membership.end",
    "role.add",
    "role.map",
    "auth.cutover",
    "login.canonicalize",
    "role.end",
    "assignment.add",
    "assignment.end",
    "session.revoke",
    "bootstrap",
    "admin.denied",
}
METADATA_KEYS = {
    "name",
    "is_active",
    "role",
    "membership_id",
    "grant_id",
    "assignment_id",
    "effective_from",
    "effective_until",
    "intent_digest",
    "operation_id",
    "source_role_assignment_id",
}


def record_event(
    *,
    action,
    actor=None,
    subject=None,
    company=None,
    branch=None,
    resource=None,
    reason="",
    metadata=None,
    outcome="success",
    request_id=None,
    bootstrap_operation_id=None,
):
    metadata = metadata or {}
    if action not in ACTIONS or outcome not in {"success", "denied", "failed"}:
        raise ValidationError("Unsupported security event")
    if not isinstance(metadata, dict) or set(metadata) - METADATA_KEYS:
        raise ValidationError("Unsupported audit metadata")
    if any(not isinstance(v, (str, bool, int, type(None))) for v in metadata.values()):
        raise ValidationError("Nested audit metadata is not permitted")
    if (
        len(json.dumps(metadata)) > 4096
        or not isinstance(reason, str)
        or len(reason) > 500
    ):
        raise ValidationError("Audit metadata exceeds bounds")
    if branch is not None and (company is None or branch.tenant_id != company.pk):
        raise ValidationError("Audit scope mismatch")
    return AccountSecurityEvent.objects.create(
        action=action,
        actor=actor,
        subject=subject,
        actor_kind="user" if actor else "system",
        company_id=company.pk if company else None,
        branch_id=branch.pk if branch else None,
        resource_type=resource._meta.label_lower if resource else "",
        resource_id=resource.pk if resource else None,
        reason=reason,
        metadata=metadata,
        outcome=outcome,
        request_id=request_id,
        bootstrap_operation_id=bootstrap_operation_id,
    )


def record_sensitive_denial(*, actor, company=None):
    """One durable denial per actor/minute, after mutation rollback only."""
    from datetime import timedelta

    from django.db import transaction
    from django.utils import timezone

    from .models import User

    if actor is None or not actor.is_authenticated:
        return None
    with transaction.atomic():
        actor = User.objects.select_for_update().get(pk=actor.pk)
        if AccountSecurityEvent.objects.filter(
            actor=actor,
            action="admin.denied",
            occurred_at__gte=timezone.now() - timedelta(minutes=1),
        ).exists():
            return None
        return record_event(
            action="admin.denied", actor=actor, company=company, outcome="denied"
        )
