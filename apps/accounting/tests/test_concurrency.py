from decimal import Decimal
from threading import Barrier, Event, Thread, current_thread
from unittest.mock import patch

from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import RoleAssignment, User
from apps.accounts.tests.test_users import make_user
from apps.accounting import services
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingApplication,
    AccountingCategory,
    AccountingEvent,
)
from apps.tenants.commands import set_company_module_state
from apps.tenants.models import Branch, CompanyModuleState, Tenant, TenantMembership


class AccountingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.company = Tenant.objects.create(name="Concurrent", slug="accounting-concurrent")
        self.branch = Branch.objects.create(tenant=self.company, name="Main")
        self.accountant = make_user(
            "p4-concurrent-accountant", role="accountant", tenant=self.company
        )
        self.revision = CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state=CompanyModuleState.State.ENABLED,
            version=1,
            effective_from=timezone.now(),
            changed_by=self.accountant,
        )
        self.category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.INCOME,
            label="Concurrent income",
            created_by=self.accountant,
        )
        self.account = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Concurrent cash",
            created_by=self.accountant,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]

        self.client = APIClient()
        self.client.force_authenticate(user=self.accountant)
        response = self.client.post(
            self.path("incomes/"),
            self.income_payload(amount="100.00", source_reference="CONCURRENT-TARGET"),
            format="json",
            HTTP_IDEMPOTENCY_KEY="concurrent-target-income",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.target_event_id = response.data["id"]

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/accounting/{suffix}"

    def income_payload(self, *, amount, source_reference):
        return {
            "amount": amount,
            "branch_id": str(self.branch.pk),
            "category_id": str(self.category.pk),
            "description": "Concurrent accounting event",
            "source_reference": source_reference,
        }

    def _prepare_worker_connection(self):
        close_old_connections()
        worker_connection = connections["default"]
        worker_connection.close()
        worker_connection.settings_dict["NAME"] = self.test_database_name

    def _post_receipt(self, *, amount, key, source_reference, barrier):
        self._prepare_worker_connection()
        try:
            client = APIClient()
            client.force_authenticate(user=self.accountant)
            barrier.wait(timeout=10)
            response = client.post(
                self.path("receipts/"),
                {
                    "amount": amount,
                    "branch_id": str(self.branch.pk),
                    "account_id": str(self.account.pk),
                    "target_event_id": self.target_event_id,
                    "effective_at": timezone.now().isoformat(),
                    "description": "Concurrent receipt",
                    "source_reference": source_reference,
                },
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )
            return response.status_code
        finally:
            close_old_connections()

    def test_concurrent_partial_receipts_cannot_overapply_income(self):
        barrier = Barrier(2)
        threads = []
        outcomes = []
        for index in range(2):
            thread = Thread(
                target=lambda i=index: outcomes.append(
                    self._post_receipt(
                        amount="70.00",
                        key=f"concurrent-receipt-{i}",
                        source_reference=f"CONCURRENT-CASH-{i}",
                        barrier=barrier,
                    )
                ),
                name=f"accounting-receipt-{index}",
                daemon=True,
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, [201, 409])
        receipts = AccountingEvent.objects.filter(
            tenant=self.company, event_type=AccountingEvent.EventType.RECEIPT
        )
        self.assertEqual(receipts.count(), 1)
        self.assertEqual(
            sum(
                (row.amount for row in AccountingApplication.objects.filter(
                    tenant=self.company,
                    target_event_id=self.target_event_id,
                    effect_sign=1,
                )),
                Decimal("0.00"),
            ),
            Decimal("70.00"),
        )
        self.assertEqual(
            sum(AccountMovement.objects.filter(event__in=receipts).values_list("delta", flat=True)),
            Decimal("70.00"),
        )

    def test_concurrent_partial_payments_cannot_overpay_expense(self):
        expense_category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.EXPENSE,
            label="Concurrent expense",
            created_by=self.accountant,
        )
        client = APIClient()
        client.force_authenticate(user=self.accountant)
        expense_response = client.post(
            self.path("expenses/"),
            {
                "amount": "100.00",
                "branch_id": str(self.branch.pk),
                "category_id": str(expense_category.pk),
                "description": "Concurrent payment target",
                "source_reference": "CONCURRENT-EXPENSE-TARGET",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="concurrent-expense-target",
        )
        self.assertEqual(expense_response.status_code, 201, expense_response.content)

        barrier = Barrier(2)
        outcomes = []

        def post_payment(index):
            self._prepare_worker_connection()
            try:
                worker = APIClient()
                worker.force_authenticate(user=self.accountant)
                barrier.wait(timeout=10)
                response = worker.post(
                    self.path("payments/"),
                    {
                        "amount": "70.00",
                        "branch_id": str(self.branch.pk),
                        "account_id": str(self.account.pk),
                        "target_event_id": expense_response.data["id"],
                        "effective_at": timezone.now().isoformat(),
                        "description": "Concurrent partial Payment",
                        "source_reference": f"CONCURRENT-PAYMENT-{index}",
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY=f"concurrent-payment-{index}",
                )
                outcomes.append(response.status_code)
            finally:
                close_old_connections()

        threads = [
            Thread(target=post_payment, args=(index,), name=f"accounting-payment-{index}", daemon=True)
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, [201, 409])
        payments = AccountingEvent.objects.filter(
            tenant=self.company,
            event_type=AccountingEvent.EventType.PAYMENT,
        )
        self.assertEqual(payments.count(), 1)
        self.assertEqual(
            sum(
                (row.amount for row in AccountingApplication.objects.filter(
                    tenant=self.company,
                    target_event_id=expense_response.data["id"],
                    effect_sign=1,
                )),
                Decimal("0.00"),
            ),
            Decimal("70.00"),
        )
        self.assertEqual(
            sum(AccountMovement.objects.filter(event__in=payments).values_list("delta", flat=True)),
            Decimal("-70.00"),
        )

    def test_concurrent_corrections_create_only_one_reversal_and_replacement(self):
        barrier = Barrier(2)
        outcomes = []
        errors = []

        def correct_income(index):
            self._prepare_worker_connection()
            try:
                worker = APIClient()
                worker.force_authenticate(user=self.accountant)
                barrier.wait(timeout=10)
                response = worker.post(
                    self.path(f"events/{self.target_event_id}/corrections/"),
                    {
                        "outcome": "REVERSE_AND_REPLACE",
                        "event_occurred": True,
                        "reason": "Concurrent correction attempt",
                        "replacement": {
                            "amount": "95.00",
                            "branch_id": str(self.branch.pk),
                            "category_id": str(self.category.pk),
                            "description": "Corrected concurrent entry",
                            "source_reference": "CONCURRENT-CORRECTION-REPLACEMENT",
                        },
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY=f"concurrent-correction-{index}",
                )
                outcomes.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        threads = [
            Thread(
                target=correct_income,
                args=(index,),
                name=f"accounting-correction-{index}",
                daemon=True,
            )
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertCountEqual(outcomes, [201, 409])
        self.assertEqual(
            AccountingEvent.objects.filter(reversal_of_id=self.target_event_id).count(),
            1,
        )
        self.assertEqual(
            AccountingEvent.objects.filter(replaces_event_id=self.target_event_id).count(),
            1,
        )
        self.assertEqual(
            AccountingEvent.objects.filter(tenant=self.company).count(),
            3,
        )

    def test_accounting_write_that_observed_old_revision_fails_if_off_wins_tenant_lock(self):
        platform = User.objects.create_superuser(
            login_id="p4-concurrent-platform",
            email="p4-concurrent-platform@example.invalid",
            password="A-long-private-module-state-test-passphrase-123!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform,
            tenant=self.company,
            assigned_by=platform,
        )
        observed_old_revision = Event()
        outcome = []
        original_latest_revision = services._latest_revision

        def observe_revision(company_id):
            revision = original_latest_revision(company_id)
            if current_thread().name == "accounting-off-race-write":
                observed_old_revision.set()
            return revision

        def post_income():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.post(
                    self.path("incomes/"),
                    self.income_payload(amount="30.00", source_reference="OFF-RACE-WRITE"),
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="off-race-write",
                )
                outcome.append(response.status_code)
            finally:
                close_old_connections()

        write_thread = Thread(target=post_income, name="accounting-off-race-write", daemon=True)
        with patch.object(services, "_latest_revision", side_effect=observe_revision):
            with transaction.atomic():
                Tenant.objects.select_for_update().get(pk=self.company.pk)
                set_company_module_state(
                    actor=platform,
                    company=self.company,
                    module_code="accounting",
                    state=CompanyModuleState.State.DISABLED,
                    expected_version=self.revision.version,
                    reason="Deterministic OFF/write concurrency test",
                )
                write_thread.start()
                self.assertTrue(observed_old_revision.wait(timeout=10))

            write_thread.join(timeout=20)

        self.assertFalse(write_thread.is_alive())
        self.assertEqual(outcome, [409])
        self.assertEqual(
            AccountingEvent.objects.filter(
                tenant=self.company,
                event_type=AccountingEvent.EventType.INCOME,
            ).count(),
            1,
        )

    def test_accounting_write_that_holds_tenant_lock_commits_before_off(self):
        platform = User.objects.create_superuser(
            login_id="p4-write-first-platform",
            email="p4-write-first-platform@example.invalid",
            password="A-long-private-module-state-test-passphrase-456!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform,
            tenant=self.company,
            assigned_by=platform,
        )
        tenant_lock_acquired = Event()
        allow_write_to_finish = Event()
        write_outcome = []
        off_outcome = []
        errors = []
        original_scope = services.accounting_scope

        def pause_after_tenant_lock(*args, **kwargs):
            if current_thread().name == "accounting-write-first":
                tenant_lock_acquired.set()
                if not allow_write_to_finish.wait(timeout=10):
                    raise TimeoutError("Timed out waiting to complete the serialized Accounting write.")
            return original_scope(*args, **kwargs)

        def post_income():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.post(
                    self.path("incomes/"),
                    self.income_payload(amount="30.00", source_reference="OFF-WRITE-WINS"),
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="off-write-wins",
                )
                write_outcome.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        def disable_accounting():
            self._prepare_worker_connection()
            try:
                off_outcome.append(
                    set_company_module_state(
                        actor=platform,
                        company=self.company,
                        module_code="accounting",
                        state=CompanyModuleState.State.DISABLED,
                        expected_version=self.revision.version,
                        reason="Deterministic write-first OFF ordering test",
                    )
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        write_thread = Thread(target=post_income, name="accounting-write-first", daemon=True)
        off_thread = Thread(target=disable_accounting, name="accounting-off-after-write", daemon=True)
        with patch.object(services, "accounting_scope", side_effect=pause_after_tenant_lock):
            write_thread.start()
            self.assertTrue(tenant_lock_acquired.wait(timeout=10))
            off_thread.start()
            allow_write_to_finish.set()
            write_thread.join(timeout=20)
            off_thread.join(timeout=20)

        self.assertFalse(write_thread.is_alive())
        self.assertFalse(off_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(write_outcome, [201])
        self.assertEqual(len(off_outcome), 1)
        created = AccountingEvent.objects.get(
            tenant=self.company,
            source_reference="OFF-WRITE-WINS",
        )
        self.assertEqual(created.module_revision_id, self.revision.pk)
        self.assertEqual(off_outcome[0].state, CompanyModuleState.State.DISABLED)

    def test_stale_receipt_fails_if_off_wins_then_retry_settles_pre_off_income(self):
        platform = User.objects.create_superuser(
            login_id="p4-off-receipt-first-platform",
            email="p4-off-receipt-first-platform@example.invalid",
            password="A-long-private-off-settlement-test-passphrase-123!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform,
            tenant=self.company,
            assigned_by=platform,
        )
        observed_old_revision = Event()
        outcomes = []
        errors = []
        original_latest_revision = services._latest_revision

        def observe_revision(company_id):
            revision = original_latest_revision(company_id)
            if current_thread().name == "accounting-off-receipt-race":
                observed_old_revision.set()
            return revision

        def post_receipt():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.post(
                    self.path("receipts/"),
                    {
                        "amount": "25.00",
                        "branch_id": str(self.branch.pk),
                        "account_id": str(self.account.pk),
                        "target_event_id": self.target_event_id,
                        "effective_at": timezone.now().isoformat(),
                        "description": "Receipt racing Accounting OFF",
                        "source_reference": "OFF-RACE-RECEIPT",
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="off-race-receipt",
                )
                outcomes.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        write_thread = Thread(
            target=post_receipt,
            name="accounting-off-receipt-race",
            daemon=True,
        )
        with patch.object(services, "_latest_revision", side_effect=observe_revision):
            with transaction.atomic():
                Tenant.objects.select_for_update().get(pk=self.company.pk)
                off = set_company_module_state(
                    actor=platform,
                    company=self.company,
                    module_code="accounting",
                    state=CompanyModuleState.State.DISABLED,
                    expected_version=self.revision.version,
                    reason="OFF wins receipt settlement race",
                )
                write_thread.start()
                self.assertTrue(observed_old_revision.wait(timeout=10))

            write_thread.join(timeout=20)

        self.assertFalse(write_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(outcomes, [409])
        self.assertFalse(
            AccountingEvent.objects.filter(
                tenant=self.company,
                source_reference="OFF-RACE-RECEIPT",
            ).exists()
        )

        retry = self.client.post(
            self.path("receipts/"),
            {
                "amount": "25.00",
                "branch_id": str(self.branch.pk),
                "account_id": str(self.account.pk),
                "target_event_id": self.target_event_id,
                "effective_at": timezone.now().isoformat(),
                "description": "Receipt retry after Accounting OFF",
                "source_reference": "OFF-RACE-RECEIPT",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="off-race-receipt",
        )
        self.assertEqual(retry.status_code, 201, retry.content)
        receipt = AccountingEvent.objects.get(pk=retry.data["id"])
        application = AccountingApplication.objects.get(
            pk=retry.data["application_ids"][0]
        )
        self.assertEqual(receipt.module_revision_id, off.pk)
        self.assertEqual(application.module_revision_id, off.pk)
        self.assertEqual(AccountMovement.objects.filter(event=receipt).count(), 1)

    def test_receipt_that_holds_tenant_lock_commits_before_off(self):
        platform = User.objects.create_superuser(
            login_id="p4-settlement-first-platform",
            email="p4-settlement-first-platform@example.invalid",
            password="A-long-private-off-settlement-test-passphrase-456!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform,
            tenant=self.company,
            assigned_by=platform,
        )
        tenant_lock_acquired = Event()
        allow_receipt_to_finish = Event()
        receipt_outcome = []
        off_outcome = []
        errors = []
        original_scope = services.accounting_scope

        def pause_after_tenant_lock(*args, **kwargs):
            if current_thread().name == "accounting-settlement-first":
                tenant_lock_acquired.set()
                if not allow_receipt_to_finish.wait(timeout=10):
                    raise TimeoutError("Timed out waiting for Receipt to finish.")
            return original_scope(*args, **kwargs)

        def post_receipt():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.post(
                    self.path("receipts/"),
                    {
                        "amount": "25.00",
                        "branch_id": str(self.branch.pk),
                        "account_id": str(self.account.pk),
                        "target_event_id": self.target_event_id,
                        "effective_at": timezone.now().isoformat(),
                        "description": "Receipt wins Accounting OFF race",
                        "source_reference": "SETTLEMENT-FIRST-RECEIPT",
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="settlement-first-receipt",
                )
                receipt_outcome.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        def disable_accounting():
            self._prepare_worker_connection()
            try:
                off_outcome.append(
                    set_company_module_state(
                        actor=platform,
                        company=self.company,
                        module_code="accounting",
                        state=CompanyModuleState.State.DISABLED,
                        expected_version=self.revision.version,
                        reason="Receipt wins OFF settlement race",
                    )
                )
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        receipt_thread = Thread(
            target=post_receipt,
            name="accounting-settlement-first",
            daemon=True,
        )
        off_thread = Thread(
            target=disable_accounting,
            name="accounting-off-after-settlement",
            daemon=True,
        )
        with patch.object(services, "accounting_scope", side_effect=pause_after_tenant_lock):
            receipt_thread.start()
            self.assertTrue(tenant_lock_acquired.wait(timeout=10))
            off_thread.start()
            allow_receipt_to_finish.set()
            receipt_thread.join(timeout=20)
            off_thread.join(timeout=20)

        self.assertFalse(receipt_thread.is_alive())
        self.assertFalse(off_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(receipt_outcome, [201])
        self.assertEqual(len(off_outcome), 1)
        receipt = AccountingEvent.objects.get(
            tenant=self.company,
            source_reference="SETTLEMENT-FIRST-RECEIPT",
        )
        application = AccountingApplication.objects.get(source_event=receipt)
        self.assertEqual(receipt.module_revision_id, self.revision.pk)
        self.assertEqual(application.module_revision_id, self.revision.pk)
        self.assertEqual(off_outcome[0].state, CompanyModuleState.State.DISABLED)
        self.assertEqual(AccountMovement.objects.filter(event=receipt).count(), 1)

    def test_receipt_then_account_archive_serializes_without_archiving_history(self):
        tenant_lock_acquired = Event()
        allow_receipt_to_finish = Event()
        receipt_outcome = []
        archive_outcome = []
        errors = []
        original_scope = services.accounting_scope

        def pause_after_tenant_lock(*args, **kwargs):
            if current_thread().name == "accounting-receipt-first":
                tenant_lock_acquired.set()
                if not allow_receipt_to_finish.wait(timeout=10):
                    raise TimeoutError("Timed out waiting to complete the serialized Receipt.")
            return original_scope(*args, **kwargs)

        def post_receipt():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.post(
                    self.path("receipts/"),
                    {
                        "amount": "20.00",
                        "branch_id": str(self.branch.pk),
                        "account_id": str(self.account.pk),
                        "target_event_id": self.target_event_id,
                        "effective_at": timezone.now().isoformat(),
                        "description": "Receipt racing account archive",
                        "source_reference": "ARCHIVE-RACE-RECEIPT",
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="archive-race-receipt",
                )
                receipt_outcome.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        def archive_account():
            self._prepare_worker_connection()
            try:
                client = APIClient()
                client.force_authenticate(user=self.accountant)
                response = client.patch(
                    self.path(f"accounts/{self.account.pk}/"),
                    {"is_active": False},
                    format="json",
                    HTTP_IDEMPOTENCY_KEY="archive-race-account",
                )
                archive_outcome.append(response.status_code)
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        receipt_thread = Thread(target=post_receipt, name="accounting-receipt-first", daemon=True)
        archive_thread = Thread(target=archive_account, name="accounting-archive-after-receipt", daemon=True)
        with patch.object(services, "accounting_scope", side_effect=pause_after_tenant_lock):
            receipt_thread.start()
            self.assertTrue(tenant_lock_acquired.wait(timeout=10))
            archive_thread.start()
            allow_receipt_to_finish.set()
            receipt_thread.join(timeout=20)
            archive_thread.join(timeout=20)

        self.assertFalse(receipt_thread.is_alive())
        self.assertFalse(archive_thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(receipt_outcome, [201])
        self.assertEqual(archive_outcome, [409])
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_active)
        self.assertTrue(AccountMovement.objects.filter(account=self.account).exists())
