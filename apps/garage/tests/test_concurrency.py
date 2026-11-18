from decimal import Decimal
from queue import Queue
from threading import Barrier, Event, Thread, current_thread
from unittest.mock import patch

from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountingAccount, AccountingEvent, AccountMovement
from apps.common.domain_mutations import DomainConflict
from apps.common import domain_mutations
from apps.garage.models import GarageCustomerReceipt, LabourPerson
from apps.garage.services import correct_customer_cost_payment, correct_labour_payment, correct_receipt, create_job, create_labour_person, create_labour_payment, create_stock_cost, pay_customer_cost, record_charge, record_receipt, update_labour_person, write_customer_cost
from apps.tenants.models import Branch, BranchAssignment, CompanyModuleState, Tenant


class GarageReceiptConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Garage race", slug="garage-receipt-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.actors = [make_user(f"garage-race-{name}", role="accountant", tenant=self.company) for name in ("a", "b")]
        for actor in self.actors:
            BranchAssignment.objects.create(membership=actor.tenant_memberships.get(tenant=self.company), branch=self.branch, assigned_by=actor)
        for module in ("garage", "vehicle_management", "accounting"):
            CompanyModuleState.objects.create(tenant=self.company, module_code=module, state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actors[0])
        self.account = AccountingAccount.objects.create(tenant=self.company, account_type="CASH", label="Race till", created_by=self.actors[0])
        client = APIClient()
        client.force_authenticate(user=self.actors[0])
        response = client.post(f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/", {"registration": "RACE-6", "model": "Race", "branch_id": str(self.branch.pk)}, format="json", HTTP_IDEMPOTENCY_KEY="race-vehicle")
        self.assertEqual(response.status_code, 201, response.content)
        self.vehicle_id = response.data["id"]
        job = create_job(actor=self.actors[0], company_id=self.company.pk, branch_id=self.branch.pk, vehicle_id=response.data["id"], context="EXTERNAL_CUSTOMER", contact_name="Customer", contact_phone="", key="race-job", path="/race/jobs/")
        self.job_id = job.body["id"]
        record_charge(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id, amount=Decimal("100.00"), expected_version=0, reason="", key="race-charge", path="/race/charge/")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.database_name = cursor.fetchone()[0]

    def run_parallel(self, functions):
        barrier = Barrier(len(functions))
        outcomes = Queue()

        def worker(fn):
            close_old_connections()
            connections["default"].close()
            connections["default"].settings_dict["NAME"] = self.database_name
            try:
                barrier.wait(timeout=10)
                outcomes.put(("success", fn().status))
            except DomainConflict as error:
                outcomes.put(("conflict", str(error.detail["code"])))
            except Exception as error:
                outcomes.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        threads = [Thread(target=worker, args=(fn,), daemon=True) for fn in functions]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads), "Concurrent operation timed out")
        return [outcomes.get_nowait() for _ in threads]

    def receipt(self, actor, amount, reference, key):
        return record_receipt(actor=actor, company_id=self.company.pk, job_id=self.job_id, account_id=self.account.pk,
                              amount=Decimal(amount), reference=reference, key=key, path="/race/receipts/")

    def test_concurrent_receipts_cannot_exceed_charge(self):
        outcomes = self.run_parallel([lambda: self.receipt(self.actors[0], "80.00", "race-ref-1", "race-r1"),
                                      lambda: self.receipt(self.actors[1], "80.00", "race-ref-2", "race-r2")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(GarageCustomerReceipt.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_RECEIPT").count(), 1)
        self.assertEqual(AccountMovement.objects.count(), 1)

    def test_charge_correction_racing_receipt_never_goes_below_collection(self):
        def correct():
            return record_charge(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id,
                                 amount=Decimal("50.00"), expected_version=1, reason="Correction",
                                 key="race-correction", path="/race/charge/")
        outcomes = self.run_parallel([lambda: self.receipt(self.actors[0], "80.00", "race-ref-3", "race-r3"), correct])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        receipts = GarageCustomerReceipt.objects.filter(job_id=self.job_id)
        from apps.garage.models import GarageJob
        charge = GarageJob.objects.get(pk=self.job_id).customer_charges.order_by("-version").first()
        collected = sum((row.event.amount for row in receipts.select_related("event")), Decimal("0.00"))
        self.assertGreaterEqual(charge.amount, collected)

    def test_concurrent_duplicate_reference_creates_one_cash_event(self):
        outcomes = self.run_parallel([lambda: self.receipt(self.actors[0], "20.00", "shared-ref", "race-duplicate-a"),
                                      lambda: self.receipt(self.actors[1], "20.00", "shared-ref", "race-duplicate-b")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(GarageCustomerReceipt.objects.filter(reference="shared-ref").count(), 1)
        self.assertEqual(AccountMovement.objects.count(), 1)

    def test_stock_cost_racing_vehicle_move_keeps_original_branch_or_rolls_back(self):
        from apps.garage.models import GarageStockCostLink
        from apps.vehicles.models import Vehicle, VehicleExpense
        from apps.vehicles.services import move_vehicle

        destination = Branch.objects.create(tenant=self.company, name="West")
        stock_job = create_job(actor=self.actors[0], company_id=self.company.pk, branch_id=self.branch.pk,
                               vehicle_id=self.vehicle_id, context="STOCK", contact_name="", contact_phone="",
                               key="race-stock-job", path="/race/jobs/")

        def cost():
            return create_stock_cost(actor=self.actors[0], company_id=self.company.pk, job_id=stock_job.body["id"],
                                     amount=Decimal("75.00"), description="Repair", key="race-stock-cost", path="/race/cost/")

        def move():
            return move_vehicle(actor=self.actors[1], company_id=self.company.pk, vehicle_id=self.vehicle_id,
                                to_branch_id=destination.pk, reason="Branch transfer", key="race-move", path="/race/move/")

        outcomes = self.run_parallel([cost, move])
        self.assertIn(outcomes[0][0], ("success", "conflict"), outcomes)
        self.assertTrue(any(item == ("success", 201) for item in outcomes), outcomes)
        self.assertFalse(any(item[0] == "error" for item in outcomes), outcomes)
        self.assertEqual(Vehicle.objects.get(pk=self.vehicle_id).current_branch_id, destination.pk)
        links = GarageStockCostLink.objects.filter(job_id=stock_job.body["id"]).select_related("expense", "job")
        self.assertEqual(VehicleExpense.objects.filter(vehicle_id=self.vehicle_id).count(), links.count())
        for link in links:
            self.assertEqual(link.expense.branch_id, self.branch.pk)
            self.assertEqual(link.job.branch_id, self.branch.pk)
        with self.assertRaises(DomainConflict) as rejected:
            create_stock_cost(actor=self.actors[0], company_id=self.company.pk, job_id=stock_job.body["id"],
                              amount=Decimal("30.00"), description="After transfer", key="after-move-cost", path="/race/cost/")
        self.assertEqual(str(rejected.exception.detail["code"]), "GARAGE_VEHICLE_BRANCH_CHANGED")
        self.assertEqual(VehicleExpense.objects.filter(vehicle_id=self.vehicle_id).count(), links.count())

    def test_customer_cost_payments_race_without_exceeding_cost(self):
        from apps.garage.models import GarageCustomerCostPayment

        cost = write_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id,
                                   description="Parts", amount=Decimal("100.00"), key="cost-race-create", path="/race/cost/")

        def pay(actor, key):
            return pay_customer_cost(actor=actor, company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"],
                                     account_id=self.account.pk, amount=Decimal("80.00"), effective_at=None, key=key, path="/race/cost-pay/")

        outcomes = self.run_parallel([lambda: pay(self.actors[0], "cost-pay-a"), lambda: pay(self.actors[1], "cost-pay-b")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(GarageCustomerCostPayment.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_COST_PAYMENT").count(), 1)
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), Decimal("-80.00"))

    def test_customer_cost_reduction_racing_payment_preserves_cost_floor(self):
        from apps.garage.models import GarageCustomerCost
        from apps.garage.services import _customer_cost_paid

        cost = write_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id,
            description="Repair", amount=Decimal("100.00"), key="floor-race-cost", path="/race/cost/")
        def reduce():
            return write_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id,
                cost_id=cost.body["id"], amount=Decimal("50.00"), expected_version=0, reason="Correct bill",
                key="floor-race-reduce", path="/race/cost-correction/")
        def pay():
            return pay_customer_cost(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id,
                cost_id=cost.body["id"], account_id=self.account.pk, amount=Decimal("80.00"), effective_at=None,
                key="floor-race-pay", path="/race/cost-pay/")
        outcomes = self.run_parallel([reduce, pay])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        saved = GarageCustomerCost.objects.get(pk=cost.body["id"])
        correction = saved.corrections.order_by("-version").first()
        amount = correction.amount if correction else saved.amount
        paid = _customer_cost_paid(saved)
        self.assertGreaterEqual(amount, paid)
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), -paid)

    def test_refund_preview_holds_job_lock_during_snapshot(self):
        from apps.garage import services

        cost = write_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id,
            description="Repair", amount=Decimal("100.00"), key="preview-lock-cost", path="/race/cost/")
        entered, release, payment_done = Event(), Event(), Event()
        outcomes = Queue()
        original = services._customer_cost_paid
        def observed_paid(row):
            result = original(row)
            if current_thread().name == "preview-lock":
                entered.set()
                if not release.wait(10):
                    raise RuntimeError("Preview test synchronization timed out")
            return result
        def worker(kind):
            close_old_connections()
            connections["default"].close()
            connections["default"].settings_dict["NAME"] = self.database_name
            try:
                if kind == "preview":
                    result = services.preview_customer_cost_refund(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"], amount=Decimal("50.00"))
                else:
                    result = pay_customer_cost(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"], account_id=self.account.pk, amount=Decimal("40.00"), effective_at=None, key="preview-race-pay", path="/race/cost-pay/").status
                    payment_done.set()
                outcomes.put((kind, result))
            except Exception as error:
                outcomes.put(("error", str(error)))
            finally:
                close_old_connections()
        preview_thread = Thread(target=worker, args=("preview",), name="preview-lock", daemon=True)
        payment_thread = Thread(target=worker, args=("payment",), daemon=True)
        with patch.object(services, "_customer_cost_paid", side_effect=observed_paid):
            preview_thread.start()
            try:
                self.assertTrue(entered.wait(10))
                payment_thread.start()
                self.assertFalse(payment_done.wait(1), "Payment committed while preview held the Job lock")
            finally:
                release.set()
            preview_thread.join(20)
            payment_thread.join(20)
        self.assertFalse(preview_thread.is_alive() or payment_thread.is_alive())
        results = dict(outcomes.get_nowait() for _ in range(2))
        self.assertNotIn("error", results)
        self.assertEqual(results["preview"]["paid"], "0.00")
        self.assertEqual(results["payment"], 201)

    def test_cost_payment_correction_racing_new_payment_preserves_cost_cap(self):
        from uuid import UUID
        from apps.garage.models import GarageCustomerCost
        from apps.garage.services import _customer_cost_paid

        cost = write_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id,
                                   description="Parts", amount=Decimal("100.00"), key="cost-corr-race-create", path="/race/cost/")
        payment = pay_customer_cost(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"],
                                    account_id=self.account.pk, amount=Decimal("40.00"), effective_at=None, key="cost-corr-race-pay", path="/race/cost-pay/")
        def correct():
            return correct_customer_cost_payment(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"],
                payment_id=payment.body["id"], expected_event_id=UUID(payment.body["event_id"]), outcome="REVERSE_AND_REPLACE", reason="Correct amount",
                replacement={"account_id": self.account.pk, "amount": Decimal("80.00"), "effective_at": timezone.now()}, key="cost-corr-race-correct", path="/race/cost-correct/")
        def pay():
            return pay_customer_cost(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id, cost_id=cost.body["id"],
                account_id=self.account.pk, amount=Decimal("40.00"), effective_at=None, key="cost-corr-race-extra", path="/race/cost-pay/")
        outcomes = self.run_parallel([correct, pay])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        paid = _customer_cost_paid(GarageCustomerCost.objects.get(pk=cost.body["id"]))
        self.assertEqual(paid, Decimal("80.00"))
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), -paid)

    def test_concurrent_labour_edits_reject_stale_details(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actors[0])
        created = create_labour_person(actor=self.actors[0], company_id=self.company.pk, branch_id=self.branch.pk, name="Worker", phone="", key="race-person", path="/race/labour/")
        person = LabourPerson.objects.get(pk=created.body["id"])
        def edit(actor, name, key):
            return update_labour_person(actor=actor, company_id=self.company.pk, person_id=person.pk, name=name, phone="", expected_updated_at=person.updated_at, key=key, path="/race/labour/person/")
        outcomes = self.run_parallel([lambda: edit(self.actors[0], "Worker A", "race-edit-a"), lambda: edit(self.actors[1], "Worker B", "race-edit-b")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        person.refresh_from_db()
        self.assertIn(person.name, ("Worker A", "Worker B"))
        from apps.accounts.models import AccountSecurityEvent
        self.assertEqual(AccountSecurityEvent.objects.filter(action="labour.person.update", resource_id=person.pk).count(), 1)

    def test_receipt_observing_enabled_module_is_rejected_when_off_wins(self):
        observed = Event()
        outcomes = Queue()
        revision_map = domain_mutations._revision_map
        def observe(company_id, module_codes):
            revisions = revision_map(company_id, module_codes)
            if current_thread().name == "garage-receipt-off-race":
                observed.set()
            return revisions
        def receipt_worker():
            close_old_connections()
            connections["default"].close()
            connections["default"].settings_dict["NAME"] = self.database_name
            try:
                outcomes.put(("success", self.receipt(self.actors[1], "40.00", "off-race-ref", "off-race-key").status))
            except DomainConflict as error:
                outcomes.put(("conflict", str(error.detail["code"])))
            except Exception as error:
                outcomes.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()
        worker = Thread(target=receipt_worker, name="garage-receipt-off-race", daemon=True)
        with patch.object(domain_mutations, "_revision_map", side_effect=observe):
            with transaction.atomic():
                Tenant.objects.select_for_update().get(pk=self.company.pk)
                CompanyModuleState.objects.create(tenant=self.company, module_code="garage", state="disabled", version=2, effective_from=timezone.now(), changed_by=self.actors[0])
                worker.start()
                self.assertTrue(observed.wait(timeout=10))
            worker.join(timeout=30)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcomes.get_nowait(), ("conflict", "MODULE_STATE_CHANGED"))
        self.assertFalse(GarageCustomerReceipt.objects.filter(job_id=self.job_id).exists())
        self.assertFalse(AccountMovement.objects.filter(tenant=self.company).exists())

    def test_concurrent_labour_payment_corrections_only_apply_once(self):
        CompanyModuleState.objects.create(tenant=self.company, module_code="labour", state="enabled", version=1, effective_from=timezone.now(), changed_by=self.actors[0])
        person = create_labour_person(actor=self.actors[0], company_id=self.company.pk, branch_id=self.branch.pk, name="Worker", phone="", key="correction-race-person", path="/race/labour/")
        at = timezone.now()
        payment = create_labour_payment(actor=self.actors[0], company_id=self.company.pk, person_id=person.body["id"], account_id=self.account.pk, amount=Decimal("100.00"), note="", effective_at=at, key="correction-race-payment", path="/race/payments/")
        from uuid import UUID
        def correct(actor, amount, key):
            return correct_labour_payment(actor=actor, company_id=self.company.pk, person_id=person.body["id"], payment_id=payment.body["id"], expected_event_id=UUID(payment.body["event_id"]), outcome="REVERSE_AND_REPLACE", reason="Correct entry", replacement={"account_id": self.account.pk, "amount": Decimal(amount), "effective_at": at}, key=key, path="/race/correction/")
        outcomes = self.run_parallel([lambda: correct(self.actors[0], "80.00", "corr-race-a"), lambda: correct(self.actors[1], "70.00", "corr-race-b")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        from apps.garage.models import LabourPaymentCorrection
        self.assertEqual(LabourPaymentCorrection.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="LABOUR_PAYMENT").count(), 3)
        self.assertIn(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), (Decimal("-80.00"), Decimal("-70.00")))

    def test_receipt_correction_racing_new_receipt_preserves_charge_cap(self):
        from uuid import UUID
        first = self.receipt(self.actors[0], "40.00", "corr-race-original", "corr-race-initial")
        def correct():
            return correct_receipt(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id, receipt_id=first.body["id"], expected_event_id=UUID(first.body["event_id"]), outcome="REVERSE_AND_REPLACE", reason="Correct amount", replacement={"account_id": self.account.pk, "amount": Decimal("80.00"), "effective_at": timezone.now()}, key="corr-race-correction", path="/race/receipt-correction/")
        outcomes = self.run_parallel([correct, lambda: self.receipt(self.actors[0], "40.00", "corr-race-new", "corr-race-new-key")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        from apps.garage.services import job_detail
        from apps.garage.models import GarageJob
        detail = job_detail(GarageJob.objects.get(pk=self.job_id))
        self.assertLessEqual(Decimal(detail["received"]), Decimal("100.00"))
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), Decimal(detail["received"]))

    def test_concurrent_receipt_corrections_only_apply_once(self):
        from uuid import UUID
        first = self.receipt(self.actors[0], "40.00", "corr-both-original", "corr-both-initial")
        def correct(actor, amount, key):
            return correct_receipt(actor=actor, company_id=self.company.pk, job_id=self.job_id, receipt_id=first.body["id"], expected_event_id=UUID(first.body["event_id"]), outcome="REVERSE_AND_REPLACE", reason="Correct amount", replacement={"account_id": self.account.pk, "amount": Decimal(amount), "effective_at": timezone.now()}, key=key, path="/race/receipt-correction/")
        outcomes = self.run_parallel([lambda: correct(self.actors[0], "60.00", "corr-both-a"), lambda: correct(self.actors[1], "70.00", "corr-both-b")])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        from apps.garage.models import GarageReceiptCorrection
        self.assertEqual(GarageReceiptCorrection.objects.count(), 1)
        self.assertEqual(AccountingEvent.objects.filter(event_type="GARAGE_RECEIPT").count(), 3)

    def test_receipt_correction_racing_charge_reduction_preserves_floor(self):
        from uuid import UUID
        first = self.receipt(self.actors[0], "40.00", "corr-charge-original", "corr-charge-initial")
        def correct_receipt_amount():
            return correct_receipt(actor=self.actors[0], company_id=self.company.pk, job_id=self.job_id, receipt_id=first.body["id"], expected_event_id=UUID(first.body["event_id"]), outcome="REVERSE_AND_REPLACE", reason="Correct amount", replacement={"account_id": self.account.pk, "amount": Decimal("80.00"), "effective_at": timezone.now()}, key="corr-charge-receipt", path="/race/receipt-correction/")
        def reduce_charge():
            return record_charge(actor=self.actors[1], company_id=self.company.pk, job_id=self.job_id, amount=Decimal("60.00"), expected_version=1, reason="Correct charge", key="corr-charge-reduction", path="/race/charge/")
        outcomes = self.run_parallel([correct_receipt_amount, reduce_charge])
        self.assertCountEqual([item[0] for item in outcomes], ["success", "conflict"], outcomes)
        from apps.garage.models import GarageJob
        from apps.garage.services import job_detail
        job = GarageJob.objects.get(pk=self.job_id)
        detail = job_detail(job)
        self.assertGreaterEqual(Decimal(detail["customer_charge"]), Decimal(detail["received"]))
        self.assertEqual(sum((row.delta for row in AccountMovement.objects.filter(account=self.account)), Decimal("0")), Decimal(detail["received"]))
