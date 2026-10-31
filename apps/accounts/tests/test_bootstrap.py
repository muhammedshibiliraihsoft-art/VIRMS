import uuid
from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.tenants.models import Tenant, TenantMembership


class PlatformBootstrapTests(TestCase):
    def setUp(self):
        self.password = "A-long-private-bootstrap-test-passphrase-123!"
        self.admin = User.objects.create_superuser(
            login_id="bootstrap-admin",
            email="bootstrap-admin@example.invalid",
            password=self.password,
        )

    def bootstrap_first_company(self, operation_id):
        output = StringIO()
        with patch(
            "apps.accounts.management.commands.operator_auth.prompt_platform_password",
            return_value=self.password,
        ):
            call_command(
                "bootstrap_platform_admin",
                user_id=str(self.admin.pk),
                company_name="North Company",
                company_slug="north-company",
                operation_id=str(operation_id),
                stdout=output,
            )
        return output.getvalue()

    def test_first_company_bootstrap_is_explicit_audited_and_repeat_safe(self):
        operation_id = uuid.uuid4()

        output = self.bootstrap_first_company(operation_id)

        company = Tenant.objects.get(slug="north-company")
        membership = TenantMembership.objects.get(
            user=self.admin, tenant=company, effective_until__isnull=True
        )
        role = RoleAssignment.objects.get(
            user=self.admin, role="back_office", effective_until__isnull=True
        )
        event = AccountSecurityEvent.objects.get(bootstrap_operation_id=operation_id)
        self.assertEqual(membership.assigned_by_id, self.admin.pk)
        self.assertEqual(role.assigned_by_id, self.admin.pk)
        self.assertEqual(event.actor_id, self.admin.pk)
        self.assertEqual(event.subject_id, self.admin.pk)
        self.assertEqual(event.company_id, company.pk)
        self.assertEqual(event.action, "bootstrap")
        self.assertEqual(len(event.metadata["intent_digest"]), 64)
        self.assertNotIn("password", output.lower())
        self.assertTrue(
            self.admin.check_password("A-long-private-bootstrap-test-passphrase-123!")
        )

        replay = self.bootstrap_first_company(operation_id)

        self.assertIn("already applied", replay.lower())
        self.assertEqual(Tenant.objects.count(), 1)
        self.assertEqual(TenantMembership.objects.count(), 1)
        self.assertEqual(RoleAssignment.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="bootstrap").count(), 1
        )

    def test_same_operation_id_with_different_intent_conflicts_without_partial_rows(
        self,
    ):
        operation_id = uuid.uuid4()
        self.bootstrap_first_company(operation_id)

        with patch(
            "apps.accounts.management.commands.operator_auth.prompt_platform_password",
            return_value=self.password,
        ):
            with self.assertRaises(CommandError):
                call_command(
                    "bootstrap_platform_admin",
                    user_id=str(self.admin.pk),
                    company_name="Different Company",
                    company_slug="different-company",
                    operation_id=str(operation_id),
                    stdout=StringIO(),
                )

        self.assertEqual(Tenant.objects.count(), 1)
        self.assertEqual(TenantMembership.objects.count(), 1)
        self.assertEqual(RoleAssignment.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="bootstrap").count(), 1
        )

    def test_existing_company_bootstrap_requires_explicit_user_and_company_ids(self):
        company = Tenant.objects.create(name="Existing", slug="existing")
        operation_id = uuid.uuid4()
        with patch(
            "apps.accounts.management.commands.operator_auth.prompt_platform_password",
            return_value=self.password,
        ):
            call_command(
                "bootstrap_platform_admin",
                user_id=str(self.admin.pk),
                company_id=str(company.pk),
                operation_id=str(operation_id),
                stdout=StringIO(),
            )

        self.assertTrue(
            TenantMembership.objects.filter(user=self.admin, tenant=company).exists()
        )
        self.assertEqual(
            AccountSecurityEvent.objects.get(
                bootstrap_operation_id=operation_id
            ).company_id,
            company.pk,
        )

    def test_company_user_and_implicit_company_selection_are_rejected(self):
        company_user = User.objects.create_user(
            login_id="company-user",
            email="company-user@example.invalid",
            password="A-long-private-company-test-passphrase-123!",
        )
        with patch(
            "apps.accounts.management.commands.operator_auth.prompt_platform_password",
            return_value="A-long-private-company-test-passphrase-123!",
        ):
            with self.assertRaisesMessage(
                CommandError,
                "Explicit user must be an active Django Platform superuser",
            ):
                call_command(
                    "bootstrap_platform_admin",
                    user_id=str(company_user.pk),
                    company_id=str(uuid.uuid4()),
                    operation_id=str(uuid.uuid4()),
                    stdout=StringIO(),
                )
        with self.assertRaises(CommandError):
            call_command(
                "bootstrap_platform_admin",
                user_id=str(self.admin.pk),
                operation_id=str(uuid.uuid4()),
                stdout=StringIO(),
            )

        self.assertEqual(Tenant.objects.count(), 0)
        self.assertFalse(RoleAssignment.objects.exists())
        self.assertFalse(TenantMembership.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_wrong_operator_password_does_not_bootstrap_anything(self):
        with patch(
            "apps.accounts.management.commands.operator_auth.prompt_platform_password",
            return_value="incorrect-operator-password",
        ):
            with self.assertRaisesMessage(
                CommandError, "Platform Back Office authentication failed"
            ):
                call_command(
                    "bootstrap_platform_admin",
                    user_id=str(self.admin.pk),
                    company_name="North Company",
                    company_slug="north-company",
                    operation_id=str(uuid.uuid4()),
                    stdout=StringIO(),
                )

        self.assertEqual(Tenant.objects.count(), 0)
        self.assertFalse(RoleAssignment.objects.exists())
        self.assertFalse(TenantMembership.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
