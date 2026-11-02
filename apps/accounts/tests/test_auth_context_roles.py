from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import CompanyRoleGrant
from apps.accounts.policy import require_action
from apps.accounts.tests.test_users import make_user
from apps.tenants.models import Branch, BranchAssignment, Tenant


class AuthContextRoleTests(TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Context", slug="context")
        self.user = make_user("context-investor", role="investor", tenant=self.company)
        self.membership = self.user.tenant_memberships.get()
        self.client.force_login(self.user)

    def test_investor_context_does_not_grant_business_reads(self):
        branch = Branch.objects.create(tenant=self.company, name="North")
        BranchAssignment.objects.create(
            membership=self.membership, branch=branch, assigned_by=self.user
        )
        context = self.client.get("/api/v1/auth/me/").json()
        self.assertEqual(context["roles"], ["investor"])
        self.assertEqual(context["tenant_ids"], [str(self.company.pk)])
        self.assertEqual(context["companies"][0]["roles"], ["investor"])
        self.assertEqual(context["companies"][0]["company_wide_roles"], ["investor"])
        self.assertEqual(context["companies"][0]["branches"][0]["roles"], ["investor"])
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "core.company.read", company=self.company)
        with self.assertRaises(PermissionDenied):
            require_action(self.user, "account.provision.media", company=self.company)
        with self.assertRaises(PermissionDenied):
            require_action(
                self.user, "core.branch.read", company=self.company, branch=branch
            )
        self.assertEqual(self.client.get("/api/v1/tenants/").json()["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/v1/tenants/{self.company.pk}/branches/").json()[
                "count"
            ],
            0,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/tenants/{self.company.pk}/").status_code, 404
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/tenants/{self.company.pk}/branches/{branch.pk}/"
            ).status_code,
            404,
        )

    def test_mixed_roles_preserve_per_branch_scope_without_business_expansion(self):
        user = make_user("mixed-scope", tenant=self.company)
        membership = user.tenant_memberships.get()
        north = Branch.objects.create(tenant=self.company, name="North")
        south = Branch.objects.create(tenant=self.company, name="South")
        for branch, role in ((north, "accountant"), (south, "investor")):
            BranchAssignment.objects.create(
                membership=membership, branch=branch, assigned_by=user
            )
            CompanyRoleGrant.objects.create(
                membership=membership, role=role, branch=branch, assigned_by=user
            )
        self.client.force_login(user)
        context = self.client.get("/api/v1/auth/me/").json()["companies"][0]
        self.assertEqual(context["roles"], ["accountant", "investor"])
        self.assertEqual(context["company_wide_roles"], [])
        self.assertEqual(
            {branch["id"]: branch["roles"] for branch in context["branches"]},
            {str(north.pk): ["accountant"], str(south.pk): ["investor"]},
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/tenants/{self.company.pk}/branches/{north.pk}/"
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                f"/api/v1/tenants/{self.company.pk}/branches/{south.pk}/"
            ).status_code,
            404,
        )

    def test_company_wide_role_and_branch_role_are_distinguished(self):
        user = make_user("mixed-company", role="owner", tenant=self.company)
        membership = user.tenant_memberships.get()
        north = Branch.objects.create(tenant=self.company, name="North")
        south = Branch.objects.create(tenant=self.company, name="South")
        for branch in (north, south):
            BranchAssignment.objects.create(
                membership=membership, branch=branch, assigned_by=user
            )
        CompanyRoleGrant.objects.create(
            membership=membership, role="investor", branch=south, assigned_by=user
        )
        self.client.force_login(user)
        company = self.client.get("/api/v1/auth/me/").json()["companies"][0]
        self.assertEqual(company["company_wide_roles"], ["owner"])
        self.assertEqual(
            {branch["id"]: branch["roles"] for branch in company["branches"]},
            {str(north.pk): ["owner"], str(south.pk): ["investor", "owner"]},
        )
        with self.assertRaises(PermissionDenied):
            require_action(user, "account.provision.media", company=self.company)

    def test_existing_role_context_and_business_visibility(self):
        for role in ("owner", "accountant", "media", "investor", "back_office"):
            with self.subTest(role=role):
                user = make_user(
                    f"matrix-{role}",
                    role=role,
                    tenant=self.company,
                    account_kind="platform" if role == "back_office" else "company",
                )
                self.client.force_login(user)
                context = self.client.get("/api/v1/auth/me/").json()
                self.assertEqual(context["roles"], [role])
                self.assertEqual(context["tenant_ids"], [str(self.company.pk)])
                self.assertEqual(
                    self.client.get("/api/v1/tenants/").json()["count"],
                    0 if role == "investor" else 1,
                )

    def test_platform_role_remains_separate_from_company_grant_roles(self):
        operator = make_user(
            "context-platform-scopes",
            role="back_office",
            tenant=self.company,
            account_kind="platform",
        )
        membership = operator.tenant_memberships.get()
        branch = Branch.objects.create(tenant=self.company, name="Platform Scope")
        BranchAssignment.objects.create(
            membership=membership, branch=branch, assigned_by=operator
        )
        self.client.force_login(operator)
        context = self.client.get("/api/v1/auth/me/").json()
        self.assertEqual(context["roles"], ["back_office"])
        self.assertEqual(context["companies"][0]["roles"], [])
        self.assertEqual(context["companies"][0]["company_wide_roles"], [])
        self.assertEqual(context["companies"][0]["branches"][0]["roles"], [])

    def test_ended_membership_and_other_company_do_not_appear(self):
        other = Tenant.objects.create(name="Other", slug="other")
        other_user = make_user("context-other", role="investor", tenant=other)
        self.assertEqual(
            self.client.get("/api/v1/auth/me/").json()["tenant_ids"],
            [str(self.company.pk)],
        )
        self.client.force_login(other_user)
        self.assertEqual(
            self.client.get("/api/v1/auth/me/").json()["tenant_ids"], [str(other.pk)]
        )
        self.client.force_login(self.user)
        self.membership.effective_until = timezone.now()
        self.membership.save(update_fields=["effective_until"])
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["companies"], [])

    def test_branch_role_requires_current_assignment(self):
        branch = Branch.objects.create(tenant=self.company, name="Branch")
        grant = self.membership.role_grants.get(role="investor")
        grant.effective_until = timezone.now()
        grant.save(update_fields=["effective_until"])
        CompanyRoleGrant.objects.create(
            membership=self.membership,
            role="investor",
            branch=branch,
            assigned_by=self.user,
        )
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["companies"], [])
        assignment = BranchAssignment.objects.create(
            membership=self.membership, branch=branch, assigned_by=self.user
        )
        context = self.client.get("/api/v1/auth/me/").json()
        self.assertEqual(context["companies"][0]["roles"], ["investor"])
        self.assertEqual(context["companies"][0]["branches"][0]["id"], str(branch.pk))
        assignment.effective_until = timezone.now()
        assignment.save(update_fields=["effective_until"])
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["companies"], [])

    def test_expired_branch_role_not_projected_when_another_role_is_current(self):
        branch = Branch.objects.create(tenant=self.company, name="South")
        CompanyRoleGrant.objects.create(
            membership=self.membership,
            role="media",
            branch=branch,
            assigned_by=self.user,
        )
        now = timezone.now()
        BranchAssignment.objects.create(
            membership=self.membership,
            branch=branch,
            assigned_by=self.user,
            effective_from=now - timedelta(days=2),
            effective_until=now - timedelta(days=1),
        )
        context = self.client.get("/api/v1/auth/me/").json()
        self.assertEqual(context["companies"][0]["roles"], ["investor"])
        self.assertEqual(context["companies"][0]["branches"], [])

    def test_future_and_expired_grants_and_assignments_are_not_current(self):
        now = timezone.now()
        for suffix, grant_start, grant_end, assignment_start, assignment_end in (
            (
                "future-assignment",
                now - timedelta(days=2),
                None,
                now + timedelta(days=1),
                None,
            ),
            (
                "future-grant",
                now + timedelta(days=1),
                None,
                now - timedelta(days=1),
                None,
            ),
            (
                "expired-grant",
                now - timedelta(days=3),
                now - timedelta(days=2),
                now - timedelta(days=1),
                None,
            ),
        ):
            branch = Branch.objects.create(tenant=self.company, name=suffix)
            CompanyRoleGrant.objects.create(
                membership=self.membership,
                role="media",
                branch=branch,
                assigned_by=self.user,
                effective_from=grant_start,
                effective_until=grant_end,
            )
            BranchAssignment.objects.create(
                membership=self.membership,
                branch=branch,
                assigned_by=self.user,
                effective_from=assignment_start,
                effective_until=assignment_end,
            )
        context = self.client.get("/api/v1/auth/me/").json()["companies"][0]
        self.assertEqual(context["roles"], ["investor"])
        # Company-wide investor scope can see its own current assignments in
        # auth context; it does not turn those assignments into core reads.
        for branch in context["branches"]:
            with self.assertRaises(PermissionDenied):
                require_action(
                    self.user,
                    "core.branch.read",
                    company=self.company,
                    branch=Branch.objects.get(pk=branch["id"]),
                )

    def test_investor_branch_context_is_bounded_and_query_count_stable(self):
        created = 0
        query_count = None
        previous_names = None
        for size in (1, 25, 75, 250):
            branches = Branch.objects.bulk_create(
                [
                    Branch(tenant=self.company, name=f"B{index:04}")
                    for index in range(created, size)
                ]
            )
            BranchAssignment.objects.bulk_create(
                [
                    BranchAssignment(
                        membership=self.membership, branch=branch, assigned_by=self.user
                    )
                    for branch in branches
                ]
            )
            created = size
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get("/api/v1/auth/me/")
            self.assertEqual(response.status_code, 200)
            if query_count is None:
                query_count = len(queries)
            self.assertEqual(len(queries), query_count)
            context = response.json()["companies"][0]
            self.assertEqual(len(context["branches"]), min(size, 20))
            self.assertEqual(context["branches_truncated"], size > 20)
            names = [branch["name"] for branch in context["branches"]]
            self.assertEqual(names, sorted(names))
            if size > 25:
                self.assertEqual(names, previous_names)
            if size == 25:
                previous_names = names
