"""Company-scoped account lifecycle operations on one immutable User UUID."""

import secrets

from django.core.exceptions import PermissionDenied, ValidationError

from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.selectors import current_interval

from .audit import record_event
from .locks import locked_users
from .models import CompanyRoleGrant, User
from .policy import require_action


def _target_company(target):
    company_ids = set(
        TenantMembership.objects.filter(user=target)
        .values_list("tenant_id", flat=True)
        .distinct()
    )
    if target.account_kind != User.AccountKind.COMPANY or len(company_ids) != 1:
        raise PermissionDenied("Account scope unavailable")
    company = (
        Tenant.objects.select_for_update().filter(pk=next(iter(company_ids))).first()
    )
    membership = (
        TenantMembership.objects.select_for_update()
        .filter(user=target, tenant=company)
        .filter(current_interval())
        .first()
    )
    if company is None or membership is None:
        raise PermissionDenied("Account scope unavailable")
    roles = set(
        CompanyRoleGrant.objects.select_for_update()
        .filter(membership=membership)
        .filter(current_interval())
        .values_list("role", flat=True)
    )
    if not roles:
        raise PermissionDenied("Account scope unavailable")
    return company, membership, roles


def _authorize(actor, target, verb):
    company, membership, roles = _target_company(target)
    for role in roles:
        require_action(
            actor, f"account.{verb}.{role}", company=company, resource=membership
        )
    return company


def reset_account(*, actor, user_id):
    with locked_users(actor.pk, user_id) as users:
        target = users[user_id]
        company = _authorize(users[actor.pk], target, "reset")
        temporary_password = secrets.token_urlsafe(24)
        target.set_password(temporary_password)
        target.must_change_password = True
        target.auth_epoch += 1
        target.updated_by = users[actor.pk]
        target.save(
            update_fields=[
                "password",
                "must_change_password",
                "auth_epoch",
                "updated_by",
                "updated_at",
            ]
        )
        record_event(
            action="reset_password",
            actor=users[actor.pk],
            subject=target,
            company=company,
            resource=target,
        )
        return temporary_password


def set_account_status(*, actor, user_id, active):
    if type(active) is not bool:
        raise ValidationError("is_active must be boolean")
    with locked_users(actor.pk, user_id) as users:
        target = users[user_id]
        company = _authorize(users[actor.pk], target, "status")
        if target.is_active == active:
            return active
        target.is_active = active
        target.auth_epoch += 1
        target.updated_by = users[actor.pk]
        if not active:
            target.set_unusable_password()
            target.must_change_password = True
        target.save(
            update_fields=[
                "is_active",
                "password",
                "must_change_password",
                "auth_epoch",
                "updated_by",
                "updated_at",
            ]
        )
        record_event(
            action="activate" if active else "deactivate",
            actor=users[actor.pk],
            subject=target,
            company=company,
            resource=target,
        )
        return active


def revoke_account_sessions(*, actor, user_id):
    with locked_users(actor.pk, user_id) as users:
        target = users[user_id]
        company = _authorize(users[actor.pk], target, "revoke")
        target.auth_epoch += 1
        target.updated_by = users[actor.pk]
        target.save(update_fields=["auth_epoch", "updated_by", "updated_at"])
        record_event(
            action="session.revoke",
            actor=users[actor.pk],
            subject=target,
            company=company,
            resource=target,
        )
        return target.auth_epoch
