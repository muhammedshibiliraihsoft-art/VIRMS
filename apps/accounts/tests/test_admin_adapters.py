import re

from django.contrib import admin
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.admin import UserAdmin
from apps.accounts.models import (
    AccountSecurityEvent,
    CompanyRoleGrant,
    RoleAssignment,
    User,
)
from apps.tenants.admin import TenantMembershipAdmin
from apps.tenants.models import Tenant, TenantMembership


class AdminCommandAdapterTests(TestCase):
    password = "A-long-private-admin-adapter-test-passphrase-123!"

    def setUp(self):
        self.client = Client()
        self.north = Tenant.objects.create(name="North", slug="north")
        self.south = Tenant.objects.create(name="South", slug="south")
        self.operator = User.objects.create_superuser(
            login_id="platform-operator",
            email="platform-operator@example.invalid",
            password=self.password,
        )
        RoleAssignment.objects.create(
            user=self.operator,
            role="back_office",
            assigned_by=self.operator,
        )
        self.operator_membership = TenantMembership.objects.create(
            user=self.operator,
            tenant=self.north,
            assigned_by=self.operator,
        )
        self.target = User.objects.create_user(
            login_id="north-investor",
            email="north-investor@example.invalid",
            password=self.password,
        )
        self.target_membership = TenantMembership.objects.create(
            user=self.target,
            tenant=self.north,
            assigned_by=self.operator,
        )
        CompanyRoleGrant.objects.create(
            membership=self.target_membership,
            role="investor",
            assigned_by=self.operator,
        )
        self.other = User.objects.create_user(
            login_id="south-investor",
            email="south-investor@example.invalid",
            password=self.password,
        )
        other_membership = TenantMembership.objects.create(
            user=self.other,
            tenant=self.south,
            assigned_by=self.operator,
        )
        CompanyRoleGrant.objects.create(
            membership=other_membership,
            role="investor",
            assigned_by=self.operator,
        )
        self.client.force_login(self.operator)

    def test_admin_lists_and_autocomplete_are_company_scoped(self):
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "north-investor")
        self.assertNotContains(response, "south-investor")

        response = self.client.get(reverse("admin:tenants_tenant_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "North")
        self.assertNotContains(response, "South")

        response = self.client.get(
            "/admin/autocomplete/",
            {
                "app_label": "tenants",
                "model_name": "tenantmembership",
                "field_name": "user",
                "term": "south",
                "page": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("south-investor", response.content.decode())

    def test_admin_reset_uses_company_lifecycle_and_one_time_nostore_response(self):
        path = f"/admin/accounts/user/{self.target.pk}/password/"
        confirmation = self.client.get(path)
        self.assertEqual(confirmation.status_code, 200)
        self.assertContains(confirmation, "north-investor")
        self.assertNotContains(confirmation, self.password)

        response = self.client.post(path, {"confirm": "yes"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        temporary_password = re.search(
            r"<code>([^<]+)</code>", response.content.decode()
        ).group(1)
        self.target.refresh_from_db()
        self.assertTrue(self.target.check_password(temporary_password))
        self.assertTrue(self.target.must_change_password)
        self.assertEqual(self.target.auth_epoch, 2)
        event = AccountSecurityEvent.objects.get(
            action="reset_password", subject=self.target
        )
        self.assertEqual(event.actor_id, self.operator.pk)
        self.assertEqual(event.company_id, self.north.pk)
        self.assertNotIn(temporary_password, str(event.metadata))

    def test_admin_cannot_reset_another_company_even_when_user_is_superuser(self):
        path = f"/admin/accounts/user/{self.other.pk}/password/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, 403)
        self.other.refresh_from_db()
        self.assertEqual(self.other.auth_epoch, 1)
        self.assertTrue(self.other.check_password(self.password))

    def test_admin_provision_adapter_creates_privileged_account_with_temp_secret(self):
        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="password1"')
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "company": str(self.north.pk),
                "branch": "",
                "role": "owner",
                "login_id": "new-media",
                "email": "new-media@example.invalid",
                "first_name": "New",
                "last_name": "Media",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        temporary_password = re.search(
            r"<code>([^<]+)</code>", response.content.decode()
        ).group(1)
        created = User.objects.get(login_id="new-media")
        self.assertTrue(created.check_password(temporary_password))
        self.assertTrue(created.must_change_password)
        self.assertTrue(
            CompanyRoleGrant.objects.filter(
                membership__user=created,
                membership__tenant=self.north,
                role="owner",
            ).exists()
        )

    def test_platform_admin_adapter_cannot_provision_investor_or_media(self):
        for role in ("investor", "media"):
            with self.subTest(role=role):
                response = self.client.post(
                    reverse("admin:accounts_user_add"),
                    {
                        "company": str(self.north.pk),
                        "branch": "",
                        "role": role,
                        "login_id": f"new-{role}",
                        "email": f"new-{role}@example.invalid",
                    },
                )
                self.assertEqual(response.status_code, 400)
                self.assertFalse(User.objects.filter(login_id=f"new-{role}").exists())

    def test_membership_end_action_is_scoped_and_audited(self):
        model_admin = TenantMembershipAdmin(TenantMembership, admin.site)
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        request = RequestFactory().post("/admin/tenants/tenantmembership/")
        request.user = self.operator
        request.session = self.client.session
        request._messages = FallbackStorage(request)
        rows = model_admin.get_queryset(request).filter(pk=self.target_membership.pk)
        model_admin.end_selected_memberships(request, rows)

        self.target_membership.refresh_from_db()
        self.assertIsNotNone(self.target_membership.effective_until)
        event = AccountSecurityEvent.objects.get(
            action="membership.end", subject=self.target
        )
        self.assertEqual(event.actor_id, self.operator.pk)
        self.assertEqual(event.company_id, self.north.pk)

    def test_superuser_without_back_office_scope_cannot_browse_company_admin(self):
        unscoped = User.objects.create_superuser(
            login_id="unscoped-superuser",
            email="unscoped-superuser@example.invalid",
            password=self.password,
        )
        client = Client()
        client.force_login(unscoped)
        self.assertEqual(
            client.get(reverse("admin:tenants_tenant_changelist")).status_code, 403
        )
        model_admin = UserAdmin(User, admin.site)
        from django.test import RequestFactory

        request = RequestFactory().get("/admin/accounts/user/")
        request.user = unscoped
        self.assertEqual(list(model_admin.get_queryset(request)), [unscoped])
