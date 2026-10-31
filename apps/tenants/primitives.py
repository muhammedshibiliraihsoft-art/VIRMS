"""PRIVATE persistence primitives: not routes or Admin authority.

Call only inside the policy/command layer transaction. Old readers are not switched here.
"""

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from apps.accounts.audit import record_event

from .models import Branch, BranchAssignment, Tenant, TenantMembership
from .selectors import current_interval


def _atomic_required():
    if not connection.in_atomic_block:
        raise RuntimeError("Primitive requires authorized transaction")


def _create_company(*, actor, name, slug):
    _atomic_required()
    company = Tenant(name=name, slug=slug)
    company.full_clean()
    company.save()
    record_event(
        action="company.create",
        actor=actor,
        company=company,
        resource=company,
        metadata={"name": name},
    )
    return company


def _set_company(*, actor, company, is_active=None, name=None):
    _atomic_required()
    company = Tenant.objects.select_for_update().get(pk=company.pk)
    if is_active is not None and type(is_active) is not bool:
        raise ValidationError("is_active must be boolean")
    action = "company.rename"
    if is_active is not None:
        if company.is_active == is_active:
            return company
        company.is_active = is_active
        action = "company.activate" if is_active else "company.suspend"
    elif name is not None:
        if company.name == name:
            return company
        company.name = name
    else:
        raise ValidationError("No transition")
    company.full_clean()
    company.save()
    record_event(
        action=action,
        actor=actor,
        company=company,
        resource=company,
        metadata={"name": company.name, "is_active": company.is_active},
    )
    return company


def _add_membership(*, actor, company, user):
    _atomic_required()
    if not company.is_active or not user.is_active:
        raise ValidationError("Inactive scope")
    # A Company account cannot acquire a second Company identity, including
    # by reopening membership after a historical interval has ended.
    if (
        user.account_kind != "platform"
        and TenantMembership.objects.filter(user=user).exclude(tenant=company).exists()
    ):
        raise ValidationError("Account belongs to another Company")
    if (
        TenantMembership.objects.filter(user=user, tenant=company)
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gt=timezone.now()))
        .exists()
    ):
        raise ValidationError("Membership already effective")
    row = TenantMembership.objects.create(user=user, tenant=company, assigned_by=actor)
    record_event(
        action="membership.add",
        actor=actor,
        subject=user,
        company=company,
        resource=row,
    )
    return row


def _end_membership(*, actor, membership):
    _atomic_required()
    row = TenantMembership.objects.select_for_update().get(pk=membership.pk)
    if row.effective_until is not None:
        return row
    now = timezone.now()
    if now <= row.effective_from:
        raise ValidationError("Cannot end a future membership")
    row.effective_until = now
    row.save(update_fields=["effective_until", "updated_at"])
    record_event(
        action="membership.end",
        actor=actor,
        subject=row.user,
        company=row.tenant,
        resource=row,
    )
    return row


def _create_branch(*, actor, company, name):
    _atomic_required()
    branch = Branch(tenant=company, name=name)
    branch.full_clean()
    branch.save()
    record_event(
        action="branch.create",
        actor=actor,
        company=company,
        branch=branch,
        resource=branch,
    )
    return branch


def _assign_branch(*, actor, membership, branch):
    _atomic_required()
    if membership.tenant_id != branch.tenant_id:
        raise ValidationError("Company mismatch")
    if (
        not TenantMembership.objects.filter(
            pk=membership.pk, tenant__is_active=True, user__is_active=True
        )
        .filter(current_interval())
        .exists()
    ):
        raise ValidationError("Membership not effective")
    if (
        BranchAssignment.objects.filter(membership=membership, branch=branch)
        .filter(Q(effective_until__isnull=True) | Q(effective_until__gt=timezone.now()))
        .exists()
    ):
        raise ValidationError("Assignment already effective")
    row = BranchAssignment.objects.create(
        membership=membership, branch=branch, assigned_by=actor
    )
    record_event(
        action="assignment.add",
        actor=actor,
        subject=membership.user,
        company=branch.tenant,
        branch=branch,
        resource=row,
    )
    return row
