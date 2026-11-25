from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.audit import record_event
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingEvent,
    AccountingSourceLink,
)
from apps.investment.models import (
    Investor,
    InvestorFundCredit,
    InvestorProfitShareAgreement,
    InvestorProfitPeriodReconciliation,
    InvestorProfitLossOffset,
    InvestorVehicleProfitPayment,
    VehicleResultConfirmation,
)
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle, VehicleSale, VehicleSaleReceipt, VehicleSaleRefund


class VehicleSaleApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Sale Co", slug="p5-sale-co")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.company_accountant = make_user(
            "p5-sale-company-accountant", role="accountant", tenant=self.company
        )
        self.branch_accountant = make_user("p5-sale-branch-accountant", tenant=self.company)
        membership = self.branch_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch,
            assigned_by=self.branch_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch,
            assigned_by=self.branch_accountant,
        )
        self.add_revision("vehicle_management", 1)
        self.add_revision("accounting", 1)
        self.add_revision("investment", 1)
        self.cash = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Till",
            created_by=self.company_accountant,
        )
        self.bank = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.BANK,
            label="Bank",
            created_by=self.company_accountant,
        )
        self.client = APIClient()

    def add_revision(self, code, version, state=CompanyModuleState.State.ENABLED):
        return CompanyModuleState.objects.create(
            tenant=self.company,
            module_code=code,
            state=state,
            version=version,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )

    def post(self, suffix, body, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/{suffix}",
            body,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def create_vehicle(self, registration="KL 11 P 5050"):
        response = self.post(
            "vehicles/",
            {"registration": registration, "model": "Hatchback", "branch_id": str(self.branch.pk)},
            f"vehicle-{registration}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Vehicle.objects.get(pk=response.data["id"])

    def create_investor(self, registration="one", credit_effective_at=None):
        self.client.force_authenticate(user=self.company_accountant)
        response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/",
            {"name": "Ayaan"},
            format="json",
            HTTP_IDEMPOTENCY_KEY=f"sale-investor-{registration}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        credit = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": response.data["id"],
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": "10000.00",
                "reference": f"SALE-FUND-{registration}",
                "effective_at": (
                    credit_effective_at or timezone.now() - timedelta(minutes=2)
                ).isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=f"sale-fund-credit-{registration}",
        )
        self.assertEqual(credit.status_code, 201, credit.content)
        return Investor.objects.get(pk=response.data["id"])

    def create_purchase(self, vehicle, investor=None, funded_by_expense=False):
        fund_amount = Decimal("6000.00") if investor and not funded_by_expense else Decimal("0.00")
        response = self.post(
            "purchases/",
            {
                "vehicle_id": str(vehicle.pk),
                "branch_id": str(self.branch.pk),
                "purchase_cost": "10000.00",
                "seller_name": "North Motors",
                "investor_id": str(investor.pk) if investor and fund_amount else None,
                "investor_fund_amount": format(fund_amount, ".2f"),
                "running_capital_amount": format(Decimal("10000.00") - fund_amount, ".2f"),
                "initial_payment_amount": "0.00",
            },
            f"purchase-{vehicle.pk}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        if investor and funded_by_expense:
            expense = self.post(
                f"vehicles/{vehicle.pk}/expenses/",
                {
                    "amount": "1000.00",
                    "description": "Investor-funded repair",
                    "investor_id": str(investor.pk),
                    "investor_fund_amount": "1000.00",
                    "running_capital_amount": "0.00",
                },
                f"sale-expense-{vehicle.pk}",
            )
            self.assertEqual(expense.status_code, 201, expense.content)
        return response.data

    def create_sale(self, vehicle):
        response = self.post(
            "sales/",
            {
                "vehicle_id": str(vehicle.pk),
                "branch_id": str(self.branch.pk),
                "sale_price": "12000.00",
                "buyer_name": "Maya",
                "buyer_phone": "9876543210",
            },
            f"sale-{vehicle.pk}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response

    def receipt(self, sale_id, key="sale-receipt", amount="2000.00"):
        return self.post(
            f"sales/{sale_id}/receipts/",
            {"account_id": str(self.bank.pk), "amount": amount, "reference": "BANK-SALE-1"},
            key,
            self.branch_accountant,
        )

    def financial_position(self, vehicle, user=None, company=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        target = company or self.company
        return self.client.get(
            f"/api/v1/tenants/{target.pk}/vehicle-management/vehicles/{vehicle.pk}/financial-position/"
        )

    def test_operational_summary_uses_current_sale_corrections_receipts_and_scope(self):
        vehicle = self.create_vehicle("KL 11 P 5991")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        receipt = self.receipt(sale.data["id"], amount="2000.00")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "15000.00", "reason": "Correct signed price"},
            "operational-summary-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)

        endpoint = f"/api/v1/tenants/{self.company.pk}/vehicle-management/operational-summary/"
        summary = self.client.get(endpoint)
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["vehicle_count"], 1)
        self.assertEqual(summary.data["unsold_vehicle_count"], 0)
        self.assertEqual(summary.data["sold_vehicle_count"], 1)
        self.assertEqual(summary.data["corrected_sale_count"], 1)
        self.assertEqual(summary.data["sale_correction_count"], 1)
        self.assertEqual(summary.data["buyer_receipt_count"], 1)
        self.assertEqual(summary.data["current_sale_price_total"], "15000.00")
        self.assertEqual(summary.data["buyer_receipts_received"], "2000.00")
        self.assertEqual(summary.data["buyer_net_receipts"], "2000.00")
        self.assertEqual(summary.data["buyer_receivable"], "13000.00")
        self.assertEqual(summary.data["running_capital_contributed"], "10000.00")
        self.assertEqual(summary.data["running_capital_recovered"], "0.00")
        self.assertEqual(summary.data["running_capital_outstanding"], "10000.00")

        scoped = self.client.get(endpoint, {"branch_id": str(self.branch.pk)})
        self.assertEqual(scoped.status_code, 200, scoped.content)
        self.assertEqual(scoped.data["branch_id"], str(self.branch.pk))
        other_company = Tenant.objects.create(name="Other Company", slug="summary-other-company")
        other_branch = Branch.objects.create(tenant=other_company, name="Other Branch")
        forbidden = self.client.get(endpoint, {"branch_id": str(other_branch.pk)})
        self.assertIn(forbidden.status_code, (403, 404))
        self.assertNotIn("vehicle_count", forbidden.json())

    def test_operational_summary_counts_confirmed_running_capital_recovery_once(self):
        from apps.investment.services import create_vehicle_capital_recovery

        vehicle = self.create_vehicle("KL 11 P 5992")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        receipt = self.receipt(sale.data["id"], amount="12000.00")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        recovery = create_vehicle_capital_recovery(
            actor=self.company_accountant,
            company_id=self.company.pk,
            sale_id=sale.data["id"],
            expected_source_version=position.data["source_version"],
            reason="Confirm Company capital recovery",
            key="operational-summary-capital-recovery",
            path="/internal-test/capital-recovery/",
        )
        self.assertEqual(recovery.status, 201)
        summary = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/operational-summary/"
        )
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["running_capital_contributed"], "10000.00")
        self.assertEqual(summary.data["running_capital_recovered"], "10000.00")
        self.assertEqual(summary.data["running_capital_outstanding"], "0.00")

    def test_operational_summary_fails_closed_for_stale_running_capital_after_sale_correction_and_refund(self):
        from apps.investment.services import create_vehicle_capital_recovery

        vehicle = self.create_vehicle("KL 11 P 5993")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        receipt = self.receipt(sale.data["id"], key="stale-cap-receipt", amount="12000.00")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        recovery = create_vehicle_capital_recovery(
            actor=self.company_accountant,
            company_id=self.company.pk,
            sale_id=sale.data["id"],
            expected_source_version=position.data["source_version"],
            reason="Confirm Company capital recovery",
            key="stale-cap-recovery",
            path="/internal-test/capital-recovery/",
        )
        self.assertEqual(recovery.status, 201)

        endpoint = f"/api/v1/tenants/{self.company.pk}/vehicle-management/operational-summary/"
        for params in ({}, {"branch_id": str(self.branch.pk)}):
            summary = self.client.get(endpoint, params)
            self.assertEqual(summary.status_code, 200, summary.content)
            self.assertEqual(summary.data["running_capital_contributed"], "10000.00")
            self.assertEqual(summary.data["running_capital_recovered"], "10000.00")
            self.assertEqual(summary.data["running_capital_outstanding"], "0.00")

        corrected = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "8000.00", "reason": "Reduced agreed buyer price"},
            "stale-cap-correction",
        )
        self.assertEqual(corrected.status_code, 201, corrected.content)

        for params in ({}, {"branch_id": str(self.branch.pk)}):
            after_correction = self.client.get(endpoint, params)
            self.assertEqual(after_correction.status_code, 200, after_correction.content)
            self.assertEqual(after_correction.data["running_capital_contributed"], "10000.00")
            self.assertIsNone(after_correction.data["running_capital_recovered"])
            self.assertIsNone(after_correction.data["running_capital_outstanding"])

        refunded = self.post(
            f"sales/{sale.data['id']}/refunds/",
            {"account_id": str(self.bank.pk), "amount": "4000.00"},
            "stale-cap-refund",
            self.branch_accountant,
        )
        self.assertEqual(refunded.status_code, 201, refunded.content)

        for params in ({}, {"branch_id": str(self.branch.pk)}):
            after_refund = self.client.get(endpoint, params)
            self.assertEqual(after_refund.status_code, 200, after_refund.content)
            self.assertEqual(after_refund.data["buyer_net_receipts"], "8000.00")
            self.assertEqual(after_refund.data["running_capital_contributed"], "10000.00")
            self.assertIsNone(after_refund.data["running_capital_recovered"])
            self.assertIsNone(after_refund.data["running_capital_outstanding"])

    def test_operational_summary_running_capital_freshness_uses_constant_query_count(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from apps.investment.services import create_vehicle_capital_recovery

        def add_recovered_vehicle(reg, suffix):
            veh = self.create_vehicle(reg)
            self.create_purchase(veh)
            sale = self.create_sale(veh)
            rcpt = self.post(
                f"sales/{sale.data['id']}/receipts/",
                {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": f"BANK-SALE-QC-{suffix}"},
                f"qc-rcpt-{suffix}",
                self.branch_accountant,
            )
            self.assertEqual(rcpt.status_code, 201, rcpt.content)
            pos = self.financial_position(veh)
            rec = create_vehicle_capital_recovery(
                actor=self.company_accountant, company_id=self.company.pk,
                sale_id=sale.data["id"], expected_source_version=pos.data["source_version"],
                reason=f"Recover {reg}", key=f"qc-rec-{suffix}", path="/internal-test/capital-recovery/",
            )
            self.assertEqual(rec.status, 201)

        add_recovered_vehicle("KL 11 Q 0001", "1")
        endpoint = f"/api/v1/tenants/{self.company.pk}/vehicle-management/operational-summary/"
        with CaptureQueriesContext(connection) as ctx1:
            r1 = self.client.get(endpoint)
        self.assertEqual(r1.status_code, 200, r1.content)
        self.assertEqual(r1.data["running_capital_recovered"], "10000.00")

        for i in range(2, 5):
            add_recovered_vehicle(f"KL 11 Q 000{i}", str(i))

        with CaptureQueriesContext(connection) as ctx4:
            r4 = self.client.get(endpoint)
        self.assertEqual(r4.status_code, 200, r4.content)
        self.assertEqual(r4.data["running_capital_contributed"], "40000.00")
        self.assertEqual(r4.data["running_capital_recovered"], "40000.00")
        self.assertEqual(r4.data["running_capital_outstanding"], "0.00")
        self.assertEqual(len(ctx4), len(ctx1))

    def test_financial_position_reads_current_sources_without_posting_cash_or_profit(self):
        vehicle = self.create_vehicle("KL 11 P 5081")
        self.create_purchase(vehicle)
        expense = self.post(
            f"vehicles/{vehicle.pk}/expenses/",
            {"amount": "1000.00", "description": "Tyres", "running_capital_amount": "1000.00"},
            "position-expense",
        )
        self.assertEqual(expense.status_code, 201, expense.content)
        sale = self.create_sale(vehicle)
        event_count = AccountingEvent.objects.count()

        provisional = self.financial_position(vehicle)
        self.assertEqual(provisional.status_code, 200, provisional.content)
        self.assertEqual(provisional.data["total_vehicle_cost"], "11000.00")
        self.assertEqual(provisional.data["calculated_result"], "1000.00")
        self.assertEqual(provisional.data["status"], "PROVISIONAL_COLLECTION")
        self.assertFalse(provisional.data["settlement_eligible"])
        self.assertEqual(provisional.data["buyer_receivable"], "12000.00")

        self.assertEqual(self.receipt(sale.data["id"], amount="2000.00").status_code, 201)
        partial = self.financial_position(vehicle)
        self.assertEqual(partial.data["buyer_receivable"], "10000.00")
        self.assertEqual(partial.data["status"], "PROVISIONAL_COLLECTION")

        final_receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "10000.00", "reference": "BANK-SALE-POSITION-FINAL"},
            "position-final",
            self.branch_accountant,
        )
        self.assertEqual(final_receipt.status_code, 201, final_receipt.content)
        complete = self.financial_position(vehicle)
        self.assertEqual(complete.data["status"], "READY_FOR_REVIEW")
        self.assertFalse(complete.data["settlement_eligible"])
        self.assertEqual(complete.data["actual_net_collection"], "12000.00")
        self.assertEqual(AccountingEvent.objects.count(), event_count + 2)
        corrected_expense = self.post(
            f"expenses/{expense.data['id']}/corrections/",
            {"amount": "500.00", "reason": "Corrected tyre invoice"},
            "position-expense-correction",
        )
        self.assertEqual(corrected_expense.status_code, 201, corrected_expense.content)
        refreshed = self.financial_position(vehicle)
        self.assertEqual(refreshed.data["total_vehicle_cost"], "10500.00")
        self.assertEqual(refreshed.data["calculated_result"], "1500.00")
        self.assertEqual(refreshed.data["expense_correction_versions"], [
            {"expense_id": expense.data["id"], "version": 1}
        ])
        self.assertEqual(AccountingEvent.objects.count(), event_count + 2)

    def test_confirmed_vehicle_result_recognizes_company_share_once_without_cash_effect(self):
        investor = self.create_investor("result-confirm")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5091")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        paid = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RESULT-FULL-COLLECTION"},
            "result-full-collection",
            self.branch_accountant,
        )
        self.assertEqual(paid.status_code, 201, paid.content)
        position = self.financial_position(vehicle)
        self.assertRegex(position.data["sale_effective_date"], r"^\d{4}-\d{2}-\d{2}$")
        event_count = AccountingEvent.objects.count()
        request_body = {
            "expected_source_version": position.data["source_version"],
            "reason": "Verified sale and source costs",
        }
        first = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", request_body,
            "vehicle-result-confirm-1",
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.data["result_kind"], "PROFIT")
        self.assertEqual(first.data["result_amount"], "2000.00")
        self.assertEqual(first.data["investor_share_amount"], "700.00")
        self.assertEqual(first.data["company_share_amount"], "1300.00")
        company_share_event = AccountingEvent.objects.get(
            event_type=AccountingEvent.EventType.VEHICLE_COMPANY_SHARE,
        )
        sale_row = VehicleSale.objects.get(pk=sale.data["id"])
        self.assertEqual(company_share_event.amount, Decimal("1300.00"))
        self.assertEqual(company_share_event.branch_id, sale_row.branch_id)
        self.assertEqual(company_share_event.effective_at, sale_row.sold_at)
        self.assertEqual(company_share_event.effect_sign, 1)
        self.assertFalse(AccountMovement.objects.filter(event=company_share_event).exists())
        self.assertEqual(
            str(company_share_event.source_link.vehicle_result_confirmation_id),
            first.data["id"],
        )
        accounting_result = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/accounting/reports/accounting-result/"
            f"?period=monthly&year={sale_row.sold_at.year}&month={sale_row.sold_at.month}"
        )
        self.assertEqual(accounting_result.status_code, 200, accounting_result.content)
        self.assertEqual(accounting_result.data["income_amount"], "1300.00")
        self.assertEqual(accounting_result.data["accounting_result_amount"], "1300.00")
        replay = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", request_body,
            "vehicle-result-confirm-1",
        )
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(replay.data["id"], first.data["id"])
        duplicate = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", request_body,
            "vehicle-result-confirm-2",
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(VehicleResultConfirmation.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.count(), event_count + 1)

    def test_investor_period_reconciliation_is_company_confirmed_and_idempotent(self):
        investor = self.create_investor("period-reconciliation")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5098")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "PERIOD-RECONCILE-FULL"},
            "period-reconcile-receipt",
            self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        result = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Verified period source"},
            "period-reconcile-result",
        )
        self.assertEqual(result.status_code, 201, result.content)

        period_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-periods/"
        projection = self.client.get(period_path)
        self.assertEqual(projection.status_code, 200, projection.content)
        period = projection.data["periods"][0]
        self.assertEqual(period["gross_investor_profit"], "700.00")
        self.assertEqual(period["reconciliation_status"], "NOT_RECONCILED")
        self.assertEqual(len(period["source_version"]), 64)

        path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-period-reconciliations/"
        payload = {
            "period_start": period["period_start"],
            "expected_source_version": period["source_version"],
            "reason": "Reviewed the period source totals",
        }
        movement_count = AccountMovement.objects.count()
        first = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-1",
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.data["net_position"], "700.00")
        self.assertEqual(first.data["version"], 1)
        self.assertEqual(AccountMovement.objects.count(), movement_count)

        refreshed_projection = self.client.get(period_path)
        self.assertEqual(refreshed_projection.status_code, 200, refreshed_projection.content)
        refreshed_period = refreshed_projection.data["periods"][0]
        self.assertEqual(refreshed_projection.data["status"], "RECONCILED")
        self.assertEqual(refreshed_period["reconciliation_status"], "RECONCILED")
        self.assertEqual(refreshed_period["reconciliation_id"], first.data["id"])
        self.assertEqual(refreshed_period["paid_status"], "NOT_RECONCILED")
        self.assertEqual(refreshed_period["last_reconciled_net_position"], "700.00")
        self.assertIsNone(refreshed_period["confirmed_position"])
        position_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-positions/"
        position_payload = {"reconciliation_id": first.data["id"],
                            "expected_source_version": period["source_version"], "reason": "Confirm amount due"}
        self.client.force_authenticate(user=self.branch_accountant)
        denied_position = self.client.post(position_path, position_payload, format="json", HTTP_IDEMPOTENCY_KEY="period-position-denied")
        self.assertEqual(denied_position.status_code, 403, denied_position.content)
        self.client.force_authenticate(user=self.company_accountant)
        confirmed_position = self.client.post(position_path, position_payload, format="json", HTTP_IDEMPOTENCY_KEY="period-position-confirm")
        self.assertEqual(confirmed_position.status_code, 201, confirmed_position.content)
        self.assertEqual(confirmed_position.data["kind"], "PAYABLE")
        self.assertEqual(confirmed_position.data["amount"], "700.00")
        position_replay = self.client.post(position_path, position_payload, format="json", HTTP_IDEMPOTENCY_KEY="period-position-confirm")
        self.assertEqual(position_replay.data, confirmed_position.data)
        self.assertEqual(AccountMovement.objects.count(), movement_count)
        from apps.investment.models import InvestorProfitPeriodPosition
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorProfitPeriodPosition.objects.filter(pk=confirmed_position.data["id"]).update(reason="Overwrite")

        replay = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-1",
        )
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(replay.data["id"], first.data["id"])
        duplicate_source = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-2",
        )
        self.assertEqual(duplicate_source.status_code, 200, duplicate_source.content)
        self.assertEqual(duplicate_source.data["id"], first.data["id"])
        self.assertEqual(AccountMovement.objects.count(), movement_count)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InvestorProfitPeriodReconciliation.objects.filter(pk=first.data["id"]).update(
                    reason="Unreviewed database edit",
                )

        self.client.force_authenticate(user=self.company_accountant)
        current_position = self.financial_position(vehicle)
        recovery = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/",
            {"expected_source_version": current_position.data["source_version"], "reason": "Recover period fixture capital"},
            format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-capital-recovery",
        )
        self.assertEqual(recovery.status_code, 201, recovery.content)
        self.client.force_authenticate(user=self.branch_accountant)
        payment_path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{result.data['id']}/profit-payments/"
        )
        movement_count_before_payment = AccountMovement.objects.count()
        payment = self.client.post(
            payment_path,
            {
                "account_id": str(self.bank.pk),
                "amount": "100.00",
                "effective_at": timezone.now().isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="period-reconcile-deal-payment",
        )
        self.assertEqual(payment.status_code, 201, payment.content)
        self.assertEqual(AccountMovement.objects.count(), movement_count_before_payment + 1)

        self.client.force_authenticate(user=self.company_accountant)
        changed_projection = self.client.get(period_path)
        self.assertEqual(changed_projection.status_code, 200, changed_projection.content)
        changed_period = changed_projection.data["periods"][0]
        self.assertEqual(changed_projection.data["status"], "CALCULATED_NOT_RECONCILED")
        self.assertEqual(changed_period["reconciliation_status"], "RESTATEMENT_REQUIRED")
        self.assertEqual(changed_period["last_reconciled_net_position"], "700.00")
        self.assertEqual(changed_period["last_restatement_adjustment"], "0.00")
        self.assertEqual(changed_period["pending_restatement_adjustment"], "-100.00")
        self.assertFalse(changed_period["confirmed_position"]["is_current"])
        stale_position = self.client.post(position_path, position_payload, format="json", HTTP_IDEMPOTENCY_KEY="period-position-stale")
        self.assertEqual(stale_position.status_code, 409, stale_position.content)
        restatement = self.client.post(
            path,
            {
                "period_start": changed_period["period_start"],
                "expected_source_version": changed_period["source_version"],
                "reason": "Record the later confirmed Profit payment",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="period-reconcile-restatement-1",
        )
        self.assertEqual(restatement.status_code, 201, restatement.content)
        self.assertEqual(restatement.data["version"], 2)
        self.assertEqual(restatement.data["previous_reconciliation_id"], first.data["id"])
        self.assertEqual(restatement.data["net_position"], "600.00")
        self.assertEqual(restatement.data["restatement_adjustment"], "-100.00")
        new_position = self.client.post(position_path, {
            "reconciliation_id": restatement.data["id"], "expected_source_version": changed_period["source_version"],
            "reason": "Confirm restated amount",
        }, format="json", HTTP_IDEMPOTENCY_KEY="period-position-restated")
        self.assertEqual(new_position.status_code, 201, new_position.content)
        self.assertEqual(new_position.data["amount"], "600.00")
        self.assertEqual(new_position.data["previous_position_id"], confirmed_position.data["id"])
        self.assertEqual(AccountMovement.objects.count(), movement_count_before_payment + 1)

        self.add_revision("investor_portal", 1)
        investor_user = make_user(
            "period-reconciliation-portal-investor", role="investor", tenant=self.company
        )
        binding = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/portal-binding/",
            {"account_id": str(investor_user.pk)}, format="json",
            HTTP_IDEMPOTENCY_KEY="period-reconciliation-portal-binding",
        )
        self.assertEqual(binding.status_code, 201, binding.content)
        self.client.force_authenticate(user=investor_user)
        portal = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/portal/self/")
        self.assertEqual(portal.status_code, 200, portal.content)
        portal_period = portal.data["profit_periods"][0]
        self.assertEqual(portal_period["reconciliation_status"], "RECONCILED")
        self.assertEqual(portal_period["confirmed_snapshot"]["net_position"], "600.00")
        self.assertNotIn("reason", portal_period["confirmed_snapshot"])
        self.assertNotIn("source_version", portal_period["confirmed_snapshot"])
        self.assertIn("not a payable", portal_period["confirmed_snapshot"]["notice"].lower())

        self.client.force_authenticate(user=self.branch_accountant)
        additional_payment = self.client.post(
            payment_path,
            {"account_id": str(self.bank.pk), "amount": "50.00",
             "effective_at": timezone.now().isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-portal-stale-payment",
        )
        self.assertEqual(additional_payment.status_code, 201, additional_payment.content)
        self.client.force_authenticate(user=investor_user)
        stale_portal = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/portal/self/")
        self.assertEqual(stale_portal.status_code, 200, stale_portal.content)
        stale_period = stale_portal.data["profit_periods"][0]
        self.assertEqual(stale_period["reconciliation_status"], "RESTATEMENT_REQUIRED")
        self.assertEqual(stale_period["confirmed_snapshot"]["net_position"], "600.00")
        self.assertEqual(stale_period["confirmed_snapshot"]["pending_restatement_adjustment"], "-50.00")
        self.assertEqual(AccountMovement.objects.count(), movement_count_before_payment + 2)

        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="period-reconcile-branch",
        )
        self.assertEqual(denied.status_code, 403, denied.content)

    def test_internal_recovery_can_classify_repeated_investor_only_receipts(self):
        from apps.investment.services import create_vehicle_capital_recovery

        investor = self.create_investor("recovery-partial")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5194")
        purchase = self.post(
            "purchases/", {"vehicle_id": str(vehicle.pk), "branch_id": str(self.branch.pk),
            "purchase_cost": "10000.00", "seller_name": "North Motors", "investor_id": str(investor.pk),
            "investor_fund_amount": "10000.00", "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
            "recovery-partial-purchase",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        sale = self.create_sale(vehicle)
        first_receipt = self.post(
            f"sales/{sale.data['id']}/receipts/", {"account_id": str(self.bank.pk), "amount": "3000.00", "reference": "PARTIAL-RECOVERY-1"},
            "partial-recovery-receipt-1", self.branch_accountant,
        )
        self.assertEqual(first_receipt.status_code, 201, first_receipt.content)
        first_position = self.financial_position(vehicle)
        first = create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk, sale_id=sale.data["id"],
            expected_source_version=first_position.data["source_version"], reason="Confirm collected capital",
            key="partial-recovery-1", path="/internal-test/capital-recovery/",
        )
        self.assertEqual(first.body["investor_principal"], "3000.00")
        second_receipt = self.post(
            f"sales/{sale.data['id']}/receipts/", {"account_id": str(self.bank.pk), "amount": "9000.00", "reference": "PARTIAL-RECOVERY-2"},
            "partial-recovery-receipt-2", self.branch_accountant,
        )
        self.assertEqual(second_receipt.status_code, 201, second_receipt.content)
        second_position = self.financial_position(vehicle)
        second = create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk, sale_id=sale.data["id"],
            expected_source_version=second_position.data["source_version"], reason="Confirm collected capital",
            key="partial-recovery-2", path="/internal-test/capital-recovery/",
        )
        self.assertEqual(second.body["investor_principal"], "7000.00")
        from apps.investment.fund_position import investor_fund_position
        before_correction = investor_fund_position(company=self.company, investor=investor)
        self.assertEqual(before_correction.available, Decimal("10000.00"))
        correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "8000.00", "reason": "Correct agreement"}, "partial-recovery-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        after_correction = investor_fund_position(company=self.company, investor=investor)
        self.assertEqual(after_correction.gross_available, Decimal("10000.00"))
        self.assertEqual(after_correction.principal_refund_due, Decimal("2000.00"))
        self.assertEqual(after_correction.reserve, Decimal("2000.00"))
        self.assertEqual(after_correction.available, Decimal("8000.00"))
        self.client.force_authenticate(user=self.company_accountant)
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["available_amount"], "8000.00")
        self.assertEqual(summary.data["reserved_amount"], "2000.00")
        branch_summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/", {"investor_id": str(investor.pk), "branch_id": str(self.branch.pk)})
        self.assertEqual(branch_summary.status_code, 200, branch_summary.content)
        self.assertEqual(branch_summary.data["reserved_amount"], "2000.00")
        other_branch = Branch.objects.create(tenant=self.company, name="Empty Branch")
        empty_summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/", {"investor_id": str(investor.pk), "branch_id": str(other_branch.pk)})
        self.assertEqual(empty_summary.status_code, 200, empty_summary.content)
        self.assertEqual(empty_summary.data["reserved_amount"], "0.00")
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            credit_id = investor.fund_credits.get().pk
            cursor.execute("SELECT investment_credit_available(%s)", [credit_id])
            self.assertEqual(cursor.fetchone()[0], Decimal("8000.00"))
        from apps.investment.models import InvestorPrincipalReturn, InvestorPrincipalReturnAllocation
        with self.assertRaisesRegex(IntegrityError, "available Fund"), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL DEFERRED")
            attempted = InvestorPrincipalReturn.objects.create(
                tenant=self.company, investor=investor, branch=self.branch, amount=Decimal("8000.01"),
                effective_at=timezone.now(), reference="RESERVE-GUARD", actor=self.company_accountant,
                module_revision=CompanyModuleState.objects.get(tenant=self.company, module_code="investment", version=1),
            )
            InvestorPrincipalReturnAllocation.objects.create(
                tenant=self.company, principal_return=attempted, credit_id=credit_id,
                amount=Decimal("8000.01"), actor=self.company_accountant,
            )
            self.fail("The database accepted a withdrawal that spends the refund reserve.")
        from apps.investment.models import InvestorFundUseAllocation
        original_use = InvestorFundUseAllocation.objects.get(tenant=self.company, credit_id=credit_id)
        with self.assertRaisesRegex(IntegrityError, "available Fund"), transaction.atomic():
            InvestorFundUseAllocation.objects.create(
                tenant=self.company, fund_use=original_use.fund_use, credit_id=credit_id,
                amount=Decimal("8000.01"), actor=self.company_accountant,
            )
            self.fail("The database accepted Vehicle funding that spends the refund reserve.")

    def test_internal_recovery_classification_reconciles_receipt_and_credit_sources(self):
        from apps.investment.services import create_vehicle_capital_recovery
        from apps.investment.models import VehicleCapitalRecovery, VehicleCapitalRecoveryReceiptAllocation

        investor = self.create_investor("recovery-internal")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5195")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RECOVERY-INTERNAL"},
            "recovery-internal-receipt", self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        movements = AccountMovement.objects.count()
        recovered = create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk, sale_id=sale.data["id"],
            expected_source_version=position.data["source_version"], reason="Confirm collected capital",
            key="internal-capital-recovery", path="/internal-test/capital-recovery/",
        )
        self.assertEqual(recovered.status, 201)
        row = VehicleCapitalRecovery.objects.get(pk=recovered.body["id"])
        self.assertEqual(row.investor_principal, Decimal("6000.00"))
        self.assertEqual(row.running_capital, Decimal("4000.00"))
        self.assertEqual(row.credit_allocations.get().amount, Decimal("6000.00"))
        self.assertEqual(str(row.receipt_allocations.get().receipt_id), receipt.data["receipt_id"])
        self.assertEqual(AccountMovement.objects.count(), movements)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SELECT investment_credit_gross_available(%s)", [row.credit_allocations.get().credit_id])
            self.assertEqual(cursor.fetchone()[0], Decimal("10000.00"))
            cursor.execute("SELECT investment_credit_available(%s)", [row.credit_allocations.get().credit_id])
            self.assertEqual(cursor.fetchone()[0], Decimal("10000.00"))
        # A direct database writer must not classify the remaining Profit as
        # Company capital merely because the Buyer receipt has unused cash.
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL DEFERRED")
            forged = VehicleCapitalRecovery.objects.create(
                tenant=self.company, sale=row.sale, investor=investor,
                investor_principal=Decimal("0.00"), running_capital=Decimal("2000.00"),
                source_version=row.source_version, funding_version=row.funding_version,
                reason="Invalid extra capital", actor=self.company_accountant,
                investment_revision=row.investment_revision, vehicle_revision=row.vehicle_revision,
                accounting_revision=row.accounting_revision,
            )
            VehicleCapitalRecoveryReceiptAllocation.objects.create(
                tenant=self.company, recovery=forged, receipt_id=receipt.data["receipt_id"],
                investor_principal=Decimal("0.00"), running_capital=Decimal("2000.00"),
            )
            record_event(
                action="investment.capital.recovery.confirm", actor=self.company_accountant,
                subject=self.company_accountant, company=self.company, branch=row.sale.branch,
                resource=forged, reason=forged.reason,
                metadata={"sale_id": str(row.sale_id), "investor_principal": "0.00", "running_capital": "2000.00"},
            )
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_period_position_confirms_excess_interim_as_recoverable_without_cash(self):
        credit_at = timezone.now() - timedelta(days=35)
        investor = self.create_investor("position-recoverable", credit_effective_at=credit_at)
        base = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/"
        self.client.force_authenticate(user=self.company_accountant)
        config = self.client.post(base + "interim-configurations/", {
            "amount": "1000.00", "effective_date": credit_at.date().replace(day=1).isoformat(),
        }, format="json", HTTP_IDEMPOTENCY_KEY="position-interim-config")
        self.assertEqual(config.status_code, 201, config.content)
        paid = self.client.post(base + "interim-payments/", {
            "branch_id": str(self.branch.pk), "account_id": str(self.bank.pk),
            "amount": "1000.00", "effective_at": timezone.now().isoformat(),
        }, format="json", HTTP_IDEMPOTENCY_KEY="position-interim-payment")
        self.assertEqual(paid.status_code, 201, paid.content)
        movements = AccountMovement.objects.count()
        projection = self.client.get(base + "profit-periods/")
        self.assertEqual(projection.status_code, 200, projection.content)
        period = projection.data["periods"][0]
        snapshot = self.client.post(base + "profit-period-reconciliations/", {
            "period_start": period["period_start"], "expected_source_version": period["source_version"],
            "reason": "Review actual advances",
        }, format="json", HTTP_IDEMPOTENCY_KEY="position-recoverable-snapshot")
        self.assertEqual(snapshot.status_code, 201, snapshot.content)
        with connection.cursor() as cursor:
            cursor.execute("SELECT investment_profit_period_source_version(%s)", [snapshot.data["id"]])
            self.assertEqual(cursor.fetchone()[0], snapshot.data["source_version"])
        position = self.client.post(base + "profit-positions/", {
            "reconciliation_id": snapshot.data["id"], "expected_source_version": period["source_version"],
            "reason": "Confirm excess advance recoverable",
        }, format="json", HTTP_IDEMPOTENCY_KEY="position-recoverable-confirm")
        self.assertEqual(position.status_code, 201, position.content)
        self.assertEqual(position.data["kind"], "RECOVERABLE")
        self.assertEqual(position.data["amount"], "1000.00")
        self.assertEqual(AccountMovement.objects.count(), movements)
        self.assertEqual(AccountingEvent.objects.filter(event_type="INCOME").count(), 0)
        repay_path = base + f"profit-positions/{position.data['id']}/repayments/"
        repay_body = {
            "branch_id": str(self.branch.pk), "account_id": str(self.bank.pk), "amount": "400.00",
            "expected_source_version": period["source_version"], "reason": "Actual partial Investor repayment",
        }
        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(repay_path, repay_body, format="json", HTTP_IDEMPOTENCY_KEY="position-repay-branch-denied")
        self.assertEqual(denied.status_code, 403, denied.content)
        self.client.force_authenticate(user=self.company_accountant)
        other = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/", {"name": "Other Investor"},
            format="json", HTTP_IDEMPOTENCY_KEY="position-other-investor",
        )
        self.assertEqual(other.status_code, 201, other.content)
        wrong_investor = self.client.post(
            base.replace(str(investor.pk), str(other.data["id"])) + f"profit-positions/{position.data['id']}/repayments/",
            repay_body, format="json", HTTP_IDEMPOTENCY_KEY="position-repay-wrong-investor",
        )
        self.assertEqual(wrong_investor.status_code, 404, wrong_investor.content)
        first = self.client.post(repay_path, repay_body, format="json", HTTP_IDEMPOTENCY_KEY="position-repay-first")
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.data["position"]["amount"], "600.00")
        retry = self.client.post(repay_path, repay_body, format="json", HTTP_IDEMPOTENCY_KEY="position-repay-first")
        self.assertEqual(retry.data, first.data)
        self.assertEqual(AccountMovement.objects.count(), movements + 1)
        self.assertEqual(AccountMovement.objects.get(event_id=first.data["accounting_event_id"]).delta, Decimal("400.00"))
        excess = self.client.post(repay_path, {**repay_body, "amount": "600.01"}, format="json",
                                  HTTP_IDEMPOTENCY_KEY="position-repay-excess")
        self.assertEqual(excess.status_code, 409, excess.content)
        final = self.client.post(repay_path, {**repay_body, "amount": "600.00"}, format="json",
                                 HTTP_IDEMPOTENCY_KEY="position-repay-final")
        self.assertEqual(final.status_code, 201, final.content)
        self.assertEqual(final.data["position"]["kind"], "BALANCED")
        self.assertEqual(AccountMovement.objects.count(), movements + 2)
        refreshed = self.client.get(base + "profit-periods/")
        self.assertEqual(refreshed.data["periods"][0]["confirmed_position"]["amount"], "0.00")
        self.assertEqual(AccountingEvent.objects.filter(event_type="INCOME").count(), 0)
        from apps.investment.models import InvestorProfitRecoveryReceipt
        receipt = InvestorProfitRecoveryReceipt.objects.get(pk=first.data["receipt_id"])
        with self.assertRaisesMessage(IntegrityError, "repayment exceeds"), transaction.atomic():
            InvestorProfitRecoveryReceipt.objects.create(
                tenant=self.company, position=receipt.position, branch=self.branch, account=self.bank,
                amount=Decimal("0.01"), effective_at=timezone.now(), actor=self.company_accountant,
                reason="Direct excess attempt", investment_revision=receipt.investment_revision,
                accounting_revision=receipt.accounting_revision,
            )

    def test_future_profit_adjustment_reduces_both_positions_and_prevents_double_payment(self):
        first_credit = timezone.now() - timedelta(days=220)
        investor = self.create_investor("future-adjustment", credit_effective_at=first_credit)
        base = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/"
        self.client.force_authenticate(user=self.company_accountant)
        config = self.client.post(base + "interim-configurations/", {
            "amount": "1000.00", "effective_date": first_credit.date().replace(day=1).isoformat(),
        }, format="json", HTTP_IDEMPOTENCY_KEY="future-config")
        self.assertEqual(config.status_code, 201, config.content)
        interim = self.client.post(base + "interim-payments/", {
            "branch_id": str(self.branch.pk), "account_id": str(self.bank.pk), "amount": "1000.00",
            "effective_at": (first_credit + timedelta(days=1)).isoformat(),
        }, format="json", HTTP_IDEMPOTENCY_KEY="future-interim")
        self.assertEqual(interim.status_code, 201, interim.content)
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5921")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(f"sales/{sale.data['id']}/receipts/", {
            "account_id": str(self.bank.pk), "amount": "12000.00", "reference": "FUTURE-PROFIT",
        }, "future-sale-receipt")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        financial = self.financial_position(vehicle)
        confirmed = self.post(f"vehicles/{vehicle.pk}/financial-position/confirm/", {
            "expected_source_version": financial.data["source_version"], "reason": "Confirm future Profit",
        }, "future-result")
        self.assertEqual(confirmed.status_code, 201, confirmed.content)
        self.client.force_authenticate(user=self.company_accountant)
        recovered = self.client.post(f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/",
            {"expected_source_version": financial.data["source_version"], "reason": "Recover actual capital"},
            format="json", HTTP_IDEMPOTENCY_KEY="future-capital")
        self.assertEqual(recovered.status_code, 201, recovered.content)
        projection = self.client.get(base + "profit-periods/")
        self.assertEqual(projection.status_code, 200, projection.content)
        positions = {}
        for n, period in enumerate(projection.data["periods"]):
            snapshot = self.client.post(base + "profit-period-reconciliations/", {
                "period_start": period["period_start"], "expected_source_version": period["source_version"],
                "reason": "Review period",
            }, format="json", HTTP_IDEMPOTENCY_KEY=f"future-snapshot-{n}")
            self.assertEqual(snapshot.status_code, 201, snapshot.content)
            pos = self.client.post(base + "profit-positions/", {
                "reconciliation_id": snapshot.data["id"], "expected_source_version": period["source_version"],
                "reason": "Confirm period position",
            }, format="json", HTTP_IDEMPOTENCY_KEY=f"future-position-{n}")
            self.assertEqual(pos.status_code, 201, pos.content)
            positions[pos.data["kind"]] = pos.data
        debt, profit = positions["RECOVERABLE"], positions["PAYABLE"]
        movements = AccountMovement.objects.count()
        path = base + f"profit-positions/{debt['id']}/future-adjustments/"
        body = {"profit_position_id": profit["id"], "profit_result_id": confirmed.data["id"], "amount": "400.00",
                "expected_source_version": debt["source_version"], "expected_profit_source_version": profit["source_version"],
                "reason": "Apply specifically confirmed future Profit"}
        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(path, body, format="json", HTTP_IDEMPOTENCY_KEY="future-denied")
        self.assertEqual(denied.status_code, 403, denied.content)
        self.client.force_authenticate(user=self.company_accountant)
        adjusted = self.client.post(path, body, format="json", HTTP_IDEMPOTENCY_KEY="future-adjust")
        self.assertEqual(adjusted.status_code, 201, adjusted.content)
        self.assertEqual(adjusted.data["recoverable_position"]["amount"], "600.00")
        self.assertEqual(adjusted.data["profit_position"]["amount"], "300.00")
        replay = self.client.post(path, body, format="json", HTTP_IDEMPOTENCY_KEY="future-adjust")
        self.assertEqual(replay.data, adjusted.data)
        self.assertEqual(AccountMovement.objects.count(), movements)
        excess = self.client.post(path, {**body, "amount": "300.01"}, format="json", HTTP_IDEMPOTENCY_KEY="future-excess")
        self.assertEqual(excess.status_code, 409, excess.content)
        payment_path = f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{confirmed.data['id']}/profit-payments/"
        double = self.client.post(payment_path, {"account_id": str(self.bank.pk), "amount": "400.00"},
                                  format="json", HTTP_IDEMPOTENCY_KEY="future-double-payment")
        self.assertEqual(double.status_code, 409, double.content)
        # Keep the SQL/Python freshness assertion deterministic when PostgreSQL
        # JSON formatting would otherwise omit the final microsecond digits.
        payment_time = (timezone.now() - timedelta(seconds=1)).replace(microsecond=123400)
        paid = self.client.post(
            payment_path,
            {"account_id": str(self.bank.pk), "amount": "300.00", "effective_at": payment_time.isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY="future-valid-payment",
        )
        self.assertEqual(paid.status_code, 201, paid.content)
        profit_period = next(row for row in self.client.get(base + "profit-periods/").data["periods"]
                             if Decimal(row["gross_investor_profit"]) > 0)
        payment_snapshot = self.client.post(base + "profit-period-reconciliations/", {
            "period_start": profit_period["period_start"],
            "expected_source_version": profit_period["source_version"],
            "reason": "Review paid Deal source",
        }, format="json", HTTP_IDEMPOTENCY_KEY="future-paid-snapshot")
        self.assertEqual(payment_snapshot.status_code, 201, payment_snapshot.content)
        with connection.cursor() as cursor:
            cursor.execute("SELECT investment_profit_period_source_version(%s)", [payment_snapshot.data["id"]])
            self.assertEqual(cursor.fetchone()[0], payment_snapshot.data["source_version"])
        repay_path = base + f"profit-positions/{debt['id']}/repayments/"
        excess_receipt = self.client.post(repay_path, {
            "branch_id": str(self.branch.pk), "account_id": str(self.bank.pk), "amount": "600.01",
            "expected_source_version": debt["source_version"], "reason": "Cannot collect adjusted amount twice",
        }, format="json", HTTP_IDEMPOTENCY_KEY="future-excess-receipt")
        self.assertEqual(excess_receipt.status_code, 409, excess_receipt.content)
        self.assertEqual(AccountMovement.objects.count(), movements + 1)

    def test_mixed_vehicle_recovery_reuses_receipt_and_unlocks_profit_payment(self):
        investor = self.create_investor("recovery-vertical")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5197")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RECOVERY-VERTICAL"},
            "recovery-vertical-receipt", self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        result = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Review result"},
            "recovery-vertical-result",
        )
        self.assertEqual(result.status_code, 201, result.content)
        recovery_path = f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/"
        request = {"expected_source_version": position.data["source_version"], "reason": "Confirm collected capital"}
        movements = AccountMovement.objects.count()
        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(recovery_path, request, format="json", HTTP_IDEMPOTENCY_KEY="recovery-branch")
        self.assertEqual(denied.status_code, 403, denied.content)
        self.client.force_authenticate(user=self.company_accountant)
        recovery = self.client.post(recovery_path, request, format="json", HTTP_IDEMPOTENCY_KEY="recovery-vertical")
        self.assertEqual(recovery.status_code, 201, recovery.content)
        self.assertEqual(recovery.data["investor_principal"], "6000.00")
        self.assertEqual(recovery.data["running_capital"], "4000.00")
        replay = self.client.post(recovery_path, request, format="json", HTTP_IDEMPOTENCY_KEY="recovery-vertical")
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(replay.data["id"], recovery.data["id"])
        self.assertEqual(AccountMovement.objects.count(), movements)
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["available_amount"], "10000.00")
        self.client.force_authenticate(user=self.branch_accountant)
        payment = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{result.data['id']}/profit-payments/",
            {"account_id": str(self.bank.pk), "amount": "100.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="recovery-vertical-profit-payment",
        )
        self.assertEqual(payment.status_code, 201, payment.content)
        self.assertEqual(AccountMovement.objects.count(), movements + 1)

        # An upward Sale correction changes Profit, but must not recover the
        # same capital again or strand its original Fund lots.
        corrected = self.post(f"sales/{sale.data['id']}/corrections/",
                              {"sale_price": "13000.00", "reason": "Correct agreed price"},
                              "recovery-vertical-upward")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        extra = self.post(f"sales/{sale.data['id']}/receipts/",
                          {"account_id": str(self.bank.pk), "amount": "1000.00", "reference": "RECOVERY-VERTICAL-EXTRA"},
                          "recovery-vertical-extra", self.branch_accountant)
        self.assertEqual(extra.status_code, 201, extra.content)
        position = self.financial_position(vehicle)
        confirmed = self.post(f"vehicles/{vehicle.pk}/financial-position/confirm/",
                              {"expected_source_version": position.data["source_version"], "reason": "Review corrected result"},
                              "recovery-vertical-corrected-result")
        self.assertEqual(confirmed.status_code, 201, confirmed.content)
        before_review = AccountMovement.objects.count()
        self.client.force_authenticate(user=self.company_accountant)
        stale_summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(stale_summary.status_code, 409, stale_summary.content)
        request = {"expected_source_version": position.data["source_version"], "reason": "Revalidate unchanged capital"}
        reviewed = self.client.post(recovery_path, request, format="json", HTTP_IDEMPOTENCY_KEY="recovery-vertical-review")
        self.assertEqual(reviewed.status_code, 201, reviewed.content)
        self.assertTrue(reviewed.data["review_only"])
        replay = self.client.post(recovery_path, request, format="json", HTTP_IDEMPOTENCY_KEY="recovery-vertical-review")
        self.assertEqual(replay.data, reviewed.data)
        self.assertEqual(AccountMovement.objects.count(), before_review)
        from apps.investment.models import VehicleCapitalRecovery, VehicleCapitalRecoveryReview
        from apps.investment.fund_position import investor_fund_position
        self.assertEqual(VehicleCapitalRecovery.objects.filter(sale_id=sale.data["id"]).count(), 1)
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.data["available_amount"], "10000.00")
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).available, Decimal("10000.00"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehicleCapitalRecoveryReview.objects.filter(pk=reviewed.data["id"]).update(reason="Overwrite review")
        from importlib import import_module
        from django.db import DatabaseError
        reverse_sql = import_module("apps.investment.migrations.0033_capital_recovery_review").REVERSE
        with self.assertRaises(DatabaseError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(reverse_sql)
        self.assertTrue(VehicleCapitalRecoveryReview.objects.filter(pk=reviewed.data["id"]).exists())
        self.client.force_authenticate(user=self.branch_accountant)
        next_payment = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{confirmed.data['id']}/profit-payments/",
            {"account_id": str(self.bank.pk), "amount": "100.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="recovery-vertical-corrected-profit",
        )
        self.assertEqual(next_payment.status_code, 201, next_payment.content)
        self.assertEqual(AccountMovement.objects.count(), before_review + 1)
        corrected_loss = self.post(f"sales/{sale.data['id']}/corrections/",
                                   {"sale_price": "8000.00", "reason": "Review final Buyer correction"},
                                   "mixed-principal-refund-correction")
        self.assertEqual(corrected_loss.status_code, 201, corrected_loss.content)
        current = self.financial_position(vehicle)
        review_path = f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/principal-refund-reviews/"
        self.client.force_authenticate(user=self.company_accountant)
        principal_review = self.client.post(review_path, {
            "principal_amount": "2000.00", "expected_source_version": current.data["source_version"],
            "reason": "Accountant confirms principal part of Buyer obligation",
        }, format="json", HTTP_IDEMPOTENCY_KEY="mixed-principal-review")
        self.assertEqual(principal_review.status_code, 201, principal_review.content)
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["available_amount"], "8000.00")
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).reserve, Decimal("2000.00"))
        partial = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "1000.00", "investor_principal_amount": "1000.00",
        }, "mixed-principal-partial")
        self.assertEqual(partial.status_code, 201, partial.content)
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).reserve, Decimal("1000.00"))
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.data["available_amount"], "8000.00")

    def test_principal_refund_debit_database_scope_cap_and_history(self):
        from apps.investment.fund_position import FundPositionReviewRequired, investor_fund_position
        from apps.investment.models import VehicleCapitalRecovery, VehiclePrincipalRefundDebit
        from apps.investment.services import create_vehicle_capital_recovery

        investor = self.create_investor("refund-debit-guards")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5193")
        purchase = self.post(
            "purchases/", {"vehicle_id": str(vehicle.pk), "branch_id": str(self.branch.pk),
            "purchase_cost": "10000.00", "seller_name": "North Motors", "investor_id": str(investor.pk),
            "investor_fund_amount": "10000.00", "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
            "refund-debit-purchase",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/", {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "REFUND-DEBIT-RECEIPT"},
            "refund-debit-receipt", self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        result = create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk, sale_id=sale.data["id"],
            expected_source_version=position.data["source_version"], reason="Confirm capital", key="refund-debit-recovery",
            path="/internal-test/refund-debit/",
        )
        allocation = VehicleCapitalRecovery.objects.get(pk=result.body["id"]).credit_allocations.get()
        corrected = self.post(f"sales/{sale.data['id']}/corrections/", {"sale_price": "8000.00", "reason": "Correct sale"}, "refund-debit-correction")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).available, Decimal("8000.00"))
        missing = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "4000.00",
        }, "refund-debit-missing")
        self.assertEqual(missing.status_code, 409, missing.content)
        invalid = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "1000.00", "investor_principal_amount": "1000.01",
        }, "refund-debit-invalid")
        self.assertEqual(invalid.status_code, 409, invalid.content)
        denied = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "1000.00", "investor_principal_amount": "0.00",
        }, "refund-debit-denied", self.branch_accountant)
        self.assertEqual(denied.status_code, 403, denied.content)
        partial = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "1000.00", "investor_principal_amount": "0.00",
        }, "refund-debit-zero")
        self.assertEqual(partial.status_code, 201, partial.content)
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).reserve, Decimal("2000.00"))
        refunded = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "3000.00", "investor_principal_amount": "2000.00",
        }, "refund-debit-actual")
        self.assertEqual(refunded.status_code, 201, refunded.content)
        self.assertEqual(investor_fund_position(company=self.company, investor=investor).available, Decimal("8000.00"))
        self.client.force_authenticate(user=self.company_accountant)
        summary = self.client.get(f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}")
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["used_total"], "2000.00")
        with connection.cursor() as cursor:
            cursor.execute("SELECT investment_credit_available(%s)", [allocation.credit_id])
            self.assertEqual(cursor.fetchone()[0], Decimal("8000.00"))
        movements_after_refund = AccountMovement.objects.count()
        replay = self.post(f"sales/{sale.data['id']}/refunds/", {
            "account_id": str(self.bank.pk), "amount": "3000.00", "investor_principal_amount": "2000.00",
        }, "refund-debit-actual")
        self.assertEqual(replay.data, refunded.data)
        self.assertEqual(AccountMovement.objects.count(), movements_after_refund)
        foreign = Tenant.objects.create(name="Foreign", slug="refund-debit-foreign")
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehiclePrincipalRefundDebit.objects.create(tenant=foreign, refund_id=refunded.data["refund_id"], recovery_allocation=allocation, fund_credit=allocation.credit, amount=Decimal("1.00"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehiclePrincipalRefundDebit.objects.create(tenant=self.company, refund_id=refunded.data["refund_id"], recovery_allocation=allocation, fund_credit=allocation.credit, amount=Decimal("4000.01"))
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        debit = VehiclePrincipalRefundDebit.objects.get(refund_id=refunded.data["refund_id"])
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(AccountMovement.objects.count(), movements_after_refund)
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehiclePrincipalRefundDebit.objects.filter(pk=debit.pk).update(amount=Decimal("1.00"))

    def test_investor_only_recovery_reserves_principal_backed_buyer_refund(self):
        investor = self.create_investor("recovery-refund")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5196")
        purchase = self.post(
            "purchases/",
            {"vehicle_id": str(vehicle.pk), "branch_id": str(self.branch.pk),
             "purchase_cost": "10000.00", "seller_name": "North Motors",
             "investor_id": str(investor.pk), "investor_fund_amount": "10000.00",
             "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
            "recovery-refund-purchase",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RECOVERY-REFUND"},
            "recovery-refund-receipt", self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        recovery_path = f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/"
        self.client.force_authenticate(user=self.company_accountant)
        recovery = self.client.post(
            recovery_path, {"expected_source_version": position.data["source_version"], "reason": "Confirm collected capital"},
            format="json", HTTP_IDEMPOTENCY_KEY="recovery-refund-confirm",
        )
        self.assertEqual(recovery.status_code, 201, recovery.content)
        correction = self.post(
            f"sales/{sale.data['id']}/corrections/", {"sale_price": "8000.00", "reason": "Correct sale agreement"},
            "recovery-refund-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        summary_path = f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/?investor_id={investor.pk}"
        summary = self.client.get(summary_path)
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["available_amount"], "8000.00")
        refund = self.post(
            f"sales/{sale.data['id']}/refunds/", {"account_id": str(self.bank.pk), "amount": "4000.00", "investor_principal_amount": "2000.00"},
            "recovery-refund-payment",
        )
        self.assertEqual(refund.status_code, 201, refund.content)
        summary_after = self.client.get(summary_path)
        self.assertEqual(summary_after.status_code, 200, summary_after.content)
        self.assertEqual(summary_after.data["available_amount"], "8000.00")

    def test_profit_payment_requires_verified_principal_recovery(self):
        investor = self.create_investor("recovery-required")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5199")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RECOVERY-REQUIRED"},
            "recovery-required-receipt", self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        confirmed = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Verified result"},
            "recovery-required-result",
        )
        self.assertEqual(confirmed.status_code, 201, confirmed.content)
        before = AccountMovement.objects.count()
        self.client.force_authenticate(user=self.branch_accountant)
        response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{confirmed.data['id']}/profit-payments/",
            {"account_id": str(self.bank.pk), "amount": "100.00"},
            format="json", HTTP_IDEMPOTENCY_KEY="recovery-required-payment",
        )
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()["code"], "VEHICLE_CAPITAL_RECOVERY_REQUIRED")
        self.assertEqual(AccountMovement.objects.count(), before)
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorVehicleProfitPayment.objects.create(
                tenant=self.company, result_confirmation_id=confirmed.data["id"], investor=investor,
                branch=self.branch, account=self.bank, amount=Decimal("100.00"),
                effective_at=timezone.now(), actor=self.branch_accountant,
                vehicle_module_revision=CompanyModuleState.objects.get(
                    tenant=self.company, module_code="vehicle_management", version=1),
                investment_module_revision=CompanyModuleState.objects.get(
                    tenant=self.company, module_code="investment", version=1),
                description="Attempt without recovered capital", source_reference="UNRECOVERED-PROFIT",
            )

    def test_confirmed_investor_share_can_be_paid_in_sale_branch_once_and_with_cap(self):
        investor = self.create_investor("deal-profit-payment")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("35.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5101")
        self.create_purchase(vehicle, investor=investor)
        sale = self.create_sale(vehicle)
        receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "DEAL-PROFIT-COLLECTION"},
            "deal-profit-full-collection",
            self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        confirmed = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Verified Vehicle result"},
            "deal-profit-result-confirmation",
        )
        self.assertEqual(confirmed.status_code, 201, confirmed.content)
        self.client.force_authenticate(user=self.company_accountant)
        recovery = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/sales/{sale.data['id']}/capital-recoveries/",
            {"expected_source_version": position.data["source_version"], "reason": "Recover Vehicle capital"},
            format="json", HTTP_IDEMPOTENCY_KEY="deal-profit-capital-recovery",
        )
        self.assertEqual(recovery.status_code, 201, recovery.content)

        path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{confirmed.data['id']}/profit-payments/"
        )
        payload = {
            "account_id": str(self.bank.pk),
            "amount": "400.00",
            "effective_at": timezone.now().isoformat(),
        }
        self.client.force_authenticate(user=self.branch_accountant)
        first = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="deal-profit-payment-1"
        )
        self.assertEqual(first.status_code, 201, first.content)
        replay = self.client.post(
            path, payload, format="json", HTTP_IDEMPOTENCY_KEY="deal-profit-payment-1"
        )
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(replay.data["payment_id"], first.data["payment_id"])
        reused_key = self.client.post(
            path, {**payload, "amount": "401.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="deal-profit-payment-1",
        )
        self.assertEqual(reused_key.status_code, 409, reused_key.content)
        self.assertEqual(
            AccountingEvent.objects.filter(
                event_type="INVESTOR_PROFIT_PAYMENT",
                source_link__investor_vehicle_profit_payment_id=first.data["payment_id"],
            ).count(),
            1,
        )
        movement = AccountMovement.objects.get(event_id=first.data["accounting_event_id"])
        self.assertEqual(movement.delta, Decimal("-400.00"))
        first_payment = InvestorVehicleProfitPayment.objects.get(pk=first.data["payment_id"])
        self.assertEqual(first_payment.vehicle_module_revision.module_code, "vehicle_management")
        self.assertEqual(first_payment.vehicle_module_revision.version, 1)

        second_payload = {**payload, "amount": "300.00"}
        second = self.client.post(
            path, second_payload, format="json", HTTP_IDEMPOTENCY_KEY="deal-profit-payment-2"
        )
        self.assertEqual(second.status_code, 201, second.content)
        over_cap = self.client.post(
            path, {**payload, "amount": "0.01"},
            format="json", HTTP_IDEMPOTENCY_KEY="deal-profit-payment-over-cap",
        )
        self.assertEqual(over_cap.status_code, 409, over_cap.content)
        self.assertEqual(AccountMovement.objects.filter(
            event__event_type="INVESTOR_PROFIT_PAYMENT"
        ).count(), 2)
        self.client.force_authenticate(user=self.company_accountant)
        projection = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-periods/"
        )
        self.assertEqual(projection.status_code, 200, projection.content)
        self.assertEqual(len(projection.data["periods"]), 1)
        self.assertEqual(projection.data["periods"][0]["gross_investor_profit"], "700.00")
        self.assertEqual(projection.data["periods"][0]["deal_profit_paid"], "700.00")
        self.assertEqual(projection.data["periods"][0]["paid_status"], "NOT_RECONCILED")

        west = Branch.objects.create(tenant=self.company, name="West")
        west_accountant = make_user("p8-sale-profit-west-accountant", tenant=self.company)
        west_membership = west_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=west_membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=west,
            assigned_by=self.company_accountant,
        )
        BranchAssignment.objects.create(
            membership=west_membership,
            branch=west,
            assigned_by=self.company_accountant,
        )
        self.client.force_authenticate(user=west_accountant)
        denied_branch = self.client.post(
            path, {**payload, "amount": "1.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="deal-profit-payment-wrong-branch",
        )
        self.assertEqual(denied_branch.status_code, 403, denied_branch.content)
        self.assertEqual(InvestorVehicleProfitPayment.objects.count(), 2)

        self.client.force_authenticate(user=self.branch_accountant)
        self.add_revision("vehicle_management", 2, CompanyModuleState.State.DISABLED)
        blocked_vehicle_module = self.client.post(
            path, {**payload, "amount": "1.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="deal-profit-payment-vehicle-module-off",
        )
        self.assertEqual(blocked_vehicle_module.status_code, 403, blocked_vehicle_module.content)
        self.assertEqual(InvestorVehicleProfitPayment.objects.count(), 2)
        self.add_revision("vehicle_management", 3, CompanyModuleState.State.ENABLED)

        CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="investment",
            state=CompanyModuleState.State.DISABLED,
            version=2,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )
        self.client.force_authenticate(user=self.branch_accountant)
        blocked_offline = self.client.post(
            path, {**payload, "amount": "1.00"}, format="json",
            HTTP_IDEMPOTENCY_KEY="deal-profit-payment-investment-off",
        )
        self.assertEqual(blocked_offline.status_code, 403, blocked_offline.content)
        self.assertEqual(AccountMovement.objects.filter(
            event__event_type="INVESTOR_PROFIT_PAYMENT"
        ).count(), 2)

    def test_confirming_corrected_vehicle_result_reverses_and_replaces_company_share(self):
        vehicle = self.create_vehicle("KL 11 P 5099")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        paid = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RESULT-REVERSAL-COLLECTION"},
            "result-reversal-collection",
            self.branch_accountant,
        )
        self.assertEqual(paid.status_code, 201, paid.content)
        first_position = self.financial_position(vehicle)
        first = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": first_position.data["source_version"], "reason": "First verified result"},
            "vehicle-result-reversal-1",
        )
        self.assertEqual(first.status_code, 201, first.content)
        old_event = AccountingEvent.objects.get(
            event_type=AccountingEvent.EventType.VEHICLE_COMPANY_SHARE,
            effect_sign=1,
        )

        correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "12500.00", "reason": "Corrected sale agreement"},
            "result-reversal-sale-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        extra_receipt = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "500.00", "reference": "RESULT-REVERSAL-EXTRA"},
            "result-reversal-extra-collection",
            self.branch_accountant,
        )
        self.assertEqual(extra_receipt.status_code, 201, extra_receipt.content)
        second_position = self.financial_position(vehicle)
        second = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": second_position.data["source_version"], "reason": "Verified corrected result"},
            "vehicle-result-reversal-2",
        )
        self.assertEqual(second.status_code, 201, second.content)

        old_event.refresh_from_db()
        reversal = old_event.reversal_rows.get()
        new_event = AccountingEvent.objects.get(
            event_type=AccountingEvent.EventType.VEHICLE_COMPANY_SHARE,
            effect_sign=1,
            source_link__vehicle_result_confirmation_id=second.data["id"],
        )
        self.assertEqual(reversal.amount, Decimal("2000.00"))
        self.assertEqual(reversal.effect_sign, -1)
        self.assertEqual(new_event.amount, Decimal("2500.00"))
        self.assertEqual(old_event.amount, Decimal("2000.00"))
        self.assertEqual(AccountMovement.objects.filter(
            event__event_type=AccountingEvent.EventType.VEHICLE_COMPANY_SHARE
        ).count(), 0)
        accounting_result = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/accounting/reports/accounting-result/"
            f"?period=monthly&year={VehicleSale.objects.get(pk=sale.data['id']).sold_at.year}"
            f"&month={VehicleSale.objects.get(pk=sale.data['id']).sold_at.month}"
        )
        self.assertEqual(accounting_result.status_code, 200, accounting_result.content)
        self.assertEqual(accounting_result.data["income_amount"], "2500.00")

    def test_vehicle_result_confirmation_requires_accounting_to_recognize_company_share(self):
        vehicle = self.create_vehicle("KL 11 P 5100")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        self.assertEqual(
            self.post(
                f"sales/{sale.data['id']}/receipts/",
                {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "RESULT-ACCOUNTING-OFF"},
                "result-accounting-off-receipt",
                self.branch_accountant,
            ).status_code,
            201,
        )
        position = self.financial_position(vehicle)
        self.add_revision("accounting", 2, CompanyModuleState.State.DISABLED)

        blocked = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Attempt without Accounting"},
            "result-accounting-off-confirm",
        )

        self.assertEqual(blocked.status_code, 403, blocked.content)
        self.assertEqual(VehicleResultConfirmation.objects.count(), 0)
        self.assertFalse(
            AccountingEvent.objects.filter(
                event_type=AccountingEvent.EventType.VEHICLE_COMPANY_SHARE
            ).exists()
        )

    def test_vehicle_loss_requires_full_collection_and_company_accountant_confirmation(self):
        investor = self.create_investor("result-loss")
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("40.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        vehicle = self.create_vehicle("KL 11 P 5092")
        self.create_purchase(vehicle, investor=investor)
        sale = self.post(
            "sales/",
            {"vehicle_id": str(vehicle.pk), "branch_id": str(self.branch.pk),
             "sale_price": "8000.00", "buyer_name": "Maya", "buyer_phone": "9876543210"},
            "result-loss-sale",
        )
        self.assertEqual(sale.status_code, 201, sale.content)
        preview = self.financial_position(vehicle)
        not_collected = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": preview.data["source_version"], "reason": "Loss confirmed"},
            "result-loss-not-collected",
        )
        self.assertEqual(not_collected.status_code, 409)

        paid = self.post(
            f"sales/{sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "8000.00", "reference": "RESULT-LOSS-FULL"},
            "result-loss-full-collection",
        )
        self.assertEqual(paid.status_code, 201, paid.content)
        preview = self.financial_position(vehicle)
        self.assertEqual(preview.data["suggested_loss_split"], {
            "investor_loss": "800.00", "company_loss": "1200.00",
        })
        self.assertIsNone(preview.data["confirmed_result"])
        result_body = {
            "expected_source_version": preview.data["source_version"],
            "reason": "Reviewed loss and source costs",
        }
        missing_amounts = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", result_body,
            "result-loss-requires-explicit-amounts",
        )
        self.assertEqual(missing_amounts.status_code, 400, missing_amounts.content)
        invalid_split = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {**result_body, "investor_loss_amount": "600.00", "company_loss_amount": "1000.00"},
            "result-loss-invalid-split",
        )
        self.assertEqual(invalid_split.status_code, 400, invalid_split.content)
        result_body.update({"investor_loss_amount": "600.00", "company_loss_amount": "1400.00"})
        denied = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", result_body,
            "result-loss-branch-denied", self.branch_accountant,
        )
        self.assertEqual(denied.status_code, 403)
        movement_count = AccountMovement.objects.count()
        credit_count = InvestorFundCredit.objects.count()
        confirmed = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/", result_body,
            "result-loss-confirmed",
        )
        self.assertEqual(confirmed.status_code, 201, confirmed.content)
        self.assertEqual(confirmed.data["result_kind"], "LOSS")
        self.assertEqual(confirmed.data["result_amount"], "-2000.00")
        self.assertEqual(confirmed.data["investor_share_amount"], "-600.00")
        self.assertEqual(confirmed.data["company_share_amount"], "-1400.00")
        self.assertEqual(confirmed.data["suggested_investor_loss"], "800.00")
        self.assertEqual(confirmed.data["suggested_company_loss"], "1200.00")
        self.assertEqual(AccountMovement.objects.count(), movement_count)
        self.assertEqual(InvestorFundCredit.objects.count(), credit_count)
        additional_credit = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {"investor_id": str(investor.pk), "branch_id": str(self.branch.pk), "account_id": str(self.cash.pk),
             "amount": "6000.00", "reference": "EXIT-PROFIT-CREDIT", "effective_at": timezone.now().isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY="exit-profit-credit",
        )
        self.assertEqual(additional_credit.status_code, 201, additional_credit.content)
        profit_vehicle = self.create_vehicle("KL 11 P 5192")
        self.create_purchase(profit_vehicle, investor=investor)
        profit_sale = self.create_sale(profit_vehicle)
        profit_receipt = self.post(f"sales/{profit_sale.data['id']}/receipts/", {
            "account_id": str(self.bank.pk), "amount": "12000.00", "reference": "EXIT-PROFIT-FULL",
        }, "exit-profit-full-collection")
        self.assertEqual(profit_receipt.status_code, 201, profit_receipt.content)
        from apps.investment.services import create_vehicle_capital_recovery
        profit_capital = self.financial_position(profit_vehicle)
        recovery = create_vehicle_capital_recovery(
            actor=self.company_accountant, company_id=self.company.pk, sale_id=profit_sale.data["id"],
            expected_source_version=profit_capital.data["source_version"], reason="Reconcile capital before Exit",
            key="exit-profit-capital-recovery", path="/internal-test/exit-profit-capital-recovery/",
        )
        profit_preview = self.financial_position(profit_vehicle)
        profit_result = self.post(f"vehicles/{profit_vehicle.pk}/financial-position/confirm/", {
            "expected_source_version": profit_preview.data["source_version"], "reason": "Confirm Exit period Profit",
        }, "exit-profit-result")
        self.assertEqual(profit_result.status_code, 201, profit_result.content)
        period_base = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/"
        period = self.client.get(period_base + "profit-periods/").data["periods"][0]
        snapshot = self.client.post(period_base + "profit-period-reconciliations/", {
            "period_start": period["period_start"], "expected_source_version": period["source_version"],
            "reason": "Confirm the Sale-date period",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-period-snapshot")
        self.assertEqual(snapshot.status_code, 201, snapshot.content)
        position = self.client.post(period_base + "profit-positions/", {
            "reconciliation_id": snapshot.data["id"], "expected_source_version": period["source_version"],
            "reason": "Confirm the Investor period position",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-period-position")
        self.assertEqual(position.status_code, 201, position.content)
        reloaded = self.financial_position(vehicle)
        self.assertEqual(reloaded.data["confirmed_result"]["investor_share_amount"], "-600.00")
        self.assertEqual(reloaded.data["confirmed_result"]["suggested_investor_loss"], "800.00")
        self.add_revision("investor_portal", 1)
        investor_user = make_user("exit-loss-portal-investor", role="investor", tenant=self.company)
        binding = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/portal-binding/",
            {"account_id": str(investor_user.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-portal-binding",
        )
        self.assertEqual(binding.status_code, 201, binding.content)
        self.client.force_authenticate(user=investor_user)
        exit_request = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/portal/self/exit-requests/",
            {"terms_accepted": True}, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-request",
        )
        self.assertEqual(exit_request.status_code, 201, exit_request.content)
        loss_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/exit-requests/{exit_request.data['id']}/loss-applications/"
        settlement_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/exit-requests/{exit_request.data['id']}/settlement/"
        self.client.force_authenticate(user=self.company_accountant)
        settlement = self.client.get(settlement_path)
        self.assertEqual(settlement.status_code, 200, settlement.content)
        self.assertEqual(settlement.data["residual_confirmed_loss"], "600.00")
        self.assertEqual(settlement.data["confirmed_positions"][0]["kind"], "PAYABLE")
        self.assertEqual(settlement.data["confirmed_losses"][0]["loss_result_id"], confirmed.data["id"])
        principal_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/exit-requests/{exit_request.data['id']}/principal-payments/"
        principal_body = {"branch_id": str(self.branch.pk), "account_id": str(self.cash.pk),
            "amount": "9750.00", "reference": "EXIT-PRINCIPAL-BEFORE-LOSS",
            "effective_at": timezone.now().isoformat(), "expected_source_version": settlement.data["source_version"],
            "reason": "Return available principal before Exit Loss settlement"}
        principal = self.client.post(principal_path, principal_body, format="json",
                                     HTTP_IDEMPOTENCY_KEY="exit-loss-principal-return")
        principal_replay = self.client.post(principal_path, principal_body, format="json",
                                            HTTP_IDEMPOTENCY_KEY="exit-loss-principal-return")
        self.assertEqual(principal.status_code, 201, principal.content)
        self.assertEqual(principal_replay.data["id"], principal.data["id"])
        self.assertEqual(AccountMovement.objects.get(event_id=principal.data["accounting_event_id"]).delta,
                         Decimal("-9750.00"))
        settlement = self.client.get(settlement_path)
        available_body = {"loss_result_id": confirmed.data["id"], "branch_id": str(self.branch.pk),
            "source": "AVAILABLE_FUND", "amount": "250.00", "effective_at": timezone.now().isoformat(),
            "expected_source_version": settlement.data["source_version"], "reason": "Apply available Fund to Exit Loss"}
        event_count = AccountingEvent.objects.count()
        available = self.client.post(loss_path, available_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-fund-application")
        available_replay = self.client.post(loss_path, available_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-fund-application")
        self.assertEqual(available.status_code, 201, available.content)
        self.assertEqual(available_replay.data["id"], available.data["id"])
        self.assertEqual(available.data["allocations"][0]["amount"], "250.00")
        self.assertEqual(AccountingEvent.objects.count(), event_count)
        movement_count = AccountMovement.objects.count()
        offset_path = f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/{confirmed.data['id']}/profit-loss-offsets/"
        offset_targets = self.client.get(offset_path)
        self.assertEqual(offset_targets.status_code, 200, offset_targets.content)
        self.assertEqual(offset_targets.data["loss_remaining_amount"], "350.00")
        offset = self.client.post(offset_path, {
            "profit_result_id": profit_result.data["id"], "amount": "100.00",
            "reason": "Offset the remaining confirmed Loss against later Vehicle Profit",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-ordinary-offset")
        offset_replay = self.client.post(offset_path, {
            "profit_result_id": profit_result.data["id"], "amount": "100.00",
            "reason": "Offset the remaining confirmed Loss against later Vehicle Profit",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-ordinary-offset")
        self.assertEqual(offset.status_code, 201, offset.content)
        self.assertEqual(offset_replay.data["offset_id"], offset.data["offset_id"])
        self.assertEqual(offset.data["loss_remaining"], "250.00")
        excess_offset = self.client.post(offset_path, {
            "profit_result_id": profit_result.data["id"], "amount": "250.01",
            "reason": "Try to settle the same Loss twice",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-offset-over-combined-cap")
        self.assertEqual(excess_offset.status_code, 409, excess_offset.content)
        self.assertEqual(AccountingEvent.objects.count(), event_count)
        self.assertEqual(AccountMovement.objects.count(), movement_count)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                direct_offset = InvestorProfitLossOffset.objects.create(
                    tenant=self.company,
                    loss_result=VehicleResultConfirmation.objects.get(pk=confirmed.data["id"]),
                    profit_result=VehicleResultConfirmation.objects.get(pk=profit_result.data["id"]),
                    investor=investor, branch=self.branch, amount=Decimal("250.01"),
                    effective_at=timezone.now(), actor=self.company_accountant,
                    vehicle_module_revision=CompanyModuleState.objects.get(
                        tenant=self.company, module_code="vehicle_management", version=1,
                    ),
                    investment_module_revision=CompanyModuleState.objects.get(
                        tenant=self.company, module_code="investment", version=1,
                    ),
                    reason="Direct SQL combined Loss cap test",
                )
                record_event(
                    action="investment.profit.loss_offset.create", actor=self.company_accountant,
                    subject=self.company_accountant, company=self.company, branch=self.branch,
                    resource=direct_offset, reason=direct_offset.reason,
                    metadata={
                        "offset_id": str(direct_offset.pk), "investor_id": str(investor.pk),
                        "loss_result_id": str(direct_offset.loss_result_id),
                        "profit_result_id": str(direct_offset.profit_result_id),
                        "loss_vehicle_id": str(direct_offset.loss_result.vehicle_id),
                        "profit_vehicle_id": str(direct_offset.profit_result.vehicle_id),
                        "loss_branch_id": str(direct_offset.loss_result.sale.branch_id),
                        "profit_branch_id": str(direct_offset.profit_result.sale.branch_id),
                        "amount": "250.01", "cash_movement_created": False,
                    },
                )
                with connection.cursor() as cursor:
                    cursor.execute("SET CONSTRAINTS investment_profit_loss_offset_bounds IMMEDIATE")
        updated_period = self.client.get(period_base + "profit-periods/").data["periods"][0]
        refreshed_snapshot = self.client.post(period_base + "profit-period-reconciliations/", {
            "period_start": updated_period["period_start"],
            "expected_source_version": updated_period["source_version"],
            "reason": "Refresh after the confirmed Loss offset",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-period-snapshot-after-offset")
        self.assertEqual(refreshed_snapshot.status_code, 201, refreshed_snapshot.content)
        refreshed_position = self.client.post(period_base + "profit-positions/", {
            "reconciliation_id": refreshed_snapshot.data["id"],
            "expected_source_version": updated_period["source_version"],
            "reason": "Confirm the updated Investor position",
        }, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-period-position-after-offset")
        self.assertEqual(refreshed_position.status_code, 201, refreshed_position.content)
        position = refreshed_position
        settlement = self.client.get(settlement_path)
        fund_summary = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/summary/", {"investor_id": str(investor.pk)},
        )
        self.assertEqual(fund_summary.status_code, 200, fund_summary.content)
        self.assertEqual(fund_summary.data["available_amount"], "0.00")
        settlement = self.client.get(settlement_path)
        receipt_body = {**available_body, "source": "DIRECT_RECEIPT", "account_id": str(self.bank.pk),
            "amount": "100.00", "expected_source_version": settlement.data["source_version"],
            "reason": "Receive partial Exit Loss repayment"}
        receipt = self.client.post(loss_path, receipt_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-direct-receipt")
        receipt_replay = self.client.post(loss_path, receipt_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-direct-receipt")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        self.assertEqual(receipt_replay.data["id"], receipt.data["id"])
        receipt_event = AccountingEvent.objects.get(pk=receipt.data["accounting_event_id"])
        self.assertEqual(receipt_event.event_type, AccountingEvent.EventType.INVESTOR_EXIT_LOSS_RECOVERY)
        self.assertEqual(AccountMovement.objects.get(event=receipt_event).delta, Decimal("100.00"))
        self.assertEqual(receipt_event.category_id, None)
        settlement = self.client.get(settlement_path)
        self.assertEqual(settlement.data["residual_confirmed_loss"], "150.00")
        payable_before_exit_payment = Decimal(next(
            item["amount"] for item in settlement.data["confirmed_positions"] if item["id"] == position.data["id"]
        ))
        profit_payment_path = f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/exit-requests/{exit_request.data['id']}/profit-payments/"
        payment_body = {"position_id": position.data["id"], "branch_id": str(self.branch.pk),
            "account_id": str(self.bank.pk), "amount": "200.00", "effective_at": timezone.now().isoformat(),
            "expected_source_version": settlement.data["source_version"], "reason": "Pay partial confirmed Exit Profit"}
        blocked_event_count = AccountingEvent.objects.count()
        blocked_movement_count = AccountMovement.objects.count()
        blocked_profit_payment = self.client.post(
            profit_payment_path, payment_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-profit-blocked-by-loss",
        )
        self.assertEqual(blocked_profit_payment.status_code, 409, blocked_profit_payment.content)
        self.assertEqual(AccountingEvent.objects.count(), blocked_event_count)
        self.assertEqual(AccountMovement.objects.count(), blocked_movement_count)
        remaining_loss_body = {**receipt_body, "amount": "150.00",
            "expected_source_version": settlement.data["source_version"],
            "reason": "Receive remaining Exit Loss repayment"}
        remaining_loss = self.client.post(
            loss_path, remaining_loss_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-direct-receipt-final",
        )
        self.assertEqual(remaining_loss.status_code, 201, remaining_loss.content)
        settlement = self.client.get(settlement_path)
        self.assertEqual(settlement.data["principal_available"], "0.00")
        self.assertEqual(settlement.data["residual_confirmed_loss"], "0.00")
        with connection.cursor() as cursor:
            cursor.execute("SELECT investment_profit_period_source_version(%s)", [refreshed_snapshot.data["id"]])
            self.assertEqual(cursor.fetchone()[0], refreshed_snapshot.data["source_version"])
        payment_body["expected_source_version"] = settlement.data["source_version"]
        profit_payment = self.client.post(profit_payment_path, payment_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-profit-partial-payment")
        profit_payment_replay = self.client.post(profit_payment_path, payment_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-profit-partial-payment")
        self.assertEqual(profit_payment.status_code, 201, profit_payment.content)
        self.assertEqual(profit_payment_replay.data["id"], profit_payment.data["id"])
        profit_event = AccountingEvent.objects.get(pk=profit_payment.data["accounting_event_id"])
        self.assertEqual(profit_event.event_type, AccountingEvent.EventType.INVESTOR_EXIT_PROFIT_PAYMENT)
        self.assertEqual(AccountMovement.objects.get(event=profit_event).delta, Decimal("-200.00"))
        refreshed_settlement = self.client.get(settlement_path)
        self.assertEqual(
            next(item["amount"] for item in refreshed_settlement.data["confirmed_positions"] if item["id"] == position.data["id"]),
            format(payable_before_exit_payment - Decimal("200.00"), ".2f"),
        )
        stale_receipt = self.client.post(loss_path, receipt_body, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-stale-receipt")
        self.assertEqual(stale_receipt.status_code, 409, stale_receipt.content)
        over_loss = {**receipt_body, "amount": "251.00", "expected_source_version": settlement.data["source_version"]}
        over_application = self.client.post(loss_path, over_loss, format="json", HTTP_IDEMPOTENCY_KEY="exit-loss-over-application")
        self.assertEqual(over_application.status_code, 409, over_application.content)
        self.assertEqual(AccountingEvent.objects.filter(event_type=AccountingEvent.EventType.INVESTOR_EXIT_LOSS_RECOVERY).count(), 2)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        existing = VehicleResultConfirmation.objects.get(pk=confirmed.data["id"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            VehicleResultConfirmation.objects.filter(pk=existing.pk).update(investor_share_amount=Decimal("-601.00"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            forged = VehicleResultConfirmation.objects.create(
                tenant=existing.tenant, vehicle=existing.vehicle, purchase=existing.purchase, sale=existing.sale,
                investor=existing.investor, version=2, source_version="f" * 64, result_kind="LOSS",
                purchase_cost=existing.purchase_cost, expense_cost=existing.expense_cost, sale_price=existing.sale_price,
                investor_share_percentage=existing.investor_share_percentage, result_amount=Decimal("-2000.00"),
                investor_share_amount=Decimal("-600.00"), company_share_amount=Decimal("-1400.00"),
                suggested_investor_loss=Decimal("800.00"), suggested_company_loss=Decimal("1200.00"),
                reason="Forged amounts", confirmed_by=self.company_accountant,
                vehicle_module_revision=existing.vehicle_module_revision,
                investment_module_revision=existing.investment_module_revision,
                accounting_module_revision=existing.accounting_module_revision,
            )
            record_event(action="investment.vehicle_result.confirm", actor=self.company_accountant,
                         subject=self.company_accountant, company=self.company, resource=forged,
                         reason=forged.reason, metadata={"result_id": str(forged.pk), "vehicle_id": str(vehicle.pk),
                           "source_version": forged.source_version, "result_kind": "LOSS", "result_amount": "-2000.00",
                           "investor_share_amount": "-800.00", "company_share_amount": "-1200.00",
                           "suggested_investor_loss": "800.00", "suggested_company_loss": "1200.00"})
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS investment_vehicle_result_audit IMMEDIATE")

        # A source correction invalidates the latest position even without a newer reconciliation.
        from apps.investment.models import InvestorExitProfitPayment
        source_correction = self.post(
            f"sales/{profit_sale.data['id']}/corrections/",
            {"sale_price": "11999.00", "reason": "Correct Profit Sale source"},
            "exit-profit-source-correction",
        )
        self.assertEqual(source_correction.status_code, 201, source_correction.content)
        with connection.cursor() as cursor:
            cursor.execute("SELECT investment_profit_period_source_version(%s)", [refreshed_snapshot.data["id"]])
            self.assertNotEqual(cursor.fetchone()[0], refreshed_snapshot.data["source_version"])
        prior = InvestorExitProfitPayment.objects.get(pk=profit_payment.data["id"])
        stale_payment_count = InvestorExitProfitPayment.objects.count()
        stale_event_count = AccountingEvent.objects.count()
        stale_movement_count = AccountMovement.objects.count()
        with self.assertRaisesMessage(IntegrityError, "current same-Company sources"):
            with transaction.atomic():
                direct = InvestorExitProfitPayment.objects.create(
                    tenant=self.company, exit_request=prior.exit_request,
                    position=prior.position, branch=prior.branch, account=prior.account,
                    amount=Decimal("0.01"), effective_at=timezone.now(),
                    reason="Direct payment against stale period", actor=self.company_accountant,
                    investment_revision=prior.investment_revision,
                    accounting_revision=prior.accounting_revision,
                )
                from apps.accounting.services import record_investor_exit_profit_payment
                event, _ = record_investor_exit_profit_payment(
                    tenant=self.company, payment=direct, actor=self.company_accountant,
                    accounting_revision=prior.accounting_revision,
                )
                record_event(
                    action="investment.exit.settlement.profit", actor=self.company_accountant,
                    subject=self.company_accountant, company=self.company, branch=prior.branch,
                    resource=direct, reason=direct.reason,
                    metadata={"investor_id": str(investor.pk),
                              "exit_request_id": str(direct.exit_request_id),
                              "reconciliation_id": str(direct.position.reconciliation_id),
                              "amount": "0.01", "accounting_event_id": str(event.pk),
                              "branch_id": str(prior.branch_id)},
                )
                with connection.cursor() as cursor:
                    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(InvestorExitProfitPayment.objects.count(), stale_payment_count)
        self.assertEqual(AccountingEvent.objects.count(), stale_event_count)
        self.assertEqual(AccountMovement.objects.count(), stale_movement_count)

        calendar_correction = self.client.post(
            period_base + "profit-calendar-configurations/",
            {"effective_start": period["period_start"], "duration_months": 12},
            format="json", HTTP_IDEMPOTENCY_KEY="exit-profit-calendar-correction",
        )
        self.assertEqual(calendar_correction.status_code, 201, calendar_correction.content)
        stale_period = self.client.get(period_base + "profit-periods/")
        self.assertEqual(stale_period.status_code, 200, stale_period.content)
        self.assertFalse(any(
            (row.get("confirmed_position") or {}).get("is_current")
            for row in stale_period.data["periods"]
            if (row.get("confirmed_position") or {}).get("id") == position.data["id"]
        ))

    def test_financial_position_restates_sale_correction_and_rejects_other_company(self):
        vehicle = self.create_vehicle("KL 11 P 5082")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        before = self.financial_position(vehicle)
        self.assertEqual(before.data["calculated_result"], "2000.00")

        collected = self.receipt(sale.data["id"], key="position-full-collection", amount="12000.00")
        self.assertEqual(collected.status_code, 201, collected.content)
        event_count = AccountingEvent.objects.count()

        correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "9000.00", "reason": "Correct signed price"},
            "position-sale-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        after = self.financial_position(vehicle)
        self.assertEqual(after.data["calculated_result"], "-1000.00")
        self.assertEqual(after.data["status"], "REFUND_PENDING")
        self.assertEqual(after.data["buyer_refund_payable"], "3000.00")
        self.assertEqual(after.data["sale_correction_version"], 1)

        refunded = self.post(
            f"sales/{sale.data['id']}/refunds/",
            {"account_id": str(self.cash.pk), "amount": "3000.00"},
            "position-buyer-refund",
        )
        self.assertEqual(refunded.status_code, 201, refunded.content)
        resolved = self.financial_position(vehicle)
        self.assertEqual(resolved.data["status"], "LOSS_REVIEW_REQUIRED")
        self.assertEqual(resolved.data["actual_net_collection"], "9000.00")
        self.assertEqual(AccountingEvent.objects.count(), event_count + 1)

        other_company = Tenant.objects.create(name="Other position Co", slug="other-position-co")
        other_user = make_user("other-position-accountant", role="accountant", tenant=other_company)
        denied = self.financial_position(vehicle, user=other_user, company=other_company)
        self.assertEqual(denied.status_code, 404)

    def test_financial_position_requires_access_to_original_source_branch_after_move(self):
        vehicle = self.create_vehicle("KL 11 P 5083")
        self.create_purchase(vehicle)
        west = Branch.objects.create(tenant=self.company, name="West")
        west_accountant = make_user("position-west-accountant", tenant=self.company)
        membership = west_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership, role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=west, assigned_by=self.company_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership, branch=west, assigned_by=self.company_accountant,
        )
        moved = self.post(
            f"vehicles/{vehicle.pk}/branch-movements/",
            {"to_branch_id": str(west.pk), "reason": "Moved to West"},
            "position-move-west",
        )
        self.assertEqual(moved.status_code, 201, moved.content)
        denied = self.financial_position(vehicle, user=west_accountant)
        self.assertIn(denied.status_code, (403, 404), denied.content)
        allowed = self.financial_position(vehicle)
        self.assertEqual(allowed.status_code, 200, allowed.content)

    def test_company_funded_sale_receipt_refund_and_correction_need_no_investment_module(self):
        vehicle = self.create_vehicle()
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)
        self.assertFalse(sale.data["investor_funded"])
        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)

        receipt = self.receipt(sale.data["id"])
        self.assertEqual(receipt.status_code, 201, receipt.content)
        event = AccountingEvent.objects.get(pk=receipt.data["accounting_event_id"])
        self.assertEqual(event.event_type, "VEHICLE_SALE_RECEIPT")
        self.assertEqual(AccountMovement.objects.filter(event=event).count(), 1)
        self.assertEqual(AccountMovement.objects.get(event=event).delta, Decimal("2000.00"))
        link = AccountingSourceLink.objects.get(event=event)
        self.assertEqual(str(link.vehicle_sale_receipt_id), receipt.data["receipt_id"])
        self.assertIsNone(VehicleSaleReceipt.objects.get(pk=receipt.data["receipt_id"]).investment_module_revision_id)

        premature_refund = self.post(
            f"sales/{sale.data['id']}/refunds/",
            {"account_id": str(self.cash.pk), "amount": "500.00"},
            "sale-refund-before-correction",
            self.branch_accountant,
        )
        self.assertEqual(premature_refund.status_code, 409, premature_refund.content)
        self.assertFalse(VehicleSaleRefund.objects.exists())
        self.assertEqual(AccountingEvent.objects.count(), 1)

        correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "1500.00", "reason": "Corrected signed sale amount"},
            "sale-correction-downward",
            self.branch_accountant,
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        self.assertEqual(correction.data["sale_price"], "1500.00")
        self.assertEqual(correction.data["receivable"], "0.00")
        self.assertEqual(correction.data["refund_payable"], "500.00")
        self.assertEqual(correction.data["refund_available"], "500.00")

        excessive_refund = self.post(
            f"sales/{sale.data['id']}/refunds/",
            {"account_id": str(self.cash.pk), "amount": "500.01"},
            "sale-refund-over-payable",
            self.branch_accountant,
        )
        self.assertEqual(excessive_refund.status_code, 409, excessive_refund.content)
        self.assertFalse(VehicleSaleRefund.objects.exists())

        refund = self.post(
            f"sales/{sale.data['id']}/refunds/",
            {"account_id": str(self.cash.pk), "amount": "500.00"},
            "sale-refund-payable",
            self.branch_accountant,
        )
        self.assertEqual(refund.status_code, 201, refund.content)
        self.assertEqual(refund.data["refund_payable"], "0.00")
        self.assertEqual(refund.data["refund_available"], "0.00")
        self.assertEqual(AccountMovement.objects.filter(event_id=refund.data["accounting_event_id"]).count(), 1)

        higher_correction = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "11500.00", "reason": "Corrected signed sale amount"},
            "sale-correction-upward",
            self.branch_accountant,
        )
        self.assertEqual(higher_correction.status_code, 201, higher_correction.content)
        self.assertEqual(higher_correction.data["sale_price"], "11500.00")

    def test_sale_receipt_and_refund_replay_without_optional_dates(self):
        vehicle = self.create_vehicle("KL 11 P 5052")
        self.create_purchase(vehicle)
        sale_body = {
            "vehicle_id": str(vehicle.pk),
            "branch_id": str(self.branch.pk),
            "sale_price": "12000.00",
            "buyer_name": "Maya",
            "buyer_phone": "9876543210",
        }
        first_sale = self.post("sales/", sale_body, "sale-no-date-replay")
        repeated_sale = self.post("sales/", sale_body, "sale-no-date-replay")
        self.assertEqual(first_sale.status_code, 201, first_sale.content)
        self.assertEqual(repeated_sale.status_code, 201, repeated_sale.content)
        self.assertEqual(first_sale.data["id"], repeated_sale.data["id"])
        self.assertEqual(first_sale.data["sold_at"], repeated_sale.data["sold_at"])

        receipt_body = {
            "account_id": str(self.bank.pk),
            "amount": "12000.00",
            "reference": "BANK-SALE-NO-DATE",
        }
        receipt_path = f"sales/{first_sale.data['id']}/receipts/"
        first_receipt = self.post(receipt_path, receipt_body, "sale-receipt-no-date")
        repeated_receipt = self.post(receipt_path, receipt_body, "sale-receipt-no-date")
        self.assertEqual(first_receipt.status_code, 201, first_receipt.content)
        self.assertEqual(repeated_receipt.status_code, 201, repeated_receipt.content)
        self.assertEqual(first_receipt.data["receipt_id"], repeated_receipt.data["receipt_id"])

        correction = self.post(
            f"sales/{first_sale.data['id']}/corrections/",
            {"sale_price": "9000.00", "reason": "Corrected agreed price"},
            "sale-price-for-refund-no-date",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        refund_body = {"account_id": str(self.cash.pk), "amount": "3000.00"}
        refund_path = f"sales/{first_sale.data['id']}/refunds/"
        first_refund = self.post(refund_path, refund_body, "sale-refund-no-date")
        repeated_refund = self.post(refund_path, refund_body, "sale-refund-no-date")
        self.assertEqual(first_refund.status_code, 201, first_refund.content)
        self.assertEqual(repeated_refund.status_code, 201, repeated_refund.content)
        self.assertEqual(first_refund.data["refund_id"], repeated_refund.data["refund_id"])
        self.assertEqual(AccountMovement.objects.count(), 2)

    def test_purchase_funded_sale_receipt_requires_investment_and_database_guard(self):
        investor = self.create_investor()
        vehicle = self.create_vehicle()
        self.create_purchase(vehicle, investor)
        sale = self.create_sale(vehicle)
        self.assertTrue(sale.data["investor_funded"])

        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)
        denied = self.receipt(sale.data["id"])
        self.assertEqual(denied.status_code, 403, denied.content)
        self.assertFalse(VehicleSaleReceipt.objects.exists())

        self.add_revision("investment", 3)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VehicleSaleReceipt.objects.create(
                    tenant=self.company,
                    sale_id=sale.data["id"],
                    branch=self.branch,
                    amount=Decimal("100.00"),
                    account=self.bank,
                    reference="DIRECT-INVALID-RECEIPT",
                    effective_at=timezone.now(),
                    actor=self.company_accountant,
                    vehicle_module_revision=CompanyModuleState.objects.get(
                        tenant=self.company, module_code="vehicle_management", version=1
                    ),
                    accounting_module_revision=CompanyModuleState.objects.get(
                        tenant=self.company, module_code="accounting", version=1
                    ),
                    investment_module_revision=None,
                )

    def test_expense_funded_vehicle_receipt_requires_investment_module(self):
        investor = self.create_investor("expense")
        vehicle = self.create_vehicle("KL 11 P 5051")
        self.create_purchase(vehicle, investor, funded_by_expense=True)
        sale = self.create_sale(vehicle)
        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)

        denied = self.receipt(sale.data["id"], key="expense-funded-sale-receipt")
        self.assertEqual(denied.status_code, 403, denied.content)
        self.assertFalse(VehicleSaleReceipt.objects.exists())

    def test_expense_only_investor_cannot_be_treated_as_company_only_result(self):
        investor = self.create_investor("expense-result")
        vehicle = self.create_vehicle("KL 11 P 5198")
        self.create_purchase(vehicle, investor, funded_by_expense=True)
        sale = self.create_sale(vehicle)
        receipt = self.receipt(sale.data["id"], key="expense-result-receipt", amount="12000.00")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        position = self.financial_position(vehicle)
        self.assertEqual(position.status_code, 200, position.content)
        self.assertEqual(position.data["profit_share_status"], "AGREEMENT_SNAPSHOT_MISSING")
        event_count = AccountingEvent.objects.count()
        confirmation = self.post(
            f"vehicles/{vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": position.data["source_version"], "reason": "Review result"},
            "expense-only-investor-result",
        )
        self.assertEqual(confirmation.status_code, 409, confirmation.content)
        self.assertEqual(confirmation.json()["code"], "INVESTOR_AGREEMENT_SNAPSHOT_MISSING")
        self.assertFalse(VehicleResultConfirmation.objects.filter(vehicle=vehicle).exists())
        self.assertEqual(AccountingEvent.objects.count(), event_count)

    def test_sale_detail_returns_audited_correction_history_after_reload(self):
        vehicle = self.create_vehicle("KL 11 P 5053")
        self.create_purchase(vehicle)
        sale = self.create_sale(vehicle)

        first = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "11000.00", "reason": "Signed sale price corrected"},
            "sale-history-correction-1",
        )
        self.assertEqual(first.status_code, 201, first.content)
        second = self.post(
            f"sales/{sale.data['id']}/corrections/",
            {"sale_price": "10000.00", "reason": "Buyer agreement updated"},
            "sale-history-correction-2",
        )
        self.assertEqual(second.status_code, 201, second.content)

        detail = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/sales/{sale.data['id']}/"
        )

        self.assertEqual(detail.status_code, 200, detail.content)
        history = detail.data["corrections"]
        self.assertEqual(
            [
                {
                    "version": row["version"],
                    "previous_sale_price": row["previous_sale_price"],
                    "sale_price": row["sale_price"],
                    "reason": row["reason"],
                    "effective_at": row["effective_at"],
                }
                for row in history
            ],
            [
                {
                    "version": 1,
                    "previous_sale_price": "12000.00",
                    "sale_price": "11000.00",
                    "reason": "Signed sale price corrected",
                    "effective_at": sale.data["sold_at"],
                },
                {
                    "version": 2,
                    "previous_sale_price": "11000.00",
                    "sale_price": "10000.00",
                    "reason": "Buyer agreement updated",
                    "effective_at": sale.data["sold_at"],
                },
            ],
        )
        self.assertTrue(all(row["recorded_at"] for row in history))
        self.assertEqual(detail.data["sale_price"], "10000.00")

    def test_phase6_stock_job_cost_and_phase7_sale_keep_one_vehicle_source(self):
        vehicle = self.create_vehicle("KL 11 P 5054")
        self.create_purchase(vehicle)
        self.add_revision("garage", 1)
        self.client.force_authenticate(user=self.branch_accountant)
        job = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/garage/jobs/",
            {
                "branch_id": str(self.branch.pk),
                "vehicle_id": str(vehicle.pk),
                "context": "STOCK",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="phase7-stock-job",
        )
        self.assertEqual(job.status_code, 201, job.content)

        expense = self.post(
            f"vehicles/{vehicle.pk}/expenses/",
            {"amount": "1500.00", "description": "Garage service cost"},
            "phase7-stock-expense",
            self.branch_accountant,
        )
        self.assertEqual(expense.status_code, 201, expense.content)
        stock_cost_path = f"/api/v1/tenants/{self.company.pk}/garage/jobs/{job.data['id']}/stock-costs/"
        linked_cost = self.client.post(
            stock_cost_path,
            {"expense_id": expense.data["id"]},
            format="json",
            HTTP_IDEMPOTENCY_KEY="phase7-link-stock-cost",
        )
        self.assertEqual(linked_cost.status_code, 201, linked_cost.content)
        self.client.force_authenticate(user=self.branch_accountant)

        sale = self.create_sale(vehicle)
        self.client.force_authenticate(user=self.branch_accountant)
        sale_detail = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/sales/{sale.data['id']}/"
        )
        expenses = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/{vehicle.pk}/expenses/"
        )
        stock_costs = self.client.get(stock_cost_path)

        self.assertEqual(sale_detail.status_code, 200, sale_detail.content)
        self.assertEqual(sale_detail.data["vehicle_id"], str(vehicle.pk))
        self.assertEqual(expenses.data["count"], 1)
        self.assertEqual(expenses.data["results"][0]["id"], expense.data["id"])
        self.assertEqual(stock_costs.data["count"], 1)
        self.assertEqual(stock_costs.data["results"][0]["expense_id"], expense.data["id"])
        self.assertEqual(AccountingEvent.objects.count(), 0)

    def test_confirmed_investor_loss_offsets_future_profit_once_without_cash_movement(self):
        self._assert_loss_offsets_unpaid_profit(loss_days_ago=1, profit_days_ago=0)

    def test_confirmed_investor_loss_offsets_earlier_unpaid_profit(self):
        self._assert_loss_offsets_unpaid_profit(loss_days_ago=0, profit_days_ago=1)

    def test_confirmed_investor_loss_offsets_same_day_unpaid_profit(self):
        self._assert_loss_offsets_unpaid_profit(loss_days_ago=0, profit_days_ago=0)

    def _assert_loss_offsets_unpaid_profit(self, *, loss_days_ago, profit_days_ago):
        investor = self.create_investor(
            "loss-offset", credit_effective_at=timezone.now() - timedelta(days=2),
        )
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("40.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        extra_credit = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": str(investor.pk), "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk), "amount": "2000.00",
                "reference": "LOSS-OFFSET-TOPUP",
                "effective_at": (timezone.now() - timedelta(minutes=1)).isoformat(),
            },
            format="json", HTTP_IDEMPOTENCY_KEY="loss-offset-topup",
        )
        self.assertEqual(extra_credit.status_code, 201, extra_credit.content)

        loss_vehicle = self.create_vehicle("KL 11 P 5160")
        self.create_purchase(loss_vehicle, investor=investor)
        loss_sale = self.post(
            "sales/",
            {"vehicle_id": str(loss_vehicle.pk), "branch_id": str(self.branch.pk),
             "sale_price": "8000.00", "buyer_name": "Maya", "buyer_phone": "9876543210",
             "sold_at": (timezone.now() - timedelta(days=loss_days_ago)).isoformat()},
            "loss-offset-loss-sale",
        )
        self.assertEqual(loss_sale.status_code, 201, loss_sale.content)
        loss_receipt = self.post(
            f"sales/{loss_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "8000.00", "reference": "LOSS-OFFSET-LOSS"},
            "loss-offset-loss-receipt", self.branch_accountant,
        )
        self.assertEqual(loss_receipt.status_code, 201, loss_receipt.content)
        loss_position = self.financial_position(loss_vehicle)
        loss_result = self.post(
            f"vehicles/{loss_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": loss_position.data["source_version"], "reason": "Confirmed Vehicle loss", "investor_loss_amount": "800.00", "company_loss_amount": "1200.00"},
            "loss-offset-loss-confirmation",
        )
        self.assertEqual(loss_result.status_code, 201, loss_result.content)
        self.assertEqual(loss_result.data["investor_share_amount"], "-800.00")

        profit_vehicle = self.create_vehicle("KL 11 P 5161")
        self.create_purchase(profit_vehicle, investor=investor)
        profit_sale = self.post(
            "sales/",
            {"vehicle_id": str(profit_vehicle.pk), "branch_id": str(self.branch.pk),
             "sale_price": "12000.00", "buyer_name": "Maya", "buyer_phone": "9876543210",
             "sold_at": (timezone.now() - timedelta(days=profit_days_ago)).isoformat()},
            "loss-offset-profit-sale",
        )
        self.assertEqual(profit_sale.status_code, 201, profit_sale.content)
        profit_receipt = self.post(
            f"sales/{profit_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "LOSS-OFFSET-PROFIT"},
            "loss-offset-profit-receipt", self.branch_accountant,
        )
        self.assertEqual(profit_receipt.status_code, 201, profit_receipt.content)
        profit_position = self.financial_position(profit_vehicle)
        profit_result = self.post(
            f"vehicles/{profit_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": profit_position.data["source_version"], "reason": "Confirmed Vehicle profit"},
            "loss-offset-profit-confirmation",
        )
        self.assertEqual(profit_result.status_code, 201, profit_result.content)
        self.assertEqual(profit_result.data["investor_share_amount"], "800.00")

        events_before_offset = AccountingEvent.objects.count()
        movements_before_offset = AccountMovement.objects.count()
        offset_path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{loss_result.data['id']}/profit-loss-offsets/"
        )
        targets = self.client.get(offset_path)
        self.assertEqual(targets.status_code, 200, targets.content)
        self.assertEqual(targets.data["loss_remaining_amount"], "800.00")
        self.assertEqual(
            [row["result_id"] for row in targets.data["target_options"]],
            [profit_result.data["id"]],
        )
        self.assertEqual(targets.data["target_options"][0]["remaining_amount"], "800.00")
        payload = {
            "profit_result_id": profit_result.data["id"],
            "amount": "500.00",
            "reason": "Apply confirmed loss against later Vehicle profit",
        }
        self.client.force_authenticate(user=self.branch_accountant)
        offset = self.client.post(
            offset_path, payload, format="json", HTTP_IDEMPOTENCY_KEY="loss-offset-1",
        )
        self.assertEqual(offset.status_code, 201, offset.content)
        self.assertEqual(offset.data["loss_remaining"], "300.00")
        self.assertEqual(offset.data["profit_remaining"], "300.00")
        self.assertEqual(AccountingEvent.objects.count(), events_before_offset)
        self.assertEqual(AccountMovement.objects.count(), movements_before_offset)

        excessive_offset = self.client.post(
            offset_path,
            {**payload, "amount": "300.01"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="loss-offset-over-cap",
        )
        self.assertEqual(excessive_offset.status_code, 409, excessive_offset.content)
        self.assertEqual(AccountingEvent.objects.count(), events_before_offset)
        self.assertEqual(AccountMovement.objects.count(), movements_before_offset)

        self.client.force_authenticate(user=self.company_accountant)
        projection = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-periods/"
        )
        self.assertEqual(projection.status_code, 200, projection.content)
        self.assertEqual(projection.data["periods"][0]["gross_investor_profit"], "800.00")
        self.assertEqual(projection.data["periods"][0]["investor_loss_share"], "800.00")
        self.assertEqual(projection.data["periods"][0]["loss_offset_applied"], "500.00")
        self.assertEqual(projection.data["periods"][0]["paid_status"], "NOT_RECONCILED")

        payment_path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{profit_result.data['id']}/profit-payments/"
        )
        payment = self.client.post(
            payment_path,
            {"account_id": str(self.bank.pk), "amount": "300.01",
             "effective_at": timezone.now().isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY="loss-offset-payment-over-cap",
        )
        self.assertEqual(payment.status_code, 409, payment.content)
        self.assertEqual(payment.json()["code"], "INVESTOR_PROFIT_PAYMENT_EXCEEDS_BALANCE")

        correction = self.post(
            f"sales/{loss_sale.data['id']}/corrections/",
            {"sale_price": "8500.00", "reason": "Correct loss source"},
            "loss-offset-loss-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        refreshed = self.client.get(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/{investor.pk}/profit-periods/"
        )
        self.assertEqual(refreshed.status_code, 200, refreshed.content)
        self.assertEqual(refreshed.data["status"], "REVIEW_REQUIRED")
        self.assertEqual(refreshed.data["periods"][0]["loss_offset_applied"], "0.00")

    def test_cross_branch_loss_offset_requires_company_accountant(self):
        investor = self.create_investor(
            "loss-offset-cross-branch",
            credit_effective_at=timezone.now() - timedelta(days=2),
        )
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company, investor=investor, share_percentage=Decimal("40.0000"),
            effective_at=timezone.now() - timedelta(minutes=5), actor=self.company_accountant,
        )
        self.client.force_authenticate(user=self.company_accountant)
        topup = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": str(investor.pk), "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk), "amount": "2000.00",
                "reference": "LOSS-OFFSET-CROSS-TOPUP",
                "effective_at": (timezone.now() - timedelta(minutes=1)).isoformat(),
            },
            format="json", HTTP_IDEMPOTENCY_KEY="loss-offset-cross-topup",
        )
        self.assertEqual(topup.status_code, 201, topup.content)

        west = Branch.objects.create(tenant=self.company, name="West")
        loss_vehicle = self.create_vehicle("KL 11 P 5170")
        self.create_purchase(loss_vehicle, investor=investor)
        loss_sale = self.post(
            "sales/",
            {
                "vehicle_id": str(loss_vehicle.pk), "branch_id": str(self.branch.pk),
                "sale_price": "8000.00", "buyer_name": "Maya",
                "buyer_phone": "9876543210",
                "sold_at": (timezone.now() - timedelta(days=1)).isoformat(),
            },
            "loss-offset-cross-loss-sale",
        )
        self.assertEqual(loss_sale.status_code, 201, loss_sale.content)
        loss_receipt = self.post(
            f"sales/{loss_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "8000.00", "reference": "LOSS-OFFSET-CROSS-LOSS"},
            "loss-offset-cross-loss-receipt", self.branch_accountant,
        )
        self.assertEqual(loss_receipt.status_code, 201, loss_receipt.content)
        loss_position = self.financial_position(loss_vehicle)
        loss_result = self.post(
            f"vehicles/{loss_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": loss_position.data["source_version"], "reason": "Confirmed Vehicle loss", "investor_loss_amount": "800.00", "company_loss_amount": "1200.00"},
            "loss-offset-cross-loss-confirmation",
        )
        self.assertEqual(loss_result.status_code, 201, loss_result.content)

        profit_vehicle = self.create_vehicle("KL 11 P 5171")
        self.create_purchase(profit_vehicle, investor=investor)
        moved = self.post(
            f"vehicles/{profit_vehicle.pk}/branch-movements/",
            {"to_branch_id": str(west.pk), "reason": "Moved for cross-Branch Sale"},
            "loss-offset-cross-profit-move",
        )
        self.assertEqual(moved.status_code, 201, moved.content)
        profit_sale = self.post(
            "sales/",
            {
                "vehicle_id": str(profit_vehicle.pk), "branch_id": str(west.pk),
                "sale_price": "12000.00", "buyer_name": "Maya",
                "buyer_phone": "9876543210",
            },
            "loss-offset-cross-profit-sale",
        )
        self.assertEqual(profit_sale.status_code, 201, profit_sale.content)
        profit_receipt = self.post(
            f"sales/{profit_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": "LOSS-OFFSET-CROSS-PROFIT"},
            "loss-offset-cross-profit-receipt", self.company_accountant,
        )
        self.assertEqual(profit_receipt.status_code, 201, profit_receipt.content)
        profit_position = self.financial_position(profit_vehicle)
        profit_result = self.post(
            f"vehicles/{profit_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": profit_position.data["source_version"], "reason": "Confirmed Vehicle profit"},
            "loss-offset-cross-profit-confirmation",
        )
        self.assertEqual(profit_result.status_code, 201, profit_result.content)

        target_path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{loss_result.data['id']}/profit-loss-offsets/"
        )
        self.client.force_authenticate(user=self.branch_accountant)
        branch_targets = self.client.get(target_path)
        self.assertEqual(branch_targets.status_code, 200, branch_targets.content)
        self.assertEqual(branch_targets.data["target_options"], [])
        self.client.force_authenticate(user=self.company_accountant)
        company_targets = self.client.get(target_path)
        self.assertEqual(company_targets.status_code, 200, company_targets.content)
        self.assertEqual(
            [row["result_id"] for row in company_targets.data["target_options"]],
            [profit_result.data["id"]],
        )

        path = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{loss_result.data['id']}/profit-loss-offsets/"
        )
        payload = {
            "profit_result_id": profit_result.data["id"],
            "amount": "100.00",
            "reason": "Cross-Branch loss offset approval",
        }
        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(
            path, payload, format="json",
            HTTP_IDEMPOTENCY_KEY="loss-offset-cross-branch-denied",
        )
        self.assertEqual(denied.status_code, 403, denied.content)

        events_before = AccountingEvent.objects.count()
        movements_before = AccountMovement.objects.count()
        self.client.force_authenticate(user=self.company_accountant)
        approved = self.client.post(
            path, payload, format="json",
            HTTP_IDEMPOTENCY_KEY="loss-offset-cross-branch-approved",
        )
        self.assertEqual(approved.status_code, 201, approved.content)
        self.assertEqual(approved.data["branch_id"], str(west.pk))
        self.assertEqual(AccountingEvent.objects.count(), events_before)
        self.assertEqual(AccountMovement.objects.count(), movements_before)

    def test_financial_source_fingerprint_is_deterministic_across_expense_orders(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from apps.investment.services import create_vehicle_capital_recovery
        from apps.vehicles.models import VehicleExpense
        from apps.vehicles.services import _build_vehicle_financial_source_payload

        def create_recovered_multi_expense_vehicle(reg, suffix):
            vehicle = self.create_vehicle(reg)
            purchase_data = self.create_purchase(vehicle)
            exp_a = self.post(
                f"vehicles/{vehicle.pk}/expenses/",
                {"amount": "300.00", "description": f"Tyres {suffix}", "running_capital_amount": "300.00"},
                f"fp-exp-a-{suffix}",
            )
            exp_b = self.post(
                f"vehicles/{vehicle.pk}/expenses/",
                {"amount": "700.00", "description": f"Paint {suffix}", "running_capital_amount": "700.00"},
                f"fp-exp-b-{suffix}",
            )
            self.assertEqual(exp_a.status_code, 201, exp_a.content)
            self.assertEqual(exp_b.status_code, 201, exp_b.content)
            sale = self.create_sale(vehicle)
            rcpt = self.post(
                f"sales/{sale.data['id']}/receipts/",
                {"account_id": str(self.bank.pk), "amount": "12000.00", "reference": f"FP-RCPT-{suffix}"},
                f"fp-rcpt-{suffix}",
                self.branch_accountant,
            )
            self.assertEqual(rcpt.status_code, 201, rcpt.content)
            pos = self.financial_position(vehicle)
            rec = create_vehicle_capital_recovery(
                actor=self.company_accountant,
                company_id=self.company.pk,
                sale_id=sale.data["id"],
                expected_source_version=pos.data["source_version"],
                reason=f"Recover {reg}",
                key=f"fp-rec-{suffix}",
                path="/internal-test/capital-recovery/",
            )
            self.assertEqual(rec.status, 201)
            return vehicle, purchase_data["id"], [exp_a.data["id"], exp_b.data["id"]]

        veh1, _, exp_ids_1 = create_recovered_multi_expense_vehicle("KL 11 F 0001", "1")
        e1, e2 = list(VehicleExpense.objects.filter(pk__in=exp_ids_1).prefetch_related("corrections"))
        p1, _, _, _ = _build_vehicle_financial_source_payload(
            company=self.company, vehicle=veh1, purchase=veh1.purchase, expenses=[e1, e2], sale=veh1.confirmed_sale,
        )
        p2, _, _, _ = _build_vehicle_financial_source_payload(
            company=self.company, vehicle=veh1, purchase=veh1.purchase, expenses=[e2, e1], sale=veh1.confirmed_sale,
        )
        self.assertEqual(p1["source_version"], p2["source_version"])
        self.assertEqual(p1["expense_correction_versions"], p2["expense_correction_versions"])
        self.assertEqual(p1["source_version"], self.financial_position(veh1).data["source_version"])

        summary_url = f"/api/v1/tenants/{self.company.pk}/vehicle-management/operational-summary/"
        with CaptureQueriesContext(connection) as ctx1:
            s1 = self.client.get(summary_url)
        self.assertEqual(s1.status_code, 200, s1.content)
        self.assertEqual(s1.data["running_capital_contributed"], "11000.00")
        self.assertEqual(s1.data["running_capital_recovered"], "11000.00")

        create_recovered_multi_expense_vehicle("KL 11 F 0002", "2")
        create_recovered_multi_expense_vehicle("KL 11 F 0003", "3")
        with CaptureQueriesContext(connection) as ctx3:
            s3 = self.client.get(summary_url)
        self.assertEqual(s3.status_code, 200, s3.content)
        self.assertEqual(s3.data["running_capital_contributed"], "33000.00")
        self.assertEqual(s3.data["running_capital_recovered"], "33000.00")
        self.assertEqual(s3.data["running_capital_outstanding"], "0.00")
        self.assertEqual(len(ctx3), len(ctx1))

    def test_vehicle_monetary_arithmetic_preserves_precision_at_38_digit_boundary(self):
        from types import SimpleNamespace
        from apps.vehicles.services import _build_vehicle_financial_source_payload, _money

        # Ordinary calculations stay unchanged
        self.assertEqual(_money("1234.565"), Decimal("1234.57"))
        self.assertEqual(_money("1000.00"), Decimal("1000.00"))

        # Boundary 38-digit value (36 integer digits + 2 decimals) must not raise InvalidOperation
        max_38 = Decimal("999999999999999999999999999999999999.99")
        self.assertEqual(_money(max_38), max_38)
        self.assertEqual(_money("999999999999999999999999999999999999.985"), max_38)

        # Adding 0.01 to a 30-digit purchase must not drop the paise under default 28-digit context
        big_cost = Decimal("1000000000000000000000000000.00")
        big_sale = Decimal("1000000000000000000000000005.00")
        vehicle = SimpleNamespace(pk="veh-1", current_branch_id="branch-1")
        purchase = SimpleNamespace(
            pk="pur-1",
            investor_id=None,
            investor_share_agreement_id=None,
            investor_share_percentage_snapshot=None,
            purchase_cost=big_cost,
            investor_fund_amount=Decimal("0.00"),
            running_capital_amount=big_cost,
            corrections=SimpleNamespace(all=lambda: []),
        )
        expense = SimpleNamespace(
            pk="exp-1",
            amount=Decimal("0.01"),
            investor_fund_amount=Decimal("0.00"),
            running_capital_amount=Decimal("0.01"),
            corrections=SimpleNamespace(all=lambda: []),
        )
        sale = SimpleNamespace(pk="sale-1", sold_at=timezone.now())
        sale_data = {
            "sale_price": format(big_sale, ".2f"),
            "net_received": format(big_sale, ".2f"),
            "receivable": "0.00",
            "refund_payable": "0.00",
            "correction_version": 0,
        }
        payload, _, running_capital_cost, result = _build_vehicle_financial_source_payload(
            company=self.company,
            vehicle=vehicle,
            purchase=purchase,
            expenses=[expense],
            sale=sale,
            sale_data=sale_data,
        )
        self.assertEqual(running_capital_cost, Decimal("1000000000000000000000000000.01"))
        self.assertEqual(payload["total_vehicle_cost"], "1000000000000000000000000000.01")
        self.assertEqual(result, Decimal("4.99"))
        self.assertEqual(payload["calculated_result"], "4.99")

    def test_profit_reconfirmation_reconciles_historical_loss_offset_and_blocks_overpayment(self):
        from django.db import IntegrityError, transaction
        from apps.investment.models import InvestorVehicleProfitPayment, VehicleResultConfirmation
        from apps.investment.services import create_vehicle_capital_recovery

        investor = self.create_investor(
            "reconfirm-offset-reconcile",
            credit_effective_at=timezone.now() - timedelta(days=3),
        )
        InvestorProfitShareAgreement.objects.create(
            tenant=self.company,
            investor=investor,
            share_percentage=Decimal("50.0000"),
            effective_at=timezone.now() - timedelta(minutes=10),
            actor=self.company_accountant,
        )
        self.client.force_authenticate(user=self.company_accountant)
        topup = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": str(investor.pk),
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": "10000.00",
                "reference": "RECONF-OFFSET-TOPUP",
                "effective_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="reconf-offset-topup",
        )
        self.assertEqual(topup.status_code, 201, topup.content)

        # 1. Vehicle A: Loss with confirmed Investor Loss Rs 5,000.00
        loss_vehicle = self.create_vehicle("KL 11 R 0001")
        self.create_purchase(loss_vehicle, investor=investor)
        loss_sale = self.post(
            "sales/",
            {
                "vehicle_id": str(loss_vehicle.pk),
                "branch_id": str(self.branch.pk),
                "sale_price": "2000.00",
                "buyer_name": "Loss Buyer",
                "buyer_phone": "9876543210",
                "sold_at": (timezone.now() - timedelta(days=2)).isoformat(),
            },
            "reconf-loss-sale",
        )
        self.assertEqual(loss_sale.status_code, 201, loss_sale.content)
        loss_rcpt = self.post(
            f"sales/{loss_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "2000.00", "reference": "RECONF-LOSS-RCPT"},
            "reconf-loss-rcpt",
            self.branch_accountant,
        )
        self.assertEqual(loss_rcpt.status_code, 201, loss_rcpt.content)
        loss_pos = self.financial_position(loss_vehicle)
        loss_conf = self.post(
            f"vehicles/{loss_vehicle.pk}/financial-position/confirm/",
            {
                "expected_source_version": loss_pos.data["source_version"],
                "reason": "Confirmed Loss Rs 5000",
                "investor_loss_amount": "5000.00",
                "company_loss_amount": "3000.00",
            },
            "reconf-loss-confirm",
        )
        self.assertEqual(loss_conf.status_code, 201, loss_conf.content)

        # 2. Vehicle B: Profit v1 Rs 40,000 -> Investor Share 50% = Rs 20,000.00
        profit_vehicle = self.create_vehicle("KL 11 R 0002")
        self.create_purchase(profit_vehicle, investor=investor)
        profit_sale = self.post(
            "sales/",
            {
                "vehicle_id": str(profit_vehicle.pk),
                "branch_id": str(self.branch.pk),
                "sale_price": "50000.00",
                "buyer_name": "Profit Buyer",
                "buyer_phone": "9876543211",
                "sold_at": (timezone.now() - timedelta(days=1)).isoformat(),
            },
            "reconf-profit-sale",
        )
        self.assertEqual(profit_sale.status_code, 201, profit_sale.content)
        profit_rcpt = self.post(
            f"sales/{profit_sale.data['id']}/receipts/",
            {"account_id": str(self.bank.pk), "amount": "50000.00", "reference": "RECONF-PROFIT-RCPT"},
            "reconf-profit-rcpt",
            self.branch_accountant,
        )
        self.assertEqual(profit_rcpt.status_code, 201, profit_rcpt.content)
        v1_pos = self.financial_position(profit_vehicle)
        profit_v1 = self.post(
            f"vehicles/{profit_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": v1_pos.data["source_version"], "reason": "Confirmed Profit v1"},
            "reconf-profit-v1-confirm",
        )
        self.assertEqual(profit_v1.status_code, 201, profit_v1.content)
        self.assertEqual(profit_v1.data["investor_share_amount"], "20000.00")

        # 3. Record Loss Offset Rs 5,000.00 against Profit v1
        offset_url = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{loss_conf.data['id']}/profit-loss-offsets/"
        )
        offset_resp = self.client.post(
            offset_url,
            {
                "profit_result_id": profit_v1.data["id"],
                "amount": "5000.00",
                "reason": "Apply Rs 5000 Loss offset against Profit v1",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="reconf-loss-offset-5000",
        )
        self.assertEqual(offset_resp.status_code, 201, offset_resp.content)

        # 4. Add a Rs 4,000 Vehicle Expense -> Profit drops Rs 40,000 -> Rs 36,000 -> Investor Profit v2 = Rs 18,000.00
        extra_exp = self.post(
            f"vehicles/{profit_vehicle.pk}/expenses/",
            {
                "amount": "4000.00",
                "description": "Post-confirmation cost adjustment",
                "investor_id": str(investor.pk),
            },
            "reconf-profit-extra-exp-4000",
        )
        self.assertEqual(extra_exp.status_code, 201, extra_exp.content)
        v2_pos = self.financial_position(profit_vehicle)
        rec = create_vehicle_capital_recovery(
            actor=self.company_accountant,
            company_id=self.company.pk,
            sale_id=profit_sale.data["id"],
            expected_source_version=v2_pos.data["source_version"],
            reason="Capital recovery at updated total cost",
            key="reconf-profit-rec",
            path="/internal-test/capital-recovery/",
        )
        self.assertEqual(rec.status, 201)
        profit_v2 = self.post(
            f"vehicles/{profit_vehicle.pk}/financial-position/confirm/",
            {"expected_source_version": v2_pos.data["source_version"], "reason": "Reconfirmed Profit v2"},
            "reconf-profit-v2-confirm",
        )
        self.assertEqual(profit_v2.status_code, 201, profit_v2.content)
        self.assertEqual(profit_v2.data["version"], 2)
        self.assertEqual(profit_v2.data["investor_share_amount"], "18000.00")

        # 5. Projection must reconcile historical Loss Offset: remaining Rs 13,000.00 (NOT Rs 18,000.00)
        reconfirmed_pos = self.financial_position(profit_vehicle).data["confirmed_result"]
        self.assertEqual(reconfirmed_pos["id"], profit_v2.data["id"])
        self.assertEqual(reconfirmed_pos["investor_share_amount"], "18000.00")
        self.assertEqual(reconfirmed_pos["investor_loss_offset_applied"], "5000.00")
        self.assertEqual(reconfirmed_pos["investor_profit_remaining"], "13000.00")
        self.assertEqual(reconfirmed_pos["investor_profit_overpaid"], "0.00")

        # 6. Profit Payment API remains blocked because historical offset linked to v1 requires review
        pay_url = (
            f"/api/v1/tenants/{self.company.pk}/investment/vehicle-results/"
            f"{profit_v2.data['id']}/profit-payments/"
        )
        self.client.force_authenticate(user=self.company_accountant)
        pay_resp = self.client.post(
            pay_url,
            {
                "account_id": str(self.bank.pk),
                "amount": "18000.00",
                "description": "Attempted payout ignoring historical offset",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="reconf-pay-attempt-18000",
        )
        self.assertEqual(pay_resp.status_code, 409, pay_resp.content)
        self.assertEqual(pay_resp.json()["code"], "INVESTOR_PROFIT_OFFSET_REVIEW_REQUIRED")

        # 7. PostgreSQL trigger 0051 independently rejects payment exceeding Rs 13,000.00 across sale_id
        from django.db import connection

        v2_row = VehicleResultConfirmation.objects.select_related(
            "sale", "investor", "vehicle_module_revision", "investment_module_revision",
        ).get(pk=profit_v2.data["id"])
        with self.assertRaises(IntegrityError) as trigger_exc, transaction.atomic():
            InvestorVehicleProfitPayment.objects.create(
                tenant=self.company,
                result_confirmation=v2_row,
                investor=v2_row.investor,
                branch=v2_row.sale.branch,
                account=self.bank,
                amount=Decimal("13000.01"),
                effective_at=timezone.now(),
                actor=self.company_accountant,
                vehicle_module_revision=v2_row.vehicle_module_revision,
                investment_module_revision=v2_row.investment_module_revision,
                description="Direct DB trigger check",
                source_reference="RECONF-TRIGGER-EXCEED",
            )
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS investment_vehicle_profit_payment_bounds IMMEDIATE")
        self.assertIn("exceed the confirmed Profit share", str(trigger_exc.exception))
