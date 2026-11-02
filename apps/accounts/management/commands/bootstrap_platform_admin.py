"""Explicit, idempotent control-plane bootstrap; never called from HTTP."""

import hashlib
import json
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.audit import record_event
from apps.accounts.management.commands import operator_auth
from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.accounts.platform_identity import has_company_business_history
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.primitives import _create_company


def _intent_digest(*, user_id, company_id=None, company_name=None, company_slug=None):
    intent = {
        "company_id": str(company_id) if company_id else None,
        "company_name": company_name,
        "company_slug": company_slug,
        "user_id": str(user_id),
    }
    encoded = json.dumps(intent, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_platform_superuser(user):
    return (
        user.account_kind == User.AccountKind.PLATFORM
        and user.is_active
        and user.is_staff
        and user.is_superuser
        and not user.must_change_password
        and not has_company_business_history(user.pk)
    )


def _apply_bootstrap(
    *, user_id, company_id, company_name, company_slug, operation_id, operator_password
):
    digest = _intent_digest(
        user_id=user_id,
        company_id=company_id,
        company_name=company_name,
        company_slug=company_slug,
    )
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        if user is None or not _is_platform_superuser(user):
            raise CommandError(
                "Explicit user must be an active Django Platform superuser"
            )
        operator_auth.require_platform_password(operator_password, user)

        previous = AccountSecurityEvent.objects.filter(
            bootstrap_operation_id=operation_id
        ).first()
        if previous is not None:
            if (
                previous.actor_id != user.pk
                or previous.subject_id != user.pk
                or previous.metadata.get("intent_digest") != digest
            ):
                raise CommandError("Bootstrap operation ID conflicts with prior intent")
            return previous.company_id, True

        if company_id is not None:
            company = Tenant.objects.select_for_update().filter(pk=company_id).first()
            if company is None or not company.is_active:
                raise CommandError("Explicit active Company ID was not found")
        else:
            company = _create_company(
                actor=user,
                name=company_name,
                slug=company_slug,
            )

        now = timezone.now()
        relevant_roles = list(
            RoleAssignment.objects.select_for_update()
            .filter(
                user=user,
                role=RoleAssignment.Role.BACK_OFFICE,
            )
            .filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now))
            .order_by("id")
        )
        if any(row.effective_from > now for row in relevant_roles):
            raise CommandError("A future back-office role needs manual review")
        if len(relevant_roles) > 1:
            raise CommandError("Overlapping back-office roles need manual review")
        if not relevant_roles:
            RoleAssignment.objects.create(
                user=user,
                role=RoleAssignment.Role.BACK_OFFICE,
                assigned_by=user,
            )

        relevant_memberships = list(
            TenantMembership.objects.select_for_update()
            .filter(user=user, tenant=company)
            .filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now))
            .order_by("id")
        )
        if any(row.effective_from > now for row in relevant_memberships):
            raise CommandError("A future Company membership needs manual review")
        if len(relevant_memberships) > 1:
            raise CommandError("Overlapping Company memberships need manual review")
        active_membership = relevant_memberships[0] if relevant_memberships else None
        if active_membership is None:
            active_membership = TenantMembership.objects.create(
                user=user,
                tenant=company,
                assigned_by=user,
            )

        record_event(
            action="bootstrap",
            actor=user,
            subject=user,
            company=company,
            resource=company,
            reason="Explicit Platform administrator bootstrap",
            metadata={
                "intent_digest": digest,
                "membership_id": str(active_membership.pk),
                "role": "back_office",
            },
            bootstrap_operation_id=operation_id,
        )
        return company.pk, False


class Command(BaseCommand):
    help = "Bootstrap one explicitly selected Platform superuser for one Company"

    def add_arguments(self, parser):
        parser.add_argument("--user-id", required=True, type=uuid.UUID)
        company = parser.add_mutually_exclusive_group(required=True)
        company.add_argument("--company-id", type=uuid.UUID)
        company.add_argument("--company-name")
        parser.add_argument("--company-slug")
        parser.add_argument("--operation-id", required=True, type=uuid.UUID)

    def handle(self, *args, **options):
        company_id = options["company_id"]
        company_name = options["company_name"]
        company_slug = options["company_slug"]
        if company_id is not None and (company_name or company_slug):
            raise CommandError(
                "Company ID cannot be combined with Company name or slug"
            )
        if company_id is None and (not company_name or not company_slug):
            raise CommandError("Company name and Company slug are both required")
        if company_name is not None and company_slug is not None:
            try:
                company_name.encode("utf-8", "strict")
                company_slug.encode("utf-8", "strict")
            except UnicodeError as error:
                raise CommandError("Company name or slug is invalid") from error

        operator_password = operator_auth.prompt_platform_password()
        try:
            company_pk, replayed = _apply_bootstrap(
                user_id=options["user_id"],
                company_id=company_id,
                company_name=company_name,
                company_slug=company_slug,
                operation_id=options["operation_id"],
                operator_password=operator_password,
            )
        except IntegrityError as error:
            previous = AccountSecurityEvent.objects.filter(
                bootstrap_operation_id=options["operation_id"]
            ).first()
            if previous is None:
                raise CommandError("Bootstrap could not be completed") from error
            digest = _intent_digest(
                user_id=options["user_id"],
                company_id=company_id,
                company_name=company_name,
                company_slug=company_slug,
            )
            if (
                previous.actor_id != options["user_id"]
                or previous.subject_id != options["user_id"]
                or previous.metadata.get("intent_digest") != digest
            ):
                raise CommandError(
                    "Bootstrap operation ID conflicts with prior intent"
                ) from error
            company_pk, replayed = previous.company_id, True

        if replayed:
            self.stdout.write(f"Bootstrap already applied for Company {company_pk}")
        else:
            self.stdout.write(
                f"Platform administrator bootstrapped for Company {company_pk}"
            )
