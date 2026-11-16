"""Phase 5 Purchase writes serialize pooled Fund use and module revisions."""

from datetime import timedelta
from decimal import Decimal
from queue import Queue
from threading import Barrier, Event, Thread, current_thread
from unittest.mock import patch

from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent
from apps.common import domain_mutations
from apps.common.domain_mutations import DomainConflict
from apps.investment.models import InvestorFundCredit, InvestorFundUse, InvestorFundUseAllocation
from apps.investment.services import create_fund_credit
from apps.tenants.models import Branch, CompanyModuleState, Tenant
from apps.vehicles.models import Vehicle, VehiclePurchase
from apps.vehicles.services import create_purchase


class VehiclePurchaseConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.company = Tenant.objects.create(name="Purchase Race", slug="p5-purchase-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.accountants = [
            make_user("p5-purchase-race-a", role="accountant", tenant=self.company),
            make_user("p5-purchase-race-b", role="accountant", tenant=self.company),
        ]
        self.cash = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Purchase race till",
            created_by=self.accountants[0],
        )
        self.revisions = {}
        for index, code in enumerate(("vehicle_management", "accounting", "investment"), start=1):
            self.revisions[code] = CompanyModuleState.objects.create(
                tenant=self.company,
                module_code=code,
                state=CompanyModuleState.State.ENABLED,
                version=1,
                effective_from=timezone.now() - timedelta(minutes=1),
                changed_by=self.accountants[0],
            )

        client = APIClient()
        client.force_authenticate(user=self.accountants[0])
        investment_base = f"/api/v1/tenants/{self.company.pk}/investment"
        investor_response = client.post(
            f"{investment_base}/investors/",
            {"name": "Race Investor"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-race-investor",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        self.investor_id = investor_response.data["id"]

        credit_response = client.post(
            f"{investment_base}/fund/credits/",
            {
                "investor_id": self.investor_id,
                "branch_id": str(self.branch.pk),
                "account_id": str(self.cash.pk),
                "amount": "10000.00",
                "reference": "PURCHASE-RACE-CREDIT",
                "effective_at": (timezone.now() - timedelta(seconds=10)).isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="purchase-race-credit",
        )
        self.assertEqual(credit_response.status_code, 201, credit_response.content)

        self.vehicles = []
        vehicle_base = f"/api/v1/tenants/{self.company.pk}/vehicle-management/vehicles/"
        for index in range(2):
            vehicle_response = client.post(
                vehicle_base,
                {
                    "registration": f"RACE-{index + 1}",
                    "model": "Test Vehicle",
                    "branch_id": str(self.branch.pk),
                },
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"purchase-race-vehicle-{index + 1}",
            )
            self.assertEqual(vehicle_response.status_code, 201, vehicle_response.content)
            self.vehicles.append(Vehicle.objects.get(pk=vehicle_response.data["id"]))

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.outcomes = Queue()

    def _prepare_worker_connection(self):
        close_old_connections()
        worker_connection = connections["default"]
        worker_connection.close()
        worker_connection.settings_dict["NAME"] = self.test_database_name

    def test_parallel_fund_credits_cannot_repeat_account_reference(self):
        barrier = Barrier(2)

        def credit(actor, index):
            self._prepare_worker_connection()
            try:
                barrier.wait(timeout=10)
                result = create_fund_credit(
                    actor=actor, company_id=self.company.pk, key=f"duplicate-race-{index}",
                    path="/fund/credits/", investor_id=self.investor_id,
                    branch_id=self.branch.pk, account_id=self.cash.pk,
                    amount=Decimal("100.00"), reference=" Duplicate-Race " if index == 0 else "duplicate-race",
                    effective_at=timezone.now() - timedelta(seconds=1),
                )
                self.outcomes.put(("success", result.status))
            except DomainConflict as error:
                self.outcomes.put(("conflict", str(error.detail["code"])))
            except Exception as error:
                self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        threads = [Thread(target=credit, args=(actor, i), daemon=True) for i, actor in enumerate(self.accountants)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        outcomes = [self.outcomes.get_nowait() for _ in threads]
        self.assertCountEqual([outcome for outcome, _ in outcomes], ["success", "conflict"], outcomes)
        self.assertEqual(InvestorFundCredit.objects.filter(reference__iexact="duplicate-race").count(), 1)
        self.assertEqual(AccountMovement.objects.count(), 2)

    def _purchase(self, actor, vehicle_id, key):
        return create_purchase(
            actor=actor,
            company_id=self.company.pk,
            key=key,
            path=f"/api/v1/tenants/{self.company.pk}/vehicle-management/purchases/",
            vehicle_id=vehicle_id,
            branch_id=self.branch.pk,
            purchase_cost=Decimal("6000.00"),
            seller_name="Race Motors",
            investor_id=self.investor_id,
            investor_fund_amount=Decimal("6000.00"),
            running_capital_amount=Decimal("0.00"),
            purchased_at=timezone.now() - timedelta(seconds=1),
        )

    def _parallel_purchase(self, actor, vehicle_id, key):
        self._prepare_worker_connection()
        try:
            result = self._purchase(actor, vehicle_id, key)
            self.outcomes.put(("success", result.status))
        except DomainConflict as error:
            self.outcomes.put(("conflict", error.detail["code"]))
        except Exception as error:  # surfaced in the main test thread
            self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
        finally:
            close_old_connections()

    def test_parallel_purchases_cannot_overallocate_one_investor_fund(self):
        threads = [
            Thread(
                target=self._parallel_purchase,
                args=(actor, str(vehicle.pk), f"purchase-race-{index}"),
                daemon=True,
            )
            for index, (actor, vehicle) in enumerate(zip(self.accountants, self.vehicles), start=1)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        outcomes = [self.outcomes.get_nowait() for _ in threads]
        self.assertEqual(
            sorted(outcome for outcome, _detail in outcomes),
            ["conflict", "success"],
            msg=f"Unexpected concurrent purchase outcomes: {outcomes!r}",
        )
        self.assertEqual(VehiclePurchase.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(InvestorFundUse.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(InvestorFundUseAllocation.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(
            InvestorFundUseAllocation.objects.get().amount,
            Decimal("6000.00"),
        )
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(AccountMovement.objects.filter(tenant=self.company).count(), 1)

    def test_purchase_observing_enabled_module_is_rejected_when_off_wins_company_lock(self):
        observed_enabled_revision = Event()
        result = []
        failures = []
        original_revision_map = domain_mutations._revision_map

        def observe_revision(company_id, module_codes):
            revisions = original_revision_map(company_id, module_codes)
            if current_thread().name == "phase5-purchase-off-race":
                observed_enabled_revision.set()
            return revisions

        def attempt_purchase():
            self._prepare_worker_connection()
            try:
                created = self._purchase(
                    self.accountants[1], str(self.vehicles[0].pk), "purchase-module-off-race"
                )
                result.append(created.status)
            except DomainConflict as error:
                result.append((409, error.detail["code"]))
            except Exception as error:  # surfaced in the main test thread
                failures.append(f"{type(error).__name__}: {error}")
            finally:
                close_old_connections()

        worker = Thread(target=attempt_purchase, name="phase5-purchase-off-race", daemon=True)
        with patch.object(domain_mutations, "_revision_map", side_effect=observe_revision):
            with transaction.atomic():
                Tenant.objects.select_for_update().get(pk=self.company.pk)
                CompanyModuleState.objects.create(
                    tenant=self.company,
                    module_code="vehicle_management",
                    state=CompanyModuleState.State.DISABLED,
                    version=2,
                    effective_from=timezone.now(),
                    changed_by=self.accountants[0],
                )
                worker.start()
                self.assertTrue(observed_enabled_revision.wait(timeout=10))

            worker.join(timeout=20)

        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(result, [(409, "MODULE_STATE_CHANGED")])
        self.assertFalse(VehiclePurchase.objects.filter(tenant=self.company).exists())
        self.assertFalse(InvestorFundUse.objects.filter(tenant=self.company).exists())
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(AccountMovement.objects.filter(tenant=self.company).count(), 1)
