from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingEvent,
    AccountingSourceLink,
)
from apps.investment.models import Investor
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle, VehicleSaleReceipt, VehicleSaleRefund


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

    def create_investor(self, registration="one"):
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
                "effective_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
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
