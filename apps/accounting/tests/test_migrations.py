from uuid import uuid4

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.recorder import MigrationRecorder
from django.test import TransactionTestCase

from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountingAccount
from apps.tenants.models import Tenant


class AccountingMigrationSafetyTests(TransactionTestCase):
    reset_sequences = False

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    @staticmethod
    def migrate_accounting(target):
        MigrationExecutor(connection).migrate([("accounting", target)])

    def create_account(self):
        suffix = uuid4().hex
        company = Tenant.objects.create(
            name="Accounting migration fixture",
            slug=f"acct-migration-{suffix[:36]}",
        )
        actor = make_user(
            f"acct-migration-{suffix}", role="accountant", tenant=company
        )
        return AccountingAccount.objects.create(
            tenant=company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Migration fixture account",
            created_by=actor,
        )

    def test_full_downgrade_with_accounting_data_is_blocked_without_partial_rollback(self):
        account = self.create_account()

        with self.assertRaises(IrreversibleError):
            self.migrate_accounting(None)

        self.assertTrue(AccountingAccount.objects.filter(pk=account.pk).exists())
        self.assertIn(
            ("accounting", "0003_relation_integrity"),
            MigrationRecorder(connection).applied_migrations(),
        )

    def test_empty_accounting_schema_can_be_downgraded_and_reapplied(self):
        self.migrate_accounting(None)
        table_names = set(connection.introspection.table_names())
        self.assertNotIn("accounting_accountingaccount", table_names)
        self.assertNotIn("accounting_accountingevent", table_names)

        self.migrate_accounting("0003_relation_integrity")
        table_names = set(connection.introspection.table_names())
        self.assertIn("accounting_accountingaccount", table_names)
        self.assertIn("accounting_accountingevent", table_names)

    def test_archive_guard_migration_cannot_be_reversed_with_catalogue_data(self):
        self.migrate_accounting("0002_history_and_archive_guards")
        account = self.create_account()

        with self.assertRaises(IrreversibleError):
            self.migrate_accounting("0001_initial")

        self.assertTrue(AccountingAccount.objects.filter(pk=account.pk).exists())
        self.assertIn(
            ("accounting", "0002_history_and_archive_guards"),
            MigrationRecorder(connection).applied_migrations(),
        )

    def test_initial_accounting_schema_cannot_be_reversed_with_catalogue_data(self):
        self.migrate_accounting("0001_initial")
        account = self.create_account()

        with self.assertRaises(IrreversibleError):
            self.migrate_accounting(None)

        self.assertTrue(AccountingAccount.objects.filter(pk=account.pk).exists())
        self.assertIn(
            ("accounting", "0001_initial"),
            MigrationRecorder(connection).applied_migrations(),
        )
