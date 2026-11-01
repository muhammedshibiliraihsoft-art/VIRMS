import io
import uuid

from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models.signals import pre_migrate
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import CompanyRoleGrant, RoleAssignment, User
from apps.accounts.policy import require_action
from apps.tenants.admin_scope import is_platform_admin_actor
from apps.tenants.models import Tenant, TenantMembership
from apps.tenants.selectors import company_context, visible_companies

LEGACY_STATE = [
    ("accounts", "0006_session_activity"),
    ("tenants", "0002_platform_scope"),
]
EARLY_STATE = [
    ("accounts", "0003_audit_immutability"),
    ("tenants", "0002_platform_scope"),
]
POST_0007_STATE = [
    ("accounts", "0007_one_company_account"),
    ("tenants", "0002_platform_scope"),
]
POST_0009_STATE = [
    ("accounts", "0009_canonical_login_id"),
    ("tenants", "0002_platform_scope"),
]
CURRENT_STATE = [
    ("accounts", "0010_platform_identity_preflight"),
    ("tenants", "0002_platform_scope"),
]


class PlatformIdentityPreflightTests(TransactionTestCase):
    """Exercise additive identity cutover checks against historical DB states."""

    reset_sequences = False

    def setUp(self):
        super().setUp()
        self.migrate(POST_0009_STATE)
        self.migrate(LEGACY_STATE)
        self.apps = (
            MigrationExecutor(connection).loader.project_state(LEGACY_STATE).apps
        )

    def tearDown(self):
        self.migrate(POST_0009_STATE)
        super().tearDown()

    @staticmethod
    def migrate(state):
        MigrationExecutor(connection).migrate(state)

    def create_legacy_user(
        self, *, back_office=False, company_roles=(), membership_count=2
    ):
        User = self.apps.get_model("accounts", "User")
        RoleAssignment = self.apps.get_model("accounts", "RoleAssignment")
        Tenant = self.apps.get_model("tenants", "Tenant")
        TenantMembership = self.apps.get_model("tenants", "TenantMembership")

        user_id = uuid.uuid4()
        user = User.objects.create(
            id=user_id,
            login_id=f"legacy-{user_id.hex}",
            email=f"legacy-{user_id.hex}@example.invalid",
            password="!",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        roles = (["back_office"] if back_office else []) + list(company_roles)
        for role in roles:
            RoleAssignment.objects.create(user=user, role=role, assigned_by=user)

        memberships = []
        for number in range(membership_count):
            company_id = uuid.uuid4()
            company = Tenant.objects.create(
                id=company_id,
                name=f"Legacy Company {number}",
                slug=f"legacy-{company_id.hex}",
            )
            memberships.append(
                TenantMembership.objects.create(
                    user=user, tenant=company, assigned_by=user
                )
            )
        return user.pk, memberships

    def assert_read_only_preflight_rejects(self):
        User = self.apps.get_model("accounts", "User")
        TenantMembership = self.apps.get_model("tenants", "TenantMembership")
        user_id = (
            User.objects.filter(is_superuser=True).values_list("pk", flat=True).get()
        )
        before_user = User.objects.get(pk=user_id)
        before_memberships = list(
            TenantMembership.objects.filter(user_id=user_id)
            .order_by("id")
            .values_list("id", "tenant_id")
        )
        output = io.StringIO()

        with self.assertRaisesRegex(
            CommandError, "Reviewed identity treatment required"
        ):
            call_command("check_account_identity_cutover", stdout=output)

        after_user = User.objects.get(pk=user_id)
        self.assertEqual(after_user.pk, before_user.pk)
        self.assertEqual(after_user.is_superuser, before_user.is_superuser)
        self.assertEqual(
            list(
                TenantMembership.objects.filter(user_id=user_id)
                .order_by("id")
                .values_list("id", "tenant_id")
            ),
            before_memberships,
        )

    def test_preflight_rejects_superuser_with_two_company_memberships_and_no_role(self):
        user_id, memberships = self.create_legacy_user()
        self.assertEqual(len(memberships), 2)
        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, "accounts_user"
                )
            }
        self.assertNotIn("account_kind", columns)
        self.assert_read_only_preflight_rejects()
        self.assertEqual(
            self.apps.get_model("accounts", "User").objects.get(pk=user_id).pk,
            user_id,
        )

    def test_migrate_command_preflights_before_0007_changes_legacy_identity(self):
        user_id, memberships = self.create_legacy_user()
        self.assertEqual(len(memberships), 2)

        with self.assertRaisesRegex(CommandError, "preflight"):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, "accounts_user"
                )
            }
            cursor.execute("SELECT id FROM accounts_user WHERE id=%s", [user_id])
            self.assertEqual(cursor.fetchone()[0], user_id)
            cursor.execute(
                "SELECT COUNT(*) FROM tenants_tenantmembership WHERE user_id=%s",
                [user_id],
            )
            self.assertEqual(cursor.fetchone()[0], 2)
        self.assertNotIn("account_kind", columns)

    def test_migrate_from_valid_prefix_before_company_grant_table_exists(self):
        self.migrate(EARLY_STATE)
        early_apps = (
            MigrationExecutor(connection).loader.project_state(EARLY_STATE).apps
        )
        User = early_apps.get_model("accounts", "User")
        Tenant = early_apps.get_model("tenants", "Tenant")
        TenantMembership = early_apps.get_model("tenants", "TenantMembership")

        user_id = uuid.uuid4()
        user = User.objects.create(
            id=user_id,
            login_id=f"early-{user_id.hex}",
            email=f"early-{user_id.hex}@example.invalid",
            password="!",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        company = Tenant.objects.create(
            name="Early Company",
            slug=f"early-{user_id.hex}",
        )
        membership = TenantMembership.objects.create(
            user=user,
            tenant=company,
            assigned_by=user,
        )

        with connection.cursor() as cursor:
            self.assertNotIn(
                "accounts_companyrolegrant", connection.introspection.table_names()
            )
            cursor.execute(
                "SELECT 1 FROM django_migrations "
                "WHERE app='accounts' AND name='0004_platform_scope'"
            )
            self.assertIsNone(cursor.fetchone())

        call_command("migrate", interactive=False, verbosity=0)

        current_apps = (
            MigrationExecutor(connection)
            .loader.project_state(
                MigrationExecutor(connection).loader.graph.leaf_nodes()
            )
            .apps
        )
        CurrentUser = current_apps.get_model("accounts", "User")
        CurrentMembership = current_apps.get_model("tenants", "TenantMembership")
        self.assertEqual(CurrentUser.objects.get(pk=user_id).account_kind, "company")
        self.assertTrue(
            CurrentMembership.objects.filter(
                pk=membership.pk,
                user_id=user_id,
                tenant_id=company.pk,
            ).exists()
        )

    def test_company_role_added_after_preflight_is_rejected_without_history_loss(self):
        user_id, memberships = self.create_legacy_user(back_office=True)
        membership_ids = [membership.pk for membership in memberships]
        injected = []

        def add_company_role_after_guard(sender, *, plan, using, **kwargs):
            if getattr(sender, "label", None) != "accounts" or injected:
                return
            if not any(
                migration.app_label == "accounts"
                and migration.name == "0007_one_company_account"
                and not backwards
                for migration, backwards in plan
            ):
                return
            RoleAssignment = self.apps.get_model("accounts", "RoleAssignment")
            RoleAssignment.objects.using(using).create(
                user_id=user_id,
                role="accountant",
                assigned_by_id=user_id,
            )
            injected.append(True)

        pre_migrate.connect(add_company_role_after_guard, weak=False)
        try:
            with self.assertRaisesRegex(
                RuntimeError, "Platform identity preflight rejected"
            ):
                call_command("migrate", interactive=False, verbosity=0)
        finally:
            pre_migrate.disconnect(add_company_role_after_guard)

        self.assertEqual(injected, [True])
        migrated_apps = (
            MigrationExecutor(connection).loader.project_state(POST_0009_STATE).apps
        )
        CurrentUser = migrated_apps.get_model("accounts", "User")
        CurrentRole = migrated_apps.get_model("accounts", "RoleAssignment")
        CurrentMembership = migrated_apps.get_model("tenants", "TenantMembership")
        self.assertEqual(CurrentUser.objects.get(pk=user_id).account_kind, "platform")
        self.assertCountEqual(
            CurrentRole.objects.filter(user_id=user_id).values_list("role", flat=True),
            ["back_office", "accountant"],
        )
        self.assertEqual(
            list(
                CurrentMembership.objects.filter(user_id=user_id)
                .order_by("id")
                .values_list("id", flat=True)
            ),
            sorted(membership_ids),
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM django_migrations "
                "WHERE app='accounts' AND name='0010_platform_identity_preflight'"
            )
            self.assertIsNone(cursor.fetchone())

    def test_migrate_command_preserves_backoffice_and_company_history_on_rejection(
        self,
    ):
        user_id, memberships = self.create_legacy_user(
            back_office=True, company_roles=("accountant",)
        )
        Grant = self.apps.get_model("accounts", "CompanyRoleGrant")
        for membership in memberships:
            Grant.objects.create(
                membership_id=membership.pk,
                role="accountant",
                assigned_by_id=user_id,
            )

        with self.assertRaisesRegex(CommandError, "preflight"):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, "accounts_user"
                )
            }
        RoleAssignment = self.apps.get_model("accounts", "RoleAssignment")
        self.assertCountEqual(
            RoleAssignment.objects.filter(user_id=user_id).values_list(
                "role", flat=True
            ),
            ["back_office", "accountant"],
        )
        self.assertEqual(Grant.objects.filter(membership__user_id=user_id).count(), 2)
        self.assertNotIn("account_kind", columns)

    def test_preflight_rejects_mixed_business_role_and_grant_history(self):
        user_id, memberships = self.create_legacy_user(
            back_office=True, company_roles=("accountant",)
        )
        Grant = self.apps.get_model("accounts", "CompanyRoleGrant")
        for membership in memberships:
            Grant.objects.create(
                membership_id=membership.pk,
                role="accountant",
                assigned_by_id=user_id,
            )
        self.assert_read_only_preflight_rejects()
        self.assertEqual(
            Grant.objects.filter(
                membership_id__in=[row.pk for row in memberships]
            ).count(),
            2,
        )

    def test_preflight_accepts_explicit_backoffice_only_platform_candidate(self):
        user_id, memberships = self.create_legacy_user(back_office=True)
        self.assertEqual(len(memberships), 2)
        output = io.StringIO()

        call_command("check_account_identity_cutover", stdout=output)

        self.assertIn("passed", output.getvalue())
        self.assertEqual(
            self.apps.get_model("accounts", "User").objects.get(pk=user_id).pk,
            user_id,
        )

    def test_explicit_backoffice_only_identity_passes_successor_migration(self):
        user_id, memberships = self.create_legacy_user(back_office=True)
        membership_ids = [row.pk for row in memberships]
        self.migrate(POST_0009_STATE)

        call_command("migrate", interactive=False, verbosity=0)

        current_apps = (
            MigrationExecutor(connection).loader.project_state(CURRENT_STATE).apps
        )
        User = current_apps.get_model("accounts", "User")
        RoleAssignment = current_apps.get_model("accounts", "RoleAssignment")
        TenantMembership = current_apps.get_model("tenants", "TenantMembership")
        self.assertEqual(User.objects.get(pk=user_id).account_kind, "platform")
        self.assertEqual(
            list(
                RoleAssignment.objects.filter(user_id=user_id).values_list(
                    "role", flat=True
                )
            ),
            ["back_office"],
        )
        self.assertEqual(
            list(
                TenantMembership.objects.filter(user_id=user_id)
                .order_by("id")
                .values_list("id", flat=True)
            ),
            sorted(membership_ids),
        )

    def test_successor_preflight_rejects_0007_misclassification_without_data_loss(self):
        user_id, memberships = self.create_legacy_user(company_roles=("accountant",))
        RoleAssignment = self.apps.get_model("accounts", "RoleAssignment")
        role_ids = list(
            RoleAssignment.objects.filter(user_id=user_id)
            .order_by("id")
            .values_list("id", flat=True)
        )
        membership_ids = [row.pk for row in memberships]

        self.migrate(POST_0007_STATE)
        self.migrate(POST_0009_STATE)
        current_apps = (
            MigrationExecutor(connection).loader.project_state(POST_0009_STATE).apps
        )
        CurrentUser = current_apps.get_model("accounts", "User")
        self.assertEqual(CurrentUser.objects.get(pk=user_id).account_kind, "platform")

        output = io.StringIO()
        with self.assertRaisesRegex(
            CommandError, "Reviewed identity treatment required"
        ):
            call_command("check_account_identity_cutover", stdout=output)
        with self.assertRaises(RuntimeError):
            self.migrate(CURRENT_STATE)

        self.assertEqual(CurrentUser.objects.get(pk=user_id).pk, user_id)
        self.assertEqual(CurrentUser.objects.get(pk=user_id).account_kind, "platform")
        self.assertEqual(
            list(
                current_apps.get_model("accounts", "RoleAssignment")
                .objects.filter(user_id=user_id)
                .order_by("id")
                .values_list("id", flat=True)
            ),
            role_ids,
        )
        self.assertEqual(
            list(
                current_apps.get_model("tenants", "TenantMembership")
                .objects.filter(user_id=user_id)
                .order_by("id")
                .values_list("id", flat=True)
            ),
            sorted(membership_ids),
        )

    def test_successor_preflight_rejects_superuser_only_platform(self):
        user_id, memberships = self.create_legacy_user(membership_count=0)
        self.assertEqual(memberships, [])

        self.migrate(POST_0007_STATE)
        self.migrate(POST_0009_STATE)
        current_apps = (
            MigrationExecutor(connection).loader.project_state(POST_0009_STATE).apps
        )
        User = current_apps.get_model("accounts", "User")
        self.assertEqual(User.objects.get(pk=user_id).account_kind, "platform")

        output = io.StringIO()
        with self.assertRaisesRegex(
            CommandError, "Reviewed identity treatment required"
        ):
            call_command("check_account_identity_cutover", stdout=output)
        with self.assertRaises(RuntimeError):
            self.migrate(CURRENT_STATE)

        self.assertEqual(User.objects.get(pk=user_id).pk, user_id)
        self.assertEqual(User.objects.get(pk=user_id).account_kind, "platform")


class AmbiguousPlatformRuntimeDenialTests(TestCase):
    def test_platform_superuser_with_company_history_has_no_platform_or_business_authority(
        self,
    ):
        user = User.objects.create_superuser(
            login_id="ambiguous-platform",
            email="ambiguous-platform@example.invalid",
            password="Synthetic private test password 2026!",
        )
        RoleAssignment.objects.create(
            user=user, role=RoleAssignment.Role.BACK_OFFICE, assigned_by=user
        )
        RoleAssignment.objects.create(
            user=user, role=RoleAssignment.Role.ACCOUNTANT, assigned_by=user
        )
        companies = [
            Tenant.objects.create(name=f"Ambiguous {index}", slug=f"ambiguous-{index}")
            for index in range(2)
        ]
        memberships = [
            TenantMembership.objects.create(user=user, tenant=company, assigned_by=user)
            for company in companies
        ]
        for membership in memberships:
            CompanyRoleGrant.objects.create(
                membership=membership,
                role=CompanyRoleGrant.Role.ACCOUNTANT,
                assigned_by=user,
            )

        with self.assertRaises(PermissionDenied):
            require_action(user, "company.create")
        with self.assertRaises(PermissionDenied):
            require_action(user, "core.company.read", company=companies[0])
        self.assertFalse(is_platform_admin_actor(user))
        self.assertFalse(visible_companies(user).exists())
        self.assertEqual(company_context(user), ([], False))

        self.client.force_login(user)
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["roles"], [])
        self.assertEqual(response.json()["companies"], [])

    def test_superuser_without_explicit_backoffice_cannot_fall_back_to_company_grants(
        self,
    ):
        user = User.objects.create_superuser(
            login_id="platform-without-backoffice",
            email="platform-without-backoffice@example.invalid",
            password="Synthetic private test password 2026!",
        )
        company = Tenant.objects.create(name="No Back Office", slug="no-back-office")
        membership = TenantMembership.objects.create(
            user=user, tenant=company, assigned_by=user
        )
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            assigned_by=user,
        )

        with self.assertRaises(PermissionDenied):
            require_action(user, "core.company.read", company=company)
        self.assertFalse(is_platform_admin_actor(user))
        self.assertFalse(visible_companies(user).exists())

        self.client.force_login(user)
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["roles"], [])
        self.assertEqual(response.json()["companies"], [])
