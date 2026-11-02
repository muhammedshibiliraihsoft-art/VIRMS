import uuid
from datetime import timedelta

from django.core.management import CommandError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.management.commands.bootstrap_platform_admin import _apply_bootstrap
from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.tenants.models import Tenant, TenantMembership


class BootstrapTemporalScopeTests(TestCase):
    password = "local-bootstrap-test-passphrase-123!"

    def make_scope(self):
        unique = uuid.uuid4().hex
        user = User.objects.create_superuser(
            login_id=f"b3-{unique}",
            email=f"b3-{unique}@example.invalid",
            password=self.password,
        )
        company = Tenant.objects.create(name="B3 company", slug=f"b3-{unique}")
        return user, company

    def bootstrap(self, user, company, operation_id=None):
        return _apply_bootstrap(
            user_id=user.pk,
            company_id=company.pk,
            company_name=None,
            company_slug=None,
            operation_id=operation_id or uuid.uuid4(),
            operator_password=self.password,
        )

    def test_current_open_and_finite_scope_is_reused(self):
        now = timezone.now()
        for kind in ("role", "membership"):
            for finite in (False, True):
                with self.subTest(kind=kind, finite=finite):
                    user, company = self.make_scope()
                    interval = {
                        "effective_from": now - timedelta(days=1),
                        "effective_until": now + timedelta(days=1) if finite else None,
                    }
                    if kind == "role":
                        row = RoleAssignment.objects.create(
                            user=user, role="back_office", assigned_by=user, **interval
                        )
                        rows = RoleAssignment.objects.filter(
                            user=user, role="back_office"
                        )
                    else:
                        row = TenantMembership.objects.create(
                            user=user, tenant=company, assigned_by=user, **interval
                        )
                        rows = TenantMembership.objects.filter(
                            user=user, tenant=company
                        )
                    operation_id = uuid.uuid4()
                    self.assertEqual(
                        self.bootstrap(user, company, operation_id), (company.pk, False)
                    )
                    self.assertEqual(
                        self.bootstrap(user, company, operation_id), (company.pk, True)
                    )
                    self.assertEqual(list(rows.values_list("pk", flat=True)), [row.pk])
                    self.assertEqual(
                        AccountSecurityEvent.objects.filter(
                            bootstrap_operation_id=operation_id
                        ).count(),
                        1,
                    )

    def test_expired_history_creates_new_scope_without_rewriting_history(self):
        user, company = self.make_scope()
        now = timezone.now()
        interval = {
            "effective_from": now - timedelta(days=2),
            "effective_until": now - timedelta(days=1),
        }
        role = RoleAssignment.objects.create(
            user=user, role="back_office", assigned_by=user, **interval
        )
        membership = TenantMembership.objects.create(
            user=user, tenant=company, assigned_by=user, **interval
        )
        self.bootstrap(user, company)
        role.refresh_from_db()
        membership.refresh_from_db()
        self.assertEqual(role.effective_until, interval["effective_until"])
        self.assertEqual(membership.effective_until, interval["effective_until"])
        self.assertEqual(
            RoleAssignment.objects.filter(user=user, role="back_office").count(), 2
        )
        self.assertEqual(
            TenantMembership.objects.filter(user=user, tenant=company).count(), 2
        )

    def test_future_open_and_finite_scope_requires_review_without_partial_changes(self):
        now = timezone.now()
        for kind in ("role", "membership"):
            for finite in (False, True):
                with self.subTest(kind=kind, finite=finite):
                    user, company = self.make_scope()
                    interval = {
                        "effective_from": now + timedelta(days=1),
                        "effective_until": now + timedelta(days=2) if finite else None,
                    }
                    if kind == "role":
                        RoleAssignment.objects.create(
                            user=user, role="back_office", assigned_by=user, **interval
                        )
                    else:
                        TenantMembership.objects.create(
                            user=user, tenant=company, assigned_by=user, **interval
                        )
                    with self.assertRaisesMessage(CommandError, "future"):
                        self.bootstrap(user, company)
                    self.assertEqual(
                        RoleAssignment.objects.filter(user=user).count(),
                        int(kind == "role"),
                    )
                    self.assertEqual(
                        TenantMembership.objects.filter(
                            user=user, tenant=company
                        ).count(),
                        int(kind == "membership"),
                    )
                    self.assertFalse(
                        AccountSecurityEvent.objects.filter(
                            actor=user, action="bootstrap"
                        ).exists()
                    )

    def test_current_and_future_scope_requires_review(self):
        now = timezone.now()
        for kind in ("role", "membership"):
            with self.subTest(kind=kind):
                user, company = self.make_scope()
                for starts, ends in (
                    (now - timedelta(days=1), now + timedelta(days=1)),
                    (now + timedelta(days=2), now + timedelta(days=3)),
                ):
                    if kind == "role":
                        RoleAssignment.objects.create(
                            user=user,
                            role="back_office",
                            assigned_by=user,
                            effective_from=starts,
                            effective_until=ends,
                        )
                    else:
                        TenantMembership.objects.create(
                            user=user,
                            tenant=company,
                            assigned_by=user,
                            effective_from=starts,
                            effective_until=ends,
                        )
                with self.assertRaisesMessage(CommandError, "future"):
                    self.bootstrap(user, company)
                self.assertFalse(
                    AccountSecurityEvent.objects.filter(
                        actor=user, action="bootstrap"
                    ).exists()
                )

    def test_overlapping_current_scope_requires_review(self):
        now = timezone.now()
        for kind in ("role", "membership"):
            with self.subTest(kind=kind):
                user, company = self.make_scope()
                for days in (1, 2):
                    if kind == "role":
                        RoleAssignment.objects.create(
                            user=user,
                            role="back_office",
                            assigned_by=user,
                            effective_from=now - timedelta(days=days),
                            effective_until=now + timedelta(days=days),
                        )
                    else:
                        TenantMembership.objects.create(
                            user=user,
                            tenant=company,
                            assigned_by=user,
                            effective_from=now - timedelta(days=days),
                            effective_until=now + timedelta(days=days),
                        )
                with self.assertRaisesMessage(CommandError, "Overlapping"):
                    self.bootstrap(user, company)
                self.assertFalse(
                    AccountSecurityEvent.objects.filter(
                        actor=user, action="bootstrap"
                    ).exists()
                )

    def test_future_role_rolls_back_new_company_creation(self):
        user, _ = self.make_scope()
        now = timezone.now()
        RoleAssignment.objects.create(
            user=user,
            role="back_office",
            assigned_by=user,
            effective_from=now + timedelta(days=1),
            effective_until=now + timedelta(days=2),
        )
        slug = f"future-b3-{uuid.uuid4().hex}"
        with self.assertRaisesMessage(CommandError, "future"):
            _apply_bootstrap(
                user_id=user.pk,
                company_id=None,
                company_name="Rejected future bootstrap",
                company_slug=slug,
                operation_id=uuid.uuid4(),
                operator_password=self.password,
            )
        self.assertFalse(Tenant.objects.filter(slug=slug).exists())
        self.assertFalse(AccountSecurityEvent.objects.filter(actor=user).exists())
