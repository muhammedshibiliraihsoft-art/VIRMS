"""Database protection for ended authorization intervals."""

import uuid
from datetime import timedelta
from threading import Event, Thread

from django.db import DatabaseError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.accounts.models import CompanyRoleGrant, RoleAssignment, User
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership


class ScopeHistoryMonotonicTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.company = Tenant.objects.create(name="History", slug="history")
        self.branch = Branch.objects.create(tenant=self.company, name="History")

    def make_row(self, kind, effective_until):
        identity = uuid.uuid4().hex
        user = User.objects.create(
            login_id=identity,
            email=f"{identity}@example.invalid",
            password="!",
            account_kind="company",
        )
        start = self.now - timedelta(days=10)
        membership = TenantMembership.objects.create(
            user=user,
            tenant=self.company,
            assigned_by=user,
            effective_from=start,
            effective_until=effective_until if kind == "membership" else None,
        )
        if kind == "membership":
            return membership
        if kind == "role":
            return RoleAssignment.objects.create(
                user=user,
                role="investor",
                assigned_by=user,
                effective_from=start,
                effective_until=effective_until,
            )
        if kind == "grant":
            return CompanyRoleGrant.objects.create(
                membership=membership,
                role="investor",
                assigned_by=user,
                effective_from=start,
                effective_until=effective_until,
            )
        return BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch,
            assigned_by=user,
            effective_from=start,
            effective_until=effective_until,
        )

    def test_closed_intervals_cannot_be_reopened_or_expanded_through_orm(self):
        ended = self.now - timedelta(days=2)
        for kind in ("membership", "role", "grant", "assignment"):
            for replacement in (
                None,
                self.now + timedelta(days=1),
                ended + timedelta(days=1),
            ):
                with self.subTest(kind=kind, replacement=replacement):
                    row = self.make_row(kind, ended)
                    with self.assertRaises(DatabaseError), transaction.atomic():
                        type(row).objects.filter(pk=row.pk).update(
                            effective_until=replacement
                        )
                    row.refresh_from_db()
                    self.assertEqual(row.effective_until, ended)

    def test_closed_intervals_cannot_be_reopened_through_raw_sql_or_save(self):
        ended = self.now - timedelta(days=2)
        for kind in ("membership", "role", "grant", "assignment"):
            for replacement in (
                None,
                self.now + timedelta(days=1),
                ended + timedelta(days=1),
            ):
                with self.subTest(kind=kind, method="raw", replacement=replacement):
                    row = self.make_row(kind, ended)
                    table = connection.ops.quote_name(row._meta.db_table)
                    with self.assertRaises(DatabaseError), transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f"UPDATE {table} SET effective_until=%s WHERE id=%s",
                                [replacement, row.pk],
                            )
                    row.refresh_from_db()
                    self.assertEqual(row.effective_until, ended)
            with self.subTest(kind=kind, method="save"):
                row = self.make_row(kind, ended)
                row.effective_until = self.now + timedelta(days=1)
                with self.assertRaises(DatabaseError), transaction.atomic():
                    row.save(update_fields=["effective_until"])
                row.refresh_from_db()
                self.assertEqual(row.effective_until, ended)

    def test_active_rows_can_close_and_ended_value_is_idempotent(self):
        ended = self.now - timedelta(days=2)
        for kind in ("membership", "role", "grant", "assignment"):
            for previous in (None, self.now + timedelta(days=1)):
                with self.subTest(kind=kind, previous=previous):
                    row = self.make_row(kind, previous)
                    row.effective_until = self.now
                    row.save(update_fields=["effective_until"])
                    row.refresh_from_db()
                    self.assertEqual(row.effective_until, self.now)
            with self.subTest(kind=kind, previous="ended"):
                row = self.make_row(kind, ended)
                row.save(update_fields=["effective_until"])
                row.refresh_from_db()
                self.assertEqual(row.effective_until, ended)
            with self.subTest(kind=kind, method="raw future to now"):
                row = self.make_row(kind, self.now + timedelta(days=1))
                table = connection.ops.quote_name(row._meta.db_table)
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE {table} SET effective_until=%s WHERE id=%s",
                        [self.now, row.pk],
                    )
                row.refresh_from_db()
                self.assertEqual(row.effective_until, self.now)

    def test_scheduled_end_cannot_be_removed_or_extended(self):
        future = self.now + timedelta(days=1)
        for kind in ("membership", "role", "grant", "assignment"):
            for replacement in (None, future + timedelta(days=1)):
                with self.subTest(kind=kind, replacement=replacement):
                    row = self.make_row(kind, future)
                    with self.assertRaises(DatabaseError), transaction.atomic():
                        type(row).objects.filter(pk=row.pk).update(
                            effective_until=replacement
                        )
                    row.refresh_from_db()
                    self.assertEqual(row.effective_until, future)

    def test_identity_fields_remain_immutable(self):
        other = User.objects.create(
            login_id="history-other",
            email="history-other@example.invalid",
            password="!",
            account_kind="company",
        )
        other_company = Tenant.objects.create(name="Other", slug="history-other")
        other_membership = TenantMembership.objects.create(
            user=other, tenant=self.company, assigned_by=other
        )
        other_branch = Branch.objects.create(tenant=self.company, name="Other")
        fields = {
            "membership": {"user_id": other.pk, "tenant_id": other_company.pk},
            "role": {"user_id": other.pk, "role": "media"},
            "grant": {
                "membership_id": other_membership.pk,
                "branch_id": other_branch.pk,
                "role": "media",
            },
            "assignment": {
                "membership_id": other_membership.pk,
                "branch_id": other_branch.pk,
            },
        }
        for kind in ("membership", "role", "grant", "assignment"):
            for field in ("id", "effective_from", *fields[kind]):
                with self.subTest(kind=kind, field=field):
                    row = self.make_row(kind, self.now - timedelta(days=2))
                    replacement = (
                        uuid.uuid4()
                        if field == "id"
                        else (
                            row.effective_from + timedelta(seconds=1)
                            if field == "effective_from"
                            else fields[kind][field]
                        )
                    )
                    with (
                        self.assertRaisesRegex(
                            DatabaseError, "Immutable scope identity"
                        ),
                        transaction.atomic(),
                    ):
                        type(row).objects.filter(pk=row.pk).update(
                            **{field: replacement}
                        )


class ScopeHistoryUpgradeTests(TransactionTestCase):
    previous = [
        ("accounts", "0011_login_state_expiry_idx"),
        ("tenants", "0002_platform_scope"),
    ]
    current = [
        ("accounts", "0012_scope_end_monotonic"),
        ("tenants", "0002_platform_scope"),
    ]

    def tearDown(self):
        MigrationExecutor(connection).migrate(self.current)
        super().tearDown()

    def test_upgrade_preserves_history_and_allows_future_end_now(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.previous)
        apps = executor.loader.project_state(self.previous).apps
        User = apps.get_model("accounts", "User")
        Tenant = apps.get_model("tenants", "Tenant")
        Membership = apps.get_model("tenants", "TenantMembership")
        BranchModel = apps.get_model("tenants", "Branch")
        Assignment = apps.get_model("tenants", "BranchAssignment")
        Role = apps.get_model("accounts", "RoleAssignment")
        Grant = apps.get_model("accounts", "CompanyRoleGrant")
        user = User.objects.create(
            login_id="upgrade-history",
            email="upgrade-history@example.invalid",
            password="!",
            account_kind="company",
        )
        company = Tenant.objects.create(name="Upgrade History", slug="upgrade-history")
        now = timezone.now()
        ended = Membership.objects.create(
            user=user,
            tenant=company,
            assigned_by=user,
            effective_from=now - timedelta(days=5),
            effective_until=now - timedelta(days=2),
        )
        active = Membership.objects.create(
            user=user,
            tenant=company,
            assigned_by=user,
            effective_from=now - timedelta(days=1),
            effective_until=now + timedelta(days=1),
        )
        branch = BranchModel.objects.create(tenant=company, name="Upgrade Branch")
        rows = [(ended, active)]
        for model, closed_scope, active_scope in (
            (
                Role,
                {"user": user, "role": "investor"},
                {"user": user, "role": "investor"},
            ),
            (
                Grant,
                {"membership": ended, "role": "investor"},
                {"membership": active, "role": "investor"},
            ),
            (
                Assignment,
                {"membership": ended, "branch": branch},
                {"membership": active, "branch": branch},
            ),
        ):
            closed_row = model.objects.create(
                assigned_by=user,
                effective_from=ended.effective_from,
                effective_until=ended.effective_until,
                **closed_scope,
            )
            active_row = model.objects.create(
                assigned_by=user,
                effective_from=active.effective_from,
                effective_until=active.effective_until,
                **active_scope,
            )
            rows.append((closed_row, active_row))
        before = [
            (row.pk, row.effective_from, row.effective_until)
            for pair in rows
            for row in pair
        ]

        MigrationExecutor(connection).migrate(self.current)
        after = []
        for closed_row, active_row in rows:
            for row in (closed_row, active_row):
                row.refresh_from_db()
                after.append((row.pk, row.effective_from, row.effective_until))
            with self.assertRaises(DatabaseError), transaction.atomic():
                type(closed_row).objects.filter(pk=closed_row.pk).update(
                    effective_until=None
                )
            type(active_row).objects.filter(pk=active_row.pk).update(
                effective_until=now
            )
            active_row.refresh_from_db()
            self.assertEqual(active_row.effective_until, now)
        self.assertEqual(after, before)


class ScopeHistoryConcurrencyTests(TransactionTestCase):
    def test_concurrent_update_cannot_reopen_a_just_closed_membership(self):
        MigrationExecutor(connection).migrate(
            [
                ("accounts", "0012_scope_end_monotonic"),
                ("tenants", "0002_platform_scope"),
            ]
        )
        user = User.objects.create(
            login_id="concurrent-history",
            email="concurrent-history@example.invalid",
            password="!",
            account_kind="company",
        )
        company = Tenant.objects.create(
            name="Concurrent History", slug="concurrent-history"
        )
        membership = TenantMembership.objects.create(
            user=user, tenant=company, assigned_by=user
        )
        locked = Event()
        attempted = Event()
        release = Event()
        errors = []
        outcomes = []

        def close_scope():
            close_old_connections()
            try:
                with transaction.atomic():
                    row = TenantMembership.objects.select_for_update().get(
                        pk=membership.pk
                    )
                    row.effective_until = timezone.now()
                    row.save(update_fields=["effective_until"])
                    locked.set()
                    if not release.wait(10):
                        raise RuntimeError("closure release timed out")
            except Exception as error:
                errors.append(str(error))
                locked.set()
            finally:
                close_old_connections()

        def reopen_scope():
            close_old_connections()
            try:
                if not locked.wait(10):
                    raise RuntimeError("closure lock timed out")
                attempted.set()
                try:
                    with transaction.atomic():
                        TenantMembership.objects.filter(pk=membership.pk).update(
                            effective_until=None
                        )
                except DatabaseError:
                    outcomes.append("rejected")
                else:
                    outcomes.append("allowed")
            except Exception as error:
                errors.append(str(error))
                attempted.set()
            finally:
                close_old_connections()

        closer = Thread(target=close_scope)
        reopener = Thread(target=reopen_scope)
        closer.start()
        reopener.start()
        try:
            self.assertTrue(locked.wait(10))
            self.assertTrue(attempted.wait(10))
        finally:
            release.set()
            closer.join(15)
            reopener.join(15)
        self.assertFalse(closer.is_alive())
        self.assertFalse(reopener.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(outcomes, ["rejected"])
        membership.refresh_from_db()
        self.assertIsNotNone(membership.effective_until)
