from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.db.models import Sum
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent
from apps.investment.models import (
    InvestorFundUse,
    InvestorFundUseAllocation,
    InvestorProfitShareAgreement,
)
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle, VehiclePurchase


class VehiclePurchaseApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Purchase Co", slug="p5-purchase-co")
        self.other_company = Tenant.objects.create(name="Other Co", slug="p5-purchase-other")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.other_branch = Branch.objects.create(tenant=self.company, name="West")
        self.foreign_branch = Branch.objects.create(tenant=self.other_company, name="Foreign")
        self.company_accountant = make_user(
            "p5-purchase-company-accountant", role="accountant", tenant=self.company
        )
        self.branch_accountant = make_user("p5-purchase-branch-accountant", tenant=self.company)
        self.owner = make_user("p5-purchase-owner", role="owner", tenant=self.company)
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
        self.client = APIClient()
        self.vehicle = self._create_vehicle()

    def add_revision(self, code, version, state=CompanyModuleState.State.ENABLED):
        return CompanyModuleState.objects.create(
            tenant=self.company,
            module_code=code,
            state=state,
            version=version,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )

    def _create_vehicle(self):
        self.client.force_authenticate(user=self.company_accountant)
        response = self.client.post(
            self.path("vehicles/"),
            {"registration": "KL 11 P 5050", "model": "Hatchback", "branch_id": str(self.branch.pk)},
            format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-test-vehicle",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Vehicle.objects.get(pk=response.data["id"])

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/vehicle-management/{suffix}"

    def post(self, suffix, data, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(
            self.path(suffix), data, format="json", HTTP_IDEMPOTENCY_KEY=key
        )

    def purchase_payload(self, **overrides):
        body = {
            "vehicle_id": str(self.vehicle.pk),
            "branch_id": str(self.branch.pk),
            "purchase_cost": "10000.00",
            "seller_name": "North Motors",
            "seller_phone": "",
            "investor_id": None,
            "investor_fund_amount": "0.00",
            "initial_payment_amount": "0.00",
            "running_capital_amount": "10000.00",
        }
        body.update(overrides)
        return body

    def create_investor_and_credit(self, amount="10000.00"):
        self.client.force_authenticate(user=self.company_accountant)
        investor_response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/",
            {"name": "Ayaan"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-investor-create",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        credit_response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": investor_response.data["id"],
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": amount,
                "reference": "FUND-CREDIT-PURCHASE-001",
                "effective_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-investor-credit",
        )
        self.assertEqual(credit_response.status_code, 201, credit_response.content)
        return investor_response.data["id"]

    def test_company_funded_purchase_allows_zero_advance_and_tracks_payable(self):
        created = self.post("purchases/", self.purchase_payload(), "purchase-zero")
        retry = self.post("purchases/", self.purchase_payload(), "purchase-zero")

        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(created.data["id"], retry.data["id"])
        self.assertEqual(created.data["purchase_cost"], "10000.00")
        self.assertEqual(created.data["seller_paid"], "0.00")
        self.assertEqual(created.data["seller_payable"], "10000.00")
        self.assertTrue(created.data["no_advance_warning"])
        self.assertFalse(AccountingEvent.objects.exists())
        self.assertEqual(VehiclePurchase.objects.count(), 1)

    def test_company_funded_purchase_cost_correction_preserves_history(self):
        created = self.post("purchases/", self.purchase_payload(), "purchase-correct-create")
        self.assertEqual(created.status_code, 201, created.content)
        corrected = self.post(
            f"purchases/{created.data['id']}/corrections/",
            {"purchase_cost": "9000.00", "reason": "Corrected seller price"},
            "purchase-correct-company-only",
        )
        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(corrected.data["purchase_cost"], "9000.00")
        self.assertEqual(corrected.data["running_capital_amount"], "9000.00")
        self.assertEqual(VehiclePurchase.objects.get(pk=created.data["id"]).purchase_cost, Decimal("10000.00"))
        self.assertFalse(AccountMovement.objects.exists())

        excessive = self.post(
            f"purchases/{created.data['id']}/installments/",
            {"account_id": str(self.cash.pk), "amount": "9500.00"},
            "purchase-corrected-cost-overpay",
        )
        self.assertEqual(excessive.status_code, 409, excessive.content)
        self.assertEqual(excessive.json()["code"], "PURCHASE_PAYABLE_EXCEEDED")
        self.assertFalse(AccountMovement.objects.exists())

        exact = self.post(
            f"purchases/{created.data['id']}/installments/",
            {"account_id": str(self.cash.pk), "amount": "9000.00"},
            "purchase-corrected-cost-exact-pay",
        )
        self.assertEqual(exact.status_code, 201, exact.content)
        self.assertEqual(exact.data["seller_payable"], "0.00")
        self.assertEqual(AccountMovement.objects.get().delta, Decimal("-9000.00"))

    def test_same_vehicle_cannot_receive_another_investors_purchase_fund(self):
        first_investor_id = self.create_investor_and_credit(amount="10000.00")
        self.client.force_authenticate(user=self.company_accountant)
        second_investor = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/investors/",
            {"name": "Second Investor"}, format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-second-investor",
        )
        self.assertEqual(second_investor.status_code, 201, second_investor.content)
        second_credit = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/investment/fund/credits/",
            {
                "investor_id": second_investor.data["id"],
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": "10000.00",
                "reference": "PURCHASE-SECOND-INVESTOR",
                "effective_at": (timezone.now() - timedelta(minutes=2)).isoformat(),
            }, format="json", HTTP_IDEMPOTENCY_KEY="purchase-second-credit",
        )
        self.assertEqual(second_credit.status_code, 201, second_credit.content)
        expense = self.post(
            f"vehicles/{self.vehicle.pk}/expenses/",
            {"amount": "1000.00", "description": "Investor repair", "investor_id": first_investor_id},
            "purchase-vehicle-investor-expense",
        )
        self.assertEqual(expense.status_code, 201, expense.content)

        purchase = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=second_investor.data["id"],
                investor_fund_amount="2000.00",
                running_capital_amount="8000.00",
            ),
            "purchase-second-vehicle-investor",
        )
        self.assertEqual(purchase.status_code, 409, purchase.content)
        self.assertEqual(purchase.json()["code"], "VEHICLE_INVESTOR_MISMATCH")
        self.assertFalse(VehiclePurchase.objects.exists())
        self.assertEqual(InvestorFundUse.objects.filter(purchase__isnull=False).count(), 0)

    def test_purchase_installment_and_refund_replay_without_optional_dates(self):
        purchase = self.post("purchases/", self.purchase_payload(), "purchase-optional-date")
        self.assertEqual(purchase.status_code, 201, purchase.content)
        suffix = f"purchases/{purchase.data['id']}/installments/"
        payment_body = {"account_id": str(self.cash.pk), "amount": "2000.00"}
        first_payment = self.post(suffix, payment_body, "purchase-payment-no-date")
        repeated_payment = self.post(suffix, payment_body, "purchase-payment-no-date")
        self.assertEqual(first_payment.status_code, 201, first_payment.content)
        self.assertEqual(repeated_payment.status_code, 201, repeated_payment.content)
        self.assertEqual(first_payment.data["payment_id"], repeated_payment.data["payment_id"])
        self.assertEqual(first_payment.data["seller_payable"], repeated_payment.data["seller_payable"])

        refund_body = {"account_id": str(self.cash.pk), "amount": "500.00"}
        first_refund = self.post(
            f"purchases/{purchase.data['id']}/refunds/", refund_body, "purchase-refund-no-date"
        )
        repeated_refund = self.post(
            f"purchases/{purchase.data['id']}/refunds/", refund_body, "purchase-refund-no-date"
        )
        self.assertEqual(first_refund.status_code, 201, first_refund.content)
        self.assertEqual(repeated_refund.status_code, 201, repeated_refund.content)
        self.assertEqual(first_refund.data["refund_id"], repeated_refund.data["refund_id"])
        self.assertEqual(AccountMovement.objects.count(), 2)

    def test_branch_accountant_can_purchase_only_for_authorized_branch(self):
        allowed = self.post(
            "purchases/", self.purchase_payload(), "branch-purchase", self.branch_accountant
        )
        self.assertEqual(allowed.status_code, 201, allowed.content)

        vehicle_response = self.post(
            "vehicles/",
            {"registration": "KL 11 P 5051", "model": "Sedan", "branch_id": str(self.branch.pk)},
            "purchase-test-vehicle-2",
        )
        self.assertEqual(vehicle_response.status_code, 201, vehicle_response.content)
        wrong_branch = self.post(
            "purchases/",
            self.purchase_payload(vehicle_id=vehicle_response.data["id"], branch_id=str(self.other_branch.pk)),
            "branch-purchase-wrong-branch",
            self.branch_accountant,
        )
        self.assertIn(wrong_branch.status_code, (403, 404), wrong_branch.content)

    def test_purchase_rejects_foreign_vehicle_and_mismatched_funding_total(self):
        foreign = self.post(
            "purchases/",
            self.purchase_payload(vehicle_id=str(uuid4())),
            "purchase-foreign-vehicle",
        )
        self.assertIn(foreign.status_code, (404, 400), foreign.content)

        mismatch = self.post(
            "purchases/",
            self.purchase_payload(running_capital_amount="9999.99"),
            "purchase-mismatch",
        )
        self.assertEqual(mismatch.status_code, 400, mismatch.content)
        self.assertEqual(VehiclePurchase.objects.count(), 0)

    def test_installment_creates_one_typed_accounting_movement_and_caps_payable(self):
        purchase = self.post("purchases/", self.purchase_payload(), "purchase-installment")
        self.assertEqual(purchase.status_code, 201, purchase.content)
        payment_body = {
            "account_id": str(self.cash.pk),
            "amount": "2500.00",
            "reference": "CASH-VOUCHER-001",
            "effective_at": timezone.now().isoformat(),
        }
        first = self.post(
            f"purchases/{purchase.data['id']}/installments/",
            payment_body,
            "seller-installment-one",
            self.branch_accountant,
        )
        retry = self.post(
            f"purchases/{purchase.data['id']}/installments/",
            payment_body,
            "seller-installment-one",
            self.branch_accountant,
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(first.data["seller_payable"], "7500.00")
        event = AccountingEvent.objects.get(tenant=self.company)
        self.assertEqual(event.event_type, "VEHICLE_PAYMENT")
        self.assertEqual(AccountMovement.objects.filter(event=event).count(), 1)
        self.assertEqual(AccountMovement.objects.get(event=event).delta, Decimal("-2500.00"))

        overpay = self.post(
            f"purchases/{purchase.data['id']}/installments/",
            {**payment_body, "amount": "7500.01", "reference": "CASH-VOUCHER-002"},
            "seller-installment-overpay",
        )
        self.assertEqual(overpay.status_code, 409, overpay.content)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)

    def test_existing_payable_can_be_paid_after_vehicle_management_off(self):
        purchase = self.post("purchases/", self.purchase_payload(), "purchase-before-off")
        self.assertEqual(purchase.status_code, 201, purchase.content)
        self.add_revision("vehicle_management", 2, CompanyModuleState.State.DISABLED)

        payment = self.post(
            f"purchases/{purchase.data['id']}/installments/",
            {
                "account_id": str(self.cash.pk),
                "amount": "1000.00",
                "reference": "CASH-VOUCHER-OFF",
                "effective_at": timezone.now().isoformat(),
            },
            "seller-payment-after-off",
        )
        self.assertEqual(payment.status_code, 201, payment.content)
        self.assertEqual(payment.data["seller_payable"], "9000.00")

    def test_investor_funded_purchase_consumes_fifo_fund_without_cash_or_profit_event(self):
        investor_id = self.create_investor_and_credit()
        purchase = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=investor_id,
                investor_fund_amount="6000.00",
                running_capital_amount="4000.00",
            ),
            "purchase-investor-funded",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        self.assertEqual(purchase.data["investor_fund_amount"], "6000.00")
        self.assertEqual(purchase.data["running_capital_amount"], "4000.00")
        fund_use = InvestorFundUse.objects.get(purchase_id=purchase.data["id"])
        self.assertEqual(fund_use.amount, Decimal("6000.00"))
        self.assertEqual(
            InvestorFundUseAllocation.objects.filter(fund_use=fund_use).aggregate(total=Sum("amount"))["total"],
            Decimal("6000.00"),
        )
        self.assertEqual(
            AccountingEvent.objects.filter(event_type="CAPITAL_INFLOW").count(), 1
        )
        self.assertFalse(
            AccountingEvent.objects.filter(event_type__in=("INCOME", "EXPENSE")).exists()
        )

    def test_investor_share_agreement_is_snapshotted_at_purchase_effective_time(self):
        investor_id = self.create_investor_and_credit(amount="10000.00")
        agreement_time = timezone.now() - timedelta(minutes=1)
        agreement = InvestorProfitShareAgreement.objects.create(
            tenant=self.company,
            investor_id=investor_id,
            share_percentage=Decimal("33.0000"),
            effective_at=agreement_time,
            actor=self.company_accountant,
        )
        purchased_at = timezone.now() - timedelta(seconds=20)
        created = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=investor_id,
                investor_fund_amount="10000.00",
                running_capital_amount="0.00",
                purchased_at=purchased_at.isoformat(),
            ),
            "purchase-agreement-snapshot",
        )

        self.assertEqual(created.status_code, 201, created.content)
        purchase = VehiclePurchase.objects.get(pk=created.data["id"])
        self.assertEqual(purchase.investor_share_agreement_id, agreement.pk)
        self.assertEqual(purchase.investor_share_percentage_snapshot, Decimal("33.0000"))
        self.assertEqual(created.data["investor_share_percentage_snapshot"], "33.0000")

    def test_late_agreement_does_not_backfill_existing_purchase_snapshot(self):
        investor_id = self.create_investor_and_credit(amount="10000.00")
        purchased_at = timezone.now() - timedelta(seconds=30)
        created = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=investor_id,
                investor_fund_amount="10000.00",
                running_capital_amount="0.00",
                purchased_at=purchased_at.isoformat(),
            ),
            "purchase-no-agreement-snapshot",
        )
        self.assertEqual(created.status_code, 201, created.content)

        InvestorProfitShareAgreement.objects.create(
            tenant=self.company,
            investor_id=investor_id,
            share_percentage=Decimal("33.0000"),
            effective_at=timezone.now() - timedelta(minutes=2),
            actor=self.company_accountant,
        )

        position = self.client.get(
            self.path(f"vehicles/{self.vehicle.pk}/financial-position/")
        )
        self.assertEqual(position.status_code, 200, position.content)
        self.assertEqual(position.data["profit_share_status"], "AGREEMENT_SNAPSHOT_MISSING")
        self.assertIsNone(position.data["investor_share_percentage_snapshot"])

    def test_investor_purchase_is_capped_and_branch_accountant_cannot_use_pooled_fund(self):
        investor_id = self.create_investor_and_credit(amount="5000.00")
        denied = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=investor_id,
                investor_fund_amount="4000.00",
                running_capital_amount="6000.00",
            ),
            "branch-accountant-fund-purchase",
            self.branch_accountant,
        )
        self.assertEqual(denied.status_code, 403, denied.content)
        self.assertFalse(VehiclePurchase.objects.exists())
        self.assertFalse(InvestorFundUse.objects.exists())

        insufficient = self.post(
            "purchases/",
            self.purchase_payload(
                investor_id=investor_id,
                investor_fund_amount="6000.00",
                running_capital_amount="4000.00",
            ),
            "purchase-fund-insufficient",
        )
        self.assertEqual(insufficient.status_code, 409, insufficient.content)
        self.assertEqual(VehiclePurchase.objects.count(), 0)
        self.assertEqual(InvestorFundUse.objects.count(), 0)
