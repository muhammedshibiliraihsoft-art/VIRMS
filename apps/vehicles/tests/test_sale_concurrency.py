from datetime import timedelta
from decimal import Decimal
from queue import Queue
from threading import Barrier, Thread

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent
from apps.common.domain_mutations import DomainConflict
from apps.tenants.models import Branch, CompanyModuleState, Tenant
from apps.vehicles.models import VehicleSaleCorrection, VehicleSaleReceipt, VehicleSaleRefund
from apps.vehicles.services import correct_sale, create_sale_receipt, create_sale_refund


class VehicleSaleConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Sale race", slug="p7-sale-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.accountants = [
            make_user(f"p7-sale-race-{name}", role="accountant", tenant=self.company)
            for name in ("a", "b")
        ]
        for module in ("vehicle_management", "accounting"):
            CompanyModuleState.objects.create(
                tenant=self.company,
                module_code=module,
                state=CompanyModuleState.State.ENABLED,
                version=1,
                effective_from=timezone.now() - timedelta(minutes=1),
                changed_by=self.accountants[0],
            )
        self.cash = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Sale race till",
            created_by=self.accountants[0],
        )

        client = APIClient()
        client.force_authenticate(user=self.accountants[0])
        base = f"/api/v1/tenants/{self.company.pk}/vehicle-management"
        vehicle = client.post(
            f"{base}/vehicles/",
            {"registration": "SALE-RACE-1", "model": "Test Vehicle", "branch_id": str(self.branch.pk)},
            format="json",
            HTTP_IDEMPOTENCY_KEY="p7-sale-race-vehicle",
        )
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        purchase = client.post(
            f"{base}/purchases/",
            {
                "vehicle_id": vehicle.data["id"],
                "branch_id": str(self.branch.pk),
                "purchase_cost": "12000.00",
                "seller_name": "Sale Race Motors",
                "investor_id": None,
                "investor_fund_amount": "0.00",
                "running_capital_amount": "12000.00",
                "initial_payment_amount": "0.00",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="p7-sale-race-purchase",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        sale = client.post(
            f"{base}/sales/",
            {
                "vehicle_id": vehicle.data["id"],
                "branch_id": str(self.branch.pk),
                "sale_price": "12000.00",
                "buyer_name": "Sale Race Buyer",
                "buyer_phone": "9876543210",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="p7-sale-race-sale",
        )
        self.assertEqual(sale.status_code, 201, sale.content)
        self.sale_id = sale.data["id"]

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.outcomes = Queue()

    def run_parallel(self, operations):
        barrier = Barrier(len(operations))

        def worker(operation):
            close_old_connections()
            connections["default"].close()
            connections["default"].settings_dict["NAME"] = self.test_database_name
            try:
                barrier.wait(timeout=10)
                result = operation()
                self.outcomes.put(("success", result.status))
            except DomainConflict as error:
                self.outcomes.put(("conflict", str(error.detail["code"])))
            except Exception as error:
                self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        threads = [Thread(target=worker, args=(operation,), daemon=True) for operation in operations]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads), "Concurrent Sale operation timed out")
        outcomes = [self.outcomes.get_nowait() for _ in threads]
        self.assertFalse(any(kind == "error" for kind, _detail in outcomes), outcomes)
        return outcomes

    def _receipt(self, actor, amount, reference, key):
        return create_sale_receipt(
            actor=actor,
            company_id=self.company.pk,
            sale_id=self.sale_id,
            key=key,
            path=f"/api/v1/tenants/{self.company.pk}/vehicle-management/sales/{self.sale_id}/receipts/",
            account_id=self.cash.pk,
            amount=Decimal(amount),
            reference=reference,
            effective_at=timezone.now() - timedelta(seconds=1),
        )

    def _refund(self, actor, amount, key):
        return create_sale_refund(
            actor=actor,
            company_id=self.company.pk,
            sale_id=self.sale_id,
            key=key,
            path=f"/api/v1/tenants/{self.company.pk}/vehicle-management/sales/{self.sale_id}/refunds/",
            account_id=self.cash.pk,
            amount=Decimal(amount),
            effective_at=timezone.now() - timedelta(seconds=1),
        )

    def _correction(self, actor, amount, key, reason):
        return correct_sale(
            actor=actor,
            company_id=self.company.pk,
            sale_id=self.sale_id,
            key=key,
            path=f"/api/v1/tenants/{self.company.pk}/vehicle-management/sales/{self.sale_id}/corrections/",
            sale_price=Decimal(amount),
            reason=reason,
        )

    def test_concurrent_receipts_cannot_exceed_sale_receivable(self):
        outcomes = self.run_parallel(
            [
                lambda: self._receipt(self.accountants[0], "8000.00", "sale-race-r1", "sale-race-r1"),
                lambda: self._receipt(self.accountants[1], "8000.00", "sale-race-r2", "sale-race-r2"),
            ]
        )

        self.assertCountEqual([kind for kind, _detail in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(VehicleSaleReceipt.objects.filter(sale_id=self.sale_id).count(), 1)
        self.assertEqual(
            AccountingEvent.objects.filter(event_type=AccountingEvent.EventType.VEHICLE_SALE_RECEIPT).count(),
            1,
        )
        self.assertEqual(AccountMovement.objects.count(), 1)

    def test_concurrent_refunds_cannot_exceed_corrected_refund_payable(self):
        self.assertEqual(self._receipt(self.accountants[0], "12000.00", "sale-full-receipt", "sale-full-receipt").status, 201)
        self.assertEqual(self._correction(self.accountants[0], "10000.00", "sale-price-cut", "Refundable difference").status, 201)

        outcomes = self.run_parallel(
            [
                lambda: self._refund(self.accountants[0], "1500.00", "sale-refund-r1"),
                lambda: self._refund(self.accountants[1], "1500.00", "sale-refund-r2"),
            ]
        )

        self.assertCountEqual([kind for kind, _detail in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(VehicleSaleRefund.objects.filter(sale_id=self.sale_id).count(), 1)
        self.assertEqual(
            AccountingEvent.objects.filter(event_type=AccountingEvent.EventType.VEHICLE_SALE_REFUND).count(),
            1,
        )
        self.assertEqual(AccountMovement.objects.count(), 2)
        self.assertEqual(
            AccountMovement.objects.filter(delta=Decimal("-1500.00")).count(),
            1,
        )

    def test_concurrent_price_corrections_append_ordered_versions(self):
        outcomes = self.run_parallel(
            [
                lambda: self._correction(self.accountants[0], "11000.00", "sale-correction-r1", "First correction"),
                lambda: self._correction(self.accountants[1], "10000.00", "sale-correction-r2", "Second correction"),
            ]
        )

        self.assertCountEqual(outcomes, [("success", 201), ("success", 201)])
        history = list(VehicleSaleCorrection.objects.filter(sale_id=self.sale_id).order_by("version"))
        self.assertEqual([row.version for row in history], [1, 2])
        self.assertEqual(history[0].previous_sale_price, Decimal("12000.00"))
        self.assertEqual(history[1].previous_sale_price, history[0].sale_price)
        self.assertEqual(AccountingEvent.objects.count(), 0)
        self.assertEqual(AccountMovement.objects.count(), 0)
