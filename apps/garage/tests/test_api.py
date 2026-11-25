from rest_framework.test import APIClient

from apps.garage.tests.test_integrity import GarageIntegrityTests
from apps.accounts.tests.test_users import make_user
from apps.tenants.models import BranchAssignment, CompanyModuleState
from django.utils import timezone
from django.db import IntegrityError, connection, transaction
from unittest.mock import patch
from apps.vehicles.models import VehicleExpense
from apps.garage.services import create_stock_cost
from apps.accounting.models import AccountingAccount, AccountingEvent, AccountMovement


class GarageApiTests(GarageIntegrityTests):
    def setUp(self):
        super().setUp()
        membership = self.actor.tenant_memberships.get(tenant=self.company)
        BranchAssignment.objects.create(membership=membership, branch=self.branch, assigned_by=self.actor)
        self.client = APIClient()
        self.client.force_authenticate(user=self.actor)
        self.url = f"/api/v1/tenants/{self.company.pk}/garage/jobs/"

    def test_dashboard_summary_is_full_scoped_and_does_not_page_job_rows(self):
        from apps.garage.models import GarageJob

        self.job()
        GarageJob.objects.create(
            tenant=self.company, branch=self.branch, vehicle=self.vehicle,
            context="STOCK", created_by=self.actor, module_revision=self.revision,
        )
        response = self.client.get(f"{self.url}dashboard-summary/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.data,
            {
                "company_id": str(self.company.pk),
                "branch_id": None,
                "total_jobs": 2,
                "open_jobs": 2,
                "completed_jobs": 0,
                "external_customer_jobs": 1,
            },
        )
        scoped = self.client.get(f"{self.url}dashboard-summary/?branch_id={self.branch.pk}")
        self.assertEqual(scoped.status_code, 200, scoped.content)
        self.assertEqual(scoped.data["open_jobs"], 2)
        cross_company = self.client.get(f"{self.url}dashboard-summary/?branch_id={self.other_branch.pk}")
        self.assertEqual(cross_company.status_code, 404, cross_company.content)

    def test_unlinked_customer_cost_refund_event_fails_deferred_guard(self):
        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.create(tenant=self.company, branch=self.branch, event_type="GARAGE_COST_REFUND", amount="10.00", actor=self.actor, module_revision=revision, description="Unlinked refund", source_reference="unlinked-refund", effective_at=timezone.now())
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS garage_cost_refund_event_shape IMMEDIATE")

    def test_customer_cost_refund_records_one_cash_movement_and_classifies_excess(self):
        from apps.accounting.models import AccountingApplication, AccountingCategory

        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="BANK", label="Refund bank", created_by=self.actor)
        category = AccountingCategory.objects.create(tenant=self.company, kind="INCOME", label="Workshop adjustment", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="refund-cost")
        self.assertEqual(cost.status_code, 201, cost.content)
        payment = self.client.post(f"{costs}{cost.data['id']}/payments/", {"amount": "50.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="refund-payment")
        self.assertEqual(payment.status_code, 201, payment.content)

        refunds = f"{costs}{cost.data['id']}/refunds/"
        body = {"account_id": str(account.pk), "amount": "70.00", "excess_income_category_id": str(category.pk), "excess_income_description": "Workshop returned an overpayment"}
        response = self.client.post(refunds, body, format="json", HTTP_IDEMPOTENCY_KEY="refund-post")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual((response.data["amount"], response.data["applied_amount"], response.data["excess_amount"]), ("70.00", "50.00", "20.00"))

        retry = self.client.post(refunds, body, format="json", HTTP_IDEMPOTENCY_KEY="refund-post")
        self.assertEqual(retry.data, response.data)
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_COST_REFUND").count(), 1)
        refund_event = AccountingEvent.objects.get(event_type="GARAGE_COST_REFUND")
        self.assertEqual(AccountMovement.objects.filter(event=refund_event).count(), 1)
        self.assertEqual(AccountMovement.objects.get(event=refund_event).delta, 70)
        application = AccountingApplication.objects.get(source_event=refund_event)
        self.assertEqual((application.amount, application.target_event.amount, application.target_event.category_id), (20, 20, category.pk))
        self.assertEqual(self.client.get(refunds).data["results"][0]["excess_amount"], "20.00")
        listed_cost = self.client.get(costs).data["results"][0]
        self.assertEqual((listed_cost["paid"], listed_cost["refunded"], listed_cost["payable"]), ("50.00", "50.00", "100.00"))
        next_payment = self.client.post(f"{costs}{cost.data['id']}/payments/", {"amount": "100.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="refund-follow-up-payment")
        self.assertEqual(next_payment.status_code, 201, next_payment.content)
        self.assertEqual(self.client.get(costs).data["results"][0]["payable"], "0.00")

    def test_customer_cost_refund_requires_explicit_income_classification_for_excess(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Refund till", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="refund-excess-cost")
        self.client.post(f"{costs}{cost.data['id']}/payments/", {"amount": "10.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="refund-excess-payment")
        response = self.client.post(f"{costs}{cost.data['id']}/refunds/", {"account_id": str(account.pk), "amount": "20.00"}, format="json", HTTP_IDEMPOTENCY_KEY="refund-excess-unclassified")
        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(AccountingEvent.objects.filter(event_type="GARAGE_COST_REFUND").exists())
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 1)

    def test_customer_cost_refund_failure_rolls_back_and_can_retry(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Refund rollback till", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "10.00"}, format="json", HTTP_IDEMPOTENCY_KEY="refund-rollback-cost")
        self.client.post(f"{costs}{cost.data['id']}/payments/", {"amount": "10.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="refund-rollback-payment")
        body = {"account_id": str(account.pk), "amount": "10.00"}
        refund_url = f"{costs}{cost.data['id']}/refunds/"
        with patch("apps.garage.services.GarageCustomerCostRefund.objects.create", side_effect=RuntimeError("refund link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(refund_url, body, format="json", HTTP_IDEMPOTENCY_KEY="refund-rollback")
        self.assertFalse(AccountingEvent.objects.filter(event_type="GARAGE_COST_REFUND").exists())
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 1)
        self.assertEqual(self.client.get(refund_url).data["count"], 0)
        retried = self.client.post(refund_url, body, format="json", HTTP_IDEMPOTENCY_KEY="refund-rollback")
        self.assertEqual(retried.status_code, 201, retried.content)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 2)

    def test_refund_preview_is_scoped_and_does_not_post_cash(self):
        from decimal import Decimal
        from rest_framework.exceptions import NotFound
        from apps.garage.services import preview_customer_cost_refund

        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Preview till", created_by=self.actor)
        job = self.job()
        url = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(url, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="preview-cost")
        paid = self.client.post(f"{url}{cost.data['id']}/payments/", {"amount": "50.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="preview-payment")
        self.assertEqual(paid.status_code, 201, paid.content)
        preview = preview_customer_cost_refund(actor=self.actor, company_id=self.company.pk, job_id=job.pk, cost_id=cost.data["id"], amount=Decimal("70.00"))
        self.assertEqual((preview["applied_amount"], preview["excess_amount"]), ("50.00", "20.00"))
        preview_url = f"{url}{cost.data['id']}/refund-preview/"
        response = self.client.get(preview_url, {"amount": "70.00"})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data, preview)
        self.assertEqual(self.client.get(preview_url + "?amount=1&amount=2").status_code, 400)
        self.assertEqual(self.client.get(preview_url, {"amount": "0"}).status_code, 400)
        outsider = make_user("preview-other-company", role="accountant", tenant=self.other)
        self.client.force_authenticate(user=outsider)
        self.assertEqual(self.client.get(preview_url, {"amount": "70.00"}).status_code, 403)
        self.client.force_authenticate(user=self.actor)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 1)
        with self.assertRaises(NotFound):
            preview_customer_cost_refund(actor=self.actor, company_id=self.company.pk, job_id=job.pk, cost_id=self.other.pk, amount=Decimal("1.00"))

    def test_customer_cost_refund_rejects_wrong_accounting_event_type(self):
        from apps.garage.models import GarageCustomerCost, GarageCustomerCostRefund

        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        job = self.job()
        cost = GarageCustomerCost.objects.create(job=job, description="Parts", amount="10.00", actor=self.actor, module_revision=self.revision)
        event = AccountingEvent.objects.create(tenant=self.company, branch=self.branch, event_type="INCOME", amount="10.00", actor=self.actor, module_revision=revision, description="Existing income", source_reference="existing", effective_at=timezone.now(), category=self._refund_test_category())
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageCustomerCostRefund.objects.create(cost=cost, event=event, applied_amount="10.00", actor=self.actor, module_revision=self.revision)

    def _refund_test_category(self):
        from apps.accounting.models import AccountingCategory
        return AccountingCategory.objects.create(tenant=self.company, kind="INCOME", label="Test income", created_by=self.actor)

    def test_unlinked_customer_cost_payment_fails_deferred_guard(self):
        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.create(tenant=self.company, branch=self.branch, event_type="GARAGE_COST_PAYMENT", amount="10.00", actor=self.actor, module_revision=revision, description="Payment", source_reference="unlinked-cost-payment", effective_at=timezone.now())
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_customer_cost_partial_payments_have_one_cash_effect_and_a_floor(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Cost till", created_by=self.actor)
        job = self.job()
        costs_url = f"{self.url}{job.pk}/customer-costs/"
        created = self.client.post(costs_url, {"description": "Parts", "amount": "5000.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-payment-cost")
        self.assertEqual(created.status_code, 201, created.content)
        cost_id = created.data["id"]
        pay_url = f"{costs_url}{cost_id}/payments/"
        body = {"amount": "2000.00", "account_id": str(account.pk)}
        first = self.client.post(pay_url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-payment-first")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(pay_url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-payment-first")
        self.assertEqual(retry.data, first.data)
        self.assertEqual(self.client.post(pay_url, {**body, "amount": "3000.01"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-payment-excess").status_code, 409)
        correction = self.client.post(f"{costs_url}{cost_id}/corrections/", {"amount": "1999.99", "expected_version": 0, "reason": "Correction"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-payment-floor")
        self.assertEqual(correction.status_code, 409, correction.content)
        listed = self.client.get(costs_url).data["results"][0]
        self.assertEqual((listed["paid"], listed["payable"]), ("2000.00", "3000.00"))
        self.assertEqual(self.client.get(pay_url).data["count"], 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_COST_PAYMENT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(event_id=first.data["event_id"]).delta, -2000)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def test_customer_cost_payment_link_failure_rolls_back_and_can_retry(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Rollback till", created_by=self.actor)
        job = self.job()
        cost_url = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(cost_url, {"description": "Repair", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-rollback-create")
        url = f"{cost_url}{cost.data['id']}/payments/"
        body = {"amount": "50.00", "account_id": str(account.pk)}
        with patch("apps.garage.services.GarageCustomerCostPayment.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-rollback-pay")
        self.assertFalse(AccountingEvent.objects.filter(event_type="GARAGE_COST_PAYMENT").exists())
        self.assertFalse(AccountMovement.objects.filter(account=account).exists())
        self.assertEqual(self.client.get(cost_url).data["results"][0]["payable"], "100.00")
        retried = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-rollback-pay")
        self.assertEqual(retried.status_code, 201, retried.content)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -50)

    def test_customer_cost_payment_correction_preserves_cash_history_and_balance(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Correction till", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "5000.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-create")
        self.assertEqual(cost.status_code, 201, cost.content)
        costs += f"{cost.data['id']}/"
        payment = self.client.post(costs + "payments/", {"amount": "2000.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-payment")
        self.assertEqual(payment.status_code, 201, payment.content)
        url = costs + f"payments/{payment.data['id']}/corrections/"
        body = {"expected_event_id": payment.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Correct amount", "replacement": {"account_id": str(account.pk), "amount": "1500.00", "effective_at": timezone.now().isoformat()}}
        result = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-first")
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-first").data, result.data)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-stale").status_code, 409)
        current = self.client.get(costs + "payments/").data["results"][0]
        self.assertEqual((current["amount"], current["event_id"]), ("1500.00", result.data["replacement_event_id"]))
        listed = self.client.get(f"{self.url}{job.pk}/customer-costs/").data["results"][0]
        self.assertEqual((listed["paid"], listed["payable"]), ("1500.00", "3500.00"))
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=account)), 0), -1500)
        self.assertEqual(self.client.get(url).data["count"], 1)
        void = self.client.post(url, {"expected_event_id": result.data["replacement_event_id"], "outcome": "REVERSE_ONLY", "reason": "Duplicate"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-correct-void")
        self.assertEqual(void.status_code, 201, void.content)
        self.assertTrue(self.client.get(costs + "payments/").data["results"][0]["is_void"])
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=account)), 0), 0)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def test_customer_cost_payment_correction_scope_and_rollback(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Scope till", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-scope-create")
        payment_url = costs + f"{cost.data['id']}/payments/"
        paid = self.client.post(payment_url, {"amount": "50.00", "account_id": str(account.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="cost-scope-pay")
        url = payment_url + f"{paid.data['id']}/corrections/"
        body = {"expected_event_id": paid.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Correct amount", "replacement": {"account_id": str(account.pk), "amount": "60.00", "effective_at": timezone.now().isoformat()}}
        owner = make_user("cost-correction-owner", role="owner", tenant=self.company)
        self.client.force_authenticate(user=owner)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-scope-owner").status_code, 403)
        self.client.force_authenticate(user=self.actor)
        with patch("apps.garage.services.GarageCustomerCostPaymentCorrection.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-correction-retry")
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_COST_PAYMENT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -50)
        result = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-correction-retry")
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=account)), 0), -60)

    def test_customer_cost_payment_requires_assigned_branch_and_enabled_modules(self):
        from apps.accounts.models import CompanyRoleGrant
        from apps.tenants.models import Branch

        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Branch till", created_by=self.actor)
        job = self.job()
        costs = f"{self.url}{job.pk}/customer-costs/"
        cost = self.client.post(costs, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-permission-create")
        url = costs + f"{cost.data['id']}/payments/"
        body = {"amount": "10.00", "account_id": str(account.pk)}
        other_branch = Branch.objects.create(tenant=self.company, name="Other branch")
        other_actor = make_user("cost-payment-other-branch", tenant=self.company)
        membership = other_actor.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(membership=membership, role=CompanyRoleGrant.Role.ACCOUNTANT, branch=other_branch, assigned_by=self.actor)
        BranchAssignment.objects.create(membership=membership, branch=other_branch, assigned_by=self.actor)
        self.client.force_authenticate(user=other_actor)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-other-branch").status_code, 403)
        self.client.force_authenticate(user=self.actor)
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="disabled", version=2, effective_from=timezone.now(), changed_by=self.actor)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="cost-accounting-off").status_code, 403)
        self.assertFalse(AccountingEvent.objects.filter(event_type="GARAGE_COST_PAYMENT").exists())

    def test_customer_cost_list_query_count_does_not_grow_per_cost(self):
        from django.test.utils import CaptureQueriesContext

        job = self.job()
        url = f"{self.url}{job.pk}/customer-costs/"
        first = self.client.post(url, {"description": "Parts", "amount": "100.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-queries-one")
        self.assertEqual(first.status_code, 201, first.content)
        with CaptureQueriesContext(connection) as one:
            self.assertEqual(self.client.get(url).status_code, 200)
        second = self.client.post(url, {"description": "Service", "amount": "50.00"}, format="json", HTTP_IDEMPOTENCY_KEY="cost-queries-two")
        self.assertEqual(second.status_code, 201, second.content)
        with CaptureQueriesContext(connection) as two:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(one), len(two))

    def test_create_retry_status_and_stale_version(self):
        payload = {"branch_id": str(self.branch.pk), "vehicle_id": str(self.vehicle.pk), "context": "EXTERNAL_CUSTOMER", "contact_name": "Customer"}
        first = self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="garage-create")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="garage-create")
        self.assertEqual(retry.data["id"], first.data["id"])
        status_url = self.url + first.data["id"] + "/status/"
        result = self.client.post(status_url, {"status": "COMPLETED", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="garage-complete")
        self.assertEqual(result.status_code, 200, result.content)
        stale = self.client.post(status_url, {"status": "OPEN", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="garage-stale")
        self.assertEqual(stale.status_code, 409, stale.content)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["status"], "COMPLETED")

    def test_module_off_blocks_new_job(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="garage", state="disabled", version=2, effective_from=self.revision.effective_from, changed_by=self.actor)
        payload = {"branch_id": str(self.branch.pk), "vehicle_id": str(self.vehicle.pk), "context": "EXTERNAL_CUSTOMER", "contact_name": "Customer"}
        response = self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="garage-off")
        self.assertEqual(response.status_code, 403, response.content)

    def test_owner_and_unassigned_accountant_cannot_create(self):
        payload = {"branch_id": str(self.branch.pk), "vehicle_id": str(self.vehicle.pk), "context": "EXTERNAL_CUSTOMER", "contact_name": "Customer"}
        owner = make_user("garage-api-owner", role="owner", tenant=self.company)
        self.client.force_authenticate(user=owner)
        self.assertEqual(self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="owner-job").status_code, 403)
        accountant = make_user("garage-api-unassigned", role="accountant", tenant=self.company)
        self.client.force_authenticate(user=accountant)
        self.assertEqual(self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="unassigned-job").status_code, 403)

    def test_other_company_cannot_read_jobs(self):
        user = make_user("garage-other-company", role="accountant", tenant=self.other)
        self.client.force_authenticate(user=user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_retry_rechecks_branch_assignment(self):
        payload = {"branch_id": str(self.branch.pk), "vehicle_id": str(self.vehicle.pk), "context": "EXTERNAL_CUSTOMER", "contact_name": "Customer"}
        first = self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="replay-branch")
        self.assertEqual(first.status_code, 201, first.content)
        assignment = BranchAssignment.objects.get(membership__user=self.actor, branch=self.branch)
        assignment.effective_until = timezone.now()
        assignment.save(update_fields=["effective_until", "updated_at"])
        retry = self.client.post(self.url, payload, format="json", HTTP_IDEMPOTENCY_KEY="replay-branch")
        self.assertEqual(retry.status_code, 403, retry.content)

    def test_work_retry_completion_and_reopen(self):
        job = self.job()
        work_url = f"{self.url}{job.pk}/work/"
        first = self.client.post(work_url, {"description": "Repair brakes"}, format="json", HTTP_IDEMPOTENCY_KEY="work-1")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(work_url, {"description": "Repair brakes"}, format="json", HTTP_IDEMPOTENCY_KEY="work-1")
        self.assertEqual(retry.data["id"], first.data["id"])
        detail = self.client.get(f"{self.url}{job.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(self.client.get(work_url).data["count"], 1)
        status_url = f"{self.url}{job.pk}/status/"
        completed = self.client.post(status_url, {"status": "COMPLETED", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="complete-1")
        self.assertEqual(completed.status_code, 200, completed.content)
        blocked = self.client.post(work_url, {"description": "Paint"}, format="json", HTTP_IDEMPOTENCY_KEY="work-blocked")
        self.assertEqual(blocked.status_code, 409)
        reopened = self.client.post(status_url, {"status": "OPEN", "expected_version": 1}, format="json", HTTP_IDEMPOTENCY_KEY="reopen-1")
        self.assertEqual(reopened.status_code, 200, reopened.content)
        added = self.client.post(work_url, {"description": "Paint"}, format="json", HTTP_IDEMPOTENCY_KEY="work-2")
        self.assertEqual(added.status_code, 201, added.content)
        history = self.client.get(f"{self.url}{job.pk}/status-history/")
        self.assertEqual(history.status_code, 200)
        self.assertEqual([row["to_status"] for row in history.data["results"]], ["COMPLETED", "OPEN"])

    def test_stock_cost_links_existing_expense_once(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="vehicle_management", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        job = self.job(context="STOCK")
        vehicle_url = f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/{self.vehicle.pk}/expenses/"
        expense = self.client.post(vehicle_url, {"amount": "5000.00", "description": "Repair"}, format="json", HTTP_IDEMPOTENCY_KEY="stock-expense")
        self.assertEqual(expense.status_code, 201, expense.content)
        cost_url = f"{self.url}{job.pk}/stock-costs/"
        first = self.client.post(cost_url, {"expense_id": expense.data["id"]}, format="json", HTTP_IDEMPOTENCY_KEY="link-stock-cost")
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(first.data["amount"], "5000.00")
        retry = self.client.post(cost_url, {"expense_id": expense.data["id"]}, format="json", HTTP_IDEMPOTENCY_KEY="link-stock-cost")
        self.assertEqual(retry.data["id"], first.data["id"])
        other_job = self.job(context="STOCK")
        duplicate = self.client.post(f"{self.url}{other_job.pk}/stock-costs/", {"expense_id": expense.data["id"]}, format="json", HTTP_IDEMPOTENCY_KEY="link-again")
        self.assertEqual(duplicate.status_code, 409, duplicate.content)
        self.assertEqual(self.client.get(cost_url).data["count"], 1)

    def test_stock_cost_create_is_idempotent_and_atomic(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="vehicle_management", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        job = self.job(context="STOCK")
        create_url = f"{self.url}{job.pk}/stock-costs/create/"
        body = {"amount": "2400.00", "description": "Paint"}
        first = self.client.post(create_url, body, format="json", HTTP_IDEMPOTENCY_KEY="job-create-cost")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(create_url, body, format="json", HTTP_IDEMPOTENCY_KEY="job-create-cost")
        self.assertEqual(retry.data["expense_id"], first.data["expense_id"])
        self.assertEqual(VehicleExpense.objects.filter(vehicle=self.vehicle).count(), 1)
        with patch("apps.garage.services.GarageStockCostLink.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                create_stock_cost(actor=self.actor, company_id=self.company.pk, job_id=job.pk, key="rollback-cost", path=create_url, amount="900.00", description="Repair")
        self.assertEqual(VehicleExpense.objects.filter(vehicle=self.vehicle).count(), 1)
        self.assertEqual(job.stock_cost_links.count(), 1)

    def test_customer_charge_history_and_completed_guard(self):
        job = self.job()
        url = f"{self.url}{job.pk}/charges/"
        first = self.client.post(url, {"amount": "5000.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="charge-1")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(url, {"amount": "5000.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="charge-1")
        self.assertEqual(retry.data["id"], first.data["id"])
        no_reason = self.client.post(url, {"amount": "4500.00", "expected_version": 1}, format="json", HTTP_IDEMPOTENCY_KEY="charge-no-reason")
        self.assertEqual(no_reason.status_code, 400, no_reason.content)
        corrected = self.client.post(url, {"amount": "4500.00", "expected_version": 1, "reason": "Correct bill"}, format="json", HTTP_IDEMPOTENCY_KEY="charge-2")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        self.assertEqual(self.client.get(url).data["count"], 2)
        status_url = f"{self.url}{job.pk}/status/"
        self.assertEqual(self.client.post(status_url, {"status": "COMPLETED", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="charge-complete").status_code, 200)
        blocked = self.client.post(url, {"amount": "4000.00", "expected_version": 2, "reason": "Edit"}, format="json", HTTP_IDEMPOTENCY_KEY="charge-blocked")
        self.assertEqual(blocked.status_code, 409)

    def test_customer_partial_receipts_cash_effect_cap_and_charge_floor(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Cash", created_by=self.actor)
        job = self.job()
        charges = f"{self.url}{job.pk}/charges/"
        receipts = f"{self.url}{job.pk}/receipts/"
        charge = self.client.post(charges, {"amount": "5000.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-charge")
        self.assertEqual(charge.status_code, 201, charge.content)
        body = {"account_id": str(account.pk), "amount": "2000.00", "reference": "voucher-1"}
        first = self.client.post(receipts, body, format="json", HTTP_IDEMPOTENCY_KEY="receipt-1")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(receipts, body, format="json", HTTP_IDEMPOTENCY_KEY="receipt-1")
        self.assertEqual(first.data["event_id"], retry.data["event_id"])
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="GARAGE_RECEIPT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(event_id=first.data["event_id"]).delta, 2000)
        over = self.client.post(receipts, {"account_id": str(account.pk), "amount": "3001.00", "reference": "voucher-2"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-over")
        self.assertEqual(over.status_code, 409, over.content)
        duplicate = self.client.post(receipts, {"account_id": str(account.pk), "amount": "100.00", "reference": "voucher-1"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-dup")
        self.assertEqual(duplicate.status_code, 409, duplicate.content)
        too_low = self.client.post(charges, {"amount": "1999.00", "expected_version": 1, "reason": "Correction"}, format="json", HTTP_IDEMPOTENCY_KEY="charge-low")
        self.assertEqual(too_low.status_code, 409, too_low.content)
        final = self.client.post(receipts, {"account_id": str(account.pk), "amount": "3000.00", "reference": "voucher-3"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-final")
        self.assertEqual(final.status_code, 201, final.content)
        self.assertEqual(self.client.get(receipts).data["count"], 2)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "0.00")
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="INCOME").count(), 0)

    def test_unlinked_garage_cash_event_fails_deferred_guard(self):
        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.create(tenant=self.company, branch=self.branch, event_type="GARAGE_RECEIPT", amount="100.00", actor=self.actor, module_revision=revision, description="Receipt", source_reference="orphan", effective_at=timezone.now())
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_receipt_corrections_preserve_history_and_reconcile_job_balance(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Receipt correction", created_by=self.actor)
        job = self.job()
        self.assertEqual(self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-charge").status_code, 201)
        receipts = f"{self.url}{job.pk}/receipts/"
        at = timezone.now().isoformat()
        original = self.client.post(receipts, {"account_id": str(account.pk), "amount": "40.00", "reference": "receipt-corr-ref", "effective_at": at}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-original")
        self.assertEqual(original.status_code, 201, original.content)
        url = f"{receipts}{original.data['id']}/corrections/"
        body = {"expected_event_id": original.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Incorrect amount", "replacement": {"account_id": str(account.pk), "amount": "60.00", "effective_at": at}}
        corrected = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-one")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-one").data, corrected.data)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "40.00")
        self.assertEqual(sum(row.delta for row in AccountMovement.objects.filter(account=account)), 60)
        self.assertEqual(self.client.get(receipts).data["results"][0]["amount"], "60.00")
        self.assertEqual(self.client.get(url).data["results"][0]["previous_amount"], "40.00")
        stale = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-stale")
        self.assertEqual(stale.status_code, 409)
        final = self.client.post(receipts, {"account_id": str(account.pk), "amount": "40.00", "reference": "receipt-corr-ref-2"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-next")
        self.assertEqual(final.status_code, 201, final.content)
        too_low = self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "99.00", "expected_version": 1, "reason": "Lower charge"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-charge-low")
        self.assertEqual(too_low.status_code, 409)
        too_high = self.client.post(url, {**body, "expected_event_id": corrected.data["replacement_event_id"], "replacement": {**body["replacement"], "amount": "61.00"}}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-high")
        self.assertEqual(too_high.status_code, 409)
        void = self.client.post(url, {"expected_event_id": corrected.data["replacement_event_id"], "outcome": "REVERSE_ONLY", "reason": "Receipt was duplicated"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-void")
        self.assertEqual(void.status_code, 201, void.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "60.00")
        self.assertEqual(sum(row.delta for row in AccountMovement.objects.filter(account=account)), 40)
        self.assertTrue(self.client.get(receipts).data["results"][0]["is_void"])
        repeated = self.client.post(url, {"expected_event_id": corrected.data["replacement_event_id"], "outcome": "REVERSE_ONLY", "reason": "Duplicate"}, format="json", HTTP_IDEMPOTENCY_KEY="receipt-corr-void-again")
        self.assertEqual(repeated.status_code, 409)

    def test_receipt_correction_scope_and_link_failure_rollback(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Receipt correction rollback", created_by=self.actor)
        job = self.job()
        self.assertEqual(self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-charge").status_code, 201)
        receipts = f"{self.url}{job.pk}/receipts/"
        at = timezone.now().isoformat()
        original = self.client.post(receipts, {"account_id": str(account.pk), "amount": "40.00", "reference": "corr-safe-ref", "effective_at": at}, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-receipt")
        url = f"{receipts}{original.data['id']}/corrections/"
        body = {"expected_event_id": original.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Correction", "replacement": {"account_id": str(account.pk), "amount": "50.00", "effective_at": at}}
        with patch("apps.garage.services.GarageReceiptCorrection.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-retry")
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_RECEIPT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, 40)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "60.00")
        owner = make_user("receipt-corr-owner", role="owner", tenant=self.company)
        self.client.force_authenticate(user=owner)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-owner").status_code, 403)
        unassigned = make_user("receipt-corr-unassigned", role="accountant", tenant=self.company)
        self.client.force_authenticate(user=unassigned)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-unassigned").status_code, 403)
        other = make_user("receipt-corr-other", role="accountant", tenant=self.other)
        self.client.force_authenticate(user=other)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-other").status_code, 403)
        self.client.force_authenticate(user=self.actor)
        retry = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-safe-retry")
        self.assertEqual(retry.status_code, 201, retry.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        self.assertEqual(sum(row.delta for row in AccountMovement.objects.filter(account=account)), 50)

    def test_garage_receipt_reversal_requires_typed_correction_link(self):
        from apps.accounting.services import _reverse_event
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Orphan receipt reversal", created_by=self.actor)
        job = self.job()
        self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="orphan-receipt-charge")
        original = self.client.post(f"{self.url}{job.pk}/receipts/", {"account_id": str(account.pk), "amount": "40.00", "reference": "orphan-receipt-ref"}, format="json", HTTP_IDEMPOTENCY_KEY="orphan-receipt")
        event = AccountingEvent.objects.get(pk=original.data["event_id"])
        revision = CompanyModuleState.objects.get(tenant=self.company, module_code="accounting")
        with self.assertRaises(IntegrityError), transaction.atomic():
            _reverse_event(event, actor=self.actor, revision=revision, reason="No correction source")
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(AccountMovement.objects.get(account=account).delta, 40)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "60.00")

    def test_receipt_link_failure_rolls_back_cash_and_allows_safe_retry(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Rollback receipt till", created_by=self.actor)
        job = self.job()
        self.assertEqual(self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="rollback-charge").status_code, 201)
        url = f"{self.url}{job.pk}/receipts/"
        payload = {"account_id": str(account.pk), "amount": "40.00", "reference": "rollback-reference"}
        with patch("apps.garage.services.GarageCustomerReceipt.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="rollback-receipt")
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="GARAGE_RECEIPT").count(), 0)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 0)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "100.00")
        retry = self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="rollback-receipt")
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="GARAGE_RECEIPT").count(), 1)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 1)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "60.00")

    def test_receipt_actual_date_may_be_past_but_not_future(self):
        from datetime import timedelta
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Dated receipt till", created_by=self.actor)
        job = self.job()
        self.assertEqual(self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="date-charge").status_code, 201)
        url = f"{self.url}{job.pk}/receipts/"
        past = timezone.now() - timedelta(days=7)
        body = {"account_id": str(account.pk), "amount": "40.00", "reference": "date-reference", "effective_at": past.isoformat()}
        first = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="date-receipt")
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(AccountingEvent.objects.get(pk=first.data["event_id"]).effective_at, past)
        future = self.client.post(url, {**body, "reference": "future-reference", "effective_at": (timezone.now() + timedelta(days=1)).isoformat()}, format="json", HTTP_IDEMPOTENCY_KEY="future-receipt")
        self.assertEqual(future.status_code, 400, future.content)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 1)

    def test_garage_receipt_cannot_be_corrected_through_generic_accounting_endpoints(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Receipt guard till", created_by=self.actor)
        job = self.job()
        self.assertEqual(self.client.post(f"{self.url}{job.pk}/charges/", {"amount": "100.00", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="guard-charge").status_code, 201)
        receipt = self.client.post(f"{self.url}{job.pk}/receipts/", {"account_id": str(account.pk), "amount": "40.00", "reference": "guard-reference"}, format="json", HTTP_IDEMPOTENCY_KEY="guard-receipt")
        self.assertEqual(receipt.status_code, 201, receipt.content)
        payload = {"outcome": "REVERSE_ONLY", "event_occurred": False, "reason": "Duplicate entry"}
        for resource in ("events", "receipts", "payments"):
            response = self.client.post(f"/api/v1/tenants/{self.company.pk}/accounting/{resource}/{receipt.data['event_id']}/corrections/", payload, format="json", HTTP_IDEMPOTENCY_KEY=f"guard-{resource}")
            self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(AccountingEvent.objects.filter(reversal_of_id=receipt.data["event_id"]).count(), 0)
        self.assertEqual(AccountMovement.objects.get(event_id=receipt.data["event_id"]).delta, 40)
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["outstanding"], "60.00")

    def test_external_job_cost_and_audited_correction(self):
        job = self.job()
        url = f"{self.url}{job.pk}/customer-costs/"
        first = self.client.post(url, {"description": "Brake parts", "amount": "1500.00"}, format="json", HTTP_IDEMPOTENCY_KEY="customer-cost")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(url, {"description": "Brake parts", "amount": "1500.00"}, format="json", HTTP_IDEMPOTENCY_KEY="customer-cost")
        self.assertEqual(first.data["id"], retry.data["id"])
        correction_url = f"{url}{first.data['id']}/corrections/"
        correction = self.client.post(correction_url, {"amount": "1200.00", "reason": "Invoice correction", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="customer-cost-correction")
        self.assertEqual(correction.status_code, 201, correction.content)
        self.assertEqual(self.client.get(url).data["results"][0]["amount"], "1200.00")
        self.assertEqual(self.client.get(correction_url).data["results"][0]["reason"], "Invoice correction")
        self.assertEqual(self.client.get(f"{self.url}{job.pk}/").data["customer_cost_total"], "1200.00")
        stale = self.client.post(correction_url, {"amount": "1100.00", "reason": "Old value", "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="customer-cost-stale")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 0)
        self.assertEqual(job.customer_charges.count(), 0)

    def test_labour_person_create_status_and_module_gate(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        people_url = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        payload = {"branch_id": str(self.branch.pk), "name": "Worker", "phone": ""}
        first = self.client.post(people_url, payload, format="json", HTTP_IDEMPOTENCY_KEY="labour-person")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(people_url, payload, format="json", HTTP_IDEMPOTENCY_KEY="labour-person")
        self.assertEqual(first.data["id"], retry.data["id"])
        status_url = people_url + first.data["id"] + "/status/"
        changed = self.client.post(status_url, {"is_active": False, "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="labour-inactive")
        self.assertEqual(changed.status_code, 200, changed.content)
        self.assertFalse(changed.data["is_active"])
        stale = self.client.post(status_url, {"is_active": True, "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="labour-stale")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(self.client.get(people_url).data["count"], 1)
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="disabled", version=2, effective_from=timezone.now(), changed_by=self.actor)
        blocked = self.client.post(people_url, payload, format="json", HTTP_IDEMPOTENCY_KEY="labour-off")
        self.assertEqual(blocked.status_code, 403, blocked.content)

    def test_labour_person_edit_is_scoped_versioned_and_retry_safe(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker", "phone": "123"}, format="json", HTTP_IDEMPOTENCY_KEY="edit-create")
        self.assertEqual(person.status_code, 201, person.content)
        url = f"{people}{person.data['id']}/"
        payload = {"name": "Worker Edited", "phone": "456", "expected_updated_at": person.data["updated_at"]}
        updated = self.client.patch(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="edit-worker")
        self.assertEqual(updated.status_code, 200, updated.content)
        self.assertEqual(updated.data["name"], "Worker Edited")
        self.assertEqual(updated.data["phone"], "456")
        from apps.accounts.models import AccountSecurityEvent
        audit = AccountSecurityEvent.objects.get(action="labour.person.update", resource_id=person.data["id"])
        self.assertEqual(audit.metadata["old_name"], "Worker")
        self.assertEqual(audit.metadata["new_name"], "Worker Edited")
        self.assertTrue(audit.metadata["phone_changed"])
        self.assertNotIn("456", str(audit.metadata))
        retry = self.client.patch(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="edit-worker")
        self.assertEqual(retry.data, updated.data)
        stale = self.client.patch(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="edit-stale")
        self.assertEqual(stale.status_code, 409)
        owner = make_user("labour-edit-owner", role="owner", tenant=self.company)
        self.client.force_authenticate(user=owner)
        denied = self.client.patch(url, {**payload, "expected_updated_at": updated.data["updated_at"]}, format="json", HTTP_IDEMPOTENCY_KEY="edit-owner")
        self.assertEqual(denied.status_code, 403)
        unassigned = make_user("labour-edit-unassigned", role="accountant", tenant=self.company)
        self.client.force_authenticate(user=unassigned)
        denied = self.client.patch(url, {**payload, "expected_updated_at": updated.data["updated_at"]}, format="json", HTTP_IDEMPOTENCY_KEY="edit-unassigned")
        self.assertEqual(denied.status_code, 403)
        other = make_user("labour-edit-other", role="accountant", tenant=self.other)
        self.client.force_authenticate(user=other)
        denied = self.client.patch(url, {**payload, "expected_updated_at": updated.data["updated_at"]}, format="json", HTTP_IDEMPOTENCY_KEY="edit-other")
        self.assertEqual(denied.status_code, 403)

    def test_labour_payment_is_single_cash_outflow_and_retry_safe(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Labour till", created_by=self.actor)
        people_url = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people_url, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="pay-worker")
        self.assertEqual(person.status_code, 201, person.content)
        url = people_url + person.data["id"] + "/payments/"
        payload = {"account_id": str(account.pk), "amount": "850.00", "effective_at": timezone.now().isoformat(), "note": "Daily work"}
        first = self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="labour-pay")
        self.assertEqual(first.status_code, 201, first.content)
        retry = self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="labour-pay")
        self.assertEqual(first.data["event_id"], retry.data["event_id"])
        self.assertEqual(AccountMovement.objects.get(event_id=first.data["event_id"]).delta, -850)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="LABOUR_PAYMENT").count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="EXPENSE").count(), 0)
        self.assertEqual(self.client.get(url).data["count"], 1)
        self.assertFalse(VehicleExpense.objects.filter(vehicle=self.vehicle).exists())
        status = self.client.post(people_url + person.data["id"] + "/status/", {"is_active": False, "expected_version": 0}, format="json", HTTP_IDEMPOTENCY_KEY="inactive-worker")
        self.assertEqual(status.status_code, 200, status.content)
        denied = self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="inactive-pay")
        self.assertEqual(denied.status_code, 409, denied.content)

    def test_labour_payment_correction_preserves_history_and_net_cash(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Correction till", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="correct-worker")
        payments = f"{people}{person.data['id']}/payments/"
        paid_at = timezone.now().isoformat()
        original = self.client.post(payments, {"account_id": str(account.pk), "amount": "100.00", "effective_at": paid_at}, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment")
        self.assertEqual(original.status_code, 201, original.content)
        url = f"{payments}{original.data['id']}/corrections/"
        body = {"expected_event_id": original.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Correct entered amount", "replacement": {"account_id": str(account.pk), "amount": "80.00", "effective_at": paid_at}}
        corrected = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment-1")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        retry = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment-1")
        self.assertEqual(retry.data, corrected.data)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="LABOUR_PAYMENT").count(), 3)
        self.assertEqual(sum(row.delta for row in AccountMovement.objects.filter(account=account)), -80)
        self.assertEqual(AccountingEvent.objects.get(pk=original.data["event_id"]).amount, 100)
        stale = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment-stale")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(self.client.get(payments).data["results"][0]["amount"], "80.00")
        history = self.client.get(url)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.data["results"][0]["previous_amount"], "100.00")
        self.assertEqual(history.data["results"][0]["replacement_amount"], "80.00")
        void = self.client.post(url, {"expected_event_id": corrected.data["replacement_event_id"], "outcome": "REVERSE_ONLY", "reason": "Payment did not occur"}, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment-void")
        self.assertEqual(void.status_code, 201, void.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        self.assertEqual(sum(row.delta for row in AccountMovement.objects.filter(account=account)), 0)
        self.assertTrue(self.client.get(payments).data["results"][0]["is_void"])
        repeated = self.client.post(url, {"expected_event_id": corrected.data["replacement_event_id"], "outcome": "REVERSE_ONLY", "reason": "Duplicate"}, format="json", HTTP_IDEMPOTENCY_KEY="correct-payment-void-again")
        self.assertEqual(repeated.status_code, 409)

    def test_labour_payment_correction_rollback_and_role_scope(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Correction rollback", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="corr-rollback-worker")
        payments = f"{people}{person.data['id']}/payments/"
        at = timezone.now().isoformat()
        original = self.client.post(payments, {"account_id": str(account.pk), "amount": "100.00", "effective_at": at}, format="json", HTTP_IDEMPOTENCY_KEY="corr-rollback-payment")
        url = f"{payments}{original.data['id']}/corrections/"
        body = {"expected_event_id": original.data["event_id"], "outcome": "REVERSE_AND_REPLACE", "reason": "Correction", "replacement": {"account_id": str(account.pk), "amount": "80.00", "effective_at": at}}
        with patch("apps.garage.services.LabourPaymentCorrection.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-rollback")
        self.assertEqual(AccountingEvent.objects.filter(event_type="LABOUR_PAYMENT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -100)
        owner = make_user("labour-correction-owner", role="owner", tenant=self.company)
        self.client.force_authenticate(user=owner)
        denied = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-owner")
        self.assertEqual(denied.status_code, 403)
        unassigned = make_user("labour-correction-unassigned", role="accountant", tenant=self.company)
        self.client.force_authenticate(user=unassigned)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-unassigned").status_code, 403)
        other = make_user("labour-correction-other", role="accountant", tenant=self.other)
        self.client.force_authenticate(user=other)
        self.assertEqual(self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-other").status_code, 403)
        self.client.force_authenticate(user=self.actor)
        corrected = self.client.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY="corr-rollback")
        self.assertEqual(corrected.status_code, 201, corrected.content)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute("SET CONSTRAINTS ALL DEFERRED")

    def test_labour_reversal_requires_typed_correction_link(self):
        from apps.accounting.services import _reverse_event
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Orphan reversal till", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="orphan-worker")
        original = self.client.post(f"{people}{person.data['id']}/payments/", {"account_id": str(account.pk), "amount": "100.00", "effective_at": timezone.now().isoformat()}, format="json", HTTP_IDEMPOTENCY_KEY="orphan-payment")
        event = AccountingEvent.objects.get(pk=original.data["event_id"])
        accounting_revision = CompanyModuleState.objects.get(tenant=self.company, module_code="accounting")
        with self.assertRaises(IntegrityError), transaction.atomic():
            _reverse_event(event, actor=self.actor, revision=accounting_revision, reason="No correction source")
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -100)

    def test_labour_correction_is_denied_when_labour_module_is_off(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Off correction till", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="off-correction-worker")
        payments = f"{people}{person.data['id']}/payments/"
        original = self.client.post(payments, {"account_id": str(account.pk), "amount": "100.00", "effective_at": timezone.now().isoformat()}, format="json", HTTP_IDEMPOTENCY_KEY="off-correction-payment")
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="disabled", version=2, effective_from=timezone.now(), changed_by=self.actor)
        response = self.client.post(f"{payments}{original.data['id']}/corrections/", {"expected_event_id": original.data["event_id"], "outcome": "REVERSE_ONLY", "reason": "Duplicate"}, format="json", HTTP_IDEMPOTENCY_KEY="off-correction")
        self.assertEqual(response.status_code, 403, response.content)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -100)

    def test_unlinked_labour_payment_fails_deferred_guard(self):
        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="accounting", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AccountingEvent.objects.create(tenant=self.company, branch=self.branch, event_type="LABOUR_PAYMENT", amount="100.00", actor=self.actor, module_revision=revision, description="Payment", source_reference="orphan", effective_at=timezone.now())
            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

    def test_labour_payment_link_failure_rolls_back_cash_and_allows_safe_retry(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Rollback labour till", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="rollback-worker")
        self.assertEqual(person.status_code, 201, person.content)
        url = f"{people}{person.data['id']}/payments/"
        payload = {"account_id": str(account.pk), "amount": "25.00", "effective_at": timezone.now().isoformat()}
        with patch("apps.garage.services.LabourPayment.objects.create", side_effect=RuntimeError("link failed")):
            with self.assertRaises(RuntimeError):
                self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="rollback-labour-payment")
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="LABOUR_PAYMENT").count(), 0)
        self.assertEqual(AccountMovement.objects.filter(account=account).count(), 0)
        retry = self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="rollback-labour-payment")
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company, event_type="LABOUR_PAYMENT").count(), 1)
        self.assertEqual(AccountMovement.objects.get(account=account).delta, -25)

    def test_labour_payment_cannot_be_corrected_through_generic_accounting_endpoints(self):
        for code in ("labour", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=code, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Payment guard till", created_by=self.actor)
        people = f"/api/v1/tenants/{self.company.pk}/labour/people/"
        person = self.client.post(people, {"branch_id": str(self.branch.pk), "name": "Worker"}, format="json", HTTP_IDEMPOTENCY_KEY="guard-worker")
        self.assertEqual(person.status_code, 201, person.content)
        payment = self.client.post(f"{people}{person.data['id']}/payments/", {"account_id": str(account.pk), "amount": "25.00", "effective_at": timezone.now().isoformat()}, format="json", HTTP_IDEMPOTENCY_KEY="guard-payment")
        self.assertEqual(payment.status_code, 201, payment.content)
        payload = {"outcome": "REVERSE_ONLY", "event_occurred": False, "reason": "Duplicate entry"}
        for resource in ("events", "receipts", "payments"):
            response = self.client.post(f"/api/v1/tenants/{self.company.pk}/accounting/{resource}/{payment.data['event_id']}/corrections/", payload, format="json", HTTP_IDEMPOTENCY_KEY=f"guard-pay-{resource}")
            self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(AccountingEvent.objects.filter(reversal_of_id=payment.data["event_id"]).count(), 0)
        self.assertEqual(AccountMovement.objects.get(event_id=payment.data["event_id"]).delta, -25)
