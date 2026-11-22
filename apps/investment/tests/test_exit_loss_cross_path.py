"""The two Loss settlement paths must share one committed cap."""

from decimal import Decimal
from queue import Queue
from threading import Barrier, Event, Thread

from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.test_users import make_user
from apps.accounts.models import AccountSecurityEvent
from apps.accounting.models import AccountMovement, AccountingEvent
from apps.investment.models import InvestorExitLossApplication, InvestorProfitLossOffset, InvestorProfitShareAgreement
from apps.tenants.models import CompanyModuleState
from apps.vehicles.tests.test_sale_api import VehicleSaleApiTests


class ExitLossCrossPathConcurrencyTests(TransactionTestCase):
    setUp = VehicleSaleApiTests.setUp
    add_revision = VehicleSaleApiTests.add_revision
    post = VehicleSaleApiTests.post
    create_vehicle = VehicleSaleApiTests.create_vehicle
    create_investor = VehicleSaleApiTests.create_investor
    create_purchase = VehicleSaleApiTests.create_purchase
    create_sale = VehicleSaleApiTests.create_sale
    financial_position = VehicleSaleApiTests.financial_position

    def test_offset_and_exit_receipt_cannot_over_settle_one_loss(self):
        self._exercise_loss_cap(None)

    def test_offset_before_exit_receipt_cannot_over_settle_one_loss(self):
        self._exercise_loss_cap("offset")

    def test_exit_receipt_before_offset_cannot_over_settle_one_loss(self):
        self._exercise_loss_cap("exit")

    def _exercise_loss_cap(self, first):
        investor = self.create_investor("cross-path")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("40.0000"),
            effective_at=timezone.now(), actor=self.company_accountant,
        )
        loss_vehicle = self.create_vehicle("KL 11 P 5292")
        self.create_purchase(loss_vehicle, investor=investor)
        loss_sale = self.post("sales/", {
            "vehicle_id": str(loss_vehicle.pk), "branch_id": str(self.branch.pk),
            "sale_price": "9000.00", "buyer_name": "Maya", "buyer_phone": "9876543210",
        }, "cross-loss-sale")
        self.assertEqual(loss_sale.status_code, 201, loss_sale.content)
        collected = self.post(f"sales/{loss_sale.data['id']}/receipts/", {
            "account_id": str(self.bank.pk), "amount": "9000.00", "reference": "CROSS-LOSS-COLLECT",
        }, "cross-loss-receipt")
        self.assertEqual(collected.status_code, 201, collected.content)
        loss_preview = self.financial_position(loss_vehicle).data
        loss = self.post(f"vehicles/{loss_vehicle.pk}/financial-position/confirm/", {
            "expected_source_version": loss_preview["source_version"],
            "investor_loss_amount": "100.00", "company_loss_amount": "900.00",
            "reason": "Review cross-path confirmed Loss",
        }, "cross-loss-confirm")
        self.assertEqual(loss.status_code, 201, loss.content)

        base = f"/api/v1/tenants/{self.company.pk}/investment/"
        credit = self.client.post(base + "fund/credits/", {
            "investor_id": str(investor.pk), "branch_id": str(self.branch.pk),
            "account_id": str(self.cash.pk), "amount": "6000.00",
            "reference": "CROSS-PATH-SECOND-PURCHASE",
            "effective_at": timezone.now().isoformat(),
        }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-second-credit")
        self.assertEqual(credit.status_code, 201, credit.content)
        profit_vehicle = self.create_vehicle("KL 11 P 5293")
        self.create_purchase(profit_vehicle, investor=investor)
        profit_sale = self.create_sale(profit_vehicle)
        collected_profit = self.post(f"sales/{profit_sale.data['id']}/receipts/", {
            "account_id": str(self.bank.pk), "amount": "12000.00", "reference": "CROSS-PROFIT-COLLECT",
        }, "cross-profit-receipt")
        self.assertEqual(collected_profit.status_code, 201, collected_profit.content)
        from apps.investment.services import create_vehicle_capital_recovery
        preview = self.financial_position(profit_vehicle).data
        create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk,
            sale_id=profit_sale.data["id"], expected_source_version=preview["source_version"],
            reason="Review cross-path capital", key="cross-profit-recovery",
            path="/internal-test/cross-profit-recovery/",
        )
        preview = self.financial_position(profit_vehicle).data
        profit = self.post(f"vehicles/{profit_vehicle.pk}/financial-position/confirm/", {
            "expected_source_version": preview["source_version"],
            "reason": "Review cross-path Profit",
        }, "cross-profit-confirm")
        self.assertEqual(profit.status_code, 201, profit.content)

        period_base = base + f"investors/{investor.pk}/"
        projection = self.client.get(period_base + "profit-periods/")
        self.assertEqual(projection.status_code, 200, projection.content)
        period = projection.data["periods"][0]
        snapshot = self.client.post(period_base + "profit-period-reconciliations/", {
            "period_start": period["period_start"],
            "expected_source_version": period["source_version"],
            "reason": "Confirm cross-path period",
        }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-reconciliation")
        self.assertEqual(snapshot.status_code, 201, snapshot.content)
        position = self.client.post(period_base + "profit-positions/", {
            "reconciliation_id": snapshot.data["id"],
            "expected_source_version": period["source_version"],
            "reason": "Confirm cross-path position",
        }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-position")
        self.assertEqual(position.status_code, 201, position.content)

        self.add_revision("investor_portal", 1)
        portal_user = make_user("cross-path-portal-investor", role="investor", tenant=self.company)
        self.client.force_authenticate(user=self.company_accountant)
        bound = self.client.post(base + f"investors/{investor.pk}/portal-binding/", {
            "account_id": str(portal_user.pk),
        }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-binding")
        self.assertEqual(bound.status_code, 201, bound.content)
        self.client.force_authenticate(user=portal_user)
        exit_request = self.client.post(base + "portal/self/exit-requests/", {
            "terms_accepted": True,
        }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-exit")
        self.assertEqual(exit_request.status_code, 201, exit_request.content)
        self.client.force_authenticate(user=self.company_accountant)
        settlement_path = base + f"investors/{investor.pk}/exit-requests/{exit_request.data['id']}/settlement/"
        settlement = self.client.get(settlement_path)
        self.assertEqual(settlement.status_code, 200, settlement.content)
        principal = Decimal(settlement.data["principal_available"] or "0")
        if principal:
            returned = self.client.post(base + f"investors/{investor.pk}/exit-requests/{exit_request.data['id']}/principal-payments/", {
                "branch_id": str(self.branch.pk), "account_id": str(self.cash.pk),
                "amount": format(principal, ".2f"), "reference": "CROSS-PATH-PRINCIPAL",
                "effective_at": timezone.now().isoformat(),
                "expected_source_version": settlement.data["source_version"],
                "reason": "Return principal before Loss settlement",
            }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-principal")
            self.assertEqual(returned.status_code, 201, returned.content)
        settlement = self.client.get(settlement_path)
        self.assertEqual(settlement.data["residual_confirmed_loss"], "100.00")

        barrier, first_done, outcomes = Barrier(2), Event(), Queue()
        loss_path = base + f"investors/{investor.pk}/exit-requests/{exit_request.data['id']}/loss-applications/"
        offset_path = base + f"vehicle-results/{loss.data['id']}/profit-loss-offsets/"

        def worker(kind):
            close_old_connections()
            client = APIClient()
            client.force_authenticate(user=self.company_accountant)
            try:
                if first is None:
                    barrier.wait(timeout=10)
                elif kind != first:
                    if not first_done.wait(timeout=10):
                        raise TimeoutError("First Loss settlement did not finish")
                if kind == "offset":
                    response = client.post(offset_path, {
                        "profit_result_id": profit.data["id"], "amount": "80.00",
                        "reason": "Offset confirmed Loss against Profit",
                    }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-offset")
                else:
                    response = client.post(loss_path, {
                        "loss_result_id": loss.data["id"], "branch_id": str(self.branch.pk),
                        "account_id": str(self.bank.pk), "source": "DIRECT_RECEIPT",
                        "amount": "60.00", "effective_at": timezone.now().isoformat(),
                        "expected_source_version": settlement.data["source_version"],
                        "reason": "Receive confirmed Exit Loss repayment",
                    }, format="json", HTTP_IDEMPOTENCY_KEY="cross-path-exit-loss")
                outcomes.put((kind, response.status_code, response.content.decode()))
            except Exception as error:
                outcomes.put((kind, "error", str(error)))
            finally:
                if kind == first:
                    first_done.set()
                connections.close_all()

        threads = [Thread(target=worker, args=(kind,), daemon=True) for kind in ("offset", "exit")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads), "Loss race timed out")
        result = [outcomes.get_nowait() for _ in threads]
        self.assertCountEqual([status for _, status, _ in result], [201, 409], result)
        offset_total = sum(row.amount for row in InvestorProfitLossOffset.objects.filter(loss_result_id=loss.data["id"]))
        exit_total = sum(row.amount for row in InvestorExitLossApplication.objects.filter(loss_result_id=loss.data["id"]))
        self.assertIn(offset_total + exit_total, (Decimal("60.00"), Decimal("80.00")), result)
        self.assertLessEqual(offset_total + exit_total, Decimal("100.00"), result)
        self.assertEqual(AccountingEvent.objects.filter(event_type="INVESTOR_EXIT_LOSS_RECOVERY").count(), int(exit_total > 0))
        self.assertEqual(AccountMovement.objects.filter(event__event_type="INVESTOR_EXIT_LOSS_RECOVERY").count(), int(exit_total > 0))
        self.assertEqual(AccountSecurityEvent.objects.filter(
            company_id=self.company.pk, action="investment.exit.settlement.loss",
        ).count(), int(exit_total > 0))
        self.assertEqual(AccountSecurityEvent.objects.filter(
            company_id=self.company.pk, action="investment.profit.loss_offset.create",
        ).count(), int(offset_total > 0))
