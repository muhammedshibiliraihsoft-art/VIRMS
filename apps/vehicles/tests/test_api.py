from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.audit import record_event
from apps.accounts.tests.test_users import make_user
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle, VehicleBranchMovement


class VehicleApiTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="p5-vehicle-north")
        self.other_company = Tenant.objects.create(name="South", slug="p5-vehicle-south")
        self.branch_a = Branch.objects.create(tenant=self.company, name="Central")
        self.branch_b = Branch.objects.create(tenant=self.company, name="West")
        self.other_branch = Branch.objects.create(tenant=self.other_company, name="Other")
        self.company_accountant = make_user(
            "p5-vehicle-company-accountant", role="accountant", tenant=self.company
        )
        self.branch_accountant = make_user("p5-vehicle-branch-accountant", tenant=self.company)
        self.owner = make_user("p5-vehicle-owner", role="owner", tenant=self.company)
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
        CompanyModuleState.objects.create(
            tenant=self.company,
            module_code="vehicle_management",
            state=CompanyModuleState.State.ENABLED,
            version=1,
            effective_from=timezone.now(),
            changed_by=self.company_accountant,
        )
        self.client = APIClient()

    def path(self, suffix):
        return f"/api/v1/tenants/{self.company.pk}/vehicle-management/{suffix}"

    def post(self, suffix, data, key, user=None):
        self.client.force_authenticate(user=user or self.company_accountant)
        return self.client.post(
            self.path(suffix), data, format="json", HTTP_IDEMPOTENCY_KEY=key
        )

    def create_vehicle_record(self, company, branch, registration, model, actor):
        vehicle = Vehicle.objects.create(
            tenant=company,
            current_branch=branch,
            registration=registration,
            model=model,
            created_by=actor,
            updated_by=actor,
        )
        record_event(
            action="vehicle.create",
            actor=actor,
            subject=actor,
            company=company,
            branch=branch,
            resource=vehicle,
            metadata={
                "vehicle_id": str(vehicle.pk),
                "new_registration": vehicle.registration,
                "new_model": vehicle.model,
                "branch_id": str(branch.pk),
            },
        )
        return vehicle

    def test_vehicle_identity_normalizes_registration_and_is_idempotent(self):
        body = {
            "registration": " kl 11 ab 4821 ",
            "model": "Jeep Wrangler",
            "branch_id": str(self.branch_a.pk),
        }
        first = self.post("vehicles/", body, "vehicle-create", self.branch_accountant)
        retry = self.post("vehicles/", body, "vehicle-create", self.branch_accountant)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(retry.status_code, 201, retry.content)
        self.assertEqual(first.data["id"], retry.data["id"])
        vehicle = Vehicle.objects.get(pk=first.data["id"])
        self.assertEqual(vehicle.registration, "kl 11 ab 4821")
        self.assertEqual(vehicle.normalized_registration, "KL11AB4821")

    def test_active_registration_is_unique_per_company_only(self):
        self.create_vehicle_record(
            self.company,
            self.branch_a,
            "KL 11 AB 4821",
            "Jeep Wrangler",
            self.company_accountant,
        )
        duplicate = self.post(
            "vehicles/",
            {
                "registration": "kl11ab4821",
                "model": "Other model",
                "branch_id": str(self.branch_a.pk),
            },
            "vehicle-duplicate",
            self.company_accountant,
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.content)
        other = self.create_vehicle_record(
            self.other_company,
            self.other_branch,
            "KL11AB4821",
            "Other company vehicle",
            self.company_accountant,
        )
        self.assertIsNotNone(other.pk)

    def test_branch_accountant_cannot_create_for_other_branch_or_move_vehicle(self):
        wrong_branch = self.post(
            "vehicles/",
            {
                "registration": "KL11AB9999",
                "model": "Jeep",
                "branch_id": str(self.branch_b.pk),
            },
            "vehicle-cross-branch",
            self.branch_accountant,
        )
        self.assertIn(wrong_branch.status_code, (403, 404), wrong_branch.content)
        vehicle = self.create_vehicle_record(
            self.company,
            self.branch_a,
            "KL11AB9000",
            "Jeep",
            self.company_accountant,
        )
        move = self.post(
            f"vehicles/{vehicle.pk}/branch-movements/",
            {"to_branch_id": str(self.branch_b.pk), "reason": "Transfer"},
            "vehicle-move-denied",
            self.branch_accountant,
        )
        self.assertEqual(move.status_code, 403, move.content)
        self.assertEqual(vehicle.branch_movements.count(), 0)

    def test_company_accountant_move_appends_history_and_keeps_vehicle_uuid(self):
        vehicle = self.create_vehicle_record(
            self.company,
            self.branch_a,
            "KL11AB9001",
            "Jeep",
            self.company_accountant,
        )
        response = self.post(
            f"vehicles/{vehicle.pk}/branch-movements/",
            {"to_branch_id": str(self.branch_b.pk), "reason": "Operational move"},
            "vehicle-move",
        )
        self.assertEqual(response.status_code, 201, response.content)
        vehicle.refresh_from_db()
        self.assertEqual(str(vehicle.pk), response.data["vehicle_id"])
        self.assertEqual(vehicle.current_branch_id, self.branch_b.pk)
        movement = VehicleBranchMovement.objects.get(vehicle=vehicle)
        self.assertEqual(movement.from_branch_id, self.branch_a.pk)
        self.assertEqual(movement.to_branch_id, self.branch_b.pk)

    def test_owner_cannot_mutate_and_wrong_company_id_is_hidden(self):
        denied = self.post(
            "vehicles/",
            {
                "registration": "KL11AB9002",
                "model": "Jeep",
                "branch_id": str(self.branch_a.pk),
            },
            "vehicle-owner-denied",
            self.owner,
        )
        self.assertEqual(denied.status_code, 403, denied.content)
        self.client.force_authenticate(user=self.company_accountant)
        wrong_company = self.client.get(
            f"/api/v1/tenants/{self.other_company.pk}/vehicle-management/vehicles/"
        )
        self.assertIn(wrong_company.status_code, (403, 404), wrong_company.content)

    def test_database_rejects_deactivation_and_registration_normalization_drift(self):
        vehicle = self.create_vehicle_record(
            self.company,
            self.branch_a,
            "KL 11 AB 9100",
            "Jeep",
            self.company_accountant,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vehicle.objects.filter(pk=vehicle.pk).update(is_active=False)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vehicle.objects.filter(pk=vehicle.pk).update(registration="KL 11 AB 9101")
        vehicle.refresh_from_db()
        self.assertTrue(vehicle.is_active)
        self.assertEqual(vehicle.registration, "KL 11 AB 9100")
        self.assertEqual(vehicle.normalized_registration, "KL11AB9100")
