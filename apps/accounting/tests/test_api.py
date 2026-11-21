from decimal import Decimal

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import (
    AccountingApplication,
    AccountMovement,
    AccountingAccount,
    AccountingCategory,
    AccountingEvent,
    CompanyPeriodConfirmation,
    OwnerDistributionPayment,
)
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant


class AccountingApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="api-north")
        self.other_company = Tenant.objects.create(name="South", slug="api-south")
        self.branch_a = Branch.objects.create(tenant=self.company, name="Main")
        self.branch_b = Branch.objects.create(tenant=self.company, name="Second")
        self.other_branch = Branch.objects.create(tenant=self.other_company, name="Other")
        self.accountant = make_user("p4-api-accountant", role="accountant", tenant=self.company)
        self.owner = make_user("p4-api-owner", role="owner", tenant=self.company)
        self.branch_accountant = make_user("p4-api-branch-accountant", tenant=self.company)
        membership = self.branch_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch_a,
            assigned_by=self.branch_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch_a,
            assigned_by=self.branch_accountant,
        )
        self.revision = self.add_revision(1, CompanyModuleState.State.ENABLED)
        self.income_category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.INCOME,
            label="Service Income",
            created_by=self.accountant,
        )
        self.expense_category = AccountingCategory.objects.create(
            tenant=self.company,
            kind=AccountingCategory.Kind.EXPENSE,
            label="Materials",
            created_by=self.accountant,
        )
        self.cash = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Till",
            created_by=self.accountant,
        )
        self.client = APIClient()

    def add_revision(self, version, state, *, effective_from=None):
        return CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="accounting",
            state=state,
            version=version,
            effective_from=effective_from or timezone.now(),
            changed_by=self.accountant,
        )

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/accounting/{suffix}"

    def login(self, user=None):
        self.client.force_authenticate(user=user or self.accountant)

    def post(self, suffix, data, key, *, user=None):
        self.login(user)
        return self.client.post(
            self.path(suffix),
            data,
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def income_payload(self, *, amount="100.00", branch_id=None, source_reference="INV-100"):
        return {
            "amount": amount,
            "branch_id": str(branch_id or self.branch_a.pk),
            "category_id": str(self.income_category.pk),
            "description": "Service charge",
            "source_reference": source_reference,
        }

    def expense_payload(self, *, amount="100.00", branch_id=None):
        return {
            "amount": amount,
            "branch_id": str(branch_id or self.branch_a.pk),
            "category_id": str(self.expense_category.pk),
            "description": "Workshop expense",
            "source_reference": "EXP-100",
        }

    def test_create_income_is_idempotent_and_company_scoped(self):
        payload = self.income_payload()
        first = self.post("incomes/", payload, "income-intent-1")
        second = self.post("incomes/", payload, "income-intent-1")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        self.assertEqual(first.data["id"], second.data["id"])
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)

        changed = self.income_payload(amount="101.00")
        conflict = self.post("incomes/", changed, "income-intent-1")
        self.assertEqual(conflict.status_code, 409, conflict.content)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)

    def test_owner_can_read_but_cannot_post_accounting(self):
        response = self.post("incomes/", self.income_payload(), "owner-income", user=self.owner)
        self.assertEqual(response.status_code, 403, response.content)

    def test_branch_accountant_cannot_post_or_read_another_branch(self):
        payload = self.income_payload(branch_id=self.branch_b.pk)
        response = self.post(
            "incomes/", payload, "branch-cross-write", user=self.branch_accountant
        )
        self.assertEqual(response.status_code, 404, response.content)
        query = self.client.get(
            self.path(f"events/?branch_id={self.branch_b.pk}"),
        )
        self.assertEqual(query.status_code, 404, query.content)

    def test_cross_company_request_is_hidden(self):
        self.login()
        response = self.client.get(
            f"/api/v1/tenants/{self.other_company.pk}/accounting/events/"
        )
        self.assertEqual(response.status_code, 404, response.content)

    def test_accounting_branch_catalog_obeys_company_and_branch_scope(self):
        self.login()
        company_branches = self.client.get(self.path("branches/"))
        self.assertEqual(company_branches.status_code, 200, company_branches.content)
        self.assertEqual(
            {row["id"] for row in company_branches.data["results"]},
            {str(self.branch_a.pk), str(self.branch_b.pk)},
        )

        self.login(self.branch_accountant)
        branch_branches = self.client.get(self.path("branches/"))
        self.assertEqual(branch_branches.status_code, 200, branch_branches.content)
        self.assertEqual(
            {row["id"] for row in branch_branches.data["results"]},
            {str(self.branch_a.pk)},
        )

    def test_unfiltered_event_list_uses_authorized_company_and_branch_scope(self):
        income_a = self.post(
            "incomes/",
            self.income_payload(source_reference="EVENT-LIST-A"),
            "event-list-a",
        )
        income_b = self.post(
            "incomes/",
            self.income_payload(
                branch_id=self.branch_b.pk,
                source_reference="EVENT-LIST-B",
            ),
            "event-list-b",
        )
        self.assertEqual(income_a.status_code, 201, income_a.data)
        self.assertEqual(income_b.status_code, 201, income_b.data)

        self.login()
        company_rows = self.client.get(self.path("events/?event_type=INCOME"))
        self.assertEqual(company_rows.status_code, 200, company_rows.data)
        self.assertEqual(
            {row["id"] for row in company_rows.data["results"]},
            {income_a.data["id"], income_b.data["id"]},
        )

        branch_client = APIClient()
        branch_client.force_authenticate(user=self.branch_accountant)
        branch_rows = branch_client.get(self.path("events/?event_type=INCOME"))
        self.assertEqual(branch_rows.status_code, 200, branch_rows.data)
        self.assertEqual(
            [row["id"] for row in branch_rows.data["results"]],
            [income_a.data["id"]],
        )

    def test_branch_accountant_cannot_reallocate_a_cash_application_across_branches(self):
        membership = self.branch_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch_b,
            assigned_by=self.branch_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch_b,
            assigned_by=self.branch_accountant,
        )
        original_income = self.post("incomes/", self.income_payload(branch_id=self.branch_a.pk), "branch-reallocate-income-a")
        new_income = self.post("incomes/", self.income_payload(branch_id=self.branch_b.pk), "branch-reallocate-income-b")
        self.assertEqual(original_income.status_code, 201, original_income.data)
        self.assertEqual(new_income.status_code, 201, new_income.data)
        receipt = self.post(
            "receipts/",
            {
                "amount": "20.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": original_income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Received against Branch A income",
                "source_reference": "CASH-REASSIGN-1",
            },
            "branch-reallocate-receipt",
            user=self.branch_accountant,
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)
        reallocation = self.post(
            f"applications/{receipt.data['application_ids'][0]}/reallocations/",
            {"target_event_id": new_income.data["id"], "reason": "Wrong Branch"},
            "branch-reallocate-cross-branch",
            user=self.branch_accountant,
        )
        self.assertEqual(reallocation.status_code, 403, reallocation.content)
        self.assertEqual(AccountMovement.objects.filter(event_id=receipt.data["id"]).count(), 1)

    def test_superseded_income_detail_does_not_claim_outstanding_balance(self):
        income = self.post("incomes/", self.income_payload(), "income-detail-correct")
        self.assertEqual(income.status_code, 201, income.data)
        correction = self.post(
            f"events/{income.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct the source record",
                "replacement": {
                    "amount": "100.00",
                    "branch_id": str(self.branch_a.pk),
                    "category_id": str(self.income_category.pk),
                    "description": "Corrected income",
                    "source_reference": "INV-100-CORRECTED",
                },
            },
            "income-detail-correction",
        )
        self.assertEqual(correction.status_code, 201, correction.data)
        detail = self.client.get(self.path(f"events/{income.data['id']}/"))
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertNotIn("outstanding_amount", detail.data)

    def test_receipt_is_separate_from_income_and_over_receipt_is_rejected(self):
        income_response = self.post("incomes/", self.income_payload(), "income-for-receipt")
        income_id = income_response.data["id"]
        receipt_payload = {
            "amount": "40.00",
            "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk),
            "target_event_id": income_id,
            "effective_at": timezone.now().isoformat(),
            "description": "Part receipt",
            "source_reference": "CASH-001",
        }
        receipt = self.post("receipts/", receipt_payload, "receipt-1")
        self.assertEqual(receipt.status_code, 201, receipt.data)
        self.assertEqual(receipt.data["event_type"], "RECEIPT")
        self.assertEqual(AccountMovement.objects.filter(event_id=receipt.data["id"]).count(), 1)
        self.assertEqual(
            AccountingEvent.objects.filter(
                tenant=self.company,
                event_type=AccountingEvent.EventType.INCOME,
            ).count(),
            1,
        )

        over_receipt = dict(receipt_payload, amount="61.00")
        rejected = self.post("receipts/", over_receipt, "receipt-over")
        self.assertEqual(rejected.status_code, 409, rejected.content)
        self.assertEqual(
            AccountingEvent.objects.filter(tenant=self.company).count(), 2
        )

    def test_module_off_rejects_new_roots_but_receipt_can_settle_pre_off_income(self):
        income = self.post("incomes/", self.income_payload(), "income-before-off")
        self.assertEqual(income.status_code, 201, income.data)
        expense = self.post("expenses/", self.expense_payload(), "expense-before-off")
        self.assertEqual(expense.status_code, 201, expense.data)
        off = self.add_revision(2, CompanyModuleState.State.DISABLED)
        # The default OFF effective_from is after the root event was recorded.
        blocked_income = self.post(
            "incomes/", self.income_payload(amount="200.00"), "income-after-off"
        )
        self.assertEqual(blocked_income.status_code, 403, blocked_income.content)
        blocked_expense = self.post(
            "expenses/", self.expense_payload(), "expense-after-off"
        )
        self.assertEqual(blocked_expense.status_code, 403, blocked_expense.content)
        receipt = self.post(
            "receipts/",
            {
                "amount": "25.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Post-OFF settlement",
                "source_reference": "CASH-OFF-1",
            },
            "off-settlement",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)
        self.assertEqual(receipt.data["event_type"], "RECEIPT")
        self.assertEqual(receipt.data["source_reference"], "CASH-OFF-1")
        payment = self.post(
            "payments/",
            {
                "amount": "15.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": expense.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Post-OFF Payment settlement",
                "source_reference": "PAYMENT-OFF-1",
            },
            "off-payment-settlement",
        )
        self.assertEqual(payment.status_code, 201, payment.data)
        self.assertEqual(payment.data["event_type"], "PAYMENT")

    def test_off_allows_correction_of_pre_off_income_but_not_post_off_receipt(self):
        income = self.post("incomes/", self.income_payload(), "off-correction-income")
        self.assertEqual(income.status_code, 201, income.data)
        pre_off_settlement_target = self.post(
            "incomes/", self.income_payload(source_reference="INV-PRE-OFF-CASH"), "off-correction-pre-target"
        )
        post_off_settlement_target = self.post(
            "incomes/", self.income_payload(source_reference="INV-POST-OFF-CASH"), "off-correction-post-target"
        )
        self.assertEqual(pre_off_settlement_target.status_code, 201, pre_off_settlement_target.data)
        self.assertEqual(post_off_settlement_target.status_code, 201, post_off_settlement_target.data)
        pre_off_receipt = self.post(
            "receipts/",
            {
                "amount": "10.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": pre_off_settlement_target.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Pre-OFF receipt",
                "source_reference": "CASH-PRE-OFF",
            },
            "off-correction-pre-receipt",
        )
        self.assertEqual(pre_off_receipt.status_code, 201, pre_off_receipt.data)
        off = self.add_revision(2, CompanyModuleState.State.DISABLED)

        correction = self.post(
            f"events/{income.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct the pre-OFF amount",
                "replacement": {
                    "amount": "110.00",
                    "branch_id": str(self.branch_a.pk),
                    "category_id": str(self.income_category.pk),
                    "description": "Corrected before-OFF record",
                    "source_reference": "INV-OFF-CORRECTED",
                },
            },
            "off-correction-pre-off",
        )
        self.assertEqual(correction.status_code, 201, correction.data)
        replacement = AccountingEvent.objects.get(pk=correction.data["replacement_event_id"])
        self.assertEqual(replacement.module_revision_id, off.pk)
        self.assertEqual(replacement.effective_at, AccountingEvent.objects.get(pk=income.data["id"]).effective_at)

        corrected_pre_off_receipt = self.post(
            f"receipts/{pre_off_receipt.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct a cash event recorded before OFF",
                "replacement": {
                    "amount": "8.00",
                    "branch_id": str(self.branch_a.pk),
                    "account_id": str(self.cash.pk),
                    "effective_at": timezone.now().isoformat(),
                    "description": "Corrected pre-OFF receipt",
                    "source_reference": "CASH-PRE-OFF-CORRECTED",
                },
            },
            "off-correction-pre-off-receipt",
        )
        self.assertEqual(corrected_pre_off_receipt.status_code, 201, corrected_pre_off_receipt.content)

        receipt = self.post(
            "receipts/",
            {
                "amount": "10.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": post_off_settlement_target.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Allowed post-OFF settlement",
                "source_reference": "CASH-OFF-CORRECTED",
            },
            "off-correction-post-off-receipt",
        )
        self.assertEqual(receipt.status_code, 201, receipt.content)
        blocked = self.post(
            f"receipts/{receipt.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Attempt to correct a post-OFF cash event",
                "replacement": {
                    "amount": "10.00",
                    "branch_id": str(self.branch_a.pk),
                    "account_id": str(self.cash.pk),
                    "effective_at": timezone.now().isoformat(),
                    "description": "Replacement cash event",
                    "source_reference": "CASH-OFF-BLOCKED",
                },
            },
            "off-correction-post-off-blocked",
        )
        self.assertEqual(blocked.status_code, 403, blocked.content)

    def test_off_effective_time_equal_to_recorded_time_fails_closed(self):
        income = self.post("incomes/", self.income_payload(), "off-boundary-income")
        self.assertEqual(income.status_code, 201, income.data)
        event = AccountingEvent.objects.get(pk=income.data["id"])
        self.add_revision(
            2,
            CompanyModuleState.State.DISABLED,
            effective_from=event.recorded_at,
        )

        response = self.post(
            f"events/{event.pk}/corrections/",
            {
                "outcome": "REVERSE_ONLY",
                "event_occurred": False,
                "reason": "An entry at the OFF boundary is not pre-OFF.",
            },
            "off-boundary-correction",
        )

        self.assertEqual(response.status_code, 403, response.content)
        self.assertFalse(AccountingEvent.objects.filter(reversal_of=event).exists())

    def test_reallocation_changes_application_without_changing_cash_movement(self):
        original_income = self.post(
            "incomes/", self.income_payload(source_reference="REALLOCATE-ORIGINAL"), "reallocate-income-original"
        )
        replacement_income = self.post(
            "incomes/", self.income_payload(source_reference="REALLOCATE-NEW"), "reallocate-income-new"
        )
        receipt = self.post(
            "receipts/",
            {
                "amount": "25.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": original_income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Receipt recorded against the wrong Income",
                "source_reference": "REALLOCATE-CASH",
            },
            "reallocate-receipt",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)
        original_movement = AccountMovement.objects.get(event_id=receipt.data["id"])

        response = self.post(
            f"applications/{receipt.data['application_ids'][0]}/reallocations/",
            {"target_event_id": replacement_income.data["id"], "reason": "Correct the target only."},
            "reallocate-cash-application",
        )

        self.assertEqual(response.status_code, 201, response.content)
        reversal = AccountingApplication.objects.get(
            pk=response.data["reversal_application_id"]
        )
        replacement = AccountingApplication.objects.get(
            pk=response.data["replacement_application_id"]
        )
        self.assertEqual(reversal.effect_sign, -1)
        self.assertEqual(str(reversal.reversal_of_id), receipt.data["application_ids"][0])
        self.assertEqual(str(replacement.target_event_id), replacement_income.data["id"])
        self.assertEqual(replacement.amount, Decimal("25.00"))
        self.assertEqual(AccountMovement.objects.get(event_id=receipt.data["id"]).pk, original_movement.pk)
        self.assertEqual(AccountMovement.objects.filter(event_id=receipt.data["id"]).count(), 1)
        self.assertEqual(
            sum(AccountMovement.objects.filter(account=self.cash).values_list("delta", flat=True)),
            Decimal("25.00"),
        )

    def test_module_off_allows_reallocation_only_between_pre_off_records(self):
        original_income = self.post(
            "incomes/", self.income_payload(source_reference="OFF-REALLOCATE-ORIGINAL"), "off-reallocate-income-original"
        )
        replacement_income = self.post(
            "incomes/", self.income_payload(source_reference="OFF-REALLOCATE-NEW"), "off-reallocate-income-new"
        )
        receipt = self.post(
            "receipts/",
            {
                "amount": "25.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": original_income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Pre-OFF Receipt",
                "source_reference": "OFF-REALLOCATE-CASH",
            },
            "off-reallocate-receipt",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)
        self.add_revision(2, CompanyModuleState.State.DISABLED)

        response = self.post(
            f"applications/{receipt.data['application_ids'][0]}/reallocations/",
            {"target_event_id": replacement_income.data["id"], "reason": "Correct the pre-OFF target."},
            "off-reallocate-application",
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(
            AccountMovement.objects.filter(event_id=receipt.data["id"]).count(),
            1,
        )
        self.assertEqual(
            AccountingApplication.objects.get(pk=response.data["replacement_application_id"]).module_revision_id,
            CompanyModuleState.objects.get(
                tenant=self.company,
                module_code="accounting",
                version=2,
            ).pk,
        )

    def test_expense_partial_payments_are_bounded_and_survive_expense_correction(self):
        expense = self.post("expenses/", self.expense_payload(), "expense-partials")
        self.assertEqual(expense.status_code, 201, expense.data)

        def payment(amount, key, reference):
            return self.post(
                "payments/",
                {
                    "amount": amount,
                    "branch_id": str(self.branch_a.pk),
                    "account_id": str(self.cash.pk),
                    "target_event_id": expense.data["id"],
                    "effective_at": timezone.now().isoformat(),
                    "description": "Supplier payment",
                    "source_reference": reference,
                },
                key,
            )

        first = payment("30.00", "expense-payment-1", "PAY-1")
        second = payment("50.00", "expense-payment-2", "PAY-2")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)
        movements_before = {
            event_id: list(AccountMovement.objects.filter(event_id=event_id).values_list("id", "delta"))
            for event_id in (first.data["id"], second.data["id"])
        }

        overpayment = payment("21.00", "expense-payment-over", "PAY-OVER")
        self.assertEqual(overpayment.status_code, 409, overpayment.content)
        too_small = self.post(
            f"events/{expense.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Replacement cannot cover Payments",
                "replacement": {
                    "amount": "70.00",
                    "branch_id": str(self.branch_a.pk),
                    "category_id": str(self.expense_category.pk),
                    "description": "Too small replacement",
                    "source_reference": "EXP-TOO-SMALL",
                },
            },
            "expense-correction-too-small",
        )
        self.assertEqual(too_small.status_code, 409, too_small.content)

        corrected = self.post(
            f"events/{expense.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct expense amount",
                "replacement": {
                    "amount": "90.00",
                    "branch_id": str(self.branch_a.pk),
                    "category_id": str(self.expense_category.pk),
                    "description": "Corrected workshop expense",
                    "source_reference": "EXP-CORRECTED",
                },
            },
            "expense-correction-valid",
        )
        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(
            {
                event_id: list(AccountMovement.objects.filter(event_id=event_id).values_list("id", "delta"))
                for event_id in (first.data["id"], second.data["id"])
            },
            movements_before,
        )
        self.assertEqual(
            sum(
                (row.amount * row.effect_sign for row in AccountingApplication.objects.filter(
                    target_event_id=corrected.data["replacement_event_id"]
                )),
                Decimal("0.00"),
            ),
            Decimal("80.00"),
        )

    def test_correction_replaces_income_and_reapplies_receipts_atomically(self):
        income_payload = self.income_payload()
        income_payload["effective_at"] = "2026-06-30T23:59:59+05:30"
        income = self.post("incomes/", income_payload, "income-correct")
        h2_income_payload = self.income_payload(amount="40.00", source_reference="H2-INCOME")
        h2_income_payload["effective_at"] = "2026-07-01T00:00:00+05:30"
        h2_income = self.post("incomes/", h2_income_payload, "income-h2-boundary")
        self.assertEqual(h2_income.status_code, 201, h2_income.data)
        receipt_payload = {
            "amount": "20.00",
            "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk),
            "target_event_id": income.data["id"],
            "effective_at": timezone.now().isoformat(),
            "description": "Receipt",
            "source_reference": "CASH-CORR-1",
        }
        receipt = self.post("receipts/", receipt_payload, "receipt-correct")
        self.assertEqual(receipt.status_code, 201, receipt.data)
        correction = self.post(
            f"events/{income.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct amount and description",
                "replacement": {
                    "amount": "120.00",
                    "branch_id": str(self.branch_a.pk),
                    "category_id": str(self.income_category.pk),
                    "description": "Corrected service income",
                    "source_reference": "INV-100-CORRECTED",
                },
            },
            "income-correction-1",
        )
        self.assertEqual(correction.status_code, 201, correction.data)
        self.assertEqual(AccountMovement.objects.filter(event_id=receipt.data["id"]).count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="INCOME").count(), 4)
        replacement = AccountingEvent.objects.get(pk=correction.data["replacement_event_id"])
        self.assertEqual(replacement.amount, Decimal("120.00"))
        self.assertEqual(replacement.effective_at, AccountingEvent.objects.get(pk=income.data["id"]).effective_at)
        h1_result = self.client.get(
            self.path("reports/accounting-result/?period=h1&year=2026")
        )
        h2_result = self.client.get(
            self.path("reports/accounting-result/?period=h2&year=2026")
        )
        annual_result = self.client.get(
            self.path("reports/accounting-result/?period=annual&year=2026")
        )
        self.assertEqual(h1_result.data["income_amount"], "120.00")
        self.assertEqual(h2_result.data["income_amount"], "40.00")
        self.assertEqual(annual_result.data["income_amount"], "160.00")

    def test_receipt_correction_keeps_original_cash_event_and_reapplies_replacement(self):
        income = self.post("incomes/", self.income_payload(), "receipt-correction-income")
        receipt = self.post(
            "receipts/",
            {
                "amount": "20.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Original receipt",
                "source_reference": "CASH-ORIGINAL",
            },
            "receipt-correction-original",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)

        corrected = self.post(
            f"receipts/{receipt.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct the recorded cash amount",
                "replacement": {
                    "amount": "25.00",
                    "branch_id": str(self.branch_a.pk),
                    "account_id": str(self.cash.pk),
                    "effective_at": timezone.now().isoformat(),
                    "description": "Corrected receipt",
                    "source_reference": "CASH-CORRECTED",
                },
            },
            "receipt-correction-replace",
        )

        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(AccountMovement.objects.filter(event_id=receipt.data["id"]).count(), 1)
        self.assertEqual(
            AccountMovement.objects.filter(
                event_id=corrected.data["reversal_event_id"]
            ).get().delta,
            Decimal("-20.00"),
        )
        replacement = AccountingEvent.objects.get(pk=corrected.data["replacement_event_id"])
        self.assertEqual(replacement.amount, Decimal("25.00"))
        self.assertEqual(
            AccountingApplication.objects.filter(
                source_event=replacement, effect_sign=1
            ).get().amount,
            Decimal("25.00"),
        )
        self.assertEqual(
            sum(
                (row.amount * row.effect_sign for row in AccountingApplication.objects.filter(
                    source_event__in=(receipt.data["id"], replacement.pk)
                )),
                Decimal("0.00"),
            ),
            Decimal("25.00"),
        )

    def test_payment_correction_uses_typed_resource_and_preserves_original_movement(self):
        expense = self.post("expenses/", self.expense_payload(), "payment-correction-expense")
        payment = self.post(
            "payments/",
            {
                "amount": "20.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": expense.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Original payment",
                "source_reference": "PAYMENT-ORIGINAL",
            },
            "payment-correction-original",
        )
        self.assertEqual(payment.status_code, 201, payment.data)

        corrected = self.post(
            f"payments/{payment.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct the recorded payment amount",
                "replacement": {
                    "amount": "25.00",
                    "branch_id": str(self.branch_a.pk),
                    "account_id": str(self.cash.pk),
                    "effective_at": timezone.now().isoformat(),
                    "description": "Corrected payment",
                    "source_reference": "PAYMENT-CORRECTED",
                },
            },
            "payment-correction-replace",
        )

        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(AccountMovement.objects.filter(event_id=payment.data["id"]).get().delta, Decimal("-20.00"))
        self.assertEqual(
            AccountMovement.objects.filter(event_id=corrected.data["reversal_event_id"]).get().delta,
            Decimal("20.00"),
        )
        replacement = AccountingEvent.objects.get(pk=corrected.data["replacement_event_id"])
        self.assertEqual(replacement.event_type, AccountingEvent.EventType.PAYMENT)
        self.assertEqual(AccountMovement.objects.filter(event=replacement).get().delta, Decimal("-25.00"))

    def test_false_receipt_and_payment_reverse_their_applications_and_movements(self):
        targets = (
            ("INCOME", "RECEIPT", "receipts", "incomes", Decimal("20.00")),
            ("EXPENSE", "PAYMENT", "payments", "expenses", Decimal("-15.00")),
        )
        for target_type, cash_type, resource, target_resource, cash_delta in targets:
            with self.subTest(cash_type=cash_type):
                if target_type == "INCOME":
                    target = self.post(
                        "incomes/", self.income_payload(source_reference=f"{cash_type}-FALSE-TARGET"),
                        f"{cash_type.lower()}-false-target",
                    )
                else:
                    expense_payload = self.expense_payload()
                    expense_payload["source_reference"] = f"{cash_type}-FALSE-TARGET"
                    target = self.post(
                        "expenses/", expense_payload,
                        f"{cash_type.lower()}-false-target",
                    )
                cash_event = self.post(
                    f"{resource}/",
                    {
                        "amount": str(abs(cash_delta)),
                        "branch_id": str(self.branch_a.pk),
                        "account_id": str(self.cash.pk),
                        "target_event_id": target.data["id"],
                        "effective_at": timezone.now().isoformat(),
                        "description": f"False {cash_type.lower()}",
                        "source_reference": f"{cash_type}-FALSE-CASH",
                    },
                    f"{cash_type.lower()}-false-cash",
                )
                self.assertEqual(cash_event.status_code, 201, cash_event.data)

                correction = self.post(
                    f"{resource}/{cash_event.data['id']}/corrections/",
                    {
                        "outcome": "REVERSE_ONLY",
                        "event_occurred": False,
                        "reason": f"Duplicate {cash_type.lower()} entry",
                    },
                    f"{cash_type.lower()}-false-correction",
                )

                self.assertEqual(correction.status_code, 201, correction.content)
                original_application = AccountingApplication.objects.get(
                    source_event_id=cash_event.data["id"], effect_sign=1
                )
                application_reversal = AccountingApplication.objects.get(
                    reversal_of=original_application
                )
                self.assertEqual(application_reversal.effect_sign, -1)
                self.assertEqual(str(application_reversal.target_event_id), target.data["id"])
                movement_total = sum(
                    AccountMovement.objects.filter(
                        event_id__in=(cash_event.data["id"], correction.data["reversal_event_id"])
                    ).values_list("delta", flat=True),
                    Decimal("0.00"),
                )
                self.assertEqual(movement_total, Decimal("0.00"))

    def test_generic_event_correction_rejects_cash_event_types(self):
        income = self.post("incomes/", self.income_payload(), "generic-route-income")
        receipt = self.post(
            "receipts/",
            {
                "amount": "20.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": income.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Receipt",
                "source_reference": "GENERIC-ROUTE-RECEIPT",
            },
            "generic-route-receipt",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)

        response = self.post(
            f"events/{receipt.data['id']}/corrections/",
            {
                "outcome": "REVERSE_ONLY",
                "event_occurred": False,
                "reason": "Must use the typed Receipt correction resource",
            },
            "generic-cash-correction-reject",
        )

        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(AccountingEvent.objects.filter(reversal_of_id=receipt.data["id"]).count(), 0)

    def test_false_income_and_expense_use_reverse_only_without_replacement(self):
        for event_type, resource in (("INCOME", "incomes/"), ("EXPENSE", "expenses/")):
            with self.subTest(event_type=event_type):
                if event_type == "INCOME":
                    created = self.post(
                        resource,
                        self.income_payload(source_reference=f"FALSE-{event_type}"),
                        f"false-{event_type.lower()}",
                    )
                else:
                    created = self.post(
                        resource,
                        self.expense_payload(),
                        f"false-{event_type.lower()}",
                    )
                self.assertEqual(created.status_code, 201, created.data)

                reversed_event = self.post(
                    f"events/{created.data['id']}/corrections/",
                    {
                        "outcome": "REVERSE_ONLY",
                        "event_occurred": False,
                        "reason": f"Duplicate {event_type.lower()} entry",
                    },
                    f"false-{event_type.lower()}-reverse",
                )

                self.assertEqual(reversed_event.status_code, 201, reversed_event.content)
                net_amount = sum(
                    (
                        row.amount * row.effect_sign
                        for row in AccountingEvent.objects.filter(
                            pk__in=(created.data["id"], reversed_event.data["reversal_event_id"])
                        )
                    ),
                    Decimal("0.00"),
                )
                self.assertEqual(net_amount, Decimal("0.00"))

    def test_transfer_reverse_only_uses_typed_resource_and_appends_balanced_legs(self):
        destination = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.BANK,
            label="Reversal Bank",
            created_by=self.accountant,
        )
        transfer = self.post(
            "transfers/",
            {
                "branch_id": str(self.branch_a.pk),
                "from_account_id": str(self.cash.pk),
                "to_account_id": str(destination.pk),
                "amount": "40.00",
                "effective_at": timezone.now().isoformat(),
                "reason": "Original transfer",
                "source_reference": "TRANSFER-REVERSAL-ORIGINAL",
            },
            "transfer-reversal-original",
        )
        self.assertEqual(transfer.status_code, 201, transfer.data)

        reversed_transfer = self.post(
            f"transfers/{transfer.data['id']}/reversals/",
            {
                "outcome": "REVERSE_ONLY",
                "event_occurred": False,
                "reason": "This transfer was a duplicate entry",
            },
            "transfer-reversal-only",
        )

        self.assertEqual(reversed_transfer.status_code, 201, reversed_transfer.content)
        movement_rows = list(
            AccountMovement.objects.filter(event_id=reversed_transfer.data["reversal_event_id"])
        )
        self.assertEqual(len(movement_rows), 2)
        self.assertEqual(sum((row.delta for row in movement_rows), Decimal("0.00")), Decimal("0.00"))

    def test_opening_balance_and_transfer_replacements_append_balanced_movements(self):
        opening = self.post(
            "opening-balances/",
            {
                "account_id": str(self.cash.pk),
                "branch_id": str(self.branch_a.pk),
                "amount": "-50.00",
                "effective_at": timezone.now().isoformat(),
                "reason": "Opening debt",
                "source_reference": "OPEN-REPLACE-1",
            },
            "opening-replace-original",
        )
        self.assertEqual(opening.status_code, 201, opening.data)
        corrected_opening = self.post(
            f"opening-balances/{opening.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct signed opening position",
                "replacement_amount": "30.00",
                "source_reference": "OPEN-REPLACE-2",
            },
            "opening-replace-corrected",
        )
        self.assertEqual(corrected_opening.status_code, 201, corrected_opening.content)
        self.assertEqual(
            AccountMovement.objects.get(
                event_id=corrected_opening.data["replacement_event_id"]
            ).delta,
            Decimal("30.00"),
        )

        destination = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.BANK,
            label="Reserve Bank",
            created_by=self.accountant,
        )
        transfer = self.post(
            "transfers/",
            {
                "branch_id": str(self.branch_a.pk),
                "from_account_id": str(self.cash.pk),
                "to_account_id": str(destination.pk),
                "amount": "40.00",
                "effective_at": timezone.now().isoformat(),
                "reason": "Move funds",
                "source_reference": "TRANSFER-ORIGINAL",
            },
            "transfer-correction-original",
        )
        self.assertEqual(transfer.status_code, 201, transfer.data)
        corrected_transfer = self.post(
            f"transfers/{transfer.data['id']}/corrections/",
            {
                "outcome": "REVERSE_AND_REPLACE",
                "event_occurred": True,
                "reason": "Correct transfer amount",
                "replacement": {
                    "branch_id": str(self.branch_a.pk),
                    "from_account_id": str(self.cash.pk),
                    "to_account_id": str(destination.pk),
                    "amount": "35.00",
                    "effective_at": timezone.now().isoformat(),
                    "description": "Corrected transfer",
                    "source_reference": "TRANSFER-CORRECTED",
                },
            },
            "transfer-correction-replace",
        )
        self.assertEqual(corrected_transfer.status_code, 201, corrected_transfer.content)
        for event_id in (
            transfer.data["id"],
            corrected_transfer.data["reversal_event_id"],
            corrected_transfer.data["replacement_event_id"],
        ):
            movement_rows = list(AccountMovement.objects.filter(event_id=event_id))
            self.assertEqual(len(movement_rows), 2)
            self.assertEqual(sum((row.delta for row in movement_rows), Decimal("0.00")), Decimal("0.00"))

    def test_opening_balance_can_be_negative_and_archive_is_blocked_after_reversal(self):
        opening = self.post(
            "opening-balances/",
            {
                "account_id": str(self.cash.pk),
                "branch_id": str(self.branch_a.pk),
                "amount": "-50.00",
                "effective_at": timezone.now().isoformat(),
                "reason": "Opening debt",
                "source_reference": "OPEN-1",
            },
            "opening-1",
        )
        self.assertEqual(opening.status_code, 201, opening.data)
        account_list = self.client.get(self.path("accounts/"))
        self.assertEqual(account_list.status_code, 200, account_list.data)
        account_row = next(row for row in account_list.data["results"] if row["id"] == str(self.cash.pk))
        self.assertEqual(account_row["current_balance"], "-50.00")

        nonzero_archive = self.client.patch(
            self.path(f"accounts/{self.cash.pk}/"),
            {"is_active": False},
            format="json",
            HTTP_IDEMPOTENCY_KEY="archive-nonzero-balance",
        )
        self.assertEqual(nonzero_archive.status_code, 409, nonzero_archive.content)
        self.assertEqual(nonzero_archive.json()["code"], "ACCOUNT_BALANCE_NONZERO")

        reversal = self.post(
            f"opening-balances/{opening.data['id']}/corrections/",
            {
                "outcome": "REVERSE_ONLY",
                "event_occurred": False,
                "reason": "Duplicate opening entry",
                "replacement_amount": "0.00",
                "source_reference": "OPEN-1-REVERSAL",
            },
            "opening-reversal",
        )
        self.assertEqual(reversal.status_code, 201, reversal.content)
        archived = self.client.patch(
            self.path(f"accounts/{self.cash.pk}/"),
            {"is_active": False},
            format="json",
            HTTP_IDEMPOTENCY_KEY="archive-with-history",
        )
        self.assertEqual(archived.status_code, 409, archived.content)
        self.assertEqual(archived.json()["code"], "ACCOUNT_HISTORY_PRESENT")

    def test_zero_balance_account_without_history_can_be_archived_via_api(self):
        self.login()
        response = self.client.patch(
            self.path(f"accounts/{self.cash.pk}/"),
            {"is_active": False},
            format="json",
            HTTP_IDEMPOTENCY_KEY="archive-empty-account",
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.data["is_active"])
        self.cash.refresh_from_db()
        self.assertFalse(self.cash.is_active)
        self.assertIsNotNone(self.cash.archived_at)
        self.assertEqual(AccountMovement.objects.filter(account=self.cash).count(), 0)

    def test_accounting_result_preserves_paise_for_large_amounts(self):
        income = self.post("incomes/", self.income_payload(amount="9999999999999999999999999999.99"), "large-report-income")
        self.assertEqual(income.status_code, 201, income.content)
        expense = self.post("expenses/", self.expense_payload(amount="0.01"), "large-report-expense")
        self.assertEqual(expense.status_code, 201, expense.content)
        self.login()
        response = self.client.get(self.path("reports/accounting-result/?period=annual&year=2026"))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["accounting_result_amount"], "9999999999999999999999999999.98")

    def test_accounting_result_uses_accounting_records_and_calendar_period(self):
        payload = self.income_payload(amount="125.50")
        created = self.post("incomes/", payload, "income-report")
        self.assertEqual(created.status_code, 201, created.data)
        expense = self.post(
            "expenses/", self.expense_payload(amount="25.25"), "expense-report"
        )
        self.assertEqual(expense.status_code, 201, expense.data)
        receipt = self.post(
            "receipts/",
            {
                "amount": "50.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": created.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Actual receipt excluded from result",
                "source_reference": "RECEIPT-REPORT",
            },
            "receipt-report",
        )
        self.assertEqual(receipt.status_code, 201, receipt.data)
        payment = self.post(
            "payments/",
            {
                "amount": "5.00",
                "branch_id": str(self.branch_a.pk),
                "account_id": str(self.cash.pk),
                "target_event_id": expense.data["id"],
                "effective_at": timezone.now().isoformat(),
                "description": "Actual payment excluded from result",
                "source_reference": "PAYMENT-REPORT",
            },
            "payment-report",
        )
        self.assertEqual(payment.status_code, 201, payment.data)
        self.login()
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(
                self.path("reports/accounting-result/?period=annual&year=2026")
            )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["income_amount"], "125.50")
        self.assertEqual(response.data["expense_amount"], "25.25")
        self.assertEqual(response.data["accounting_result_amount"], "100.25")
        self.assertEqual(response.data["timezone"], "Asia/Kolkata")
        result_queries = [
            query["sql"]
            for query in captured.captured_queries
            if 'FROM "accounting_accountingevent"' in query["sql"]
        ]
        self.assertEqual(len(result_queries), 1, result_queries)

    def test_company_period_confirmation_carries_loss_and_caps_distributable_amount(self):
        h1_income = self.post("incomes/", {
            **self.income_payload(amount="20.00", source_reference="H1-INCOME"),
            "effective_at": "2026-02-01T10:00:00+05:30",
        }, "company-period-h1-income")
        h1_expense = self.post("expenses/", {
            **self.expense_payload(amount="70.00"), "source_reference": "H1-EXPENSE",
            "effective_at": "2026-03-01T10:00:00+05:30",
        }, "company-period-h1-expense")
        self.assertEqual(h1_income.status_code, 201, h1_income.data)
        self.assertEqual(h1_expense.status_code, 201, h1_expense.data)
        self.login()
        h1_report = self.client.get(self.path("reports/accounting-result/?period=h1&year=2026"))
        self.assertEqual(h1_report.data["accounting_result_amount"], "-50.00")
        from apps.accounting.company_periods import period_bounds, event_source_version
        from apps.accounting.models import AccountingEvent
        _, _, start_at, end_at = period_bounds("h1", 2026)
        self.assertEqual(h1_report.data["source_version"], event_source_version(AccountingEvent.objects.filter(
            tenant=self.company, effective_at__gte=start_at, effective_at__lt=end_at,
        )))
        h1 = self.post("company-period-confirmations/", {
            "period_type": "h1", "year": 2026, "expected_source_version": h1_report.data["source_version"],
            "distributable_amount": "0.00", "liabilities_reviewed": True,
            "liability_review_reason": "Reviewed Company liabilities", "reason": "Confirm first-half Loss",
        }, "company-period-h1-confirm")
        self.assertEqual(h1.status_code, 201, getattr(h1, "data", h1.content))
        self.assertEqual(h1.data["loss_carried_forward"], "50.00")
        h1_replay = self.post("company-period-confirmations/", {
            "period_type": "h1", "year": 2026, "expected_source_version": h1_report.data["source_version"],
            "distributable_amount": "0.00", "liabilities_reviewed": True,
            "liability_review_reason": "Reviewed Company liabilities", "reason": "Confirm first-half Loss",
        }, "company-period-h1-confirm")
        self.assertEqual(h1_replay.data["id"], h1.data["id"])

        h2_income = self.post("incomes/", {
            **self.income_payload(amount="100.00", source_reference="H2-INCOME"),
            "effective_at": "2026-08-01T10:00:00+05:30",
        }, "company-period-h2-income")
        self.assertEqual(h2_income.status_code, 201, h2_income.data)
        self.login()
        h2_report = self.client.get(self.path("reports/accounting-result/?period=h2&year=2026"))
        h2_body = {
            "period_type": "h2", "year": 2026, "expected_source_version": h2_report.data["source_version"],
            "distributable_amount": "35.00", "liabilities_reviewed": True,
            "liability_review_reason": "Reviewed unpaid bills and obligations", "reason": "Confirm second-half pool",
        }
        no_owner_split = self.post("company-period-confirmations/", h2_body, "company-period-h2-no-owner-split")
        self.assertEqual(no_owner_split.status_code, 409, no_owner_split.content)
        from apps.accounts.tests.test_users import make_user
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from apps.tenants.models import TenantMembership
        owner_membership = self.owner.tenant_memberships.get(tenant=self.company)
        owner_end = timezone.now()
        owner_membership.role_grants.filter(role="owner").update(effective_until=owner_end)
        TenantMembership.objects.filter(pk=owner_membership.pk).update(effective_until=owner_end)
        historical_owner = make_user("p4-period-historical-owner")
        owner_membership = TenantMembership.objects.create(
            user=historical_owner, tenant=self.company, assigned_by=historical_owner,
            effective_from=datetime(2025, 1, 1, tzinfo=ZoneInfo("Asia/Kolkata")),
        )
        CompanyRoleGrant.objects.create(
            membership=owner_membership, role="owner", assigned_by=historical_owner,
            effective_from=owner_membership.effective_from,
        )
        operator = make_user("p4-owner-split-operator", role="back_office", account_kind="platform")
        self.client.force_authenticate(user=operator)
        configured = self.client.post(self.path("owner-distribution-configurations/"), {
            "effective_from": "2026-01-01",
            "recipients": [{"id": str(historical_owner.pk), "percentage": "100.00"}],
            "reason": "Set approved Company Owner split",
        }, format="json", HTTP_IDEMPOTENCY_KEY="owner-split-config-v1")
        self.assertEqual(configured.status_code, 201, configured.content)
        self.login()
        h2 = self.post("company-period-confirmations/", h2_body, "company-period-h2-confirm")
        self.assertEqual(h2.status_code, 201, h2.data)
        self.assertEqual(h2.data["prior_loss_carried_forward"], "50.00")
        self.assertEqual(h2.data["positive_after_loss"], "50.00")
        self.assertEqual(h2.data["owner_allocation_snapshot"], [
            {"recipient_id": str(historical_owner.pk), "recipient_label": historical_owner.login_id,
             "percentage": "100.00", "amount": "35.00"},
        ])
        self.assertEqual(CompanyPeriodConfirmation.objects.filter(tenant=self.company).count(), 2)
        self.assertEqual(AccountMovement.objects.count(), 0)
        owner_payment_path = self.path(f"company-period-confirmations/{h2.data['id']}/owner-payments/")
        payment_body = {
            "recipient_id": str(historical_owner.pk), "branch_id": str(self.branch_a.pk),
            "account_id": str(self.cash.pk), "amount": "10.00", "effective_at": timezone.now().isoformat(),
            "expected_source_version": h2.data["source_version"], "reason": "Pay first Owner distribution part",
        }
        payment_before = AccountMovement.objects.count()
        first_payment = self.client.post(owner_payment_path, payment_body, format="json", HTTP_IDEMPOTENCY_KEY="owner-payment-part-1")
        payment_replay = self.client.post(owner_payment_path, payment_body, format="json", HTTP_IDEMPOTENCY_KEY="owner-payment-part-1")
        self.assertEqual(first_payment.status_code, 201, first_payment.content)
        self.assertEqual(payment_replay.status_code, 201, payment_replay.content)
        self.assertEqual(first_payment.data["id"], payment_replay.data["id"])
        owner_payment = OwnerDistributionPayment.objects.get(pk=first_payment.data["id"])
        self.assertEqual(owner_payment.accounting_event.event_type, AccountingEvent.EventType.OWNER_DISTRIBUTION_PAYMENT)
        self.assertEqual(AccountMovement.objects.get(event=owner_payment.accounting_event).delta, Decimal("-10.00"))
        self.assertEqual(AccountMovement.objects.count(), payment_before + 1)
        self.assertEqual(first_payment.data["outstanding_amount"], "25.00")
        _, _, h2_starts_at, h2_ends_at = period_bounds("h2", 2026)
        self.assertEqual(event_source_version(AccountingEvent.objects.filter(
            tenant=self.company, effective_at__gte=h2_starts_at, effective_at__lt=h2_ends_at,
        )), h2.data["source_version"])
        too_much_owner_payment = self.client.post(owner_payment_path, {
            **payment_body, "amount": "35.01",
        }, format="json", HTTP_IDEMPOTENCY_KEY="owner-payment-over-allocation")
        self.assertEqual(too_much_owner_payment.status_code, 409, too_much_owner_payment.content)
        self.client.force_authenticate(user=operator)
        revised_split = self.client.post(self.path("owner-distribution-configurations/"), {
            "effective_from": "2026-01-01",
            "recipients": [{"id": str(historical_owner.pk), "percentage": "100.00"}],
            "reason": "Reconfirm effective Company Owner split",
        }, format="json", HTTP_IDEMPOTENCY_KEY="owner-split-config-v2")
        self.assertEqual(revised_split.status_code, 201, revised_split.content)
        self.login()
        confirmations_after_split_change = self.client.get(self.path("company-period-confirmations/"))
        confirmed_h2 = next(row for row in confirmations_after_split_change.data["confirmations"] if row["period_type"] == "h2")
        self.assertFalse(confirmed_h2["source_current"])
        self.post("incomes/", {
            **self.income_payload(amount="1.00", source_reference="H2-LATE-INCOME"),
            "effective_at": "2026-09-01T10:00:00+05:30",
        }, "company-period-late-income")
        confirmation_history = self.client.get(self.path("company-period-confirmations/"))
        self.assertFalse(next(row for row in confirmation_history.data["confirmations"] if row["period_type"] == "h2")["source_current"])
        stale = self.post("company-period-confirmations/", h2_body, "company-period-stale-confirm")
        self.assertEqual(stale.status_code, 409, stale.content)
        too_much = self.post("company-period-confirmations/", {
            **h2_body, "distributable_amount": "50.01",
        }, "company-period-h2-over-cap")
        self.assertEqual(too_much.status_code, 409, too_much.content)

        refreshed_report = self.client.get(self.path("reports/accounting-result/?period=h2&year=2026"))
        h2_v2_body = {**h2_body, "expected_source_version": refreshed_report.data["source_version"],
                      "reason": "Reconfirm after the reviewed source change"}
        h2_v2 = self.post("company-period-confirmations/", h2_v2_body, "company-period-h2-reconfirm")
        self.assertEqual(h2_v2.status_code, 201, h2_v2.content)
        stale_service_payment = self.client.post(owner_payment_path, {
            **payment_body, "amount": "1.00",
        }, format="json", HTTP_IDEMPOTENCY_KEY="owner-payment-stale-confirmation")
        self.assertEqual(stale_service_payment.status_code, 409, stale_service_payment.content)

        from apps.accounting.services import _event_row
        latest_accounting_revision = CompanyModuleState.objects.filter(
            tenant=self.company, module_code="accounting",
        ).order_by("-version").first()
        forged = OwnerDistributionPayment(
            tenant=self.company, confirmation=CompanyPeriodConfirmation.objects.get(pk=h2.data["id"]),
            recipient=historical_owner, branch=self.branch_a, account=self.cash, amount=Decimal("1.00"),
            effective_at=timezone.now(), reason="Direct stale confirmation attempt", actor=self.accountant,
            accounting_revision=latest_accounting_revision,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                forged.accounting_event = _event_row(
                    tenant=self.company, branch=self.branch_a,
                    event_type=AccountingEvent.EventType.OWNER_DISTRIBUTION_PAYMENT,
                    amount=forged.amount, actor=self.accountant, revision=latest_accounting_revision,
                    description=forged.reason, source_reference=f"OWNER-DISTRIBUTION-{forged.pk}",
                    effective_at=forged.effective_at,
                )
                AccountMovement.objects.create(
                    tenant=self.company, event=forged.accounting_event, account=self.cash, delta=-forged.amount,
                )
                forged.save(force_insert=True)

    def test_company_period_confirmation_is_company_accountant_only_and_non_overlapping(self):
        self.login()
        report = self.client.get(self.path("reports/accounting-result/?period=h1&year=2026"))
        body = {
            "period_type": "h1", "year": 2026, "expected_source_version": report.data["source_version"],
            "distributable_amount": "0.00", "liabilities_reviewed": True,
            "liability_review_reason": "Reviewed liabilities", "reason": "Confirm period",
        }
        denied = self.post("company-period-confirmations/", body, "company-period-owner-denied", user=self.owner)
        self.assertEqual(denied.status_code, 403, denied.content)
        saved = self.post("company-period-confirmations/", body, "company-period-h1-overlap", user=self.accountant)
        self.assertEqual(saved.status_code, 201, saved.data)
        overlap = self.post("company-period-confirmations/", {
            **body, "period_type": "annual",
        }, "company-period-annual-overlap", user=self.accountant)
        self.assertEqual(overlap.status_code, 409, overlap.content)
