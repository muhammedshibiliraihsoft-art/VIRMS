from uuid import uuid4
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.audit import record_event
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount
from apps.investment.models import (
    Investor, InvestorAccountBinding, InvestorExitRequest,
    InvestorExitRequestHistory, InvestorExitNoticeExtension,
)
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant


class InvestorPortalBindingTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Portal North", slug="portal-north")
        self.other_company = Tenant.objects.create(name="Portal South", slug="portal-south")
        self.accountant = make_user("portal-accountant", role="accountant", tenant=self.company)
        self.branch_accountant = make_user("portal-branch-accountant", tenant=self.company)
        self.branch = Branch.objects.create(tenant=self.company, name="East")
        branch_membership = self.branch_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=branch_membership, role="accountant", branch=self.branch,
            assigned_by=self.accountant,
        )
        BranchAssignment.objects.create(
            membership=branch_membership, branch=self.branch, assigned_by=self.accountant,
        )
        self.investor_user = make_user("portal-investor", role="investor", tenant=self.company)
        self.other_investor_user = make_user("portal-other-investor", role="investor", tenant=self.company)
        self.investor = Investor.objects.create(
            tenant=self.company, name="Own Investor", created_by=self.accountant,
            updated_by=self.accountant,
        )
        self.other_investor = Investor.objects.create(
            tenant=self.company, name="Other Investor", created_by=self.accountant,
            updated_by=self.accountant,
        )
        self.foreign_investor = Investor.objects.create(
            tenant=self.other_company, name="Foreign Investor", created_by=self.accountant,
            updated_by=self.accountant,
        )
        for investor in (self.investor, self.other_investor, self.foreign_investor):
            record_event(
                action="investor.profile.create", actor=self.accountant, subject=self.accountant,
                company=investor.tenant, resource=investor,
                metadata={"investor_id": str(investor.pk), "new_name": investor.name},
            )
        for company in (self.company, self.other_company):
            for code in ("investment", "investor_portal", "vehicle_management", "accounting"):
                CompanyModuleState.objects.create(
                    tenant=company, module_code=code, state="enabled", version=1,
                    effective_from=timezone.now(), changed_by=self.accountant,
                )
        self.client = APIClient()

    def path(self, suffix, company=None):
        company = company or self.company
        return f"/api/v1/tenants/{company.pk}/investment/{suffix}"

    def post(self, suffix, body, actor=None):
        self.client.force_authenticate(user=actor or self.accountant)
        return self.client.post(
            self.path(suffix), body, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4())
        )

    def test_binding_and_self_profile_are_company_scoped(self):
        denied = self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)}, actor=self.investor_user,
        )
        self.assertEqual(denied.status_code, 403)
        foreign = self.post(
            f"investors/{self.foreign_investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.assertEqual(foreign.status_code, 404)
        created = self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(InvestorAccountBinding.objects.filter(effective_until__isnull=True).count(), 1)
        binding_view = self.client.get(self.path(f"investors/{self.investor.pk}/portal-binding/"))
        self.assertEqual(binding_view.status_code, 200, binding_view.content)
        self.assertEqual(binding_view.data["id"], created.data["id"])
        self.assertEqual(binding_view.data["account_id"], str(self.investor_user.pk))
        self.client.force_authenticate(user=self.branch_accountant)
        self.assertEqual(self.client.get(self.path(f"investors/{self.investor.pk}/portal-binding/")).status_code, 403)
        self.client.force_authenticate(user=self.investor_user)
        own = self.client.get(self.path("portal/self/"))
        self.assertEqual(own.status_code, 200, own.content)
        self.assertEqual(own.data["investor_id"], str(self.investor.pk))
        self.assertNotIn(str(self.other_investor.pk), str(own.data))
        self.assertEqual(own.data["profit_calendar"]["status"], "NOT_AVAILABLE")
        self.assertEqual(own.data["profit_periods"], [])
        self.assertEqual(own.data["profit_period_status"], "CALENDAR_NOT_AVAILABLE")
        self.assertEqual(self.client.get(self.path("portal/self/", self.other_company)).status_code, 404)
        self.assertEqual(self.client.get(self.path("portal/self/fund-history/", self.other_company)).status_code, 404)
        self.assertEqual(self.client.get(self.path("investors/")).status_code, 403)

    def test_investor_sees_only_own_paginated_interim_payment_history(self):
        cash = AccountingAccount.objects.create(
            tenant=self.company, account_type=AccountingAccount.AccountType.CASH,
            label="Interim portal cash", created_by=self.accountant,
        )
        month_start = timezone.localdate().replace(day=1)
        self.client.force_authenticate(user=self.accountant)
        for investor, amount, suffix in (
            (self.investor, "400.00", "own"),
            (self.other_investor, "900.00", "other"),
        ):
            config = self.client.post(
                self.path(f"investors/{investor.pk}/interim-configurations/"),
                {"amount": "1000.00", "effective_date": month_start.isoformat()},
                format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            )
            self.assertEqual(config.status_code, 201, config.content)
            payment = self.client.post(
                self.path(f"investors/{investor.pk}/interim-payments/"),
                {"branch_id": str(self.branch.pk), "account_id": str(cash.pk),
                 "amount": amount, "effective_at": timezone.now().isoformat()},
                format="json", HTTP_IDEMPOTENCY_KEY=f"interim-{suffix}-{uuid4()}",
            )
            self.assertEqual(payment.status_code, 201, payment.content)

        self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.client.force_authenticate(user=self.investor_user)
        history = self.client.get(self.path("portal/self/interim-payment-history/"))
        self.assertEqual(history.status_code, 200, history.content)
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(history.data["results"][0]["amount"], "400.00")
        self.assertEqual(
            set(history.data["results"][0]),
            {"id", "period_month", "effective_at", "amount"},
        )
        self.assertNotIn("900.00", str(history.data))
        self.assertEqual(
            self.client.get(self.path("portal/self/interim-payment-history/?investor_id=foreign")).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(self.path("portal/self/interim-payment-history/", self.other_company)).status_code,
            404,
        )

    def test_investor_portal_does_not_disclose_internal_vehicle_cost_or_buyer_balances(self):
        cash = AccountingAccount.objects.create(
            tenant=self.company, account_type=AccountingAccount.AccountType.CASH,
            label="Portal test cash", created_by=self.accountant,
        )
        self.client.force_authenticate(user=self.accountant)
        credit = self.client.post(
            self.path("fund/credits/"),
            {"investor_id": str(self.investor.pk), "branch_id": str(self.branch.pk),
             "account_id": str(cash.pk), "amount": "30000.00", "reference": "PORTAL-PRIVATE-1",
             "effective_at": timezone.now().isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(credit.status_code, 201, credit.content)
        vehicle_response = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/",
            {"branch_id": str(self.branch.pk), "registration": "KL 11 P 5050", "model": "Hatchback"},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(vehicle_response.status_code, 201, vehicle_response.content)
        purchase = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/purchases/",
            {"vehicle_id": vehicle_response.data["id"], "branch_id": str(self.branch.pk),
             "purchase_cost": "30000.00", "seller_name": "Private Seller",
             "investor_id": str(self.investor.pk), "investor_fund_amount": "30000.00",
             "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(purchase.status_code, 201, purchase.content)
        other_credit = self.client.post(
            self.path("fund/credits/"),
            {"investor_id": str(self.other_investor.pk), "branch_id": str(self.branch.pk),
             "account_id": str(cash.pk), "amount": "90000.00", "reference": "OTHER-INVESTOR-SECRET",
             "effective_at": timezone.now().isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(other_credit.status_code, 201, other_credit.content)
        self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.client.force_authenticate(user=self.investor_user)

        response = self.client.get(self.path("portal/self/"))

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.data["vehicles"]), 1)
        row = response.data["vehicles"][0]
        for private_field in (
            "purchase_cost", "vehicle_expense_cost", "total_vehicle_cost",
            "sale_price", "actual_net_collection", "buyer_receivable",
            "buyer_refund_payable", "calculated_result",
            "investor_share_percentage_snapshot",
        ):
            self.assertNotIn(private_field, row)

        history = self.client.get(self.path("portal/self/fund-history/"))
        self.assertEqual(history.status_code, 200, history.content)
        self.assertEqual(history.data["count"], 2)
        self.assertEqual(
            {entry["activity_type"] for entry in history.data["results"]},
            {"FUND_CREDIT", "VEHICLE_COMMITMENT"},
        )
        self.assertEqual(
            {entry["amount"] for entry in history.data["results"]},
            {"30000.00", "-30000.00"},
        )
        self.assertTrue(all(entry["branch_name"] == self.branch.name for entry in history.data["results"]))
        self.assertNotIn("OTHER-INVESTOR-SECRET", str(history.data))
        self.assertNotIn("PORTAL-PRIVATE-1", str(history.data))
        self.assertNotIn(str(self.other_investor.pk), str(history.data))
        self.assertEqual(self.client.get(self.path("portal/self/fund-history/?branch_id=foreign")).status_code, 400)

        correction = self.post(
            f"fund/credits/{credit.data['id']}/corrections/",
            {"to_investor_id": str(self.other_investor.pk), "reason": "Corrected Investor attribution."},
        )
        self.assertEqual(correction.status_code, 201, correction.content)
        self.client.force_authenticate(user=self.investor_user)
        old_owner_profile = self.client.get(self.path("portal/self/"))
        self.assertEqual(old_owner_profile.status_code, 200, old_owner_profile.content)
        self.assertEqual(old_owner_profile.data["fund_position"]["status"], "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(
            {key: old_owner_profile.data["fund_position"][key] for key in (
                "credit_total", "principal_return_total", "committed_vehicle_total",
                "use_adjustment_total", "ledger_available_amount",
            )},
            {key: None for key in (
                "credit_total", "principal_return_total", "committed_vehicle_total",
                "use_adjustment_total", "ledger_available_amount",
            )},
        )

        self.client.force_authenticate(user=self.accountant)
        self.post(
            f"investors/{self.other_investor.pk}/portal-binding/",
            {"account_id": str(self.other_investor_user.pk)},
        )
        self.client.force_authenticate(user=self.other_investor_user)
        new_owner_profile = self.client.get(self.path("portal/self/"))
        self.assertEqual(new_owner_profile.status_code, 200, new_owner_profile.content)
        self.assertEqual(new_owner_profile.data["fund_position"]["status"], "MANUAL_REVIEW_REQUIRED")
        self.assertIsNone(new_owner_profile.data["fund_position"]["ledger_available_amount"])

    def test_investor_fund_history_is_server_paginated(self):
        cash = AccountingAccount.objects.create(
            tenant=self.company, account_type=AccountingAccount.AccountType.CASH,
            label="Portal history paging cash", created_by=self.accountant,
        )
        self.client.force_authenticate(user=self.accountant)
        for index in range(21):
            credit = self.client.post(
                self.path("fund/credits/"),
                {"investor_id": str(self.investor.pk), "branch_id": str(self.branch.pk),
                 "account_id": str(cash.pk), "amount": "1.00", "reference": f"PAGE-{index:02d}",
                 "effective_at": timezone.now().isoformat()},
                format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            )
            self.assertEqual(credit.status_code, 201, credit.content)
        self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.client.force_authenticate(user=self.investor_user)

        first = self.client.get(self.path("portal/self/fund-history/"))
        second = self.client.get(self.path("portal/self/fund-history/?page=2"))

        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(first.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertIsNotNone(first.data["next"])
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNotNone(second.data["previous"])

    def test_profit_calendar_is_company_accountant_managed_and_versioned(self):
        self.client.force_authenticate(user=self.accountant)
        path = self.path(f"investors/{self.investor.pk}/profit-calendar-configurations/")

        created = self.client.post(
            path,
            {"effective_start": "2026-01-15", "duration_months": 6},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )

        created_data = created.json()
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created_data["effective_start"], "2026-01-15")
        self.assertEqual(created_data["duration_months"], 6)
        listed = self.client.get(path)
        self.assertEqual(listed.status_code, 200, listed.data)
        self.assertEqual(len(listed.data), 1)
        self.assertEqual(listed.data[0]["id"], created_data["id"])

        off_boundary = self.client.post(
            path,
            {"effective_start": "2026-10-01", "duration_months": 12},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(off_boundary.status_code, 409, off_boundary.content)
        next_period = self.client.post(
            path,
            {"effective_start": "2026-07-15", "duration_months": 12},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(next_period.status_code, 201, next_period.content)
        self.assertEqual(next_period.data["version"], 1)
        self.assertEqual(self.client.get(path).data[1]["effective_start"], "2026-07-15")

        self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.client.force_authenticate(user=self.investor_user)
        profile = self.client.get(self.path("portal/self/"))
        self.assertEqual(profile.status_code, 200, profile.content)
        self.assertEqual(profile.data["profit_calendar"]["status"], "CONFIGURED")
        self.assertEqual(profile.data["profit_calendar"]["start_date"], "2026-07-15")
        self.assertEqual(profile.data["profit_calendar"]["duration_months"], 12)

        self.client.force_authenticate(user=self.branch_accountant)
        denied = self.client.post(
            path,
            {"effective_start": "2026-07-15", "duration_months": 12},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(denied.status_code, 403)

    def test_profit_period_projection_is_company_scoped_and_read_only(self):
        self.client.force_authenticate(user=self.accountant)
        path = self.path(f"investors/{self.investor.pk}/profit-periods/")

        response = self.client.get(path)

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data["investor_id"], str(self.investor.pk))
        self.assertEqual(response.data["periods"], [])
        self.assertEqual(response.data["status"], "CALENDAR_NOT_AVAILABLE")
        self.assertEqual(self.client.get(path + "?branch_id=unexpected").status_code, 400)
        self.client.force_authenticate(user=self.branch_accountant)
        self.assertEqual(self.client.get(path).status_code, 403)
        self.client.force_authenticate(user=self.investor_user)
        self.assertEqual(self.client.get(path).status_code, 403)

    def test_binding_uniqueness_revocation_and_role_revocation(self):
        path = f"investors/{self.investor.pk}/portal-binding/"
        first = self.post(path, {"account_id": str(self.investor_user.pk)})
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(
            self.post(path, {"account_id": str(self.other_investor_user.pk)}).status_code, 409
        )
        self.assertEqual(
            self.post(f"investors/{self.other_investor.pk}/portal-binding/",
                      {"account_id": str(self.investor_user.pk)}).status_code, 409
        )
        self.client.force_authenticate(user=self.investor_user)
        self.assertEqual(self.client.get(self.path("portal/self/")).status_code, 200)
        grant = CompanyRoleGrant.objects.get(
            membership__user=self.investor_user, role="investor", effective_until__isnull=True
        )
        grant.effective_until = timezone.now()
        grant.save(update_fields=("effective_until",))
        self.assertEqual(self.client.get(self.path("portal/self/")).status_code, 404)
        CompanyRoleGrant.objects.create(
            membership=grant.membership, role="investor", assigned_by=self.accountant,
        )
        ended = self.post(f"portal-bindings/{first.data['id']}/revoke/", {"reason": "Access ended"})
        self.assertEqual(ended.status_code, 200, ended.content)
        self.assertEqual(self.client.get(self.path("portal/self/")).status_code, 404)
        self.assertIsNotNone(InvestorAccountBinding.objects.get(pk=first.data["id"]).effective_until)

    def test_branch_accountant_foreign_account_and_module_off_are_denied(self):
        path = f"investors/{self.investor.pk}/portal-binding/"
        branch = self.post(path, {"account_id": str(self.investor_user.pk)}, self.branch_accountant)
        self.assertEqual(branch.status_code, 403)
        foreign_user = make_user("portal-foreign-user", role="investor", tenant=self.other_company)
        foreign = self.post(path, {"account_id": str(foreign_user.pk)})
        self.assertEqual(foreign.status_code, 404)
        first = self.post(path, {"account_id": str(self.investor_user.pk)})
        self.assertEqual(first.status_code, 201, first.content)
        CompanyModuleState.objects.create(
            tenant=self.company, module_code="investor_portal", state="disabled", version=2,
            effective_from=timezone.now(), changed_by=self.accountant,
        )
        self.client.force_authenticate(user=self.investor_user)
        self.assertEqual(self.client.get(self.path("portal/self/")).status_code, 404)
        blocked = self.post(
            f"investors/{self.other_investor.pk}/portal-binding/",
            {"account_id": str(self.other_investor_user.pk)},
        )
        self.assertEqual(blocked.status_code, 403)

    def test_investor_exit_request_requires_terms_and_accountant_approves_cancellation(self):
        bound = self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.assertEqual(bound.status_code, 201, bound.content)
        rejected_terms = self.post(
            "portal/self/exit-requests/", {"terms_accepted": False}, actor=self.investor_user,
        )
        self.assertEqual(rejected_terms.status_code, 400)

        created = self.post(
            "portal/self/exit-requests/",
            {"terms_accepted": True, "investor_id": str(self.other_investor.pk)},
            actor=self.investor_user,
        )
        self.assertEqual(created.status_code, 201, created.content)
        request = InvestorExitRequest.objects.get(pk=created.data["id"])
        self.assertEqual(request.investor_id, self.investor.pk)
        self.assertEqual(created.data["status"], "REQUESTED")
        self.assertEqual(len(created.data["history"]), 1)

        duplicate = self.post(
            "portal/self/exit-requests/", {"terms_accepted": True}, actor=self.investor_user,
        )
        self.assertEqual(duplicate.status_code, 409)

        cancellation = self.post(
            f"portal/self/exit-requests/{request.pk}/cancellation/",
            {"reason": "Changed my mind"}, actor=self.investor_user,
        )
        self.assertEqual(cancellation.status_code, 200, cancellation.content)
        self.assertEqual(cancellation.data["status"], "CANCELLATION_PENDING")

        review_path = f"investors/{self.investor.pk}/exit-requests/{request.pk}/cancellation-review/"
        denied = self.post(review_path, {"approve": True}, actor=self.branch_accountant)
        self.assertEqual(denied.status_code, 403)
        approved = self.post(review_path, {"approve": True, "reason": "Approved"})
        self.assertEqual(approved.status_code, 200, approved.content)
        self.assertEqual(approved.data["status"], "CANCELLED")
        self.assertEqual(InvestorExitRequestHistory.objects.filter(exit_request=request).count(), 3)
        self.client.force_authenticate(user=self.investor_user)
        self.assertEqual(self.client.get(self.path("portal/self/")).status_code, 200)

    def test_exit_settlement_review_is_company_accountant_only_and_company_scoped(self):
        bound = self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.assertEqual(bound.status_code, 201, bound.content)
        self.client.force_authenticate(user=self.investor_user)
        created = self.post("portal/self/exit-requests/", {"terms_accepted": True}, actor=self.investor_user)
        self.assertEqual(created.status_code, 201, created.content)
        request_id = created.data["id"]
        suffix = f"investors/{self.investor.pk}/exit-requests/{request_id}/settlement/"

        self.client.force_authenticate(user=self.accountant)
        review = self.client.get(self.path(suffix))
        self.assertEqual(review.status_code, 200, review.content)
        self.assertIn("EXIT_NOTICE_NOT_EXPIRED", review.data["blockers"])
        self.assertFalse(review.data["closure_implemented"])
        self.assertEqual(review.data["settlement_order"], ["PRINCIPAL", "RESIDUAL_LOSS", "REMAINING_PROFIT", "CLOSE"])

        self.client.force_authenticate(user=self.branch_accountant)
        self.assertEqual(self.client.get(self.path(suffix)).status_code, 403)
        self.client.force_authenticate(user=self.investor_user)
        self.assertEqual(self.client.get(self.path(suffix)).status_code, 403)
        self.client.force_authenticate(user=self.accountant)
        self.assertEqual(self.client.get(self.path(
            f"investors/{self.other_investor.pk}/exit-requests/{request_id}/settlement/"
        )).status_code, 404)
        self.assertEqual(self.client.get(self.path(suffix, self.other_company)).status_code, 403)

    def test_open_exit_blocks_new_credit_and_vehicle_funding_until_cancelled(self):
        cash = AccountingAccount.objects.create(
            tenant=self.company, account_type=AccountingAccount.AccountType.CASH,
            label="Exit gate cash", created_by=self.accountant,
        )
        self.assertEqual(self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        ).status_code, 201)
        credit_body = {"investor_id": str(self.investor.pk), "branch_id": str(self.branch.pk),
                       "account_id": str(cash.pk), "amount": "10000.00",
                       "reference": "EXIT-GATE-CREDIT-1", "effective_at": timezone.now().isoformat()}
        self.assertEqual(self.post("fund/credits/", credit_body).status_code, 201)
        self.client.force_authenticate(user=self.accountant)
        vehicle = self.client.post(
            f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/",
            {"registration": "KL 11 ZZ 7211", "model": "Hatchback", "branch_id": str(self.branch.pk)},
            format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        exit_result = self.post("portal/self/exit-requests/", {"terms_accepted": True}, actor=self.investor_user)
        self.assertEqual(exit_result.status_code, 201, exit_result.content)

        def check_blocked(reference):
            credit = self.post("fund/credits/", {**credit_body, "reference": reference})
            self.assertEqual(credit.status_code, 409, credit.content)
            self.assertEqual(credit.json()["code"], "INVESTOR_EXIT_OPEN")
            self.client.force_authenticate(user=self.accountant)
            purchase = self.client.post(
                f"/api/v1/tenants/{self.company.pk}/vehicle-management/purchases/",
                {"vehicle_id": vehicle.data["id"], "branch_id": str(self.branch.pk),
                 "purchase_cost": "10000.00", "seller_name": "Seller", "investor_id": str(self.investor.pk),
                 "investor_fund_amount": "10000.00", "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
                format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            )
            self.assertEqual(purchase.status_code, 409, purchase.content)
            self.assertEqual(purchase.json()["code"], "INVESTOR_EXIT_OPEN")

        check_blocked("EXIT-GATE-CREDIT-2")
        cancellation = self.post(
            f"portal/self/exit-requests/{exit_result.data['id']}/cancellation/",
            {"reason": "Changed my mind"}, actor=self.investor_user,
        )
        self.assertEqual(cancellation.status_code, 200, cancellation.content)
        check_blocked("EXIT-GATE-CREDIT-3")
        approved = self.post(
            f"investors/{self.investor.pk}/exit-requests/{exit_result.data['id']}/cancellation-review/",
            {"approve": True, "reason": "Approved"},
        )
        self.assertEqual(approved.status_code, 200, approved.content)
        allowed = self.post("fund/credits/", {**credit_body, "reference": "EXIT-GATE-CREDIT-4"})
        self.assertEqual(allowed.status_code, 201, allowed.content)

    def test_accountant_can_reject_then_approve_cancellation_without_cash_movement(self):
        self.assertEqual(self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        ).status_code, 201)
        opened = self.post("portal/self/exit-requests/", {"terms_accepted": True}, actor=self.investor_user)
        self.assertEqual(opened.status_code, 201, opened.content)
        request_id = opened.data["id"]
        cancel_path = f"portal/self/exit-requests/{request_id}/cancellation/"
        review_path = f"investors/{self.investor.pk}/exit-requests/{request_id}/cancellation-review/"
        pending = self.post(cancel_path, {"reason": "Plans changed"}, actor=self.investor_user)
        self.assertEqual(pending.status_code, 200, pending.content)
        before = AccountMovement.objects.count()
        denied = self.post(review_path, {"approve": False}, actor=self.branch_accountant)
        self.assertEqual(denied.status_code, 403, denied.content)
        rejected = self.post(review_path, {"approve": False, "reason": "Review again"})
        self.assertEqual(rejected.status_code, 200, rejected.content)
        self.assertEqual(rejected.data["status"], "REQUESTED")
        again = self.post(cancel_path, {"reason": "Reconsider"}, actor=self.investor_user)
        self.assertEqual(again.status_code, 200, again.content)
        approved = self.post(review_path, {"approve": True, "reason": "Confirmed"})
        self.assertEqual(approved.status_code, 200, approved.content)
        self.assertEqual(approved.data["status"], "CANCELLED")
        self.assertEqual(AccountMovement.objects.count(), before)
        self.assertEqual(InvestorExitRequestHistory.objects.filter(exit_request_id=request_id).count(), 5)

    def test_company_accountant_can_extend_exit_notice_without_cash_movement(self):
        bound = self.post(
            f"investors/{self.investor.pk}/portal-binding/",
            {"account_id": str(self.investor_user.pk)},
        )
        self.assertEqual(bound.status_code, 201, bound.content)
        exit_response = self.post("portal/self/exit-requests/", {"terms_accepted": True}, actor=self.investor_user)
        self.assertEqual(exit_response.status_code, 201, exit_response.content)
        request_id = exit_response.data["id"]
        list_path = self.path(f"investors/{self.investor.pk}/exit-requests/")
        self.client.force_authenticate(user=self.branch_accountant)
        self.assertEqual(self.client.get(list_path).status_code, 403)
        self.client.force_authenticate(user=self.accountant)
        listed = self.client.get(list_path)
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(listed.data["results"][0]["id"], request_id)
        path = f"investors/{self.investor.pk}/exit-requests/{request_id}/notice-extensions/"
        new_deadline = timezone.now() + timedelta(days=150)
        data = {"deadline": new_deadline.isoformat(), "reason": "Vehicle collection remains open"}
        before = AccountMovement.objects.count()
        denied = self.post(path, data, actor=self.branch_accountant)
        self.assertEqual(denied.status_code, 403, denied.content)
        denied_investor = self.post(path, data, actor=self.investor_user)
        self.assertEqual(denied_investor.status_code, 403, denied_investor.content)
        invalid = self.post(path, {**data, "deadline": timezone.now().isoformat()})
        self.assertEqual(invalid.status_code, 409, invalid.content)
        self.client.force_authenticate(user=self.accountant)
        extension = self.client.post(self.path(path), data, format="json", HTTP_IDEMPOTENCY_KEY="exit-extension-idempotent")
        self.assertEqual(extension.status_code, 201, extension.content)
        replay = self.client.post(self.path(path), data, format="json", HTTP_IDEMPOTENCY_KEY="exit-extension-idempotent")
        self.assertEqual(replay.status_code, 201, replay.content)
        self.assertEqual(replay.data["id"], extension.data["id"])
        self.assertEqual(InvestorExitNoticeExtension.objects.filter(exit_request_id=request_id).count(), 1)
        self.assertEqual(extension.data["version"], 1)
        self.assertEqual(extension.data["reason"], data["reason"])
        self.assertEqual(AccountMovement.objects.count(), before)
        self.client.force_authenticate(user=self.investor_user)
        profile = self.client.get(self.path("portal/self/"))
        self.assertEqual(profile.status_code, 200, profile.content)
        self.assertEqual(profile.data["exit_requests"][0]["notice_extensions"][0]["id"], extension.data["id"])
        self.assertEqual(profile.data["exit_requests"][0]["status"], "REQUESTED")
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorExitNoticeExtension.objects.filter(pk=extension.data["id"]).update(reason="forged")
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorExitRequest.objects.filter(pk=request_id).update(created_at=timezone.now() - timedelta(days=20))
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorExitNoticeExtension.objects.create(
                tenant=self.other_company, exit_request_id=request_id, version=2,
                previous_deadline=new_deadline, deadline=new_deadline + timedelta(days=10),
                reason="Cross-company extension", actor=self.accountant,
                investment_module_revision=CompanyModuleState.objects.get(tenant=self.company, module_code="investment"),
            )
        second = self.post(path, {"deadline": (new_deadline + timedelta(days=20)).isoformat(), "reason": "Further extension"})
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(second.data["version"], 2)
        self.assertEqual(second.data["previous_deadline"], extension.data["deadline"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            third = InvestorExitNoticeExtension.objects.create(
                tenant=self.company, exit_request_id=request_id, version=3,
                previous_deadline=new_deadline + timedelta(days=20),
                deadline=new_deadline + timedelta(days=30), reason="Review",
                actor=self.accountant,
                investment_module_revision=CompanyModuleState.objects.get(tenant=self.company, module_code="investment"),
            )
            record_event(action="investment.exit.notice.extend", actor=self.accountant, subject=self.accountant,
                         company=self.company, resource=third, reason="Review",
                         metadata={"exit_request_id": str(request_id), "extension_id": str(third.pk),
                                   "investor_id": str(self.investor.pk), "version": 3,
                                   "previous_deadline": third.previous_deadline.isoformat(),
                                   "deadline": (new_deadline + timedelta(days=40)).isoformat()})
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_database_rejects_cross_company_binding_even_with_valid_foreign_keys(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InvestorAccountBinding.objects.create(
                tenant=self.company, investor=self.foreign_investor,
                account=self.investor_user, bound_by=self.accountant,
            )
