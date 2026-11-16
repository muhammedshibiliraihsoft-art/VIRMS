from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.test import APIClient
from django.test import TransactionTestCase

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingApplication,
    AccountingCategory,
    AccountingEvent,
    AccountingSourceLink,
)
from apps.investment.models import InvestorFundUse, InvestorFundUseAllocation
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import (
    Vehicle,
    VehicleExpense,
    VehicleExpenseCorrection,
    VehicleExpensePayment,
    VehicleExpenseRefund,
)


class VehicleExpenseApiTests(TransactionTestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Expense Co", slug="p5-expense-co")
        self.other_company = Tenant.objects.create(name="Other Expense Co", slug="p5-expense-other")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.other_branch = Branch.objects.create(tenant=self.company, name="West")
        self.foreign_branch = Branch.objects.create(tenant=self.other_company, name="Foreign")
        self.company_accountant = make_user(
            "p5-expense-company-accountant", role="accountant", tenant=self.company
        )
        self.branch_accountant = make_user("p5-expense-branch-accountant", tenant=self.company)
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
        self.vehicle = self.create_vehicle(self.branch, "KL 11 P 5050", "expense-test-vehicle")

    def add_revision(self, code, version, state=CompanyModuleState.State.ENABLED):
        return CompanyModuleState.objects.create(
            tenant=self.company,
            module_code=code,
            state=state,
            version=version,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/vehicle-management/{suffix}"

    def post(self, suffix, body, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(
            self.path(suffix), body, format="json", HTTP_IDEMPOTENCY_KEY=key
        )

    def create_vehicle(self, branch, registration, key):
        response = self.post(
            "vehicles/",
            {"registration": registration, "model": "Hatchback", "branch_id": str(branch.pk)},
            key,
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Vehicle.objects.get(pk=response.data["id"])

    def expense_body(self, **overrides):
        body = {
            "amount": "5000.00",
            "description": "Brake repair",
            "investor_id": None,
            "investor_fund_amount": "0.00",
            "running_capital_amount": "5000.00",
        }
        body.update(overrides)
        return body

    def create_expense(self, *, user=None, vehicle=None, **overrides):
        vehicle = vehicle or self.vehicle
        return self.post(
            f"vehicles/{vehicle.pk}/expenses/",
            self.expense_body(**overrides),
            f"expense-create-{VehicleExpense.objects.count()}-{vehicle.pk}",
            user,
        )

    def create_investor_with_credit(self, amount="10000.00"):
        self.client.force_authenticate(user=self.company_accountant)
        investor_response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/",
            {"name": "Ayaan"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="expense-investor-create",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        credit_response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": investor_response.data["id"],
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": amount,
                "reference": "EXPENSE-FUND-001",
                "effective_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="expense-investor-credit",
        )
        self.assertEqual(credit_response.status_code, 201, credit_response.content)
        return investor_response.data["id"]

    def test_running_capital_total_covers_all_pages_and_latest_correction(self):
        ids = []
        for index in range(21):
            result = self.create_expense(amount="100.00", running_capital_amount="100.00", description=f"Expense {index}", effective_at=(timezone.now() - timedelta(minutes=1)).isoformat())
            self.assertEqual(result.status_code, 201, result.content)
            ids.append(result.data["id"])
        correction = self.post(
            f"expenses/{ids[-1]}/corrections/",
            {"amount": "150.00", "reason": "Corrected bill"}, "expense-total-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        self.client.force_authenticate(user=self.company_accountant)
        first = self.client.get(self.path(f"vehicles/{self.vehicle.pk}/expenses/?page=1"))
        second = self.client.get(self.path(f"vehicles/{self.vehicle.pk}/expenses/?page=2"))
        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertEqual(len(second.data["results"]), 1)
        self.assertEqual(first.data["running_capital_total"], "2150.00")
        self.assertEqual(second.data["running_capital_total"], "2150.00")

    def test_branch_accountant_can_add_company_only_vehicle_cost_without_accounting_movement(self):
        result = self.create_expense(user=self.branch_accountant)
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(result.data["amount"], "5000.00")
        self.assertEqual(result.data["payable"], "5000.00")
        self.assertEqual(result.data["running_capital_amount"], "5000.00")
        self.assertFalse(AccountingEvent.objects.exists())

    def test_investor_linked_expense_uses_fifo_and_only_company_accountant_can_create(self):
        investor_id = self.create_investor_with_credit("3000.00")
        payload = {
            "amount": "5000.00",
            "description": "Brake repair",
            "investor_id": investor_id,
        }
        denied = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            payload,
            "expense-fund-denied",
            self.branch_accountant,
        )
        self.assertEqual(denied.status_code, 403, denied.content)
        self.assertFalse(VehicleExpense.objects.exists())

        created = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            payload,
            "expense-fund-first",
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created.data["investor_fund_amount"], "3000.00")
        self.assertEqual(created.data["running_capital_amount"], "2000.00")
        bypass = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            {"amount": "100.00", "description": "Must retain Investor"},
            "expense-fund-bypass", self.branch_accountant,
        )
        self.assertEqual(bypass.status_code, 409, bypass.content)
        use = InvestorFundUse.objects.get(expense_id=created.data["id"])
        self.assertEqual(use.amount, Decimal("3000.00"))
        self.assertEqual(
            InvestorFundUseAllocation.objects.filter(fund_use=use).aggregate(total=Sum("amount"))["total"],
            Decimal("3000.00"),
        )

        no_fund_left = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            {**payload, "amount": "1000.00", "description": "Further repair"},
            "expense-fund-exhausted",
        )
        self.assertEqual(no_fund_left.status_code, 201, no_fund_left.content)
        self.assertEqual(no_fund_left.data["investor_fund_amount"], "0.00")
        self.assertEqual(no_fund_left.data["running_capital_amount"], "1000.00")
        self.assertEqual(no_fund_left.data["investor_id"], investor_id)
        self.assertFalse(AccountingEvent.objects.filter(event_type__in=("INCOME", "EXPENSE")).exists())

    def test_branch_expense_correction_cannot_increase_pooled_fund_allocation(self):
        investor_id = self.create_investor_with_credit("5000.00")
        expense = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            {"amount": "1000.00", "description": "Investor repair", "investor_id": investor_id},
            "branch-expense-correction-source",
        )
        self.assertEqual(expense.status_code, 201, expense.content)
        reduced = self.post(
            f"expenses/{expense.data['id']}/corrections/",
            {"amount": "500.00", "reason": "Corrected bill"},
            "branch-expense-correction-reduce-fund",
            self.branch_accountant,
        )
        self.assertEqual(reduced.status_code, 201, reduced.content)
        self.assertEqual(reduced.data["investor_fund_amount"], "500.00")
        correction_count = VehicleExpenseCorrection.objects.filter(expense_id=expense.data["id"]).count()

        denied = self.post(
            f"expenses/{expense.data['id']}/corrections/",
            {"amount": "750.00", "reason": "Additional work"},
            "branch-expense-correction-add-fund",
            self.branch_accountant,
        )
        self.assertEqual(denied.status_code, 403, denied.content)
        self.assertEqual(VehicleExpenseCorrection.objects.filter(expense_id=expense.data["id"]).count(), correction_count)
        allowed = self.post(
            f"expenses/{expense.data['id']}/corrections/",
            {"amount": "750.00", "reason": "Additional work"},
            "company-expense-correction-add-fund",
            self.company_accountant,
        )
        self.assertEqual(allowed.status_code, 201, allowed.content)
        self.assertEqual(allowed.data["investor_fund_amount"], "750.00")

    def test_expense_rejects_stale_client_funding_split(self):
        investor_id = self.create_investor_with_credit("3000.00")
        result = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            {
                "amount": "5000.00",
                "description": "Brake repair",
                "investor_id": investor_id,
                "investor_fund_amount": "2000.00",
                "running_capital_amount": "3000.00",
            },
            "expense-fund-stale-split",
        )
        self.assertEqual(result.status_code, 409, result.content)
        self.assertFalse(VehicleExpense.objects.exists())

    def test_company_only_expense_can_be_saved_when_investment_module_is_not_configured(self):
        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)
        result = self.create_expense(user=self.branch_accountant)
        self.assertEqual(result.status_code, 201, result.content)

    def test_payment_is_typed_once_reference_unique_and_amount_is_capped(self):
        expense = self.create_expense()
        self.assertEqual(expense.status_code, 201, expense.content)
        suffix = f"expenses/{expense.data['id']}/installments/"
        body = {
            "account_id": str(self.cash.pk),
            "amount": "2000.00",
            "reference": "  VOUCHER-001  ",
        }
        first = self.post(suffix, body, "expense-payment-one", self.branch_accountant)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.data["payable"], "3000.00")
        payment = VehicleExpensePayment.objects.get(pk=first.data["payment_id"])
        self.assertEqual(payment.reference, "VOUCHER-001")
        event = AccountingEvent.objects.get(pk=first.data["accounting_event_id"])
        self.assertEqual(event.event_type, "VEHICLE_PAYMENT")
        self.assertEqual(AccountMovement.objects.filter(event=event).count(), 1)
        self.assertEqual(AccountMovement.objects.get(event=event).delta, Decimal("-2000.00"))
        self.assertEqual(AccountingSourceLink.objects.get(event=event).vehicle_expense_payment_id, payment.pk)

        duplicate = self.post(
            suffix,
            {**body, "amount": "100.00", "reference": "voucher-001"},
            "expense-payment-duplicate",
            self.branch_accountant,
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.content)
        too_much = self.post(
            suffix,
            {**body, "amount": "3000.01", "reference": "VOUCHER-002"},
            "expense-payment-overpay",
            self.branch_accountant,
        )
        self.assertEqual(too_much.status_code, 409, too_much.content)
        self.assertEqual(VehicleExpensePayment.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.count(), 1)

    def test_refund_reconciles_cash_once_and_explicitly_classifies_excess_as_income(self):
        expense = self.create_expense()
        paid = self.post(
            f"expenses/{expense.data['id']}/installments/",
            {"account_id": str(self.cash.pk), "amount": "2000.00", "reference": "PAY-EXP-1"},
            "expense-refund-setup-payment",
            self.branch_accountant,
        )
        self.assertEqual(paid.status_code, 201, paid.content)
        category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.INCOME,
            label="Vendor adjustment income",
            created_by=self.company_accountant,
        )
        receipt = self.post(
            f"expenses/{expense.data['id']}/refunds/",
            {
                "account_id": str(self.bank.pk),
                "amount": "2500.00",
                "excess_income_category_id": str(category.pk),
                "excess_income_description": "Workshop refunded excess advance",
            },
            "expense-refund-one",
            self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        self.assertEqual(receipt.data["applied_amount"], "2000.00")
        self.assertEqual(receipt.data["excess_income_amount"], "500.00")
        refund = VehicleExpenseRefund.objects.get(pk=receipt.data["refund_id"])
        event = AccountingEvent.objects.get(pk=receipt.data["accounting_event_id"])
        income = AccountingEvent.objects.get(pk=receipt.data["excess_income_event_id"])
        self.assertEqual(event.event_type, "VEHICLE_REFUND_IN")
        self.assertEqual(AccountMovement.objects.filter(event=event).count(), 1)
        self.assertEqual(AccountMovement.objects.get(event=event).delta, Decimal("2500.00"))
        self.assertEqual(AccountMovement.objects.filter(event=income).count(), 0)
        self.assertEqual(income.event_type, "INCOME")
        self.assertEqual(income.amount, Decimal("500.00"))
        self.assertEqual(AccountingSourceLink.objects.get(event=event).vehicle_expense_refund_id, refund.pk)
        application = AccountingApplication.objects.get(
            source_event=event,
            target_event=income,
        )
        self.assertEqual(application.amount, Decimal("500.00"))
        self.assertEqual(application.effect_sign, 1)
        self.assertEqual(receipt.data["payable"], "5000.00")

    def test_excess_refund_without_income_category_rolls_back_every_write(self):
        expense = self.create_expense()
        result = self.post(
            f"expenses/{expense.data['id']}/refunds/",
            {"account_id": str(self.bank.pk), "amount": "100.00"},
            "expense-refund-needs-classification",
            self.branch_accountant,
        )
        self.assertEqual(result.status_code, 400, result.content)
        self.assertFalse(VehicleExpenseRefund.objects.exists())
        self.assertFalse(AccountingEvent.objects.exists())
        self.assertFalse(AccountMovement.objects.exists())

    def test_refund_requires_all_three_modules_on(self):
        expense = self.create_expense()
        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)
        result = self.post(
            f"expenses/{expense.data['id']}/refunds/",
            {"account_id": str(self.bank.pk), "amount": "100.00"},
            "expense-refund-investment-off",
        )
        self.assertEqual(result.status_code, 403, result.content)
        self.assertFalse(VehicleExpenseRefund.objects.exists())
        self.assertFalse(AccountMovement.objects.exists())
