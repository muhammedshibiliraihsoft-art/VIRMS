from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.test_users import make_user
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership
from apps.tenants.selectors import visible_branches, visible_companies


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.north = Tenant.objects.create(name="North", slug="north")
        self.south = Tenant.objects.create(name="South", slug="south")
        self.member = make_user("member1", role="accountant", tenant=self.north)
        self.nonmember = make_user("nonmember1", role="accountant")

    def test_member_list_and_detail_are_scoped(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("tenant-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in response.json()["results"]], [str(self.north.pk)]
        )
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.north.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.south.pk])).status_code,
            404,
        )

    def test_nonmember_and_roleless_user_cannot_see_tenant(self):
        self.client.force_login(self.nonmember)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        self.assertEqual(
            self.client.get(reverse("tenant-detail", args=[self.north.pk])).status_code,
            404,
        )
        roleless = make_user("roleless1", tenant=self.north)
        self.client.force_login(roleless)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])

        legacy = make_user(
            "legacy-global-only",
            role="accountant",
            tenant=self.north,
            scoped_grant=False,
        )
        self.client.force_login(legacy)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        me = self.client.get(reverse("auth-me")).json()
        self.assertEqual(me["roles"], [])
        self.assertEqual(me["tenant_ids"], [])
        self.assertEqual(me["companies"], [])

    def test_company_account_with_legacy_back_office_role_is_not_platform(self):
        legacy_platform_role = make_user(
            "legacy-back-office", role="back_office", tenant=self.north
        )
        self.client.force_login(legacy_platform_role)
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        me = self.client.get(reverse("auth-me")).json()
        self.assertEqual(me["roles"], [])
        self.assertEqual(me["companies"], [])

    def test_expired_membership_and_inactive_tenant_are_hidden(self):
        self.client.force_login(self.member)
        membership = self.member.tenant_memberships.get(tenant=self.north)
        membership.effective_until = timezone.now()
        membership.save()
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])
        membership.effective_until = None
        membership.save()
        self.north.is_active = False
        self.north.save()
        self.assertEqual(self.client.get(reverse("tenant-list")).json()["results"], [])

    def test_no_generic_tenant_mutation_routes(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse("tenant-list"), {}).status_code, 405)
        self.assertEqual(
            self.client.delete(
                reverse("tenant-detail", args=[self.north.pk])
            ).status_code,
            405,
        )

    def test_branch_reads_require_company_grant_and_effective_assignment(self):
        visible = Branch.objects.create(tenant=self.north, name="Visible")
        hidden = Branch.objects.create(tenant=self.north, name="Hidden")
        membership = self.member.tenant_memberships.get(tenant=self.north)
        BranchAssignment.objects.create(
            membership=membership, branch=visible, assigned_by=self.member
        )
        self.client.force_login(self.member)
        listing = self.client.get(reverse("company-branch-list", args=[self.north.pk]))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(
            [row["id"] for row in listing.json()["results"]], [str(visible.pk)]
        )
        self.assertEqual(
            self.client.get(
                reverse("company-branch-detail", args=[self.north.pk, visible.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("company-branch-detail", args=[self.north.pk, hidden.pk])
            ).status_code,
            404,
        )

    def test_company_list_query_count_is_constant_and_page_is_bounded(self):
        from apps.accounts.models import RoleAssignment, User

        self.south.is_active = False
        self.south.save(update_fields=["is_active"])
        platform = User.objects.create_superuser(
            login_id="read-audit-platform",
            email="read-audit-platform@example.invalid",
            password="A-Long-Private-Test-Passphrase-123!",
        )
        RoleAssignment.objects.create(
            user=platform,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=platform,
        )
        TenantMembership.objects.create(
            user=platform,
            tenant=self.north,
            assigned_by=platform,
        )
        self.client.force_login(platform)

        with CaptureQueriesContext(connection) as one_company_queries:
            one_company = self.client.get(reverse("tenant-list"))
        self.assertEqual(one_company.status_code, 200)
        self.assertEqual(one_company.json()["count"], 1)

        for index in range(24):
            company = Tenant.objects.create(
                name=f"Audit Company {index:02d}",
                slug=f"audit-company-{index:02d}",
            )
            TenantMembership.objects.create(
                user=platform,
                tenant=company,
                assigned_by=platform,
            )
        with CaptureQueriesContext(connection) as many_company_queries:
            many_companies = self.client.get(reverse("tenant-list"))

        self.assertEqual(many_companies.status_code, 200)
        self.assertEqual(many_companies.json()["count"], 25)
        self.assertEqual(len(many_companies.json()["results"]), 20)
        self.assertEqual(len(one_company_queries), len(many_company_queries))
        print(
            "P1-19 Company read: "
            f"{len(one_company_queries)} queries / {len(one_company.content)} bytes "
            "at 1 row; "
            f"{len(many_company_queries)} queries / {len(many_companies.content)} bytes "
            "at 25 rows (20-row page)."
        )

    def test_branch_list_query_count_is_constant_and_selector_plans_compile(self):
        first = Branch.objects.create(tenant=self.north, name="Audit Branch 00")
        BranchAssignment.objects.create(
            membership=self.member.tenant_memberships.get(tenant=self.north),
            branch=first,
            assigned_by=self.member,
        )
        self.client.force_login(self.member)

        with CaptureQueriesContext(connection) as one_branch_queries:
            one_branch = self.client.get(
                reverse("company-branch-list", args=[self.north.pk])
            )
        self.assertEqual(one_branch.status_code, 200)
        self.assertEqual(one_branch.json()["count"], 1)

        membership = self.member.tenant_memberships.get(tenant=self.north)
        for index in range(1, 25):
            branch = Branch.objects.create(
                tenant=self.north,
                name=f"Audit Branch {index:02d}",
            )
            BranchAssignment.objects.create(
                membership=membership,
                branch=branch,
                assigned_by=self.member,
            )
        with CaptureQueriesContext(connection) as many_branch_queries:
            many_branches = self.client.get(
                reverse("company-branch-list", args=[self.north.pk])
            )

        self.assertEqual(many_branches.status_code, 200)
        self.assertEqual(many_branches.json()["count"], 25)
        self.assertEqual(len(many_branches.json()["results"]), 20)
        self.assertEqual(len(one_branch_queries), len(many_branch_queries))
        print(
            "P1-19 Branch read: "
            f"{len(one_branch_queries)} queries / {len(one_branch.content)} bytes "
            "at 1 row; "
            f"{len(many_branch_queries)} queries / {len(many_branches.content)} bytes "
            "at 25 rows (20-row page)."
        )

        explain_roots = []
        for queryset in (
            visible_companies(self.member),
            visible_branches(self.member, self.north.pk),
        ):
            sql, params = queryset.query.sql_with_params()
            with connection.cursor() as cursor:
                cursor.execute(f"EXPLAIN (FORMAT JSON) {sql}", params)
                plan = cursor.fetchone()[0]
            self.assertTrue(plan)
            self.assertIn("Plan", plan[0])
            explain_roots.append(plan[0]["Plan"]["Node Type"])
        print(f"P1-19 PostgreSQL EXPLAIN root nodes: {explain_roots}.")
