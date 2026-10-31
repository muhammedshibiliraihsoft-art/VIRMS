"""Apply an explicitly reviewed UUID-to-canonical-Login-ID manifest."""

import hashlib
import json
import unicodedata
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone

from apps.accounts.audit import record_event
from apps.accounts.management.commands import operator_auth
from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.selectors import current_interval

MANIFEST_VERSION = "VIRMS-P1-LOGIN-MAP-1"
MAX_MANIFEST_BYTES = 5 * 1024 * 1024
MAX_ROWS = 50000
REQUIRED_MIGRATION = ("accounts", "0008_loginattempt_login_retry_after_idx")
CANONICAL_MIGRATION = ("accounts", "0009_canonical_login_id")


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
        "operation_id",
        "mappings",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise CommandError("Manifest fields do not match the required schema")
    if value["format_version"] != MANIFEST_VERSION:
        raise CommandError("Unsupported manifest format_version")
    if not isinstance(value["source_database"], str) or not value["source_database"]:
        raise CommandError("Manifest source_database is required")
    approval_reference = value["approval_reference"]
    if (
        not isinstance(approval_reference, str)
        or not approval_reference.strip()
        or len(approval_reference) > 200
    ):
        raise CommandError("Manifest approval_reference must be 1 to 200 characters")
    if (
        not isinstance(value["mappings"], list)
        or not 1 <= len(value["mappings"]) <= MAX_ROWS
    ):
        raise CommandError("Manifest mappings must contain between 1 and 50000 rows")

    seen = set()
    for row in value["mappings"]:
        expected_row = {
            "user_id",
            "expected_login_id",
            "canonical_login_id",
            "reason",
        }
        if not isinstance(row, dict) or set(row) != expected_row:
            raise CommandError(
                "Each mapping needs user_id, expected_login_id, canonical_login_id and reason"
            )
        row["_user_id"] = _uuid(row["user_id"], "user_id")
        if row["_user_id"] in seen:
            raise CommandError("Each User UUID may appear only once")
        seen.add(row["_user_id"])
        if not isinstance(row["expected_login_id"], str):
            raise CommandError("expected_login_id must be a string")
        if not isinstance(row["canonical_login_id"], str):
            raise CommandError("canonical_login_id must be a string")
        reason = row["reason"]
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise CommandError("Each mapping needs a reason of 1 to 500 characters")
    value["approved_by"] = _uuid(value["approved_by"], "approved_by")
    value["operation_id"] = _uuid(value["operation_id"], "operation_id")
    return value


def _intent_digest(manifest):
    digest_input = {key: item for key, item in manifest.items() if key != "mappings"}
    digest_input["approved_by"] = str(manifest["approved_by"])
    digest_input["operation_id"] = str(manifest["operation_id"])
    digest_input["mappings"] = [
        {
            "user_id": str(row["_user_id"]),
            "expected_login_id": row["expected_login_id"],
            "canonical_login_id": row["canonical_login_id"],
            "reason": row["reason"],
        }
        for row in sorted(manifest["mappings"], key=lambda item: item["_user_id"].hex)
    ]
    encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _needs_mapping(login_id):
    canonical = login_id.strip().lower()
    return not canonical or len(canonical) > 150 or canonical != login_id


class Command(BaseCommand):
    help = (
        "Validate or apply an explicit legacy Login ID mapping. Dry-run is the default; "
        "--apply requires --maintenance-confirmed and a reviewed manifest."
    )

    def add_arguments(self, parser):
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--actor-user-id", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--maintenance-confirmed", action="store_true")

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Login ID mapping requires PostgreSQL")
        if unicodedata.unidata_version != "15.0.0":
            raise CommandError("Login ID mapping requires Python Unicode 15.0.0")
        if options["apply"] and not options["maintenance_confirmed"]:
            raise CommandError("--apply requires --maintenance-confirmed")
        applied = MigrationRecorder(connection).applied_migrations()
        if REQUIRED_MIGRATION not in applied or CANONICAL_MIGRATION in applied:
            raise CommandError(
                "Login ID mapping is allowed only after accounts.0008 and before accounts.0009"
            )

        manifest = _manifest(options["manifest"])
        if manifest["source_database"] != str(connection.settings_dict["NAME"]):
            raise CommandError(
                "Manifest source_database does not match this connection"
            )
        actor_id = _uuid(options["actor_user_id"], "actor_user_id")
        if actor_id != manifest["approved_by"]:
            raise CommandError("The authenticated operator must match approved_by")
        digest = _intent_digest(manifest)

        if options["apply"]:
            operator_password = operator_auth.prompt_platform_password()
            with transaction.atomic():
                self._lock_users(manifest, actor_id)
                actor = self._load_actor(actor_id)
                operator_auth.require_platform_password(operator_password, actor)
                if self._already_applied(manifest, digest, actor):
                    mode = "Mapping operation was already applied; no rows changed"
                else:
                    prepared = self._validate(manifest)
                    self._apply(prepared, manifest, digest, actor)
                    mode = f"Applied reviewed mappings to {len(prepared)} exact User account(s)"
        else:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                    )
                actor = self._load_actor(actor_id)
                if self._already_applied(manifest, digest, actor):
                    mode = "Mapping operation was already applied; no rows changed"
                else:
                    prepared = self._validate(manifest)
                    mode = f"Validated {len(prepared)} reviewed mapping(s); no rows changed"
        self.stdout.write(mode)

    @staticmethod
    def _lock_users(manifest, actor_id):
        quote = connection.ops.quote_name
        user_table = quote(User._meta.db_table)
        role_table = quote(RoleAssignment._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f"LOCK TABLE {user_table} IN SHARE ROW EXCLUSIVE MODE")
        mapping_ids = {row["_user_id"] for row in manifest["mappings"]}
        target_ids = mapping_ids | {actor_id}
        locked_users = set(
            User.objects.select_for_update()
            .filter(pk__in=target_ids)
            .order_by("id")
            .values_list("pk", flat=True)
        )
        if locked_users != target_ids:
            raise CommandError("A mapped User UUID or Platform operator was not found")

        # Prevent role changes while the actor's Platform authorization is checked.
        with connection.cursor() as cursor:
            cursor.execute(f"LOCK TABLE {role_table} IN SHARE ROW EXCLUSIVE MODE")
        list(
            RoleAssignment.objects.select_for_update()
            .filter(user_id=actor_id)
            .order_by("id")
            .values_list("pk", flat=True)
        )

        # Lock current Company membership rows too, so the audit scope remains
        # tied to the exact account identity validated for this operation. New
        # memberships for these accounts wait on their locked User rows.
        list(
            TenantMembership.objects.select_for_update()
            .filter(user_id__in=mapping_ids)
            .order_by("id")
            .values_list("pk", flat=True)
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

    def _already_applied(self, manifest, digest, actor):
        operation_id = str(manifest["operation_id"])
        events = list(
            AccountSecurityEvent.objects.filter(
                action="login.canonicalize",
                metadata__operation_id=operation_id,
            ).order_by("subject_id")
        )
        if not events:
            return False
        expected_ids = {row["_user_id"] for row in manifest["mappings"]}
        if (
            len(events) != len(expected_ids)
            or {event.subject_id for event in events} != expected_ids
            or any(
                event.actor_id != actor.pk
                or event.metadata.get("intent_digest") != digest
                for event in events
            )
        ):
            raise CommandError(
                "A Login ID mapping operation ID conflicts with prior intent"
            )
        return True

    @staticmethod
    def _validate(manifest):
        rows = manifest["mappings"]
        by_id = {row["_user_id"]: row for row in rows}
        users = dict(User.objects.order_by("id").values_list("id", "login_id"))
        if set(by_id) - set(users):
            raise CommandError("A mapped User UUID was not found")
        mapped = {}
        for user_id, row in by_id.items():
            current = users[user_id]
            if current != row["expected_login_id"]:
                raise CommandError(
                    "A mapped Login ID no longer matches the reviewed snapshot"
                )
            candidate = row["canonical_login_id"]
            if (
                not candidate
                or len(candidate) > 150
                or candidate.strip().lower() != candidate
            ):
                raise CommandError(
                    "Each target must be a nonempty canonical Login ID of at most 150 characters"
                )
            if not _needs_mapping(current):
                raise CommandError(
                    "Manifest may only change a legacy noncanonical Login ID"
                )
            mapped[user_id] = candidate

        if any(
            _needs_mapping(login_id) and user_id not in mapped
            for user_id, login_id in users.items()
        ):
            raise CommandError(
                "Manifest must map every noncanonical Login ID before migration"
            )

        owners = {}
        for user_id, current in users.items():
            candidate = mapped.get(user_id, current)
            previous = owners.get(candidate)
            if previous is not None and previous != user_id:
                raise CommandError(
                    "Reviewed mappings contain a canonical Login ID collision"
                )
            owners[candidate] = user_id

        mapped_ids = list(mapped)
        memberships = {}
        for user_id, company_id in TenantMembership.objects.filter(
            user_id__in=mapped_ids
        ).values_list("user_id", "tenant_id"):
            memberships.setdefault(user_id, set()).add(company_id)
        if any(len(company_ids) > 1 for company_ids in memberships.values()):
            raise CommandError("A mapped account has more than one Company identity")
        return [
            {
                "user_id": user_id,
                "old_login_id": users[user_id],
                "new_login_id": new_login_id,
                "company_id": next(iter(memberships.get(user_id, set())), None),
            }
            for user_id, new_login_id in mapped.items()
        ]

    @staticmethod
    def _apply(prepared, manifest, digest, actor):
        table = connection.ops.quote_name(User._meta.db_table)
        changed_at = timezone.now()
        with connection.cursor() as cursor:
            for row in prepared:
                cursor.execute(
                    f"UPDATE {table} SET login_id = %s, auth_epoch = auth_epoch + 1, "
                    "updated_by_id = %s, updated_at = %s "
                    "WHERE id = %s AND login_id = %s",
                    [
                        row["new_login_id"],
                        actor.pk,
                        changed_at,
                        row["user_id"],
                        row["old_login_id"],
                    ],
                )
                if cursor.rowcount != 1:
                    raise CommandError("A mapped User account changed during apply")
                subject = User.objects.get(pk=row["user_id"])
                company = (
                    Tenant.objects.get(pk=row["company_id"])
                    if row["company_id"] is not None
                    else None
                )
                record_event(
                    action="login.canonicalize",
                    actor=actor,
                    subject=subject,
                    company=company,
                    reason="Reviewed Login ID canonicalization",
                    metadata={
                        "intent_digest": digest,
                        "operation_id": str(manifest["operation_id"]),
                    },
                )
