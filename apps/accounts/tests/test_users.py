import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import (
    AccountSecurityEvent,
    LoginAttempt,
    RoleAssignment,
    User,
)
from apps.tenants.models import Tenant, TenantMembership


def make_user(login_id, *, role=None, tenant=None, must_change=False):
    user = User.objects.create_user(
        login_id=login_id,
        email=f"{login_id}@example.invalid",
        password="A-Long-Private-Test-Passphrase-123!",
        must_change_password=must_change,
    )
    if role:
        RoleAssignment.objects.create(user=user, role=role, assigned_by=user)
    if tenant:
        TenantMembership.objects.create(user=user, tenant=tenant, assigned_by=user)
    return user


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.tenant = Tenant.objects.create(name="North", slug="north")
        self.user = make_user("accountant1", role="accountant", tenant=self.tenant)

    def csrf_post(self, path, data):
        self.client.get(reverse("auth-csrf"))
        return self.client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

    def test_public_signup_and_jwt_routes_do_not_exist(self):
        self.assertEqual(self.client.post("/api/v1/auth/users/").status_code, 404)
        self.assertEqual(
            self.client.post("/api/v1/auth/token/refresh/").status_code, 404
        )

    def test_unauthenticated_api_is_denied(self):
        self.assertEqual(self.client.get("/api/v1/tenants/").status_code, 401)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 401)

    def test_login_requires_csrf_and_uses_session(self):
        response = self.client.post(
            reverse("auth-login"),
            data=json.dumps(
                {
                    "login_id": "accountant1",
                    "password": "A-Long-Private-Test-Passphrase-123!",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        response = self.csrf_post(
            reverse("auth-login"),
            {
                "login_id": "accountant1",
                "password": "A-Long-Private-Test-Passphrase-123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("sessionid", self.client.cookies)
        self.assertNotIn("access", response.json())
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 200)

    def test_invalid_login_is_generic_and_throttled(self):
        for _ in range(3):
            response = self.csrf_post(
                reverse("auth-login"), {"login_id": "missing", "password": "wrong"}
            )
            self.assertEqual(response.status_code, 401)
        self.assertEqual(LoginAttempt.objects.count(), 1)
        response = self.csrf_post(
            reverse("auth-login"), {"login_id": "missing", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 429)

    def test_first_login_replacement_and_current_password_required(self):
        self.user.must_change_password = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/api/v1/tenants/").status_code, 403)
        bad = self.csrf_post(
            reverse("auth-password-change"),
            {
                "current_password": "incorrect",
                "new_password": "A-Different-Long-Private-Passphrase-123!",
                "confirm_password": "A-Different-Long-Private-Passphrase-123!",
            },
        )
        self.assertEqual(bad.status_code, 400)
        good = self.csrf_post(
            reverse("auth-password-change"),
            {
                "current_password": "A-Long-Private-Test-Passphrase-123!",
                "new_password": "A-Different-Long-Private-Passphrase-123!",
                "confirm_password": "A-Different-Long-Private-Passphrase-123!",
            },
        )
        self.assertEqual(good.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/tenants/").status_code, 200)
        self.assertTrue(
            AccountSecurityEvent.objects.filter(action="change_password").exists()
        )


class ProvisioningTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="North", slug="north")
        self.other = Tenant.objects.create(name="South", slug="south")
        self.back_office = make_user(
            "backoffice1", role="back_office", tenant=self.tenant
        )
        self.accountant = make_user(
            "accountant1", role="accountant", tenant=self.tenant
        )
        self.owner = make_user("owner1", role="owner", tenant=self.tenant)

    def provision(self, actor, role, tenant, login_id="newuser"):
        self.client.force_login(actor)
        return self.client.post(
            reverse("account-provision"),
            data=json.dumps(
                {
                    "login_id": login_id,
                    "email": f"{login_id}@example.invalid",
                    "role": role,
                    "tenant_id": str(tenant.pk),
                }
            ),
            content_type="application/json",
        )

    def test_back_office_can_provision_owner_with_temporary_password(self):
        response = self.provision(self.back_office, "owner", self.tenant)
        self.assertEqual(response.status_code, 201)
        self.assertIn("no-store", response["Cache-Control"])
        user = User.objects.get(login_id="newuser")
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password(response.json()["temporary_password"]))
        self.assertTrue(
            AccountSecurityEvent.objects.filter(
                actor=self.back_office, subject=user
            ).exists()
        )

    def test_accountant_can_provision_investor_but_not_owner(self):
        self.assertEqual(
            self.provision(self.accountant, "investor", self.tenant).status_code, 201
        )
        self.assertEqual(
            self.provision(
                self.accountant, "owner", self.tenant, "noowner"
            ).status_code,
            403,
        )

    def test_owner_and_unrelated_tenant_cannot_provision(self):
        self.assertEqual(
            self.provision(self.owner, "investor", self.tenant).status_code, 403
        )
        self.assertEqual(
            self.provision(
                self.accountant, "media", self.other, "outsider"
            ).status_code,
            403,
        )
        self.assertFalse(User.objects.filter(login_id="outsider").exists())

    def test_provision_requires_authentication_and_csrf(self):
        payload = json.dumps(
            {
                "login_id": "blocked1",
                "email": "blocked1@example.invalid",
                "role": "owner",
                "tenant_id": str(self.tenant.pk),
            }
        )
        strict_client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            strict_client.post(
                reverse("account-provision"),
                data=payload,
                content_type="application/json",
            ).status_code,
            401,
        )
        strict_client.force_login(self.back_office)
        self.assertEqual(
            strict_client.post(
                reverse("account-provision"),
                data=payload,
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertFalse(User.objects.filter(login_id="blocked1").exists())

    def test_unrelated_account_reset_is_hidden(self):
        target = make_user("target1", role="investor", tenant=self.other)
        self.client.force_login(self.accountant)
        response = self.client.post(reverse("account-reset", args=[target.pk]))
        self.assertEqual(response.status_code, 404)

    def test_reset_revokes_old_session_and_requires_change(self):
        target = make_user("target1", role="investor", tenant=self.tenant)
        old_client = Client()
        old_client.force_login(target)
        self.client.force_login(self.accountant)
        response = self.client.post(reverse("account-reset", args=[target.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertTrue(User.objects.get(pk=target.pk).must_change_password)
        self.assertEqual(old_client.get(reverse("auth-me")).status_code, 401)

    def test_deactivation_blocks_login_and_preserves_history(self):
        target = make_user("target1", role="investor", tenant=self.tenant)
        self.client.force_login(self.accountant)
        response = self.client.post(
            reverse("account-status", args=[target.pk]),
            data=json.dumps({"is_active": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertFalse(target.has_usable_password())
        self.assertTrue(target.role_assignments.exists())
        self.assertTrue(target.tenant_memberships.exists())
        other_client = Client()
        self.assertFalse(
            other_client.login(
                username="target1", password="A-Long-Private-Test-Passphrase-123!"
            )
        )


class AdminFoundationTests(TestCase):
    def test_superuser_can_open_account_provisioning_form(self):
        admin = User.objects.create_superuser(
            login_id="systemadmin",
            email="systemadmin@example.invalid",
            password="A-Long-Private-Test-Passphrase-123!",
        )
        self.client.force_login(admin)
        self.assertEqual(self.client.get("/admin/accounts/user/add/").status_code, 200)
        response = self.client.post(
            "/admin/accounts/user/add/",
            {
                "login_id": "admincreated",
                "email": "admincreated@example.invalid",
                "password1": "A-Long-Private-Test-Passphrase-123!",
                "password2": "A-Long-Private-Test-Passphrase-123!",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = User.objects.get(login_id="admincreated")
        self.assertTrue(created.must_change_password)
        self.assertEqual(created.created_by, admin)
