from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.garage.models import GarageJob
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle


class VehicleRegisterProjectionApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Register Co", slug="p9-register-co")
        self.other_company = Tenant.objects.create(name="Other Register Co", slug="p9-register-other")
        self.branch_a = Branch.objects.create(tenant=self.company, name="Central")
        self.branch_b = Branch.objects.create(tenant=self.company, name="West")
        self.other_branch = Branch.objects.create(tenant=self.other_company, name="Foreign")
        self.company_accountant = make_user("p9-register-accountant", role="accountant", tenant=self.company)
        self.branch_accountant = make_user("p9-register-branch-accountant", tenant=self.company)
        self.media_user = make_user("p9-register-media", role="media", tenant=self.company)
        membership = self.branch_accountant.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch_b,
            assigned_by=self.company_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch_b,
            assigned_by=self.company_accountant,
        )
        self.revisions = {
            code: CompanyModuleState.objects.create(
                tenant=self.company,
                module_code=code,
                state=CompanyModuleState.State.ENABLED,
                version=1,
                effective_from=timezone.now(),
                changed_by=self.company_accountant,
            )
            for code in ("vehicle_management", "accounting", "investment", "garage")
        }
        self.client = APIClient()

    def path(self, suffix, company=None):
        return f"/api/v1/tenants/{(company or self.company).pk}/vehicle-management/{suffix}"

    def post(self, suffix, data, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(self.path(suffix), data, format="json", HTTP_IDEMPOTENCY_KEY=key)

    def create_vehicle(self, registration, branch=None):
        branch = branch or self.branch_a
        response = self.post(
            "vehicles/",
            {"registration": registration, "model": "Jeep Wrangler", "branch_id": str(branch.pk)},
            f"register-vehicle-{registration}",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Vehicle.objects.get(pk=response.data["id"])

    def test_projection_uses_purchase_correction_and_external_jobs_without_double_counting(self):
        vehicle = self.create_vehicle("KL11REG9001")
        purchase = self.post("purchases/", {
            "vehicle_id": str(vehicle.pk), "branch_id": str(self.branch_a.pk),
            "purchase_cost": "10000.00", "seller_name": "North Motors",
            "investor_id": None, "investor_fund_amount": "0.00", "running_capital_amount": "10000.00",
        }, "register-purchase")
        self.assertEqual(purchase.status_code, 201, purchase.content)
        corrected = self.post(
            f"purchases/{purchase.data['id']}/corrections/",
            {"purchase_cost": "9000.00", "reason": "Corrected seller price"},
            "register-purchase-correction",
        )
        self.assertEqual(corrected.status_code, 201, corrected.content)
        expense = self.post(
            f"vehicles/{vehicle.pk}/expenses/",
            {"amount": "500.00", "description": "Workshop parts", "investor_id": None,
             "investor_fund_amount": "0.00", "running_capital_amount": "500.00"},
            "register-expense",
        )
        self.assertEqual(expense.status_code, 201, expense.content)
        for index, status in enumerate((GarageJob.Status.OPEN, GarageJob.Status.OPEN), start=1):
            GarageJob.objects.create(
                tenant=self.company,
                branch=self.branch_a,
                vehicle=vehicle,
                context=GarageJob.Context.EXTERNAL_CUSTOMER,
                contact_name=f"Customer {index}",
                status=status,
                created_by=self.company_accountant,
                module_revision=self.revisions["garage"],
            )

        self.client.force_authenticate(user=self.company_accountant)
        response = self.client.get(self.path("register-summary/"))

        self.assertEqual(response.status_code, 200, response.content)
        row = response.data["results"][0]
        self.assertEqual(row["id"], str(vehicle.pk))
        self.assertEqual(row["contexts"], ["STOCK", "EXTERNAL_CUSTOMER"])
        self.assertEqual(row["status"], "IN_SERVICE")
        self.assertEqual(row["customer_job_count"], 2)
        self.assertEqual(row["customer_contact"], "Multiple jobs")
        self.assertEqual(row["total_cost"], "9500.00")
        self.assertTrue(row["financial_available"])
        self.assertEqual(response.data["summary"]["stock_count"], 1)
        self.assertEqual(response.data["summary"]["customer_count"], 1)
        self.assertEqual(response.data["summary"]["customer_jobs"], 2)
        self.assertEqual(response.data["summary"]["open_customer_jobs"], 2)
        self.assertEqual(response.data["summary"]["completed_customer_jobs"], 0)
        self.assertEqual(response.data["summary"]["stock_total_cost"], "9500.00")

        in_work = self.client.get(self.path("register-summary/?status=in_work"))
        self.assertEqual(in_work.status_code, 200, in_work.content)
        self.assertEqual(in_work.data["count"], 1)
        customer_in_work = self.client.get(self.path("register-summary/?context=customer&status=in_work"))
        self.assertEqual(customer_in_work.status_code, 200, customer_in_work.content)
        self.assertEqual(customer_in_work.data["count"], 1)
        stock_in_work = self.client.get(self.path("register-summary/?context=stock&status=in_work"))
        self.assertEqual(stock_in_work.status_code, 200, stock_in_work.content)
        self.assertEqual(stock_in_work.data["count"], 0)

    def test_branch_and_role_scope_hide_other_branch_finance_and_source_context(self):
        vehicle = self.create_vehicle("KL11REG9002", self.branch_a)
        purchase = self.post("purchases/", {
            "vehicle_id": str(vehicle.pk), "branch_id": str(self.branch_a.pk),
            "purchase_cost": "10000.00", "seller_name": "Private Seller",
            "investor_id": None, "investor_fund_amount": "0.00", "running_capital_amount": "10000.00",
        }, "register-scope-purchase")
        self.assertEqual(purchase.status_code, 201, purchase.content)
        moved = self.post(
            f"vehicles/{vehicle.pk}/branch-movements/",
            {"to_branch_id": str(self.branch_b.pk), "reason": "Operational move"},
            "register-scope-move",
        )
        self.assertEqual(moved.status_code, 201, moved.content)
        self.client.force_authenticate(user=self.branch_accountant)
        response = self.client.get(self.path(f"register-summary/?branch_id={self.branch_b.pk}"))

        self.assertEqual(response.status_code, 200, response.content)
        row = response.data["results"][0]
        self.assertEqual(row["id"], str(vehicle.pk))
        self.assertFalse(row["financial_available"])
        self.assertIsNone(row["total_cost"])
        self.assertEqual(row["contexts"], [])
        self.assertIsNone(row["customer_contact"])
        self.assertIsNone(response.data["summary"]["stock_total_cost"])

        self.client.force_authenticate(user=self.media_user)
        denied = self.client.get(self.path("register-summary/"))
        self.assertIn(denied.status_code, (403, 404), denied.content)

        self.client.force_authenticate(user=self.company_accountant)
        cross_company = self.client.get(self.path("register-summary/", self.other_company))
        self.assertIn(cross_company.status_code, (403, 404), cross_company.content)

    def test_projection_paginates_and_filters_only_authorized_company_vehicles(self):
        for index in range(21):
            self.create_vehicle(f"KL11PAGE{index:03d}", self.branch_a)

        self.client.force_authenticate(user=self.company_accountant)
        first = self.client.get(self.path("register-summary/?page=1"))
        second = self.client.get(self.path("register-summary/?page=2"))

        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(first.data["count"], 21)
        self.assertEqual(len(first.data["results"]), 20)
        self.assertIsNotNone(first.data["next"])
        self.assertEqual(len(second.data["results"]), 1)
        self.assertIsNotNone(second.data["previous"])

