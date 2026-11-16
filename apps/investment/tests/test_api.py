from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AccountSecurityEvent, CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent, FundCreditReferenceKey
from apps.investment.models import (
    InvestorFundCredit,
    InvestorFundCreditCorrection,
    InvestorFundUse,
    InvestorFundUseAllocation,
    InvestorPrincipalReturn,
    InvestorPrincipalReturnAllocation,
)
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant


class InvestmentApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="p5-north")
        self.other_company = Tenant.objects.create(name="South", slug="p5-south")
        self.branch_a = Branch.objects.create(tenant=self.company, name="Central")
        self.branch_b = Branch.objects.create(tenant=self.company, name="West")
        self.other_branch = Branch.objects.create(tenant=self.other_company, name="Other")
        self.company_accountant = make_user(
            "p5-company-accountant", role="accountant", tenant=self.company
        )
        self.branch_accountant = make_user("p5-branch-accountant", tenant=self.company)
        self.owner = make_user("p5-owner", role="owner", tenant=self.company)
        self.membership = self.branch_accountant.tenant_memberships.get(
            tenant=self.company
        )
        CompanyRoleGrant.objects.create(
            membership=self.membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch_a,
            assigned_by=self.branch_accountant,
        )
        BranchAssignment.objects.create(
            membership=self.membership,
            branch=self.branch_a,
            assigned_by=self.branch_accountant,
        )
        self.cash = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Till",
            created_by=self.company_accountant,
        )
        self.add_revision("investment", 1)
        self.add_revision("accounting", 1)
        self.add_revision("vehicle_management", 1)
        self.client = APIClient()

    def add_revision(self, module_code, version, state=CompanyModuleState.State.ENABLED):
        return CompanyModuleState.objects.create(
            tenant=self.company,
            module_code=module_code,
            state=state,
            version=version,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/investment/{suffix}"

    def post(self, suffix, data, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(
            self.path(suffix),
            data,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_phase5_branch_list_respects_company_and_branch_scope(self):
        self.client.force_authenticate(user=self.company_accountant)
        company_rows = self.client.get(self.path("branches/"))
        self.assertEqual(company_rows.status_code, 200)
        self.assertEqual({row["id"] for row in company_rows.data["results"]}, {str(self.branch_a.pk), str(self.branch_b.pk)})
        self.client.force_authenticate(user=self.branch_accountant)
        branch_rows = self.client.get(self.path("branches/"))
        self.assertEqual(branch_rows.status_code, 200)
        self.assertEqual([row["id"] for row in branch_rows.data["results"]], [str(self.branch_a.pk)])
        foreign = self.client.get(f"/api/v1/tenants/{self.other_company.pk}/investment/branches/")
        self.assertIn(foreign.status_code, (403, 404))
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(self.path("branches/")).status_code, (401, 403))

    def test_branch_accountant_can_create_company_profile_but_not_interim_config(self):
        created = self.post(
            "investors/", {"name": "Ayaan Rahman"}, "investor-create",
            user=self.branch_accountant,
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(
            self.path(f"investors/{created.data['id']}/interim-configurations/"),
            {"amount": "1000.00", "effective_date": "2026-12-01"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="interim-denied",
        )
        self.assertEqual(denied.status_code, 403, denied.content)

    def test_company_accountant_can_append_interim_configuration(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-interim")
        self.assertEqual(investor.status_code, 201, investor.content)
        self.client.force_authenticate(user=self.company_accountant)
        response = self.client.post(
            self.path(f"investors/{investor.data['id']}/interim-configurations/"),
            {"amount": "1000.00", "effective_date": "2026-12-01"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="interim-add",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.data["amount"], "1000.00")
        self.assertEqual(response.data["effective_date"], "2026-12-01")

    def test_fund_credit_creates_exactly_one_capital_movement_and_is_idempotent(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-credit")
        self.assertEqual(investor.status_code, 201, investor.content)
        body = {
            "investor_id": investor.data["id"],
            "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk),
            "amount": "50000.00",
            "reference": "INVESTOR-CASH-001",
            "effective_at": timezone.now().isoformat(),
        }
        first = self.post("fund/credits/", body, "fund-credit-1", self.branch_accountant)
        retry = self.post("fund/credits/", body, "fund-credit-1", self.branch_accountant)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(
            AccountingEvent.objects.filter(tenant=self.company).count(), 1
        )
        event = AccountingEvent.objects.get(tenant=self.company)
        self.assertEqual(event.event_type, "CAPITAL_INFLOW")
        self.assertEqual(event.amount, Decimal("50000.00"))
        self.assertEqual(event.category_id, None)
        self.assertEqual(AccountMovement.objects.filter(event=event).count(), 1)
        self.assertEqual(
            AccountMovement.objects.get(event=event).delta, Decimal("50000.00")
        )
        self.assertFalse(
            AccountingEvent.objects.filter(
                tenant=self.company, event_type__in=("INCOME", "EXPENSE")
            ).exists()
        )

    def test_fund_credit_reference_is_unique_per_company_and_account(self):
        investor = self.post("investors/", {"name": "Reference Investor"}, "ref-investor")
        body = {
            "investor_id": investor.data["id"], "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk), "amount": "100.00",
            "reference": "  Transfer ABC  ", "effective_at": timezone.now().isoformat(),
        }
        first = self.post("fund/credits/", body, "ref-first")
        self.assertEqual(first.status_code, 201, first.content)
        key_row = FundCreditReferenceKey.objects.get(credit_id=first.data["id"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            FundCreditReferenceKey.objects.filter(pk=key_row.pk).update(normalized_reference="forged")
        body.update(reference="transfer abc", branch_id=str(self.branch_b.pk))
        duplicate = self.post("fund/credits/", body, "ref-duplicate")
        self.assertEqual(duplicate.status_code, 409, duplicate.content)
        self.assertEqual(InvestorFundCredit.objects.count(), 1)
        self.assertEqual(AccountMovement.objects.count(), 1)
        bank = AccountingAccount.objects.create(
            tenant=self.company, account_type=AccountingAccount.AccountType.BANK,
            label="Reference bank", created_by=self.company_accountant,
        )
        body["account_id"] = str(bank.pk)
        different_account = self.post("fund/credits/", body, "ref-other-account")
        self.assertEqual(different_account.status_code, 201, different_account.content)
        self.assertEqual(AccountMovement.objects.count(), 2)

    def test_fund_credit_rejects_cross_branch_and_cross_company_objects(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-scope")
        body = {
            "investor_id": investor.data["id"],
            "branch_id": str(self.branch_b.pk),
            "account_id": str(self.cash.pk),
            "amount": "50000.00",
            "reference": "CROSS-BRANCH",
            "effective_at": timezone.now().isoformat(),
        }
        denied = self.post("fund/credits/", body, "fund-cross-branch", self.branch_accountant)
        self.assertIn(denied.status_code, (403, 404), denied.content)
        body["branch_id"] = str(self.other_branch.pk)
        denied_other = self.post("fund/credits/", body, "fund-other-company", self.company_accountant)
        self.assertIn(denied_other.status_code, (403, 404), denied_other.content)
        self.assertFalse(AccountingEvent.objects.exists())

    def test_fund_credit_rejects_owner_and_disabled_accounting_module(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-disabled")
        body = {
            "investor_id": investor.data["id"],
            "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk),
            "amount": "50000.00",
            "reference": "ACCOUNTING-OFF",
            "effective_at": timezone.now().isoformat(),
        }
        owner_result = self.post("fund/credits/", body, "owner-credit", self.owner)
        self.assertEqual(owner_result.status_code, 403, owner_result.content)
        self.add_revision("accounting", 2, CompanyModuleState.State.DISABLED)
        disabled = self.post("fund/credits/", body, "accounting-off", self.company_accountant)
        self.assertEqual(disabled.status_code, 403, disabled.content)
        self.assertFalse(AccountingEvent.objects.exists())

    def test_principal_return_is_fifo_capped_idempotent_and_cash_linked(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-return")
        self.assertEqual(investor.status_code, 201, investor.content)
        first_time = timezone.now() - timedelta(minutes=2)
        first_credit = self.post(
            "fund/credits/",
            {
                "investor_id": investor.data["id"],
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "amount": "30000.00",
                "reference": "CREDIT-OLD",
                "effective_at": first_time.isoformat(),
            },
            "return-credit-old",
            self.branch_accountant,
        )
        second_credit = self.post(
            "fund/credits/",
            {
                "investor_id": investor.data["id"],
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "amount": "25000.00",
                "reference": "CREDIT-NEW",
                "effective_at": (first_time + timedelta(minutes=1)).isoformat(),
            },
            "return-credit-new",
            self.branch_accountant,
        )
        self.assertEqual(first_credit.status_code, 201, first_credit.content)
        self.assertEqual(second_credit.status_code, 201, second_credit.content)
        body = {
            "investor_id": investor.data["id"],
            "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk),
            "amount": "40000.00",
            "reference": "RETURN-001",
            "effective_at": timezone.now().isoformat(),
        }
        first = self.post(
            "fund/principal-returns/", body, "return-one", self.branch_accountant
        )
        retry = self.post(
            "fund/principal-returns/", body, "return-one", self.branch_accountant
        )
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(first.data["id"], retry.data["id"])
        self.assertEqual(
            first.data["allocations"],
            [
                {"credit_id": first_credit.data["id"], "amount": "30000.00"},
                {"credit_id": second_credit.data["id"], "amount": "10000.00"},
            ],
        )
        event = AccountingEvent.objects.get(pk=first.data["accounting_event_id"])
        self.assertEqual(event.event_type, "CAPITAL_OUTFLOW")
        self.assertEqual(
            AccountMovement.objects.get(event=event).delta, Decimal("-40000.00")
        )
        from apps.accounting.models import AccountingSourceLink

        link = AccountingSourceLink.objects.get(event=event)
        self.assertEqual(str(link.investor_principal_return_id), first.data["id"])
        self.assertIsNone(link.investor_fund_credit_id)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 3)

        self.client.force_authenticate(user=self.branch_accountant)
        summary = self.client.get(
            self.path("fund/summary/"), {"branch_id": str(self.branch_a.pk)}
        )
        self.assertEqual(summary.status_code, 200, summary.content)
        self.assertEqual(summary.data["available_amount"], "15000.00")

        body["amount"] = "15000.01"
        over_return = self.post(
            "fund/principal-returns/", body, "return-over", self.branch_accountant
        )
        self.assertEqual(over_return.status_code, 409, over_return.content)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 3)

    def test_fund_credit_failure_rolls_back_source_and_cash_records(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-rollback")
        body = {
            "investor_id": investor.data["id"],
            "branch_id": str(self.branch_a.pk),
            "account_id": str(uuid4()),
            "amount": "50000.00",
            "reference": "ROLLBACK-CREDIT",
            "effective_at": timezone.now().isoformat(),
        }
        response = self.post(
            "fund/credits/", body, "fund-credit-invalid-account", self.branch_accountant
        )
        self.assertEqual(response.status_code, 404, response.content)
        from apps.investment.models import InvestorFundCredit

        self.assertFalse(InvestorFundCredit.objects.exists())
        self.assertFalse(AccountingEvent.objects.exists())
        self.assertFalse(AccountMovement.objects.exists())

    def test_future_dated_fund_credit_is_rejected(self):
        investor = self.post("investors/", {"name": "Ayaan"}, "investor-future")
        response = self.post(
            "fund/credits/",
            {
                "investor_id": investor.data["id"],
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "amount": "100.00",
                "reference": "FUTURE-CREDIT",
                "effective_at": (timezone.now() + timedelta(days=1)).isoformat(),
            },
            "fund-credit-future",
            self.branch_accountant,
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_credit_attribution_correction_preserves_prior_use_returns_and_cash(self):
        original = self.post("investors/", {"name": "Original Investor"}, "corr-original")
        target = self.post("investors/", {"name": "Correct Investor"}, "corr-target")
        self.assertEqual(original.status_code, 201, original.content)
        self.assertEqual(target.status_code, 201, target.content)

        credit = self.post(
            "fund/credits/",
            {
                "investor_id": original.data["id"],
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "amount": "50000.00",
                "reference": "CORRECTION-CREDIT-001",
                "effective_at": (timezone.now() - timedelta(minutes=5)).isoformat(),
            },
            "corr-credit-create",
            self.branch_accountant,
        )
        self.assertEqual(credit.status_code, 201, credit.content)

        self.client.force_authenticate(user=self.company_accountant)
        vehicle = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/",
            {
                "registration": "KL 11 P 7001",
                "model": "Correction test vehicle",
                "branch_id": str(self.branch_a.pk),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="corr-vehicle-create",
        )
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        purchase = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/purchases/",
            {
                "vehicle_id": vehicle.data["id"],
                "branch_id": str(self.branch_a.pk),
                "purchase_cost": "10000.00",
                "seller_name": "Seller",
                "seller_phone": "",
                "investor_id": original.data["id"],
                "investor_fund_amount": "5000.00",
                "running_capital_amount": "5000.00",
                "initial_payment_amount": "0.00",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="corr-purchase-create",
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)

        principal_return = self.post(
            "fund/principal-returns/",
            {
                "investor_id": original.data["id"],
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "amount": "5000.00",
                "reference": "CORRECTION-RETURN-001",
                "effective_at": timezone.now().isoformat(),
            },
            "corr-principal-return",
            self.branch_accountant,
        )
        self.assertEqual(principal_return.status_code, 201, principal_return.content)

        credit_row = InvestorFundCredit.objects.get(pk=credit.data["id"])
        use_row = InvestorFundUse.objects.get(purchase_id=purchase.data["id"])
        use_allocation = InvestorFundUseAllocation.objects.get(fund_use=use_row)
        return_row = InvestorPrincipalReturn.objects.get(pk=principal_return.data["id"])
        return_allocation = InvestorPrincipalReturnAllocation.objects.get(
            principal_return=return_row
        )
        original_use_snapshot = (use_row.investor_id, use_allocation.credit_id, use_allocation.amount)
        original_return_snapshot = (
            return_row.investor_id,
            return_allocation.credit_id,
            return_allocation.amount,
        )
        cash_event_ids = list(
            AccountingEvent.objects.filter(tenant=self.company)
            .order_by("created_at", "id")
            .values_list("id", flat=True)
        )
        cash_movement_ids = list(
            AccountMovement.objects.filter(tenant=self.company)
            .order_by("created_at", "id")
            .values_list("id", flat=True)
        )

        correction_body = {
            "to_investor_id": target.data["id"],
            "reason": "The received transfer was attributed to the wrong Investor.",
        }
        corrected = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            correction_body,
            "corr-credit-attribution",
            self.branch_accountant,
        )
        replay = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            correction_body,
            "corr-credit-attribution",
            self.branch_accountant,
        )
        changed_payload_replay = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            {**correction_body, "reason": "Different payload."},
            "corr-credit-attribution",
            self.branch_accountant,
        )

        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(changed_payload_replay.status_code, 409, changed_payload_replay.content)
        self.assertEqual(corrected.data["id"], credit.data["id"])
        self.assertEqual(corrected.data["investor_id"], target.data["id"])
        self.assertEqual(corrected.data["original_investor_id"], original.data["id"])
        self.assertEqual(corrected.data["correction_version"], 1)
        self.assertTrue(corrected.data["manual_review_required"])
        self.assertEqual(InvestorFundCreditCorrection.objects.count(), 1)
        correction_row = InvestorFundCreditCorrection.objects.get()
        self.assertTrue(
            AccountSecurityEvent.objects.filter(
                action="investment.fund.credit.correct",
                resource_id=correction_row.pk,
                reason=correction_body["reason"],
            ).exists()
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorFundCreditCorrection.objects.filter(pk=correction_row.pk).update(
                reason="Direct rewrite must fail."
            )
        self.assertEqual(str(credit_row.investor_id), original.data["id"])
        self.assertEqual(
            (use_row.investor_id, use_allocation.credit_id, use_allocation.amount),
            original_use_snapshot,
        )
        self.assertEqual(
            (return_row.investor_id, return_allocation.credit_id, return_allocation.amount),
            original_return_snapshot,
        )
        self.assertEqual(
            list(
                AccountingEvent.objects.filter(tenant=self.company)
                .order_by("created_at", "id")
                .values_list("id", flat=True)
            ),
            cash_event_ids,
        )
        self.assertEqual(
            list(
                AccountMovement.objects.filter(tenant=self.company)
                .order_by("created_at", "id")
                .values_list("id", flat=True)
            ),
            cash_movement_ids,
        )

        self.client.force_authenticate(user=self.company_accountant)
        new_owner_credits = self.client.get(
            self.path("fund/credits/"), {"investor_id": target.data["id"]}
        )
        old_owner_credits = self.client.get(
            self.path("fund/credits/"), {"investor_id": original.data["id"]}
        )
        self.assertEqual(new_owner_credits.status_code, 200, new_owner_credits.content)
        self.assertEqual(old_owner_credits.status_code, 200, old_owner_credits.content)
        self.assertEqual([row["id"] for row in new_owner_credits.data["results"]], [credit.data["id"]])
        self.assertEqual(old_owner_credits.data["results"], [])

    def test_fund_credit_attribution_correction_respects_source_branch_and_module(self):
        original = self.post("investors/", {"name": "Original"}, "corr-scope-original")
        target = self.post("investors/", {"name": "Target"}, "corr-scope-target")
        self.assertEqual(original.status_code, 201, original.content)
        self.assertEqual(target.status_code, 201, target.content)
        credit = self.post(
            "fund/credits/",
            {
                "investor_id": original.data["id"],
                "branch_id": str(self.branch_b.pk),
                "account_id": str(self.cash.pk),
                "amount": "500.00",
                "reference": "CORRECTION-WEST-CREDIT",
                "effective_at": timezone.now().isoformat(),
            },
            "corr-scope-credit",
        )
        self.assertEqual(credit.status_code, 201, credit.content)

        denied_branch = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            {"to_investor_id": target.data["id"], "reason": "Wrong attribution."},
            "corr-scope-branch-denied",
            self.branch_accountant,
        )
        self.assertIn(denied_branch.status_code, (403, 404), denied_branch.content)
        self.assertFalse(InvestorFundCreditCorrection.objects.exists())

        company_correction = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            {"to_investor_id": target.data["id"], "reason": "Company accountant correction."},
            "corr-scope-company-allowed",
        )
        self.assertEqual(company_correction.status_code, 201, company_correction.content)

        second_credit = self.post(
            "fund/credits/",
            {
                "investor_id": original.data["id"],
                "branch_id": str(self.branch_b.pk),
                "account_id": str(self.cash.pk),
                "amount": "300.00",
                "reference": "CORRECTION-WEST-CREDIT-2",
                "effective_at": timezone.now().isoformat(),
            },
            "corr-scope-credit-2",
        )
        self.assertEqual(second_credit.status_code, 201, second_credit.content)

        owner_denied = self.post(
            f"fund/credits/{second_credit.data['id']}/corrections/",
            {"to_investor_id": target.data["id"], "reason": "Owner must not correct."},
            "corr-scope-owner-denied",
            self.owner,
        )
        self.assertEqual(owner_denied.status_code, 403, owner_denied.content)

        self.add_revision("investment", 2, CompanyModuleState.State.DISABLED)
        disabled = self.post(
            f"fund/credits/{second_credit.data['id']}/corrections/",
            {"to_investor_id": target.data["id"], "reason": "Wrong attribution."},
            "corr-scope-module-off",
        )
        self.assertEqual(disabled.status_code, 403, disabled.content)
        self.assertEqual(InvestorFundCreditCorrection.objects.count(), 1)
