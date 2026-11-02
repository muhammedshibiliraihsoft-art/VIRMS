"""Concurrent service operations preserve scope and audit invariants."""

import threading

from django.core.exceptions import ValidationError
from django.db import DatabaseError, close_old_connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from apps.accounts.models import AccountSecurityEvent, CompanyRoleGrant
from apps.accounts.tests.test_users import make_user
from apps.tenants.commands import (
    add_membership,
    assign_branch,
    end_membership,
    end_scope_row,
    grant_role,
)
from apps.tenants.models import Branch, BranchAssignment, Tenant, TenantMembership


class ScopeConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="Concurrent", slug="concurrent")
        self.actor = make_user(
            "scope-concurrent-admin",
            role="back_office",
            tenant=self.company,
            account_kind="platform",
        )
        self.target = make_user("scope-concurrent-target")
        self.branch = Branch.objects.create(tenant=self.company, name="North")

    def race(self, operation):
        barrier = threading.Barrier(2)
        results = []

        def run():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                operation()
                results.append("ok")
            except Exception as exc:
                results.append(exc)
            finally:
                close_old_connections()

        threads = [threading.Thread(target=run, daemon=True) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 2)
        return results

    def assert_one_creation(self, operation):
        results = self.race(operation)
        self.assertEqual(results.count("ok"), 1, results)
        errors = [result for result in results if result != "ok"]
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ValidationError)

    def test_concurrent_adds_do_not_duplicate_scope_or_audit(self):
        self.assert_one_creation(
            lambda: add_membership(
                actor=self.actor, company=self.company, user=self.target
            )
        )
        membership = TenantMembership.objects.get(user=self.target, tenant=self.company)
        self.assertEqual(
            TenantMembership.objects.filter(
                user=self.target, tenant=self.company
            ).count(),
            1,
        )
        self.assertEqual(
            AccountSecurityEvent.objects.filter(
                subject=self.target, action="membership.add"
            ).count(),
            1,
        )

        self.assert_one_creation(
            lambda: assign_branch(
                actor=self.actor, membership=membership, branch=self.branch
            )
        )
        self.assertEqual(
            BranchAssignment.objects.filter(
                membership=membership, branch=self.branch
            ).count(),
            1,
        )
        self.assertEqual(
            AccountSecurityEvent.objects.filter(
                subject=self.target, action="assignment.add"
            ).count(),
            1,
        )

        self.assert_one_creation(
            lambda: grant_role(
                actor=self.actor,
                membership=membership,
                role="investor",
                branch=self.branch,
            )
        )
        self.assertEqual(
            CompanyRoleGrant.objects.filter(
                membership=membership, role="investor", branch=self.branch
            ).count(),
            1,
        )
        self.assertEqual(
            AccountSecurityEvent.objects.filter(
                subject=self.target, action="role.add"
            ).count(),
            1,
        )

    def test_concurrent_end_is_idempotent_and_audited_once(self):
        membership = TenantMembership.objects.create(
            user=self.target, tenant=self.company, assigned_by=self.actor
        )
        assignment = BranchAssignment.objects.create(
            membership=membership, branch=self.branch, assigned_by=self.actor
        )
        grant = CompanyRoleGrant.objects.create(
            membership=membership,
            role="investor",
            branch=self.branch,
            assigned_by=self.actor,
        )
        for row, event in (
            (grant, "role.end"),
            (assignment, "assignment.end"),
            (membership, "membership.end"),
        ):
            operation = (
                (lambda row=row: end_membership(actor=self.actor, membership=row))
                if isinstance(row, TenantMembership)
                else (lambda row=row: end_scope_row(actor=self.actor, row=row))
            )
            results = self.race(operation)
            self.assertEqual(results, ["ok", "ok"], results)
            row.refresh_from_db()
            self.assertLessEqual(row.effective_until, timezone.now())
            self.assertEqual(
                AccountSecurityEvent.objects.filter(
                    subject=self.target, action=event
                ).count(),
                1,
            )

    def test_reopen_waiting_for_close_cannot_restore_authority(self):
        membership = TenantMembership.objects.create(
            user=self.target, tenant=self.company, assigned_by=self.actor
        )
        locked = threading.Event()
        attempt = threading.Event()
        errors = []

        def close():
            close_old_connections()
            try:
                with transaction.atomic():
                    row = TenantMembership.objects.select_for_update().get(
                        pk=membership.pk
                    )
                    locked.set()
                    if not attempt.wait(10):
                        raise RuntimeError("reopen did not start")
                    row.effective_until = timezone.now()
                    row.save(update_fields=["effective_until"])
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        def reopen():
            close_old_connections()
            try:
                if not locked.wait(10):
                    raise RuntimeError("close did not lock")
                attempt.set()
                TenantMembership.objects.filter(pk=membership.pk).update(
                    effective_until=None
                )
                errors.append(AssertionError("reopen was accepted"))
            except DatabaseError:
                pass
            except Exception as exc:
                errors.append(exc)
            finally:
                close_old_connections()

        threads = [
            threading.Thread(target=close, daemon=True),
            threading.Thread(target=reopen, daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        membership.refresh_from_db()
        self.assertIsNotNone(membership.effective_until)
