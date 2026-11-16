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
from apps.accounting.models import AccountMovement, AccountingAccount, AccountingEvent
from apps.common.domain_mutations import DomainConflict
from apps.investment.models import (
    InvestorFundCredit,
    InvestorPrincipalReturn,
    InvestorPrincipalReturnAllocation,
)
from apps.investment.services import create_principal_return
from apps.tenants.models import (
    Branch,
    BranchAssignment,
    CompanyModuleState,
    Tenant,
)


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
