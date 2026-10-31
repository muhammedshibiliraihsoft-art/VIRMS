"""Scoped account creation; the caller only receives the temporary secret once."""

import secrets

from django.core.exceptions import PermissionDenied, ValidationError

from apps.tenants.models import Branch, Tenant, TenantMembership

from .audit import record_event
from .locks import locked_users
from .login_id import canonical_login_id
from .models import CompanyRoleGrant, User
from .policy import require_action


def provision_company_account(
    *,
    actor,
    company_id,
    role,
    login_id,
    email,
    first_name="",
    last_name="",
    branch_id=None,
):
    login_id = canonical_login_id(login_id)
    if role not in CompanyRoleGrant.Role.values:
        raise ValidationError("Unsupported role")
    with locked_users(actor.pk) as users:
        current = users[actor.pk]
        if actor.auth_epoch != current.auth_epoch or actor.password != current.password:
            raise PermissionDenied("Authentication changed")
        company = Tenant.objects.select_for_update().filter(pk=company_id).first()
        if company is None:
            raise PermissionDenied("Not authorized")
        branch = None
        if branch_id is not None:
            branch = (
                Branch.objects.select_for_update()
                .filter(pk=branch_id, tenant=company)
                .first()
            )
            if branch is None:
                raise PermissionDenied("Not authorized")
        current = require_action(
            current, f"account.provision.{role}", company=company, branch=branch
        )
        temporary_password = secrets.token_urlsafe(24)
        user = User(
            login_id=login_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            account_kind=User.AccountKind.COMPANY,
            must_change_password=True,
            created_by=current,
        )
        user.set_password(temporary_password)
        user.full_clean()
        user.save()
        membership = TenantMembership.objects.create(
            user=user, tenant=company, assigned_by=current
        )
        if branch is not None:
            from apps.tenants.models import BranchAssignment

            BranchAssignment.objects.create(
                membership=membership, branch=branch, assigned_by=current
            )
        grant = CompanyRoleGrant.objects.create(
            membership=membership,
            role=role,
            branch=branch,
            assigned_by=current,
        )
        record_event(
            action="provision",
            actor=current,
            subject=user,
            company=company,
            branch=branch,
            resource=grant,
            metadata={"role": role},
        )
        return user, temporary_password
