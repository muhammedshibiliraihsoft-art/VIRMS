from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.tests.test_users import make_user
from apps.accounts.audit import record_event
from apps.garage.models import GarageJob, GarageJobStatusChange, GarageWorkEntry, LabourPerson, LabourStatusChange
from apps.tenants.models import Branch, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle


class GarageIntegrityTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Garage North", slug="garage-test-north")
        self.other = Tenant.objects.create(name="Garage South", slug="garage-test-south")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.other_branch = Branch.objects.create(tenant=self.other, name="South")
        self.actor = make_user("garage-integrity-user", role="accountant", tenant=self.company)
        self.revision = CompanyModuleState.objects.create(tenant=self.company, module_code="garage", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        self.vehicle = Vehicle.objects.create(tenant=self.company, current_branch=self.branch, registration="KL123456", model="Test", created_by=self.actor, updated_by=self.actor)
        record_event(action="vehicle.create", actor=self.actor, subject=self.actor, company=self.company, branch=self.branch, resource=self.vehicle, metadata={"vehicle_id": str(self.vehicle.pk), "new_registration": self.vehicle.registration, "new_model": self.vehicle.model, "branch_id": str(self.branch.pk)})

    def job(self, **overrides):
        values = dict(tenant=self.company, branch=self.branch, vehicle=self.vehicle, context="EXTERNAL_CUSTOMER", contact_name="Customer", created_by=self.actor, module_revision=self.revision)
        values.update(overrides)
        return GarageJob.objects.create(**values)

    def test_external_customer_requires_nonblank_name(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.job(contact_name="   ")
        self.assertEqual(self.job(contact_phone="").contact_phone, "")

    def test_cross_company_branch_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.job(branch=self.other_branch)

    def test_work_is_retained_and_completed_job_rejects_work(self):
        job = self.job()
        entry = GarageWorkEntry.objects.create(job=job, description="Repair", actor=self.actor, module_revision=self.revision)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageWorkEntry.objects.filter(pk=entry.pk).update(description="Changed")
        GarageJobStatusChange.objects.create(job=job, version=1, from_status="OPEN", to_status="COMPLETED", actor=self.actor, module_revision=self.revision)
        GarageJob.objects.filter(pk=job.pk).update(status="COMPLETED", status_version=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageWorkEntry.objects.create(job=job, description="Extra", actor=self.actor, module_revision=self.revision)

    def test_labour_company_scope_and_status_history_guards(self):
        revision = CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            LabourPerson.objects.create(tenant=self.company, branch=self.other_branch, name="Worker", created_by=self.actor, module_revision=revision)
        person = LabourPerson.objects.create(tenant=self.company, branch=self.branch, name="Worker", created_by=self.actor, module_revision=revision)
        with self.assertRaises(IntegrityError), transaction.atomic():
            LabourPerson.objects.filter(pk=person.pk).update(is_active=False, status_version=1)
        change = LabourStatusChange.objects.create(person=person, version=1, is_active=False, actor=self.actor, module_revision=revision)
        LabourPerson.objects.filter(pk=person.pk).update(is_active=False, status_version=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            LabourStatusChange.objects.filter(pk=change.pk).update(is_active=True)

    def test_status_history_required_and_retained(self):
        job = self.job()
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageJob.objects.filter(pk=job.pk).update(status="COMPLETED")
        change = GarageJobStatusChange.objects.create(job=job, version=1, from_status="OPEN", to_status="COMPLETED", actor=self.actor, module_revision=self.revision)
        GarageJob.objects.filter(pk=job.pk).update(status="COMPLETED", status_version=1)
        job.refresh_from_db()
        self.assertEqual(job.status, "COMPLETED")
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageJobStatusChange.objects.filter(pk=change.pk).update(to_status="OPEN")
        GarageJobStatusChange.objects.create(job=job, version=2, from_status="COMPLETED", to_status="OPEN", actor=self.actor, module_revision=self.revision)
        GarageJob.objects.filter(pk=job.pk).update(status="OPEN", status_version=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GarageJob.objects.filter(pk=job.pk).update(status="COMPLETED", status_version=3)
