"""Apply an explicitly reviewed legacy-role -> Company-grant manifest."""

import hashlib
import json
import uuid
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.accounts.audit import record_event
from apps.accounts.management.commands import operator_auth
from apps.accounts.models import (
    AccountSecurityEvent,
    CompanyRoleGrant,
    RoleAssignment,
    User,
)
from apps.accounts.policy import require_action
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership
from apps.tenants.selectors import current_interval

MANIFEST_VERSION = "VIRMS-P1-ROLE-MAP-1"
MAX_MANIFEST_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50000


def _uuid(value, label):
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError) as error:
        raise CommandError(f"Invalid {label}") from error


def _manifest(path):
    try:
        if Path(path).stat().st_size > MAX_MANIFEST_BYTES:
            raise CommandError("Manifest exceeds the 5 MiB limit")
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CommandError("Manifest must be readable UTF-8 JSON") from error
    expected = {
        "format_version",
        "source_database",
        "approved_by",
        "approval_reference",
        "platform_role_assignments",
        "denied_role_assignments",
        "mappings",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise CommandError("Manifest fields do not match the required schema")
    if value["format_version"] != MANIFEST_VERSION:
        raise CommandError("Unsupported manifest format_version")
    if not isinstance(value["source_database"], str) or not value["source_database"]:
        raise CommandError("Manifest source_database is required")
    if (
        not isinstance(value["approval_reference"], str)
        or not value["approval_reference"].strip()
    ):
        raise CommandError("Manifest approval_reference is required")
    if len(value["approval_reference"]) > 200:
        raise CommandError("Manifest approval_reference exceeds 200 characters")
    for name in ("platform_role_assignments", "denied_role_assignments", "mappings"):
        if not isinstance(value[name], list) or len(value[name]) > MAX_ROWS:
            raise CommandError(f"Manifest {name} must be a bounded list")
    return value


def _row_reason(row, label):
    if not isinstance(row, dict) or set(row) != {"role_assignment_id", "reason"}:
        raise CommandError(f"Each {label} row needs role_assignment_id and reason")
    reason = row["reason"]
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise CommandError(f"Each {label} row needs a reason of 1 to 500 characters")
    return _uuid(row["role_assignment_id"], f"{label} role_assignment_id")


def _mapping_intent(source, membership_id, branch_id, approval_reference):
    intent = {
        "branch_id": str(branch_id) if branch_id else None,
        "effective_from": source.effective_from.isoformat(),
        "effective_until": (
            source.effective_until.isoformat() if source.effective_until else None
        ),
        "membership_id": str(membership_id),
        "role": source.role,
        "source_role_assignment_id": str(source.pk),
        "approval_reference": approval_reference,
    }
    encoded = json.dumps(intent, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _contained_interval(source, membership):
    if source.effective_from < membership.effective_from:
        return False
    if membership.effective_until is None:
        return True
    return (
        source.effective_until is not None
        and source.effective_until <= membership.effective_until
    )


def _overlaps(left_start, left_end, right_start, right_end):
    return (right_end is None or left_start < right_end) and (
        left_end is None or left_end > right_start
    )


class Command(BaseCommand):
    help = (
        "Validate or apply an explicit manifest mapping legacy global business roles "
        "to CompanyRoleGrant rows. Dry-run is the default; --apply requires a "
        "maintenance window with account/scope writers stopped."
    )

    def add_arguments(self, parser):
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--actor-user-id", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--maintenance-confirmed", action="store_true")

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Role mapping requires PostgreSQL")
        if options["apply"] and not options["maintenance_confirmed"]:
            raise CommandError("--apply requires --maintenance-confirmed")
        manifest = _manifest(options["manifest"])
        if manifest["source_database"] != str(connection.settings_dict["NAME"]):
            raise CommandError(
                "Manifest source_database does not match this connection"
            )
        manifest_intent = hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        actor_id = _uuid(options["actor_user_id"], "actor_user_id")
        approved_by = _uuid(manifest["approved_by"], "approved_by")
        if actor_id != approved_by:
            raise CommandError(
                "The authenticated mapping operator must match approved_by"
            )

        platform_ids = [
            _row_reason(row, "platform_role_assignments")
            for row in manifest["platform_role_assignments"]
        ]
        denied_ids = [
            _row_reason(row, "denied_role_assignments")
            for row in manifest["denied_role_assignments"]
        ]
        mapping_rows = manifest["mappings"]
        mapping_ids = []
        for row in mapping_rows:
            expected = {
                "role_assignment_id",
                "membership_id",
                "branch_id",
                "interval_policy",
                "reason",
            }
            if not isinstance(row, dict) or set(row) != expected:
                raise CommandError(
                    "Each mapping row must explicitly name source, membership, Branch and interval policy"
                )
            if row["interval_policy"] != "preserve_source":
                raise CommandError(
                    "Only explicit preserve_source interval mapping is supported"
                )
            if (
                not isinstance(row["reason"], str)
                or not row["reason"].strip()
                or len(row["reason"]) > 500
            ):
                raise CommandError(
                    "Each mapping row needs a reason of 1 to 500 characters"
                )
            row["_source_id"] = _uuid(row["role_assignment_id"], "role_assignment_id")
            row["_membership_id"] = _uuid(row["membership_id"], "membership_id")
            row["_branch_id"] = (
                None
                if row["branch_id"] is None
                else _uuid(row["branch_id"], "branch_id")
            )
            mapping_ids.append(row["_source_id"])

        all_ids = platform_ids + denied_ids + mapping_ids
        if len(all_ids) != len(set(all_ids)):
            raise CommandError("Every legacy role assignment must appear exactly once")

        if options["apply"]:
            operator_password = operator_auth.prompt_platform_password()
            with transaction.atomic():
                self._lock_apply_rows(actor_id, all_ids, mapping_rows)
                self._assert_complete_manifest(all_ids)
                actor = self._load_actor(actor_id)
                operator_auth.require_platform_password(operator_password, actor)
                self._assert_cutover_intent(manifest_intent)
                try:
                    prepared = self._validate_rows(
                        actor,
                        mapping_rows,
                        platform_ids,
                        denied_ids,
                        manifest["approval_reference"],
                    )
                except (PermissionDenied, ValidationError) as error:
                    raise CommandError(
                        "One or more mappings failed current scope validation"
                    ) from error
                applied, repeated = self._apply_rows(
                    actor,
                    prepared,
                    manifest["approval_reference"],
                )
                cutover_applied = self._invalidate_pre_cutover_sessions(
                    actor,
                    manifest_intent,
                    manifest["approval_reference"],
                )
            mode = f"Applied {applied} and recognized {repeated} repeated mappings"
            if cutover_applied:
                mode += "; all pre-cutover sessions invalidated"
            else:
                mode += "; pre-cutover sessions were already invalidated"
        else:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                    )
                self._assert_complete_manifest(all_ids)
                actor = self._load_actor(actor_id)
                self._assert_cutover_intent(manifest_intent)
                try:
                    prepared = self._validate_rows(
                        actor,
                        mapping_rows,
                        platform_ids,
                        denied_ids,
                        manifest["approval_reference"],
                    )
                except (PermissionDenied, ValidationError) as error:
                    raise CommandError(
                        "One or more mappings failed current scope validation"
                    ) from error
            mode = f"Validated {len(prepared)} mappings; no rows were changed"
        self.stdout.write(
            f"{mode}; {len(platform_ids)} Platform roles retained; "
            f"{len(denied_ids)} legacy roles explicitly left non-authorizing."
        )

    @staticmethod
    def _load_actor(actor_id):
        actor = User.objects.filter(
            pk=actor_id,
            is_active=True,
            account_kind=User.AccountKind.PLATFORM,
            must_change_password=False,
        ).first()
        if (
            actor is None
            or not RoleAssignment.objects.filter(
                user=actor, role=RoleAssignment.Role.BACK_OFFICE
            )
            .filter(current_interval())
            .exists()
        ):
            raise CommandError("Actor must be an active Platform Back Office account")
        return actor

    @staticmethod
    def _assert_complete_manifest(all_ids):
        actual_ids = set(RoleAssignment.objects.values_list("pk", flat=True))
        if set(all_ids) != actual_ids:
            raise CommandError(
                "Manifest must classify every legacy role assignment in this database"
            )

    @staticmethod
    def _assert_cutover_intent(intent_digest):
        previous = AccountSecurityEvent.objects.filter(action="auth.cutover").first()
        if (
            previous is not None
            and previous.metadata.get("intent_digest") != intent_digest
        ):
            raise CommandError(
                "A different authorization cutover manifest was already applied"
            )

    @staticmethod
    def _lock_apply_rows(actor_id, role_ids, mapping_rows):
        # Lock every account before Company rows. This also serializes login
        # issuance and ordinary account/scope writers until the epoch cutover.
        user_ids = set(User.objects.values_list("pk", flat=True))
        locked_users = set(
            User.objects.select_for_update()
            .filter(pk__in=user_ids)
            .order_by("id")
            .values_list("pk", flat=True)
        )
        if locked_users != user_ids:
            raise CommandError("A mapping user disappeared before apply")
        if actor_id not in locked_users:
            raise CommandError("Mapping operator was not found before apply")

        quote = connection.ops.quote_name
        role_table = quote(RoleAssignment._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f"LOCK TABLE {role_table} IN SHARE ROW EXCLUSIVE MODE")

        membership_ids = [row["_membership_id"] for row in mapping_rows]
        membership_companies = dict(
            TenantMembership.objects.filter(pk__in=membership_ids).values_list(
                "pk", "tenant_id"
            )
        )
        if set(membership_companies) != set(membership_ids):
            raise CommandError("A target membership disappeared before apply")
        company_ids = set(membership_companies.values())
        locked_companies = set(
            Tenant.objects.select_for_update()
            .filter(pk__in=company_ids)
            .order_by("id")
            .values_list("pk", flat=True)
        )
        if locked_companies != company_ids:
            raise CommandError("A target Company disappeared before apply")

        locked_memberships = set(
            TenantMembership.objects.select_for_update()
            .filter(pk__in=membership_ids)
            .order_by("id")
            .values_list("pk", flat=True)
        )
        if locked_memberships != set(membership_ids):
            raise CommandError("A target membership disappeared before apply")

        branch_ids = {
            row["_branch_id"] for row in mapping_rows if row["_branch_id"] is not None
        }
        if branch_ids:
            locked_branches = set(
                Branch.objects.select_for_update()
                .filter(pk__in=branch_ids)
                .order_by("id")
                .values_list("pk", flat=True)
            )
            if locked_branches != branch_ids:
                raise CommandError("A mapped Branch disappeared before apply")
            list(
                BranchAssignment.objects.select_for_update()
                .filter(membership_id__in=membership_ids, branch_id__in=branch_ids)
                .order_by("id")
                .values_list("pk", flat=True)
            )
        list(
            RoleAssignment.objects.select_for_update()
            .filter(pk__in=role_ids)
            .order_by("id")
            .values_list("pk", flat=True)
        )

    def _validate_rows(
        self, actor, mapping_rows, platform_ids, denied_ids, approval_reference
    ):
        platform_rows = {
            row.pk: row
            for row in RoleAssignment.objects.filter(
                pk__in=platform_ids
            ).select_related("user")
        }
        if set(platform_rows) != set(platform_ids):
            raise CommandError("A declared Platform role assignment was not found")
        for row in platform_rows.values():
            if (
                row.role != RoleAssignment.Role.BACK_OFFICE
                or row.user.account_kind != User.AccountKind.PLATFORM
            ):
                raise CommandError(
                    "Only Platform back-office rows may be retained as Platform roles"
                )

        denied_rows = {
            row.pk: row
            for row in RoleAssignment.objects.filter(pk__in=denied_ids).select_related(
                "user"
            )
        }
        if set(denied_rows) != set(denied_ids):
            raise CommandError("A declared denied role assignment was not found")

        prepared = []
        virtual_intervals = {}
        for item in mapping_rows:
            source = (
                RoleAssignment.objects.select_related("user", "assigned_by")
                .filter(pk=item["_source_id"])
                .first()
            )
            membership = (
                TenantMembership.objects.select_related("user", "tenant")
                .filter(pk=item["_membership_id"])
                .first()
            )
            branch_id = item["_branch_id"]
            branch = Branch.objects.filter(pk=branch_id).first() if branch_id else None
            if source is None or membership is None:
                raise CommandError(
                    "A mapping source row or target membership was not found"
                )
            if source.role not in CompanyRoleGrant.Role.values:
                raise CommandError("Only explicit Company business roles can be mapped")
            if (
                source.user_id != membership.user_id
                or membership.user.account_kind != User.AccountKind.COMPANY
                or TenantMembership.objects.filter(user_id=source.user_id)
                .values("tenant_id")
                .distinct()
                .count()
                != 1
            ):
                raise CommandError(
                    "Mapping must target the same one-Company business account"
                )
            if not _contained_interval(source, membership):
                raise CommandError(
                    "Source role interval is not contained by its explicit membership"
                )
            if branch_id is not None:
                if branch is None or branch.tenant_id != membership.tenant_id:
                    raise CommandError(
                        "Mapped Branch must belong to the explicit membership Company"
                    )
                assignments = BranchAssignment.objects.filter(
                    membership=membership, branch=branch
                )
                if not any(
                    _contained_interval(source, assignment)
                    for assignment in assignments
                ):
                    raise CommandError(
                        "Branch mapping requires a matching assignment covering the role interval"
                    )

            require_action(
                actor,
                "role.add",
                company=membership.tenant,
                branch=branch,
                resource=membership,
            )
            digest = _mapping_intent(
                source, membership.pk, branch_id, approval_reference
            )
            key = (membership.pk, source.role, branch_id)
            intervals = virtual_intervals.setdefault(key, [])
            for existing_start, existing_end in intervals:
                if _overlaps(
                    source.effective_from,
                    source.effective_until,
                    existing_start,
                    existing_end,
                ):
                    raise CommandError(
                        "Explicit mappings contain overlapping role intervals"
                    )
            existing_grants = CompanyRoleGrant.objects.filter(
                membership=membership, role=source.role, branch=branch
            ).order_by("effective_from", "id")
            for grant in existing_grants:
                if _overlaps(
                    source.effective_from,
                    source.effective_until,
                    grant.effective_from,
                    grant.effective_until,
                ):
                    event = AccountSecurityEvent.objects.filter(
                        action="role.map",
                        metadata__source_role_assignment_id=str(source.pk),
                    ).first()
                    if (
                        event is None
                        or event.metadata.get("intent_digest") != digest
                        or event.resource_id != grant.pk
                    ):
                        raise CommandError(
                            "Mapping overlaps an existing grant without the same audited source"
                        )
            intervals.append((source.effective_from, source.effective_until))
            prepared.append(
                {
                    "source_id": source.pk,
                    "membership_id": membership.pk,
                    "company_id": membership.tenant_id,
                    "branch_id": branch.pk if branch else None,
                    "role": source.role,
                    "effective_from": source.effective_from,
                    "effective_until": source.effective_until,
                    "assigned_by_id": source.assigned_by_id,
                    "digest": digest,
                    "reason": item["reason"],
                }
            )
        return prepared

    def _apply_rows(self, actor, prepared, approval_reference):
        applied = repeated = 0
        for item in prepared:
            source = (
                RoleAssignment.objects.select_for_update()
                .filter(pk=item["source_id"])
                .first()
            )
            if source is None:
                raise CommandError("A locked source role assignment disappeared")
            previous = (
                AccountSecurityEvent.objects.select_for_update()
                .filter(
                    action="role.map",
                    metadata__source_role_assignment_id=str(source.pk),
                )
                .first()
            )
            if previous is not None:
                if (
                    previous.metadata.get("intent_digest") != item["digest"]
                    or previous.company_id != item["company_id"]
                    or previous.branch_id != item["branch_id"]
                ):
                    raise CommandError(
                        "A source role assignment was already mapped with different intent"
                    )
                repeated += 1
                continue

            membership = TenantMembership.objects.select_for_update().get(
                pk=item["membership_id"]
            )
            company = membership.tenant
            branch = (
                Branch.objects.select_for_update().get(pk=item["branch_id"])
                if item["branch_id"]
                else None
            )
            grant = CompanyRoleGrant(
                membership=membership,
                role=item["role"],
                branch=branch,
                assigned_by_id=item["assigned_by_id"],
                effective_from=item["effective_from"],
                effective_until=item["effective_until"],
            )
            grant.full_clean()
            grant.save()
            record_event(
                action="role.map",
                actor=actor,
                subject=source.user,
                company=company,
                branch=branch,
                resource=grant,
                reason="Reviewed legacy role-to-Company mapping",
                metadata={
                    "source_role_assignment_id": str(source.pk),
                    "membership_id": str(membership.pk),
                    "grant_id": str(grant.pk),
                    "role": grant.role,
                    "intent_digest": item["digest"],
                },
            )
            applied += 1
        return applied, repeated

    @staticmethod
    def _invalidate_pre_cutover_sessions(actor, intent_digest, approval_reference):
        previous = (
            AccountSecurityEvent.objects.select_for_update()
            .filter(action="auth.cutover")
            .first()
        )
        if previous is not None:
            if previous.metadata.get("intent_digest") != intent_digest:
                raise CommandError(
                    "A different authorization cutover manifest was already applied"
                )
            return False

        # All User rows are locked until commit. Concurrent login/session
        # issuance completes before the epoch bump or sees the new epoch later.
        from django.db.models import F

        User.objects.update(auth_epoch=F("auth_epoch") + 1)
        record_event(
            action="auth.cutover",
            actor=actor,
            reason="Reviewed authorization role cutover",
            metadata={"intent_digest": intent_digest},
        )
        return True
