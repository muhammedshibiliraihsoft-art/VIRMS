from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase

from apps.accounts.admin import UserAdmin
from apps.accounts.models import AccountSecurityEvent, User


class AdminPasswordLifecycleTests(TestCase):
    old = "A-Long-Private-Test-Passphrase-123!"
    new = "A-Different-Long-Private-Passphrase-123!"

    def setUp(self):
        self.admin = User.objects.create_superuser(
            login_id="systemadmin",
            email="systemadmin@example.invalid",
            password=self.old,
        )
        self.client.force_login(self.admin)

    def test_admin_self_change_uses_private_lifecycle_and_preserves_only_current_session(
        self,
    ):
        other = Client()
        other.force_login(self.admin)
        self.assertEqual(self.client.get("/admin/password_change/").status_code, 200)
        response = self.client.post(
            "/admin/password_change/",
            {
                "old_password": self.old,
                "new_password1": self.new,
                "new_password2": self.new,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(self.new))
        self.assertEqual(self.admin.auth_epoch, 2)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.assertEqual(other.get("/api/v1/auth/me/").status_code, 401)
        event = AccountSecurityEvent.objects.get(action="change_password")
        self.assertEqual(event.subject_id, self.admin.pk)
        self.assertNotIn(self.new, str(event.metadata))
        self.assertNotIn(self.old, str(event.metadata))

    def test_invalid_admin_change_is_atomic(self):
        response = self.client.post(
            "/admin/password_change/",
            {
                "old_password": "incorrect",
                "new_password1": "short",
                "new_password2": "short",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(self.old))
        self.assertEqual(self.admin.auth_epoch, 1)
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_legacy_target_reset_and_direct_model_password_edit_are_blocked(self):
        target = User.objects.create_user(
            login_id="target", email="target@example.invalid", password=self.old
        )
        path = f"/admin/accounts/user/{target.pk}/password/"
        self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(
            self.client.post(
                path, {"password1": self.new, "password2": self.new}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                f"/admin/accounts/user/{self.admin.pk}/password/"
            ).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(
                f"/admin/accounts/user/{self.admin.pk}/password/",
                {"password1": self.new, "password2": self.new},
            ).status_code,
            403,
        )
        changed = User.objects.get(pk=target.pk)
        changed.set_password(self.new)
        with self.assertRaises(PermissionDenied):
            UserAdmin.save_model(None, None, changed, None, True)
        target.refresh_from_db()
        self.assertTrue(target.check_password(self.old))
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_admin_membership_add_form_and_post_are_blocked(self):
        from apps.tenants.models import Tenant, TenantMembership

        company = Tenant.objects.create(name="Other", slug="other")
        target = User.objects.create_user(
            login_id="target", email="target@example.invalid", password=self.old
        )
        path = "/admin/tenants/tenantmembership/add/"
        self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(
            self.client.post(
                path,
                {
                    "user": str(target.pk),
                    "tenant": str(company.pk),
                    "assigned_by": str(self.admin.pk),
                },
            ).status_code,
            403,
        )
        self.assertFalse(TenantMembership.objects.filter(user=target).exists())

    def test_admin_cannot_mutate_security_roles_company_or_membership_history(self):
        from apps.accounts.models import RoleAssignment
        from apps.tenants.models import Tenant, TenantMembership

        company = Tenant.objects.create(name="North", slug="north")
        member = User.objects.create_user(
            login_id="member", email="member@example.invalid", password=self.old
        )
        membership = TenantMembership.objects.create(
            user=member, tenant=company, assigned_by=self.admin
        )
        role = RoleAssignment.objects.create(
            user=member, role="investor", assigned_by=self.admin
        )
        self.client.post(
            f"/admin/accounts/user/{member.pk}/change/",
            {"is_active": "0", "is_superuser": "1", "is_staff": "1"},
        )
        self.client.post(
            f"/admin/tenants/tenant/{company.pk}/change/",
            {"name": "Changed", "slug": "changed", "is_active": "0"},
        )
        self.client.post(
            f"/admin/tenants/tenantmembership/{membership.pk}/change/",
            {"effective_until": "2000-01-01 00:00:00+00:00"},
        )
        self.client.post(
            f"/admin/accounts/roleassignment/{role.pk}/change/",
            {"role": "back_office"},
        )
        member.refresh_from_db()
        company.refresh_from_db()
        membership.refresh_from_db()
        role.refresh_from_db()
        self.assertTrue(member.is_active)
        self.assertFalse(member.is_superuser)
        self.assertFalse(member.is_staff)
        self.assertEqual(company.name, "North")
        self.assertTrue(company.is_active)
        self.assertIsNone(membership.effective_until)
        self.assertEqual(role.role, "investor")
        self.assertFalse(
            User.objects.filter(is_superuser=False, is_staff=True).exists()
        )

    def test_membership_history_fields_are_read_only_in_generic_admin(self):
        from django.contrib import admin
        from django.test import RequestFactory

        from apps.tenants.admin import TenantMembershipAdmin
        from apps.tenants.models import Tenant, TenantMembership

        model_admin = TenantMembershipAdmin(TenantMembership, admin.site)
        request = RequestFactory().get("/admin/tenants/tenantmembership/")
        request.user = self.admin
        company = Tenant.objects.create(name="North", slug="north")
        member = User.objects.create_user(
            login_id="member", email="member@example.invalid", password=self.old
        )
        membership = TenantMembership.objects.create(
            user=member, tenant=company, assigned_by=self.admin
        )
        readonly = set(model_admin.get_readonly_fields(request, membership))
        self.assertEqual(
            readonly,
            {field.name for field in TenantMembership._meta.fields},
        )
        add_readonly = set(model_admin.get_readonly_fields(request))
        self.assertTrue(
            {"id", "effective_from", "effective_until", "assigned_by"} <= add_readonly
        )
        self.assertFalse({"user", "tenant"} & add_readonly)
