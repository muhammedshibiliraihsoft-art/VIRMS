"""Protected internal commands. No generic CRUD or new public adapters."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.accounts.audit import record_event
from apps.accounts.locks import locked_users
from apps.accounts.models import CompanyRoleGrant
from apps.accounts.policy import require_action

from . import primitives
from .models import Branch, BranchAssignment, Tenant, TenantMembership
from .selectors import current_interval


def create_company(*, actor, name, slug):
    with locked_users(actor.pk) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        actor = require_action(users[actor.pk], "company.create")
        return primitives._create_company(actor=actor, name=name, slug=slug)


def set_company(*, actor, company, name=None, is_active=None):
    with locked_users(actor.pk) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=company.pk)
        action = (
            "company.rename"
            if is_active is None
            else "company.activate" if is_active else "company.suspend"
        )
        actor = require_action(users[actor.pk], action, company=company)
        return primitives._set_company(
            actor=actor, company=company, name=name, is_active=is_active
        )


def add_membership(*, actor, company, user):
    with locked_users(actor.pk, user.pk) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=company.pk)
        actor = require_action(users[actor.pk], "membership.add", company=company)
        return primitives._add_membership(
            actor=actor, company=company, user=users[user.pk]
        )


def end_membership(*, actor, membership):
    with locked_users(actor.pk, membership.user_id) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        actor = require_action(users[actor.pk], "membership.end", company=company)
        membership = TenantMembership.objects.select_for_update().get(
            pk=membership.pk, tenant=company
        )
        return primitives._end_membership(actor=actor, membership=membership)


def create_branch(*, actor, company, name):
    with locked_users(actor.pk) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=company.pk)
        actor = require_action(users[actor.pk], "branch.create", company=company)
        return primitives._create_branch(actor=actor, company=company, name=name)


def assign_branch(*, actor, membership, branch):
    with locked_users(actor.pk, membership.user_id) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        actor = require_action(users[actor.pk], "assignment.add", company=company)
        membership = TenantMembership.objects.select_for_update().get(
            pk=membership.pk, tenant=company
        )
        branch = Branch.objects.select_for_update().get(pk=branch.pk, tenant=company)
        return primitives._assign_branch(
            actor=actor, membership=membership, branch=branch
        )


def grant_role(*, actor, membership, role, branch=None):
    with locked_users(actor.pk, membership.user_id) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=membership.tenant_id)
        actor = require_action(users[actor.pk], "role.add", company=company)
        membership = (
            TenantMembership.objects.select_for_update()
            .filter(pk=membership.pk, user__is_active=True)
            .filter(current_interval())
            .first()
        )
        if membership is None or role not in CompanyRoleGrant.Role.values:
            raise ValidationError("Invalid membership or role")
        if branch is not None:
            branch = Branch.objects.select_for_update().get(
                pk=branch.pk, tenant=company
            )
            if (
                not BranchAssignment.objects.filter(
                    membership=membership, branch=branch
                )
                .filter(current_interval())
                .exists()
            ):
                raise ValidationError("Effective Branch assignment required")
        from django.db.models import Q

        if (
            CompanyRoleGrant.objects.filter(
                membership=membership, role=role, branch=branch
            )
            .filter(
                Q(effective_until__isnull=True) | Q(effective_until__gt=timezone.now())
            )
            .exists()
        ):
            raise ValidationError("Existing grant interval requires review")
        row = CompanyRoleGrant(
            membership=membership, role=role, branch=branch, assigned_by=actor
        )
        row.full_clean()
        row.save()
        record_event(
            action="role.add",
            actor=actor,
            subject=membership.user,
            company=company,
            branch=branch,
            resource=row,
            metadata={"role": role},
        )
        return row


def end_scope_row(*, actor, row):
    if not isinstance(row, (BranchAssignment, CompanyRoleGrant)):
        raise ValidationError("Unsupported scope record")
    with locked_users(actor.pk, row.membership.user_id) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=row.membership.tenant_id)
        action = "assignment.end" if isinstance(row, BranchAssignment) else "role.end"
        actor = require_action(users[actor.pk], action, company=company)
        TenantMembership.objects.select_for_update().get(pk=row.membership_id)
        if row.branch_id:
            Branch.objects.select_for_update().get(pk=row.branch_id, tenant=company)
        row = type(row).objects.select_for_update().get(pk=row.pk)
        if row.effective_until is not None:
            return row
        now = timezone.now()
        if now <= row.effective_from:
            raise ValidationError("Cannot end future scope")
        row.effective_until = now
        row.save(update_fields=["effective_until", "updated_at"])
        record_event(
            action=action,
            actor=actor,
            subject=row.membership.user,
            company=company,
            resource=row,
        )
        return row


def rename_branch(*, actor, branch, name):
    with locked_users(actor.pk) as users:
        if (
            actor.auth_epoch != users[actor.pk].auth_epoch
            or actor.password != users[actor.pk].password
        ):
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().get(pk=branch.tenant_id)
        actor = require_action(users[actor.pk], "branch.rename", company=company)
        branch = Branch.objects.select_for_update().get(pk=branch.pk, tenant=company)
        if branch.name == name:
            return branch
        branch.name = name
        branch.full_clean()
        branch.save(update_fields=["name", "updated_at"])
        record_event(
            action="branch.rename",
            actor=actor,
            company=company,
            branch=branch,
            resource=branch,
            metadata={"name": name},
        )
        return branch
