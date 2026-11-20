"""Concurrent Fund returns preserve the pooled source balance."""

from datetime import timedelta
from decimal import Decimal
from queue import Queue
from threading import Barrier, Thread

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent, AccountingSourceLink
from apps.common.domain_mutations import DomainConflict
from apps.investment.models import (
    InvestorExitRequest,
    InvestorFundCredit,
    InvestorInterimPayment,
    InvestorPrincipalReturn,
    InvestorPrincipalReturnAllocation,
)
from apps.investment.services import create_interim_payment, create_principal_return
from apps.tenants.models import (
    Branch,
    BranchAssignment,
    CompanyModuleState,
    Tenant,
)
from apps.vehicles.models import VehiclePurchase


class ConcurrentProfitRecoveryTests(TransactionTestCase):
    def test_two_accountants_cannot_overcollect_one_confirmed_recoverable(self):
        from apps.investment.period_positions import receive_period_repayment
        company = Tenant.objects.create(name="Profit repayment race", slug="profit-repay-race")
        branch = Branch.objects.create(tenant=company, name="Central")
        actors = [make_user(f"profit-repay-race-{n}", role="accountant", tenant=company) for n in (1, 2)]
        for code in ("investment", "accounting", "vehicle_management"):
            CompanyModuleState.objects.create(
                tenant=company, module_code=code, state="enabled", version=1,
                effective_from=timezone.now(), changed_by=actors[0],
            )
        account = AccountingAccount.objects.create(
            tenant=company, account_type="CASH", label="Till", created_by=actors[0],
        )
        client = APIClient()
        client.force_authenticate(user=actors[0])
        root = f"/api/v1/tenants/{company.pk}/investment/"
        def post(suffix, body, key):
            response = client.post(root + suffix, body, format="json", HTTP_IDEMPOTENCY_KEY=key)
            self.assertEqual(response.status_code, 201, response.content)
            return response.data
        investor = post("investors/", {"name": "Repayment race Investor"}, "repay-race-investor")
        credit_at = timezone.now() - timedelta(days=35)
        post("fund/credits/", {
            "investor_id": investor["id"], "branch_id": str(branch.pk), "account_id": str(account.pk),
            "amount": "10000.00", "reference": "REPAY-RACE-CREDIT", "effective_at": credit_at.isoformat(),
        }, "repay-race-credit")
        base = f"investors/{investor['id']}/"
        post(base + "interim-configurations/", {
            "amount": "1000.00", "effective_date": credit_at.date().replace(day=1).isoformat(),
        }, "repay-race-config")
        post(base + "interim-payments/", {
            "branch_id": str(branch.pk), "account_id": str(account.pk),
            "amount": "1000.00", "effective_at": timezone.now().isoformat(),
        }, "repay-race-interim")
        projection = client.get(root + base + "profit-periods/")
        self.assertEqual(projection.status_code, 200, projection.content)
        period = projection.data["periods"][0]
        snapshot = post(base + "profit-period-reconciliations/", {
            "period_start": period["period_start"], "expected_source_version": period["source_version"],
            "reason": "Review race source",
        }, "repay-race-snapshot")
        position = post(base + "profit-positions/", {
            "reconciliation_id": snapshot["id"], "expected_source_version": period["source_version"],
            "reason": "Confirm recoverable",
        }, "repay-race-position")
        barrier, outcomes = Barrier(2), Queue()
        def receive(actor, n):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = receive_period_repayment(
                    actor=actor, company_id=company.pk, investor_id=investor["id"], position_id=position["id"],
                    branch_id=branch.pk, account_id=account.pk, amount=Decimal("600.00"),
                    expected_source_version=period["source_version"], reason="Actual repayment",
                    key=f"repay-race-{n}", path=root + base + f"profit-positions/{position['id']}/repayments/",
                )
                outcomes.put(("success", result.status))
            except DomainConflict as exc:
                outcomes.put(("conflict", str(exc)))
            except Exception as exc:
                outcomes.put(("error", f"{type(exc).__name__}: {exc}"))
            finally:
                connections.close_all()
        threads = [Thread(target=receive, args=(actor, n), daemon=True) for n, actor in enumerate(actors)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads), "Repayment race timed out")
        result = [outcomes.get_nowait() for _ in threads]
        self.assertCountEqual([kind for kind, _ in result], ["success", "conflict"], result)
        self.assertEqual(AccountingEvent.objects.filter(tenant=company, event_type="INVESTOR_PROFIT_RECOVERY").count(), 1)
        self.assertEqual(AccountMovement.objects.filter(tenant=company, delta=Decimal("600.00")).count(), 1)


class ConcurrentPrincipalReturnTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.company = Tenant.objects.create(name="Concurrent Fund", slug="p5-return-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.company_accountant = make_user(
            "p5-race-company-accountant", role="accountant", tenant=self.company
        )
        self.actors = [
            self._branch_accountant("p5-race-branch-a"),
            self._branch_accountant("p5-race-branch-b"),
        ]
        self.account = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Race test till",
            created_by=self.company_accountant,
        )
        self._enable_module("investment")
        self._enable_module("accounting")

        client = APIClient()
        client.force_authenticate(user=self.company_accountant)
        base = f"/api/v1/tenants/{self.company.pk}/investment"
        investor_response = client.post(
            f"{base}/investors/",
            {"name": "Race Test Investor"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="race-investor-create",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        self.investor_id = investor_response.data["id"]

        credit_client = APIClient()
        credit_client.force_authenticate(user=self.actors[0])
        effective_at = timezone.now() - timedelta(minutes=1)
        credit_response = credit_client.post(
            f"{base}/fund/credits/",
            {
                "investor_id": self.investor_id,
                "branch_id": str(self.branch.pk),
                "account_id": str(self.account.pk),
                "amount": "50000.00",
                "reference": "RACE-CREDIT-001",
                "effective_at": effective_at.isoformat(),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="race-credit-create",
        )
        self.assertEqual(credit_response.status_code, 201, credit_response.content)
        self.credit_id = credit_response.data["id"]

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.barrier = Barrier(2)
        self.outcomes = Queue()

    def _branch_accountant(self, login_id):
        actor = make_user(login_id, tenant=self.company)
        membership = actor.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership,
            role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch,
            assigned_by=actor,
        )
        BranchAssignment.objects.create(
            membership=membership,
            branch=self.branch,
            assigned_by=actor,
        )
        return actor

    def _enable_module(self, module_code):
        CompanyModuleState.objects.create(
            tenant=self.company,
            module_code=module_code,
            state=CompanyModuleState.State.ENABLED,
            version=1,
            effective_from=timezone.now() - timedelta(minutes=2),
            changed_by=self.company_accountant,
        )

    def _return_fund(self, actor, suffix):
        close_old_connections()
        worker_connection = connections["default"]
        try:
            worker_connection.close()
            # Django's test runner redirects the main connection to its isolated
            # test database. Thread-local connections must use that same DB.
            worker_connection.settings_dict["NAME"] = self.test_database_name
            self.barrier.wait(timeout=10)
            result = create_principal_return(
                actor=actor,
                company_id=self.company.pk,
                key=f"race-return-{suffix}",
                path=f"/api/v1/tenants/{self.company.pk}/investment/fund/principal-returns/",
                investor_id=self.investor_id,
                branch_id=self.branch.pk,
                account_id=self.account.pk,
                amount=Decimal("40000.00"),
                reference=f"RACE-RETURN-{suffix}",
                effective_at=timezone.now() - timedelta(seconds=1),
            )
            self.outcomes.put(("success", result.status))
        except DomainConflict as error:
            self.outcomes.put(("conflict", error.detail))
        except Exception as error:  # surfaced in the main test thread
            self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
        finally:
            close_old_connections()

    def test_parallel_returns_cannot_overdraw_the_same_branch_credit(self):
        threads = [
            Thread(target=self._return_fund, args=(actor, str(index)), daemon=True)
            for index, actor in enumerate(self.actors, start=1)
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
            msg=f"Unexpected concurrent outcomes: {outcomes!r}",
        )
        self.assertEqual(InvestorPrincipalReturn.objects.count(), 1)
        self.assertEqual(InvestorPrincipalReturnAllocation.objects.count(), 1)
        self.assertEqual(
            str(InvestorPrincipalReturnAllocation.objects.get().credit_id),
            str(self.credit_id),
        )
        self.assertEqual(
            InvestorPrincipalReturnAllocation.objects.get().amount,
            Decimal("40000.00"),
        )
        self.assertEqual(
            InvestorFundCredit.objects.get(pk=self.credit_id).amount,
            Decimal("50000.00"),
        )
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 2)
        self.assertEqual(AccountMovement.objects.filter(tenant=self.company).count(), 2)
        self.assertEqual(
            AccountingEvent.objects.filter(
                tenant=self.company,
                event_type=AccountingEvent.EventType.CAPITAL_OUTFLOW,
            ).count(),
            1,
        )


class ConcurrentExitFundingTests(ConcurrentPrincipalReturnTests):
    """An Exit and a Fund credit serialize against the same Investor."""

    def test_exit_and_credit_are_serialized(self):
        self._enable_module("investor_portal")
        investor_actor = make_user("exit-race-investor", role="investor", tenant=self.company)
        client = APIClient()
        client.force_authenticate(user=self.company_accountant)
        base = f"/api/v1/tenants/{self.company.pk}/investment"
        bound = client.post(
            f"{base}/investors/{self.investor_id}/portal-binding/",
            {"account_id": str(investor_actor.pk)}, format="json",
            HTTP_IDEMPOTENCY_KEY="exit-race-binding",
        )
        self.assertEqual(bound.status_code, 201, bound.content)
        outcomes = Queue()
        barrier = Barrier(2)
        credit_ref = "EXIT-RACE-NEW-CREDIT"

        def run(kind):
            close_old_connections()
            worker = connections["default"]
            try:
                worker.close()
                worker.settings_dict["NAME"] = self.test_database_name
                request_client = APIClient()
                request_client.force_authenticate(user=investor_actor if kind == "exit" else self.actors[0])
                barrier.wait(timeout=10)
                if kind == "exit":
                    response = request_client.post(
                        f"{base}/portal/self/exit-requests/", {"terms_accepted": True},
                        format="json", HTTP_IDEMPOTENCY_KEY="exit-race-request",
                    )
                else:
                    response = request_client.post(
                        f"{base}/fund/credits/",
                        {"investor_id": self.investor_id, "branch_id": str(self.branch.pk),
                         "account_id": str(self.account.pk), "amount": "100.00",
                         "reference": credit_ref, "effective_at": (timezone.now() - timedelta(seconds=1)).isoformat()},
                        format="json", HTTP_IDEMPOTENCY_KEY="exit-race-credit",
                    )
                outcomes.put((kind, response.status_code, response.json()))
            except Exception as error:
                outcomes.put((kind, "error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        threads = [Thread(target=run, args=(kind,), daemon=True) for kind in ("exit", "credit")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        results = {kind: (status, body) for kind, status, body in (outcomes.get_nowait() for _ in threads)}
        self.assertEqual(results["exit"][0], 201, results)
        self.assertIn(results["credit"][0], (201, 409), results)
        exit_request = InvestorExitRequest.objects.get(tenant=self.company, investor_id=self.investor_id)
        credit = InvestorFundCredit.objects.filter(tenant=self.company, reference=credit_ref).first()
        if results["credit"][0] == 201:
            self.assertIsNotNone(credit)
            self.assertLess(credit.created_at, exit_request.created_at)
        else:
            self.assertEqual(results["credit"][1]["code"], "INVESTOR_EXIT_OPEN")
            self.assertIsNone(credit)

    def test_exit_and_investor_funded_purchase_are_serialized(self):
        self._enable_module("investor_portal")
        self._enable_module("vehicle_management")
        investor_actor = make_user("exit-purchase-race-investor", role="investor", tenant=self.company)
        client = APIClient()
        client.force_authenticate(user=self.company_accountant)
        base = f"/api/v1/tenants/{self.company.pk}"
        bound = client.post(
            f"{base}/investment/investors/{self.investor_id}/portal-binding/",
            {"account_id": str(investor_actor.pk)}, format="json",
            HTTP_IDEMPOTENCY_KEY="exit-purchase-race-binding",
        )
        self.assertEqual(bound.status_code, 201, bound.content)
        vehicle = client.post(
            f"{base}/vehicle-management/vehicles/",
            {"registration": "KL 11 ZZ 9901", "model": "Race car", "branch_id": str(self.branch.pk)},
            format="json", HTTP_IDEMPOTENCY_KEY="exit-purchase-race-vehicle",
        )
        self.assertEqual(vehicle.status_code, 201, vehicle.content)
        outcomes = Queue()
        barrier = Barrier(2)

        def run(kind):
            close_old_connections()
            worker = connections["default"]
            try:
                worker.close()
                worker.settings_dict["NAME"] = self.test_database_name
                request_client = APIClient()
                request_client.force_authenticate(user=investor_actor if kind == "exit" else self.company_accountant)
                barrier.wait(timeout=10)
                if kind == "exit":
                    response = request_client.post(
                        f"{base}/investment/portal/self/exit-requests/", {"terms_accepted": True},
                        format="json", HTTP_IDEMPOTENCY_KEY="exit-purchase-race-request",
                    )
                else:
                    response = request_client.post(
                        f"{base}/vehicle-management/purchases/",
                        {"vehicle_id": vehicle.data["id"], "branch_id": str(self.branch.pk),
                         "purchase_cost": "10000.00", "seller_name": "Seller", "investor_id": self.investor_id,
                         "investor_fund_amount": "10000.00", "running_capital_amount": "0.00", "initial_payment_amount": "0.00"},
                        format="json", HTTP_IDEMPOTENCY_KEY="exit-purchase-race-purchase",
                    )
                outcomes.put((kind, response.status_code, response.json()))
            except Exception as error:
                outcomes.put((kind, "error", f"{type(error).__name__}: {error}"))
            finally:
                close_old_connections()

        threads = [Thread(target=run, args=(kind,), daemon=True) for kind in ("exit", "purchase")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        results = {kind: (status, body) for kind, status, body in (outcomes.get_nowait() for _ in threads)}
        self.assertEqual(results["exit"][0], 201, results)
        self.assertIn(results["purchase"][0], (201, 409), results)
        exit_request = InvestorExitRequest.objects.get(tenant=self.company, investor_id=self.investor_id)
        purchase = VehiclePurchase.objects.filter(tenant=self.company, vehicle_id=vehicle.data["id"]).first()
        if results["purchase"][0] == 201:
            self.assertIsNotNone(purchase)
            self.assertLess(purchase.created_at, exit_request.created_at)
        else:
            self.assertEqual(results["purchase"][1]["code"], "INVESTOR_EXIT_OPEN")
            self.assertIsNone(purchase)


class ConcurrentInterimCapTests(TransactionTestCase):
    """Concurrent partial payments cannot exceed the Company-wide monthly cap."""

    reset_sequences = True

    def setUp(self):
        self.company = Tenant.objects.create(name="Interim Race", slug="interim-race")
        self.branch = Branch.objects.create(tenant=self.company, name="Central")
        self.company_accountant = make_user(
            "interim-race-company-accountant", role="accountant", tenant=self.company,
        )
        self.actors = [
            self._branch_accountant("interim-race-branch-a"),
            self._branch_accountant("interim-race-branch-b"),
        ]
        self.account = AccountingAccount.objects.create(
            tenant=self.company,
            account_type=AccountingAccount.AccountType.CASH,
            label="Interim race till",
            created_by=self.company_accountant,
        )
        self._enable_module("investment")
        self._enable_module("accounting")

        client = APIClient()
        client.force_authenticate(user=self.company_accountant)
        self.base = f"/api/v1/tenants/{self.company.pk}/investment"
        investor_response = client.post(
            f"{self.base}/investors/", {"name": "Interim Race Investor"},
            format="json", HTTP_IDEMPOTENCY_KEY="interim-race-investor-create",
        )
        self.assertEqual(investor_response.status_code, 201, investor_response.content)
        self.investor_id = investor_response.data["id"]
        self.period_month = timezone.localdate().replace(day=1)
        configuration_response = client.post(
            f"{self.base}/investors/{self.investor_id}/interim-configurations/",
            {"amount": "1000.00", "effective_date": self.period_month.isoformat()},
            format="json", HTTP_IDEMPOTENCY_KEY="interim-race-configure",
        )
        self.assertEqual(configuration_response.status_code, 201, configuration_response.content)

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.barrier = Barrier(2)
        self.outcomes = Queue()

    def _branch_accountant(self, login_id):
        actor = make_user(login_id, tenant=self.company)
        membership = actor.tenant_memberships.get(tenant=self.company)
        CompanyRoleGrant.objects.create(
            membership=membership, role=CompanyRoleGrant.Role.ACCOUNTANT,
            branch=self.branch, assigned_by=self.company_accountant,
        )
        BranchAssignment.objects.create(
            membership=membership, branch=self.branch,
            assigned_by=self.company_accountant,
        )
        return actor

    def _enable_module(self, module_code):
        CompanyModuleState.objects.create(
            tenant=self.company, module_code=module_code,
            state=CompanyModuleState.State.ENABLED, version=1,
            effective_from=timezone.now() - timedelta(minutes=2),
            changed_by=self.company_accountant,
        )

    def _pay_interim(self, actor, suffix):
        close_old_connections()
        worker_connection = connections["default"]
        try:
            worker_connection.close()
            worker_connection.settings_dict["NAME"] = self.test_database_name
            self.barrier.wait(timeout=10)
            result = create_interim_payment(
                actor=actor,
                company_id=self.company.pk,
                investor_id=self.investor_id,
                branch_id=self.branch.pk,
                account_id=self.account.pk,
                amount=Decimal("700.00"),
                effective_at=timezone.now() - timedelta(seconds=1),
                key=f"interim-race-payment-{suffix}",
                path=f"{self.base}/investors/{self.investor_id}/interim-payments/",
            )
            self.outcomes.put(("success", result.status))
        except DomainConflict as error:
            self.outcomes.put(("conflict", error.detail))
        except Exception as error:  # surfaced in the main test thread
            self.outcomes.put(("error", f"{type(error).__name__}: {error}"))
        finally:
            close_old_connections()

    def test_parallel_partial_payments_cannot_cross_monthly_cap(self):
        threads = [
            Thread(target=self._pay_interim, args=(actor, str(index)), daemon=True)
            for index, actor in enumerate(self.actors, start=1)
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
            msg=f"Unexpected concurrent outcomes: {outcomes!r}",
        )
        self.assertEqual(InvestorInterimPayment.objects.count(), 1)
        self.assertEqual(
            InvestorInterimPayment.objects.get().amount,
            Decimal("700.00"),
        )
        self.assertEqual(AccountingEvent.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(AccountMovement.objects.filter(tenant=self.company).count(), 1)
        self.assertEqual(AccountingSourceLink.objects.filter(
            investor_interim_payment__isnull=False,
        ).count(), 1)
