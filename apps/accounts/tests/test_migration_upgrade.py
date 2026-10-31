import importlib
import io
import json
import tempfile
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import (
    DatabaseError,
    close_old_connections,
    connection,
    connections,
    transaction,
)
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TransactionTestCase

OLD_FOUNDATION = [
    ("accounts", "0006_session_activity"),
    ("tenants", "0002_platform_scope"),
]
CURRENT_FOUNDATION = [
    ("accounts", "0009_canonical_login_id"),
    ("tenants", "0002_platform_scope"),
]
PRE_CANONICAL_FOUNDATION = [
    ("accounts", "0008_loginattempt_login_retry_after_idx"),
    ("tenants", "0002_platform_scope"),
]


class CompanyIdentityUpgradeTests(TransactionTestCase):
    """Rehearse the additive 0006 -> 0008 identity cutover on PostgreSQL."""

    reset_sequences = False

    def setUp(self):
        super().setUp()
        self.migrate_to_current()
        executor = MigrationExecutor(connection)
        executor.migrate(OLD_FOUNDATION)
        self.old_apps = executor.loader.project_state(OLD_FOUNDATION).apps

    def tearDown(self):
        self.migrate_to_current()
        super().tearDown()

    @staticmethod
    def migrate_to_current():
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def _create_legacy_rows(self, *, second_company=False):
        User = self.old_apps.get_model("accounts", "User")
        Tenant = self.old_apps.get_model("tenants", "Tenant")
        TenantMembership = self.old_apps.get_model("tenants", "TenantMembership")
        RoleAssignment = self.old_apps.get_model("accounts", "RoleAssignment")

        platform_id = uuid.uuid4()
        company_user_id = uuid.uuid4()
        platform = User.objects.create(
            id=platform_id,
            login_id=f"platform-{platform_id.hex}",
            email=f"platform-{platform_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
            is_staff=True,
            is_superuser=True,
            must_change_password=False,
        )
        company_user = User.objects.create(
            id=company_user_id,
            login_id=f"company-{company_user_id.hex}",
            email=f"company-{company_user_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
            is_superuser=False,
            is_staff=False,
            must_change_password=False,
        )
        first = Tenant.objects.create(
            id=uuid.uuid4(), name="Fixture One", slug=f"fixture-{uuid.uuid4().hex}"
        )
        membership = TenantMembership.objects.create(
            id=uuid.uuid4(), user=company_user, tenant=first, assigned_by=platform
        )
        role = RoleAssignment.objects.create(
            id=uuid.uuid4(), user=company_user, role="accountant", assigned_by=platform
        )
        second = None
        second_membership = None
        if second_company:
            second = Tenant.objects.create(
                id=uuid.uuid4(), name="Fixture Two", slug=f"fixture-{uuid.uuid4().hex}"
            )
            second_membership = TenantMembership.objects.create(
                id=uuid.uuid4(), user=company_user, tenant=second, assigned_by=platform
            )
        return (
            platform.pk,
            company_user.pk,
            first.pk,
            membership.pk,
            role.pk,
            second,
            second_membership.pk if second_membership else None,
        )

    def test_supported_upgrade_preserves_uuid_history_and_rejects_second_company(self):
        platform_id, user_id, company_id, membership_id, role_id, _, _ = (
            self._create_legacy_rows()
        )
        executor = MigrationExecutor(connection)
        executor.migrate(CURRENT_FOUNDATION)

        from apps.accounts.models import CompanyRoleGrant, RoleAssignment, User
        from apps.tenants.models import Tenant, TenantMembership

        self.assertEqual(User.objects.get(pk=platform_id).account_kind, "platform")
        self.assertEqual(User.objects.get(pk=user_id).account_kind, "company")
        self.assertTrue(Tenant.objects.filter(pk=company_id).exists())
        self.assertTrue(
            TenantMembership.objects.filter(pk=membership_id, user_id=user_id).exists()
        )
        self.assertEqual(
            RoleAssignment.objects.get(pk=role_id, user_id=user_id).role,
            "accountant",
        )
        # A legacy global role is retained as history; cutover never guesses a
        # Company grant from the role and membership Cartesian product.
        self.assertFalse(
            CompanyRoleGrant.objects.filter(membership_id=membership_id).exists()
        )
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(TenantMembership.objects.count(), 1)

        other = Tenant.objects.create(name="Unmapped", slug="unmapped")
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                TenantMembership.objects.create(
                    user_id=user_id, tenant=other, assigned_by_id=platform_id
                )

    def test_upgrade_refuses_existing_multi_company_account_without_deleting_rows(self):
        (_, user_id, _, membership_id, _, second, second_membership_id) = (
            self._create_legacy_rows(second_company=True)
        )
        self.assertIsNotNone(second)
        self.assertIsNotNone(second_membership_id)
        with self.assertRaises(DatabaseError):
            MigrationExecutor(connection).migrate(CURRENT_FOUNDATION)

        TenantMembership = self.old_apps.get_model("tenants", "TenantMembership")
        self.assertEqual(TenantMembership.objects.filter(user_id=user_id).count(), 2)
        self.assertTrue(TenantMembership.objects.filter(pk=membership_id).exists())
        # Preserve the failed-upgrade evidence above, then reverse only the
        # disposable schema to before its history guard so the fixture can be
        # removed and the test database restored for later tests.
        executor = MigrationExecutor(connection)
        executor.migrate(
            [("accounts", "0004_platform_scope"), ("tenants", "0002_platform_scope")]
        )
        old_apps = (
            MigrationExecutor(connection)
            .loader.project_state(
                [
                    ("accounts", "0004_platform_scope"),
                    ("tenants", "0002_platform_scope"),
                ]
            )
            .apps
        )
        old_membership = old_apps.get_model("tenants", "TenantMembership")
        old_membership.objects.filter(pk=second_membership_id, user_id=user_id).delete()
        self.migrate_to_current()

    def test_login_upgrade_stops_on_noncanonical_collision_without_rewriting_ids(self):
        User = self.old_apps.get_model("accounts", "User")
        first_id = uuid.uuid4()
        second_id = uuid.uuid4()
        User.objects.create(
            id=first_id,
            login_id="Echo",
            email=f"first-{first_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
        )
        User.objects.create(
            id=second_id,
            login_id=" echo ",
            email=f"second-{second_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
        )
        MigrationExecutor(connection).migrate(PRE_CANONICAL_FOUNDATION)

        with self.assertRaisesRegex(RuntimeError, "reviewed UUID-to-login mapping"):
            MigrationExecutor(connection).migrate(CURRENT_FOUNDATION)

        pre_canonical_apps = (
            MigrationExecutor(connection)
            .loader.project_state(PRE_CANONICAL_FOUNDATION)
            .apps
        )
        unchanged_user = pre_canonical_apps.get_model("accounts", "User")
        self.assertEqual(unchanged_user.objects.get(pk=first_id).login_id, "Echo")
        self.assertEqual(unchanged_user.objects.get(pk=second_id).login_id, " echo ")
        unchanged_user.objects.filter(pk__in=[first_id, second_id]).delete()
        self.migrate_to_current()

    def test_reviewed_login_mapping_is_dry_run_then_applies_exact_ids(self):
        _, first_id, company_id, _, _, _, _ = self._create_legacy_rows()
        User = self.old_apps.get_model("accounts", "User")
        second_id = uuid.uuid4()
        User.objects.create(
            id=second_id,
            login_id=" echo ",
            email=f"second-{second_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
        )
        User.objects.filter(pk=first_id).update(login_id="Echo")
        RoleAssignment = self.old_apps.get_model("accounts", "RoleAssignment")
        platform_id = (
            User.objects.filter(is_superuser=True).values_list("id", flat=True).get()
        )
        RoleAssignment.objects.create(
            user_id=platform_id,
            role="back_office",
            assigned_by_id=platform_id,
        )
        MigrationExecutor(connection).migrate(PRE_CANONICAL_FOUNDATION)

        manifest = {
            "format_version": "VIRMS-P1-LOGIN-MAP-1",
            "source_database": connection.settings_dict["NAME"],
            "approved_by": str(platform_id),
            "approval_reference": "disposable reviewed mapping fixture",
            "operation_id": str(uuid.uuid4()),
            "mappings": [
                {
                    "user_id": str(first_id),
                    "expected_login_id": "Echo",
                    "canonical_login_id": "echo-one",
                    "reason": "Resolve reviewed legacy identifier",
                },
                {
                    "user_id": str(second_id),
                    "expected_login_id": " echo ",
                    "canonical_login_id": "echo-two",
                    "reason": "Resolve reviewed legacy identifier",
                },
            ],
        }
        old_session = Client()
        from apps.accounts.models import User as CurrentUser

        old_session.force_login(CurrentUser.objects.get(pk=first_id))
        self.assertEqual(old_session.get("/api/v1/auth/me/").status_code, 200)
        self.assertEqual(CurrentUser.objects.get(pk=first_id).auth_epoch, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "login-map.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            output = io.StringIO()
            call_command(
                "canonicalize_legacy_login_ids",
                manifest=str(path),
                actor_user_id=str(platform_id),
                stdout=output,
            )
            self.assertEqual(User.objects.get(pk=first_id).login_id, "Echo")
            self.assertEqual(User.objects.get(pk=second_id).login_id, " echo ")
            self.assertEqual(CurrentUser.objects.get(pk=first_id).auth_epoch, 1)
            self.assertNotIn("Echo", output.getvalue())

            with patch(
                "apps.accounts.management.commands.operator_auth.prompt_platform_password",
                return_value="incorrect-operator-password",
            ):
                with self.assertRaisesMessage(
                    CommandError, "Platform Back Office authentication failed"
                ):
                    call_command(
                        "canonicalize_legacy_login_ids",
                        manifest=str(path),
                        actor_user_id=str(platform_id),
                        apply=True,
                        maintenance_confirmed=True,
                        stdout=output,
                    )
            self.assertEqual(User.objects.get(pk=first_id).login_id, "Echo")

            with patch(
                "apps.accounts.management.commands.operator_auth.prompt_platform_password",
                return_value="disposable-migration-fixture",
            ):
                call_command(
                    "canonicalize_legacy_login_ids",
                    manifest=str(path),
                    actor_user_id=str(platform_id),
                    apply=True,
                    maintenance_confirmed=True,
                    stdout=output,
                )
            self.assertEqual(User.objects.get(pk=first_id).login_id, "echo-one")
            self.assertEqual(User.objects.get(pk=second_id).login_id, "echo-two")
            first = User.objects.get(pk=first_id)
            self.assertEqual(first.auth_epoch, 2)
            self.assertEqual(first.updated_by_id, platform_id)
            replay = json.loads(json.dumps(manifest))
            replay["mappings"].reverse()
            replay["approved_by"] = str(platform_id).upper()
            replay["operation_id"] = replay["operation_id"].upper()
            for row in replay["mappings"]:
                row["user_id"] = row["user_id"].upper()
            path.write_text(json.dumps(replay), encoding="utf-8")
            with patch(
                "apps.accounts.management.commands.operator_auth.prompt_platform_password",
                return_value="disposable-migration-fixture",
            ):
                call_command(
                    "canonicalize_legacy_login_ids",
                    manifest=str(path),
                    actor_user_id=str(platform_id),
                    apply=True,
                    maintenance_confirmed=True,
                    stdout=output,
                )
            self.assertEqual(User.objects.get(pk=first_id).auth_epoch, 2)
        self.assertEqual(old_session.get("/api/v1/auth/me/").status_code, 401)

        AccountSecurityEvent = self.old_apps.get_model(
            "accounts", "AccountSecurityEvent"
        )
        self.assertEqual(
            AccountSecurityEvent.objects.filter(
                action="login.canonicalize", subject_id__in=[first_id, second_id]
            ).count(),
            2,
        )
        first_event = AccountSecurityEvent.objects.get(
            action="login.canonicalize", subject_id=first_id
        )
        self.assertEqual(first_event.actor_id, platform_id)
        self.assertEqual(first_event.company_id, company_id)
        self.assertEqual(first_event.reason, "Reviewed Login ID canonicalization")
        self.assertNotIn("Echo", first_event.reason)
        self.assertNotIn("echo-one", first_event.reason)
        MigrationExecutor(connection).migrate(CURRENT_FOUNDATION)

    def test_reviewed_login_mapping_rejects_colliding_targets_without_changes(self):
        _, first_id, _, _, _, _, _ = self._create_legacy_rows()
        User = self.old_apps.get_model("accounts", "User")
        second_id = uuid.uuid4()
        User.objects.create(
            id=second_id,
            login_id=" echo ",
            email=f"second-{second_id.hex}@example.invalid",
            password=make_password("disposable-migration-fixture"),
            is_active=True,
        )
        User.objects.filter(pk=first_id).update(login_id="Echo")
        RoleAssignment = self.old_apps.get_model("accounts", "RoleAssignment")
        platform_id = (
            User.objects.filter(is_superuser=True).values_list("id", flat=True).get()
        )
        RoleAssignment.objects.create(
            user_id=platform_id,
            role="back_office",
            assigned_by_id=platform_id,
        )
        MigrationExecutor(connection).migrate(PRE_CANONICAL_FOUNDATION)
        manifest = {
            "format_version": "VIRMS-P1-LOGIN-MAP-1",
            "source_database": connection.settings_dict["NAME"],
            "approved_by": str(platform_id),
            "approval_reference": "disposable collision fixture",
            "operation_id": str(uuid.uuid4()),
            "mappings": [
                {
                    "user_id": str(user_id),
                    "expected_login_id": previous,
                    "canonical_login_id": "echo",
                    "reason": "Collision must fail closed",
                }
                for user_id, previous in ((first_id, "Echo"), (second_id, " echo "))
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "login-map.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesMessage(CommandError, "canonical Login ID collision"):
                with patch(
                    "apps.accounts.management.commands.operator_auth.prompt_platform_password",
                    return_value="disposable-migration-fixture",
                ):
                    call_command(
                        "canonicalize_legacy_login_ids",
                        manifest=str(path),
                        actor_user_id=str(platform_id),
                        apply=True,
                        maintenance_confirmed=True,
                    )

        self.assertEqual(User.objects.get(pk=first_id).login_id, "Echo")
        self.assertEqual(User.objects.get(pk=second_id).login_id, " echo ")
        AccountSecurityEvent = self.old_apps.get_model(
            "accounts", "AccountSecurityEvent"
        )
        self.assertFalse(
            AccountSecurityEvent.objects.filter(action="login.canonicalize").exists()
        )
        executor = MigrationExecutor(connection)
        cleanup_targets = [
            ("accounts", "0004_platform_scope"),
            ("tenants", "0002_platform_scope"),
        ]
        executor.migrate(cleanup_targets)
        cleanup_apps = (
            MigrationExecutor(connection).loader.project_state(cleanup_targets).apps
        )
        TenantMembership = cleanup_apps.get_model("tenants", "TenantMembership")
        RoleAssignment = cleanup_apps.get_model("accounts", "RoleAssignment")
        User = cleanup_apps.get_model("accounts", "User")
        TenantMembership.objects.filter(user_id__in=[first_id, second_id]).delete()
        RoleAssignment.objects.filter(user_id__in=[first_id, second_id]).delete()
        User.objects.filter(pk__in=[first_id, second_id]).delete()
        self.migrate_to_current()

    def test_reviewed_login_mapping_requires_platform_backoffice_actor(self):
        _, target_id, _, _, _, _, _ = self._create_legacy_rows()
        User = self.old_apps.get_model("accounts", "User")
        User.objects.filter(pk=target_id).update(login_id="Echo")
        MigrationExecutor(connection).migrate(PRE_CANONICAL_FOUNDATION)
        manifest = {
            "format_version": "VIRMS-P1-LOGIN-MAP-1",
            "source_database": connection.settings_dict["NAME"],
            "approved_by": str(target_id),
            "approval_reference": "disposable authorization fixture",
            "operation_id": str(uuid.uuid4()),
            "mappings": [
                {
                    "user_id": str(target_id),
                    "expected_login_id": "Echo",
                    "canonical_login_id": "echo-reviewed",
                    "reason": "Test that Company users cannot run identity cutover",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "login-map.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesMessage(
                CommandError, "active Platform Back Office account"
            ):
                call_command(
                    "canonicalize_legacy_login_ids",
                    manifest=str(path),
                    actor_user_id=str(target_id),
                )

        cleanup_targets = [
            ("accounts", "0004_platform_scope"),
            ("tenants", "0002_platform_scope"),
        ]
        MigrationExecutor(connection).migrate(cleanup_targets)
        cleanup_apps = (
            MigrationExecutor(connection).loader.project_state(cleanup_targets).apps
        )
        cleanup_user = cleanup_apps.get_model("accounts", "User")
        cleanup_role = cleanup_apps.get_model("accounts", "RoleAssignment")
        cleanup_membership = cleanup_apps.get_model("tenants", "TenantMembership")
        cleanup_membership.objects.filter(user_id=target_id).delete()
        cleanup_role.objects.filter(user_id=target_id).delete()
        cleanup_user.objects.filter(pk=target_id).delete()
        self.migrate_to_current()

    def test_login_id_preflight_lock_closes_concurrent_insert_gap(self):
        self._create_legacy_rows()
        MigrationExecutor(connection).migrate(PRE_CANONICAL_FOUNDATION)
        migration_apps = (
            MigrationExecutor(connection)
            .loader.project_state(PRE_CANONICAL_FOUNDATION)
            .apps
        )
        migration = importlib.import_module(
            "apps.accounts.migrations.0009_canonical_login_id"
        )
        race_user_id = uuid.uuid4()
        started = threading.Event()
        finished = threading.Event()
        failures = []

        def concurrent_insert():
            close_old_connections()
            try:
                from apps.accounts.models import User as CurrentUser

                user = CurrentUser(
                    id=race_user_id,
                    login_id="  Race Writer  ",
                    email=f"race-{race_user_id.hex}@example.invalid",
                    password=make_password("disposable-race-fixture"),
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                    must_change_password=False,
                    account_kind="company",
                    auth_epoch=1,
                )
                with connections["default"].cursor() as cursor:
                    cursor.execute(
                        "SET application_name = 'virms_login_preflight_race_test'"
                    )
                started.set()
                # Bypass the model save override so only the database trigger
                # can canonicalize this insert.
                user.save_base(force_insert=True)
            except BaseException as error:  # surfaced in the main test thread
                failures.append(error)
            finally:
                finished.set()
                close_old_connections()

        writer = threading.Thread(target=concurrent_insert, daemon=True)
        migration_installed = False
        started_before_install = False
        blocked_by_preflight = False
        try:
            with transaction.atomic():
                with connection.schema_editor(atomic=False) as editor:
                    migration.preflight_existing_login_ids(migration_apps, editor)
                    writer.start()
                    started_before_install = started.wait(5)
                    if started_before_install:
                        deadline = time.monotonic() + 5
                        while time.monotonic() < deadline and not finished.is_set():
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT wait_event_type FROM pg_stat_activity "
                                    "WHERE application_name = %s",
                                    ["virms_login_preflight_race_test"],
                                )
                                state = cursor.fetchone()
                            if state and state[0] == "Lock":
                                blocked_by_preflight = True
                                break
                            finished.wait(0.05)
                    migration.install_login_id_database_policy(migration_apps, editor)
                    migration_installed = True

            writer.join(timeout=10)
            self.assertTrue(started_before_install, "concurrent insert did not start")
            self.assertTrue(
                blocked_by_preflight, "insert did not wait for migration lock"
            )
            self.assertFalse(writer.is_alive(), "concurrent insert did not finish")
            self.assertEqual(failures, [])
            User = migration_apps.get_model("accounts", "User")
            self.assertEqual(
                User.objects.get(pk=race_user_id).login_id,
                "race writer",
            )
        finally:
            if writer.ident is not None:
                writer.join(timeout=10)
            if migration_installed:
                with connection.schema_editor(atomic=False) as editor:
                    migration.remove_login_id_database_policy(migration_apps, editor)
            self.migrate_to_current()
