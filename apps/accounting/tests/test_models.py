from decimal import Decimal
from uuid import uuid4

from django.db import DatabaseError, IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.accounts.tests.test_users import make_user
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingApplication,
    AccountingCategory,
    AccountingEvent,
    AccountingIdempotencyRecord,
)
from apps.tenants.models import Branch, CompanyModuleState, Tenant


class AccountingModelTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="model-north")
        self.branch = Branch.objects.create(tenant=self.company, name="Main")
        self.actor = make_user("p4-model-accountant", role="accountant", tenant=self.company)
        self.revision = CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=self.actor,
        )
        self.income_category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.INCOME,
            label="  Service Income ",
            created_by=self.actor,
        )
        self.expense_category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.EXPENSE,
            label="Materials",
            created_by=self.actor,
        )
        self.account = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Till",
            created_by=self.actor,
        )

    def event(self, event_type, *, amount="100.00", category=None, **kwargs):
        values = {
            "tenant": self.company,
            "branch": self.branch,
            "event_type": event_type,
            "amount": Decimal(amount),
            "effective_at": timezone.now(),
            "actor": self.actor,
            "module_revision": self.revision,
            "category": category,
            "description": "Verified source entry",
            "source_reference": "SOURCE-1",
        }
        values.update(kwargs)
        return AccountingEvent.objects.create(**values)

    def test_labels_normalize_and_active_names_are_unique_per_company_and_kind(self):
        self.assertEqual(self.income_category.normalized_label, "service income")
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingCategory.objects.create(
                tenant=self.company,
                kind=AccountingCategory.Kind.INCOME,
                label="SERVICE   INCOME",
                created_by=self.actor,
            )


    def test_account_history_blocks_archive_even_when_net_balance_is_zero(self):
        opening = self.event(
            AccountingEvent.EventType.OPENING_BALANCE,
            amount="50.00",
            category=None,
        )
        AccountMovement.objects.create(
            tenant=self.company,
            event=opening,
            account=self.account,
            delta=Decimal("50.00"),
        )
        reversal = self.event(
            AccountingEvent.EventType.OPENING_BALANCE,
            amount="50.00",
            category=None,
            effect_sign=-1,
            reversal_of=opening,
            correction_reason="False receipt",
            effective_at=opening.effective_at,
            description=opening.description,
            source_reference=opening.source_reference,
        )
        AccountMovement.objects.create(
            tenant=self.company,
            event=reversal,
            account=self.account,
            delta=Decimal("-50.00"),
        )
        self.account.is_active = False
        self.account.archived_at = timezone.now()
        self.account.archived_by = self.actor
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.account.save()

    def test_zero_balance_account_without_history_can_archive_once(self):
        self.account.is_active = False
        self.account.archived_at = timezone.now()
        self.account.archived_by = self.actor
        self.account.save()
        self.account.refresh_from_db()
        self.assertFalse(self.account.is_active)
        with self.assertRaises(ValueError):
            self.account.is_active = True
            self.account.archived_at = None
            self.account.archived_by = None
            self.account.save()

    def test_used_category_can_be_archived_without_losing_event_history(self):
        income = self.event(
            AccountingEvent.EventType.INCOME,
            category=self.income_category,
        )
        self.income_category.is_active = False
        self.income_category.archived_at = timezone.now()
        self.income_category.archived_by = self.actor
        self.income_category.save()
        income.refresh_from_db()
        self.assertEqual(income.category_id, self.income_category.pk)
        self.assertFalse(income.category.is_active)

    def test_events_and_movements_are_append_only_in_database(self):
        income = self.event(
            AccountingEvent.EventType.INCOME,
            category=self.income_category,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.filter(pk=income.pk).update(description="rewrite")
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.filter(pk=income.pk).delete()

        receipt = self.event(
            AccountingEvent.EventType.RECEIPT,
            amount="25.00",
            category=None,
        )
        target = self.event(
            AccountingEvent.EventType.INCOME,
            category=self.income_category,
        )
        movement = AccountMovement.objects.create(
            tenant=self.company,
            event=receipt,
            account=self.account,
            delta=Decimal("25.00"),
        )
        AccountingApplication.objects.create(
            tenant=self.company,
            source_event=receipt,
            target_event=target,
            amount=Decimal("25.00"),
            actor=self.actor,
            module_revision=self.revision,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountMovement.objects.filter(pk=movement.pk).update(delta=Decimal("2.00"))

    def test_application_and_idempotency_records_are_append_only(self):
        income = self.event(
            AccountingEvent.EventType.INCOME,
            category=self.income_category,
        )
        receipt = self.event(
            AccountingEvent.EventType.RECEIPT,
            amount="10.00",
            category=None,
        )
        AccountMovement.objects.create(
            tenant=self.company,
            event=receipt,
            account=self.account,
            delta=Decimal("10.00"),
        )
        application = AccountingApplication.objects.create(
            tenant=self.company,
            source_event=receipt,
            target_event=income,
            amount=Decimal("10.00"),
            actor=self.actor,
            module_revision=self.revision,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingApplication.objects.filter(pk=application.pk).update(
                amount=Decimal("9.00")
            )

        idem = AccountingIdempotencyRecord.objects.create(
            tenant=self.company,
            actor=self.actor,
            key="intent-1",
            method="POST",
            path="/api/v1/accounting/incomes/",
            request_hash="a" * 64,
            response_status=201,
            response_body={"id": str(income.pk)},
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingIdempotencyRecord.objects.filter(pk=idem.pk).delete()

    def test_category_and_account_records_cannot_be_deleted(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingCategory.objects.filter(pk=self.income_category.pk).delete()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingAccount.objects.filter(pk=self.account.pk).delete()

    def test_runtime_role_cannot_update_delete_or_truncate_accounting_history(self):
        role = f"virms_test_accounting_{uuid4().hex}"
        quoted_role = connection.ops.quote_name(role)
        history_tables = (
            "accounting_accountingevent",
            "accounting_accountingapplication",
            "accounting_accountmovement",
            "accounting_accountingidempotencyrecord",
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE ROLE {quoted_role} NOLOGIN")
            cursor.execute(f"GRANT USAGE ON SCHEMA public TO {quoted_role}")
            for table in history_tables:
                cursor.execute(
                    f"GRANT SELECT, INSERT ON {table} TO {quoted_role}"
                )
        try:
            for table in history_tables:
                for statement in (
                    f"UPDATE {table} SET id = id WHERE FALSE",
                    f"DELETE FROM {table} WHERE FALSE",
                    f"TRUNCATE {table}",
                ):
                    with self.subTest(statement=statement):
                        with self.assertRaises(DatabaseError), transaction.atomic():
                            with connection.cursor() as cursor:
                                cursor.execute(f"SET LOCAL ROLE {quoted_role}")
                                cursor.execute(statement)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP OWNED BY {quoted_role}")
                cursor.execute(f"DROP ROLE {quoted_role}")

    def test_event_constraints_reject_nonpositive_amounts(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.event(
                AccountingEvent.EventType.INCOME,
                amount="0.00",
                category=self.income_category,
            )

    def test_application_cannot_link_an_event_to_itself(self):
        receipt = self.event(
            AccountingEvent.EventType.RECEIPT,
            amount="10.00",
            category=None,
        )
        income = self.event(
            AccountingEvent.EventType.INCOME,
            amount="10.00",
            category=self.income_category,
        )
        AccountMovement.objects.create(
            tenant=self.company,
            event=receipt,
            account=self.account,
            delta=Decimal("10.00"),
        )
        AccountingApplication.objects.create(
            tenant=self.company,
            source_event=receipt,
            target_event=income,
            amount=Decimal("10.00"),
            actor=self.actor,
            module_revision=self.revision,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingApplication.objects.create(
                tenant=self.company,
                source_event=receipt,
                target_event=receipt,
                amount=Decimal("1.00"),
                actor=self.actor,
                module_revision=self.revision,
            )
class AccountingDeferredIntegrityTests(TransactionTestCase):
    """Exercise deferred cross-row PostgreSQL guards across transactions."""

    reset_sequences = True

    def setUp(self):
        self.company = Tenant.objects.create(name="Integrity", slug="model-integrity")
        self.branch = Branch.objects.create(tenant=self.company, name="Main")
        self.actor = make_user("p4-integrity-accountant", role="accountant", tenant=self.company)
        self.revision = CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=self.actor,
        )
        self.category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.INCOME,
            label="Income",
            created_by=self.actor,
        )
        self.account = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Cash",
            created_by=self.actor,
        )

    def _event(self, event_type, *, amount="100.00", category=None, **kwargs):
        values = {
            "tenant": self.company,
            "branch": self.branch,
            "event_type": event_type,
            "amount": Decimal(amount),
            "effective_at": timezone.now(),
            "actor": self.actor,
            "module_revision": self.revision,
            "category": category,
            "description": "Integrity test",
            "source_reference": "INTEGRITY-1",
        }
        values.update(kwargs)
        return AccountingEvent.objects.create(**values)

    def _valid_receipt_application(self):
        with transaction.atomic():
            income = self._event(AccountingEvent.EventType.INCOME, category=self.category)
            receipt = self._event(AccountingEvent.EventType.RECEIPT, category=None)
            AccountMovement.objects.create(
                tenant=self.company,
                event=receipt,
                account=self.account,
                delta=Decimal("100.00"),
            )
            application = AccountingApplication.objects.create(
                tenant=self.company,
                source_event=receipt,
                target_event=income,
                amount=Decimal("100.00"),
                actor=self.actor,
                module_revision=self.revision,
            )
        return income, receipt, application

    def _valid_payment_application(self):
        with transaction.atomic():
            expense_category = AccountingCategory.objects.create(
                tenant=self.company,
                kind=AccountingCategory.Kind.EXPENSE,
                label="Expense",
                created_by=self.actor,
            )
            expense = self._event(AccountingEvent.EventType.EXPENSE, category=expense_category)
            payment = self._event(AccountingEvent.EventType.PAYMENT, category=None)
            AccountMovement.objects.create(
                tenant=self.company,
                event=payment,
                account=self.account,
                delta=Decimal("-100.00"),
            )
            application = AccountingApplication.objects.create(
                tenant=self.company,
                source_event=payment,
                target_event=expense,
                amount=Decimal("100.00"),
                actor=self.actor,
                module_revision=self.revision,
            )
        return expense, payment, application

    def test_event_requires_same_company_accounting_module_revision(self):
        foreign_company = Tenant.objects.create(name="Foreign", slug="model-integrity-foreign")
        foreign_actor = make_user(
            "p4-integrity-foreign-accountant",
            role="accountant",
            tenant=foreign_company,
        )
        foreign_revision = CompanyModuleState.objects.create(
            tenant=foreign_company,
            module_code="accounting",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=foreign_actor,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._event(
                AccountingEvent.EventType.INCOME,
                category=self.category,
                module_revision=foreign_revision,
            )

        non_accounting_revision = CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="vehicle_management",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=self.actor,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._event(
                AccountingEvent.EventType.INCOME,
                category=self.category,
                module_revision=non_accounting_revision,
            )

    def test_application_requires_same_company_accounting_module_revision(self):
        income, receipt, _ = self._valid_receipt_application()
        non_accounting_revision = CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="vehicle_management",
            state="enabled",
            version=1,
            effective_from=timezone.now(),
            changed_by=self.actor,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingApplication.objects.create(
                tenant=self.company,
                source_event=receipt,
                target_event=income,
                amount=Decimal("1.00"),
                actor=self.actor,
                module_revision=non_accounting_revision,
            )

    def test_cash_event_cannot_be_reversed_without_reversing_application(self):
        _, receipt, _ = self._valid_receipt_application()
        with self.assertRaises(IntegrityError), transaction.atomic():
            reversal = self._event(
                AccountingEvent.EventType.RECEIPT,
                category=None,
                amount=receipt.amount,
                effect_sign=-1,
                reversal_of=receipt,
                correction_reason="Incorrect cash event",
                effective_at=receipt.effective_at,
                description=receipt.description,
                source_reference=receipt.source_reference,
            )
            AccountMovement.objects.create(
                tenant=self.company,
                event=reversal,
                account=self.account,
                delta=Decimal("-100.00"),
            )

    def test_income_cannot_be_reversed_while_payment_application_is_active(self):
        income, _, _ = self._valid_receipt_application()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._event(
                AccountingEvent.EventType.INCOME,
                category=income.category,
                amount=income.amount,
                effect_sign=-1,
                reversal_of=income,
                correction_reason="Incorrect income",
                effective_at=income.effective_at,
                description=income.description,
                source_reference=income.source_reference,
            )

    def test_expense_cannot_be_reversed_while_payment_application_is_active(self):
        expense, _, _ = self._valid_payment_application()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._event(
                AccountingEvent.EventType.EXPENSE,
                category=expense.category,
                amount=expense.amount,
                effect_sign=-1,
                reversal_of=expense,
                correction_reason="Incorrect expense",
                effective_at=expense.effective_at,
                description=expense.description,
                source_reference=expense.source_reference,
            )
