import hashlib
import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import Client, TransactionTestCase
from django.urls import reverse

from apps.accounts.models import (
    AccountSecurityEvent,
    CompanyRoleGrant,
    RoleAssignment,
    User,
)
from apps.tenants.models import Tenant, TenantMembership


class ExplicitRoleMappingCommandTests(TransactionTestCase):
    def setUp(self):
        self.operator_password = "A-long-private-role-map-passphrase-123!"
        self.company = Tenant.objects.create(name="North", slug="north")
        self.operator = User.objects.create_user(
            login_id="mapping-operator",
            email="mapping-operator@example.invalid",
            password=self.operator_password,
            account_kind=User.AccountKind.PLATFORM,
            must_change_password=False,
            is_active=True,
        )
        self.platform_role = RoleAssignment.objects.create(
            user=self.operator,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=self.operator,
        )
        self.operator_membership = TenantMembership.objects.create(
            user=self.operator, tenant=self.company, assigned_by=self.operator
        )
        self.target = User.objects.create_user(
            login_id="mapping-target",
            email="mapping-target@example.invalid",
            must_change_password=False,
        )
        self.membership = TenantMembership.objects.create(
            user=self.target, tenant=self.company, assigned_by=self.operator
        )
        self.investor_role = RoleAssignment.objects.create(
            user=self.target,
            role=RoleAssignment.Role.INVESTOR,
            assigned_by=self.operator,
        )
        self.media_role = RoleAssignment.objects.create(
            user=self.target,
            role=RoleAssignment.Role.MEDIA,
            assigned_by=self.operator,
        )

    def manifest(self, *, membership_id=None):
        return {
            "format_version": "VIRMS-P1-ROLE-MAP-1",
            "source_database": str(connection.settings_dict["NAME"]),
            "approved_by": str(self.operator.pk),
            "approval_reference": "synthetic-rehearsal-review",
            "platform_role_assignments": [
                {
                    "role_assignment_id": str(self.platform_role.pk),
                    "reason": "Retain explicit technical Platform capability",
                }
            ],
            "denied_role_assignments": [
                {
                    "role_assignment_id": str(self.media_role.pk),
                    "reason": "Leave legacy Media role non-authorizing pending explicit scope review",
                }
            ],
            "mappings": [
                {
                    "role_assignment_id": str(self.investor_role.pk),
                    "membership_id": str(membership_id or self.membership.pk),
                    "branch_id": None,
                    "interval_policy": "preserve_source",
                    "reason": "Explicit synthetic Company-wide Investor mapping",
                }
            ],
        }

    def run_manifest(
        self,
        manifest,
        *,
        apply=False,
        maintenance_confirmed=False,
        operator_password=None,
    ):
        with tempfile.TemporaryDirectory(prefix="virms-role-map-") as folder:
            path = Path(folder) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            output = StringIO()
            if apply:
                with patch(
                    "apps.accounts.management.commands.operator_auth.prompt_platform_password",
                    return_value=operator_password or self.operator_password,
                ):
                    call_command(
                        "map_legacy_company_roles",
                        manifest=str(path),
                        actor_user_id=str(self.operator.pk),
                        apply=apply,
                        maintenance_confirmed=maintenance_confirmed,
                        stdout=output,
                    )
            else:
                call_command(
                    "map_legacy_company_roles",
                    manifest=str(path),
                    actor_user_id=str(self.operator.pk),
                    apply=apply,
                    maintenance_confirmed=maintenance_confirmed,
                    stdout=output,
                )
            return output.getvalue()

    def test_explicit_map_dry_run_apply_and_repeat_preserve_role_history(self):
        dry_run = self.run_manifest(self.manifest())
        self.assertIn("Validated 1 mappings; no rows were changed", dry_run)
        self.assertFalse(CompanyRoleGrant.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            [1, 1],
        )

        applied = self.run_manifest(
            self.manifest(), apply=True, maintenance_confirmed=True
        )
        self.assertIn("Applied 1 and recognized 0 repeated mappings", applied)
        grant = CompanyRoleGrant.objects.get()
        self.assertEqual(grant.membership_id, self.membership.pk)
        self.assertEqual(grant.role, "investor")
        self.assertIsNone(grant.branch_id)
        self.assertEqual(grant.effective_from, self.investor_role.effective_from)
        self.assertEqual(grant.effective_until, self.investor_role.effective_until)
        self.assertTrue(
            RoleAssignment.objects.filter(pk=self.investor_role.pk).exists()
        )
        self.assertTrue(RoleAssignment.objects.filter(pk=self.media_role.pk).exists())
        event = AccountSecurityEvent.objects.get(action="role.map")
        self.assertEqual(event.actor_id, self.operator.pk)
        self.assertEqual(event.subject_id, self.target.pk)
        self.assertEqual(event.company_id, self.company.pk)
        self.assertEqual(event.reason, "Reviewed legacy role-to-Company mapping")
        self.assertNotIn("synthetic-rehearsal-review", event.reason)
        self.assertEqual(
            event.metadata["source_role_assignment_id"], str(self.investor_role.pk)
        )
        cutover = AccountSecurityEvent.objects.get(action="auth.cutover")
        self.assertEqual(cutover.actor_id, self.operator.pk)
        self.assertEqual(cutover.reason, "Reviewed authorization role cutover")
        self.assertEqual(
            cutover.metadata["intent_digest"],
            hashlib.sha256(
                json.dumps(
                    self.manifest(), sort_keys=True, separators=(",", ":")
                ).encode()
            ).hexdigest(),
        )
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            [2, 2],
        )

    def test_cutover_invalidates_old_sessions_and_rejects_changed_intent(self):
        old_session = Client()
        old_session.force_login(self.target)
        self.assertEqual(old_session.get(reverse("auth-me")).status_code, 200)

        self.run_manifest(self.manifest(), apply=True, maintenance_confirmed=True)
        self.assertEqual(old_session.get(reverse("auth-me")).status_code, 401)
        epochs = list(User.objects.order_by("id").values_list("auth_epoch", flat=True))
        self.assertEqual(epochs, [2, 2])

        changed_intent = self.manifest()
        changed_intent["denied_role_assignments"][0][
            "reason"
        ] = "Different reviewed reason cannot silently reuse an applied cutover"
        with self.assertRaisesMessage(
            CommandError,
            "A different authorization cutover manifest was already applied",
        ):
            self.run_manifest(changed_intent, apply=True, maintenance_confirmed=True)
        self.assertEqual(CompanyRoleGrant.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="auth.cutover").count(), 1
        )
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            epochs,
        )

        repeated = self.run_manifest(
            self.manifest(), apply=True, maintenance_confirmed=True
        )
        self.assertIn("Applied 0 and recognized 1 repeated mappings", repeated)
        self.assertEqual(CompanyRoleGrant.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="role.map").count(), 1
        )
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="auth.cutover").count(), 1
        )
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            [2, 2],
        )

    def test_apply_requires_maintenance_confirmation_before_writing(self):
        with self.assertRaisesMessage(
            CommandError, "--apply requires --maintenance-confirmed"
        ):
            self.run_manifest(self.manifest(), apply=True)
        self.assertFalse(CompanyRoleGrant.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            [1, 1],
        )

    def test_wrong_operator_password_rejects_role_mapping_without_changes(self):
        with self.assertRaisesMessage(
            CommandError, "Platform Back Office authentication failed"
        ):
            self.run_manifest(
                self.manifest(),
                apply=True,
                maintenance_confirmed=True,
                operator_password="incorrect-operator-password",
            )

        self.assertFalse(CompanyRoleGrant.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
        self.assertEqual(
            list(User.objects.order_by("id").values_list("auth_epoch", flat=True)),
            [1, 1],
        )

    def test_manifest_must_classify_every_legacy_assignment_before_writing(self):
        extra = RoleAssignment.objects.create(
            user=self.target,
            role=RoleAssignment.Role.ACCOUNTANT,
            assigned_by=self.operator,
        )
        manifest = self.manifest()
        with self.assertRaises(CommandError):
            self.run_manifest(manifest, apply=True, maintenance_confirmed=True)
        self.assertTrue(RoleAssignment.objects.filter(pk=extra.pk).exists())
        self.assertFalse(CompanyRoleGrant.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_mapping_cannot_target_another_accounts_membership(self):
        unrelated = User.objects.create_user(
            login_id="unrelated-mapping-user",
            email="unrelated-mapping-user@example.invalid",
            must_change_password=False,
        )
        other_company = Tenant.objects.create(name="South", slug="south")
        wrong_membership = TenantMembership.objects.create(
            user=unrelated, tenant=other_company, assigned_by=self.operator
        )
        manifest = self.manifest(membership_id=wrong_membership.pk)
        with self.assertRaises(CommandError):
            self.run_manifest(manifest, apply=True, maintenance_confirmed=True)
        self.assertFalse(CompanyRoleGrant.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
