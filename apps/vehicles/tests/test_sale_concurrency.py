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
from apps.accounting.services import AccountingConflict
from apps.common.domain_mutations import DomainConflict
from apps.investment.models import InvestorProfitShareAgreement, InvestorVehicleProfitPayment, VehicleCapitalRecovery
from apps.investment.services import create_vehicle_capital_recovery, create_vehicle_profit_payment
from apps.tenants.models import Branch, CompanyModuleState, Tenant
from apps.vehicles.models import VehicleSale, VehicleSaleCorrection, VehicleSaleReceipt, VehicleSaleRefund
from apps.vehicles.services import correct_sale, create_sale_receipt, create_sale_refund, get_vehicle_financial_position


class VehicleSaleConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Sale race", slug="p7-sale-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.accountants = [
            make_user(f"p7-sale-race-{name}", role="accountant", tenant=self.company)
            for name in ("a", "b")
        ]
        for module in ("vehicle_management", "accounting", "investment"):
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

    def test_concurrent_capital_recoveries_cannot_classify_receipt_twice(self):
        self._receipt(self.accountants[0], "12000.00", "RECOVERY-RACE", "recovery-race-receipt")
        sale = VehicleSale.objects.get(pk=self.sale_id)
        position = get_vehicle_financial_position(
            actor=self.accountants[0], company_id=self.company.pk, vehicle_id=sale.vehicle_id,
        )
        before = AccountMovement.objects.count()

        def recovery(actor, key):
            return create_vehicle_capital_recovery(
                actor=actor, company_id=self.company.pk, sale_id=self.sale_id,
                expected_source_version=position["source_version"], reason="Confirm collected capital",
                key=key, path="/internal-test/race-recovery/",
            )

        outcomes = self.run_parallel([
            lambda: recovery(self.accountants[0], "recovery-race-a"),
            lambda: recovery(self.accountants[1], "recovery-race-b"),
        ])
        self.assertEqual(sorted(kind for kind, _ in outcomes), ["conflict", "success"])
        self.assertEqual(VehicleCapitalRecovery.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(AccountMovement.objects.count(), before)

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

    def test_concurrent_investor_profit_payments_cannot_exceed_confirmed_share(self):
        setup_client = APIClient()
        setup_client.force_authenticate(user=self.accountants[0])
        investment_base = f"/api/v1/tenants/{self.company.pk}/investment"
        investor_response = setup_client.post(
            f"{investment_base}/investors/", {"name": "Race Investor"}, format="json",
            HTTP_IDEMPOTENCY_KEY="profit-race-investor",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        investor_id = investor_response.data["id"]
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company,
            investor_id=investor_id,
            share_percentage=Decimal("50.0000"),
            effective_at=timezone.now() - timedelta(minutes=5),
            actor=self.accountants[0],
        )
        credit = setup_client.post(
            f"{investment_base}/fund/credits/",
            {
                "investor_id": investor_id, "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk), "amount": "10000.00",
                "reference": "PROFIT-RACE-FUND",
                "effective_at": (timezone.now() - timedelta(minutes=4)).isoformat(),
            },
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-credit",
        )
        self.assertEqual(credit.status_code, 201, credit.content)
        base = f"/api/v1/tenants/{self.company.pk}/vehicle-management"
        vehicle = setup_client.post(
            f"{base}/vehicles/",
            {"registration": "PROFIT-RACE-1", "model": "Test Vehicle", "branch_id": str(self.branch.pk)},
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-vehicle",
        )
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        purchase = setup_client.post(
            f"{base}/purchases/",
            {
                "vehicle_id": vehicle.data["id"], "branch_id": str(self.branch.pk),
                "purchase_cost": "10000.00", "seller_name": "Race Motors",
                "investor_id": investor_id, "investor_fund_amount": "10000.00",
                "running_capital_amount": "0.00", "initial_payment_amount": "0.00",
            },
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-purchase",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        sale = setup_client.post(
            f"{base}/sales/",
            {
                "vehicle_id": vehicle.data["id"], "branch_id": str(self.branch.pk),
                "sale_price": "12000.00", "buyer_name": "Race Buyer", "buyer_phone": "9876543210",
            },
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-sale",
        )
        self.assertEqual(sale.status_code, 201, sale.content)
        receipt = setup_client.post(
            f"{base}/sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.cash.pk), "amount": "12000.00", "reference": "PROFIT-RACE-SALE"},
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-receipt",
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = setup_client.get(f"{base}/vehicles/{vehicle.data['id']}/financial-position/")
        self.assertEqual(position.status_code, 200, position.content)
        confirmation = setup_client.post(
            f"{base}/vehicles/{vehicle.data['id']}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Confirm concurrency fixture"},
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-confirmation",
        )
        self.assertEqual(confirmation.status_code, 201, confirmation.content)
        self.result_confirmation_id = confirmation.data["id"]
        recovery = setup_client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/",
            {"expected_source_version": position.data["source_version"], "reason": "Recover concurrency fixture capital"},
            format="json", HTTP_IDEMPOTENCY_KEY="profit-race-capital-recovery",
        )
        self.assertEqual(recovery.status_code, 201, recovery.content)

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.outcomes = Queue()

        def payment(actor, key):
            close_old_connections()
            connections["default"].close()
            connections["default"].settings_dict["NAME"] = self.test_database_name
            try:
                barrier.wait(timeout=10)
                outcome = create_vehicle_profit_payment(
                    actor=actor, company_id=self.company.pk,
                    result_confirmation_id=self.result_confirmation_id,
                    account_id=self.cash.pk, amount=Decimal("700.00"),
                    effective_at=timezone.now() - timedelta(seconds=1),
                    description="Concurrent share payment", key=key,
                    path=f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{self.result_confirmation_id}/profit-payments/",
                )
                self.outcomes.put(("success", outcome.status))
            except (DomainConflict, AccountingConflict) as error:
                code = error.detail.get("code") if isinstance(error.detail, dict) else error.default_code
                self.outcomes.put(("conflict", code))
            except Exception as error:
                self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        barrier = Barrier(2)
        threads = [
            Thread(target=payment, args=(actor, f"profit-race-payment-{index}"), daemon=True)
            for index, actor in enumerate(self.accountants, start=1)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads), "Concurrent Investor Profit payment timed out")
        outcomes = [self.outcomes.get_nowait() for _ in threads]
        self.assertFalse(any(kind == "error" for kind, _detail in outcomes), outcomes)
        self.assertCountEqual([kind for kind, _detail in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(InvestorVehicleProfitPayment.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="INVESTOR_PROFIT_PAYMENT").count(), 1)
        self.assertEqual(AccountMovement.objects.filter(delta=Decimal("-700.00")).count(), 1)
