import uuid
from unittest.mock import patch

from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    connection,
    connections,
    transaction,
)
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.accounts.tests.test_users import make_user
from apps.tenants.admin import CompanyModuleStateAdmin
from apps.tenants.commands import set_company_module_state
from apps.tenants.exceptions import CompanyModuleStateConflict
from apps.tenants.models import (
    CompanyModuleCode,
    CompanyModuleState,
    Tenant,
    TenantMembership,
)


class CompanyModuleStateFixtureMixin:
    password = "A-long-private-module-state-test-passphrase-123!"

    def create_platform_actor(self, *, login_id, company):
        actor = User.objects.create_superuser(
            login_id=login_id,
            email=f"{login_id}@example.invalid",
            password=self.password,
        )
        RoleAssignment.objects.create(
            user=actor,
            role=RoleAssignment.Role.BACK_OFFICE,
            assigned_by=actor,
        )
        TenantMembership.objects.create(
            user=actor,
            tenant=company,
            assigned_by=actor,
        )
        return actor

    def create_revision(
        self, *, company, actor, code="garage", state="disabled", version=1
    ):
        return CompanyModuleState.objects.create(
            tenant=company,
            module_code=code,
            state=state,
            version=version,
            effective_from=timezone.now(),
            changed_by=actor,
        )


class CompanyModuleStateCommandTests(CompanyModuleStateFixtureMixin, TestCase):
    def setUp(self):
        self.company = Tenant.objects.create(name="North", slug="north")
        self.actor = self.create_platform_actor(
            login_id="module-platform", company=self.company
        )

    def test_transition_appends_version_and_audits_in_same_transaction(self):
        request_id = str(uuid.uuid4())
        first = set_company_module_state(
            actor=self.actor,
            company=self.company,
            module_code="garage",
            state="enabled",
            expected_version=0,
            reason="Approved Phase 3 configuration",
            request_id=request_id,
        )
        second = set_company_module_state(
            actor=self.actor,
            company=self.company,
            module_code="garage",
            state="disabled",
            expected_version=1,
            reason="Approved rollback",
        )

        self.assertEqual((first.version, first.state), (1, "enabled"))
        self.assertEqual((second.version, second.state), (2, "disabled"))
        self.assertEqual(
            list(
                CompanyModuleState.objects.filter(
                    tenant=self.company, module_code="garage"
                ).order_by("version").values_list("version", "state")
            ),
            [(1, "enabled"), (2, "disabled")],
        )
        events = AccountSecurityEvent.objects.filter(
            action="module.configure", company_id=self.company.pk
        ).order_by("occurred_at")
        self.assertEqual(events.count(), 2)
        self.assertEqual(str(events.first().request_id), request_id)
        self.assertEqual(events.first().metadata["previous_state"], "UNCONFIGURED")
        self.assertEqual(events.last().metadata["previous_state"], "enabled")
        self.assertEqual(events.last().metadata["version"], 2)

    def test_same_state_submission_is_a_noop_without_a_duplicate_audit_event(self):
        first = set_company_module_state(
            actor=self.actor,
            company=self.company,
            module_code="garage",
            state="enabled",
            expected_version=0,
            reason="Approved configuration",
        )
        result = set_company_module_state(
            actor=self.actor,
            company=self.company,
            module_code="garage",
            state="enabled",
            expected_version=1,
            reason="Repeated submission",
        )

        self.assertEqual(result.pk, first.pk)
        self.assertEqual(CompanyModuleState.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="module.configure").count(), 1
        )

    def test_stale_version_conflict_has_no_partial_revision_or_audit(self):
        self.create_revision(company=self.company, actor=self.actor)

        with self.assertRaises(CompanyModuleStateConflict):
            set_company_module_state(
                actor=self.actor,
                company=self.company,
                module_code="garage",
                state="enabled",
                expected_version=0,
                reason="Stale operator form",
            )

        self.assertEqual(CompanyModuleState.objects.count(), 1)
        self.assertFalse(
            AccountSecurityEvent.objects.filter(action="module.configure").exists()
        )

    def test_audit_failure_rolls_back_the_module_revision(self):
        with patch(
            "apps.tenants.primitives.record_event",
            side_effect=ValidationError("Audit store unavailable"),
        ):
            with self.assertRaises(ValidationError):
                set_company_module_state(
                    actor=self.actor,
                    company=self.company,
                    module_code="garage",
                    state="enabled",
                    expected_version=0,
                    reason="Atomicity test",
                )

        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_invalid_catalog_state_version_and_reason_are_rejected(self):
        cases = [
            {"module_code": "unknown"},
            {"state": "pending"},
            {"expected_version": -1},
            {"expected_version": True},
            {"reason": "   "},
            {"reason": "x" * 501},
        ]
        for overrides in cases:
            args = {
                "module_code": "garage",
                "state": "enabled",
                "expected_version": 0,
                "reason": "Valid reason",
            }
            args.update(overrides)
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValidationError):
                    set_company_module_state(
                        actor=self.actor, company=self.company, **args
                    )

        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_company_user_cannot_configure_platform_module_state(self):
        company_user = make_user(
            "module-company-user", role="accountant", tenant=self.company
        )

        with self.assertRaises(PermissionDenied):
            set_company_module_state(
                actor=company_user,
                company=self.company,
                module_code="garage",
                state="enabled",
                expected_version=0,
                reason="Unauthorized attempt",
            )

        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_revision_model_rejects_mutation_and_deletion(self):
        revision = self.create_revision(company=self.company, actor=self.actor)

        with self.assertRaises(ValidationError):
            revision.save()
        with self.assertRaises(ValidationError):
            revision.delete()

    def test_company_and_actor_identity_are_protected_by_foreign_keys(self):
        self.create_revision(company=self.company, actor=self.actor)

        with self.assertRaises(ProtectedError):
            self.company.delete()
        with self.assertRaises(ProtectedError):
            self.actor.delete()

    def test_database_rejects_queryset_update_and_delete(self):
        if connection.vendor != "postgresql":
            self.skipTest("Database immutability triggers are PostgreSQL-specific")
        revision = self.create_revision(company=self.company, actor=self.actor)

        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                CompanyModuleState.objects.filter(pk=revision.pk).update(
                    state="enabled"
                )
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                CompanyModuleState.objects.filter(pk=revision.pk).delete()
        revision.refresh_from_db()
        self.assertEqual(revision.state, "disabled")

    def test_database_constraints_enforce_catalog_state_version_and_revision_key(self):
        if connection.vendor != "postgresql":
            self.skipTest("Database checks and uniqueness use PostgreSQL schema")
        valid = {
            "tenant": self.company,
            "state": "enabled",
            "version": 1,
            "effective_from": timezone.now(),
            "changed_by": self.actor,
        }
        for overrides in (
            {"module_code": "unknown"},
            {"module_code": "garage", "state": "pending"},
            {"module_code": "garage", "version": 0},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    CompanyModuleState.objects.create(**{**valid, **overrides})

        self.create_revision(company=self.company, actor=self.actor)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CompanyModuleState.objects.create(
                **{**valid, "module_code": "garage"}
            )

    def test_runtime_role_cannot_mutate_or_truncate_module_state(self):
        if connection.vendor != "postgresql":
            self.skipTest("Database role grants are PostgreSQL-specific")
        role = f"virms_test_module_state_{uuid.uuid4().hex}"
        quoted_role = connection.ops.quote_name(role)
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE ROLE {quoted_role} NOLOGIN")
            cursor.execute(f"GRANT USAGE ON SCHEMA public TO {quoted_role}")
            cursor.execute(
                f"GRANT SELECT, INSERT ON tenants_companymodulestate TO {quoted_role}"
            )
        try:
            for sql in [
                "UPDATE tenants_companymodulestate SET state='enabled'",
                "DELETE FROM tenants_companymodulestate",
                "TRUNCATE tenants_companymodulestate",
            ]:
                with self.assertRaises(DatabaseError), transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(f"SET LOCAL ROLE {quoted_role}")
                        cursor.execute(sql)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP OWNED BY {quoted_role}")
                cursor.execute(f"DROP ROLE {quoted_role}")


class CompanyModuleStateConcurrencyTests(
    CompanyModuleStateFixtureMixin, TransactionTestCase
):
    reset_sequences = True

    def setUp(self):
        from queue import Queue
        from threading import Barrier

        self.company = Tenant.objects.create(name="Concurrent", slug="concurrent")
        self.actor = self.create_platform_actor(
            login_id="module-concurrency-platform", company=self.company
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            self.test_database_name = cursor.fetchone()[0]
        self.barrier = Barrier(2)
        self.outcomes = Queue()

    def _configure_concurrently(self, state):
        close_old_connections()
        try:
            # Django's main test connection is redirected to the test database;
            # fresh thread-local wrappers must use that same disposable database.
            worker_connection = connections["default"]
            worker_connection.close()
            worker_connection.settings_dict["NAME"] = self.test_database_name
            self.barrier.wait(timeout=10)
            revision = set_company_module_state(
                actor=self.actor,
                company=self.company,
                module_code="garage",
                state=state,
                expected_version=0,
                reason=f"Concurrent state {state}",
            )
            self.outcomes.put(("success", revision.state))
        except CompanyModuleStateConflict:
            self.outcomes.put(("conflict", None))
        except Exception as error:  # surfaced in the test thread below
            worker_connection = connections["default"]
            try:
                with worker_connection.cursor() as cursor:
                    cursor.execute("SELECT current_database()")
                    actual_database = cursor.fetchone()[0]
            except Exception as probe_error:
                actual_database = f"unavailable ({type(probe_error).__name__})"
            self.outcomes.put(
                (
                    "error",
                    f"{type(error).__name__}: {error} "
                    f"(test_db={self.test_database_name}, "
                    f"configured_db={worker_connection.settings_dict['NAME']}, "
                    f"actual_db={actual_database})",
                )
            )
        finally:
            close_old_connections()

    def test_competing_first_transitions_create_only_one_revision(self):
        from threading import Thread

        threads = [
            Thread(target=self._configure_concurrently, args=(state,), daemon=True)
            for state in ("enabled", "disabled")
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        outcomes = [self.outcomes.get_nowait() for _ in threads]
        self.assertEqual(
            sorted(outcome for outcome, _ in outcomes),
            ["conflict", "success"],
            msg=f"Unexpected concurrent outcomes: {outcomes!r}",
        )
        self.assertEqual(CompanyModuleState.objects.count(), 1)
        self.assertEqual(
            AccountSecurityEvent.objects.filter(action="module.configure").count(), 1
        )


class CompanyModuleStateMigrationTests(
    CompanyModuleStateFixtureMixin, TransactionTestCase
):
    def setUp(self):
        self.company = Tenant.objects.create(name="Migration", slug="migration")
        self.actor = self.create_platform_actor(
            login_id="module-migration-platform", company=self.company
        )

    def test_migration_cannot_be_reversed_after_module_history_exists(self):
        self.create_revision(company=self.company, actor=self.actor)

        with self.assertRaises(IrreversibleError):
            MigrationExecutor(connection).migrate(
                [("tenants", "0002_platform_scope")]
            )

        self.assertEqual(CompanyModuleState.objects.count(), 1)
        self.assertEqual(
            CompanyModuleState.objects.get(tenant=self.company).state, "disabled"
        )


class CompanyModuleStateReadAPITests(CompanyModuleStateFixtureMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Tenant.objects.create(name="North", slug="north")
        self.other_company = Tenant.objects.create(name="South", slug="south")
        self.member = make_user(
            "module-reader", role="accountant", tenant=self.company
        )
        self.other_member = make_user(
            "module-other-reader", role="accountant", tenant=self.other_company
        )
        self.url = reverse("company-module-state", args=[self.company.pk])

    def test_returns_stable_complete_catalog_and_latest_revision(self):
        self.create_revision(
            company=self.company,
            actor=self.member,
            code="garage",
            state="enabled",
            version=1,
        )
        self.create_revision(
            company=self.company,
            actor=self.member,
            code="garage",
            state="disabled",
            version=2,
        )
        self.client.force_login(self.member)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["company_id"], str(self.company.pk))
        self.assertEqual(
            [row["code"] for row in payload["modules"]], list(CompanyModuleCode.values)
        )
        garage = next(row for row in payload["modules"] if row["code"] == "garage")
        self.assertEqual(
            (garage["state"], garage["version"]), ("disabled", 2)
        )
        accounting = next(
            row for row in payload["modules"] if row["code"] == "accounting"
        )
        self.assertEqual(
            (accounting["state"], accounting["version"], accounting["effective_from"]),
            ("unconfigured", None, None),
        )
        self.assertIn("no-store", response["Cache-Control"])
        vary_headers = {value.strip().lower() for value in response["Vary"].split(",")}
        self.assertIn("cookie", vary_headers)

    def test_company_scope_hides_unrelated_company_and_inactive_company(self):
        self.client.force_login(self.member)
        self.assertEqual(
            self.client.get(
                reverse("company-module-state", args=[self.other_company.pk])
            ).status_code,
            404,
        )

        self.company.is_active = False
        self.company.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_query_parameters_are_rejected_and_endpoint_is_read_only(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url, {"branch_id": "attacker-selected"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.client.post(self.url, {"state": "enabled"}).status_code, 405
        )
        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, {401, 403})


class CompanyModuleStateAdminTests(CompanyModuleStateFixtureMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Tenant.objects.create(name="North", slug="north")
        self.other_company = Tenant.objects.create(name="South", slug="south")
        self.operator = self.create_platform_actor(
            login_id="module-admin", company=self.company
        )
        self.client.force_login(self.operator)
        self.admin_adapter = CompanyModuleStateAdmin(CompanyModuleState, admin.site)

    def test_history_is_company_scoped_and_direct_crud_is_disabled(self):
        revision = self.create_revision(company=self.company, actor=self.operator)
        other_actor = self.create_platform_actor(
            login_id="module-admin-other", company=self.other_company
        )
        self.create_revision(company=self.other_company, actor=other_actor)
        self.assertFalse(self.admin_adapter.has_add_permission(None))
        self.assertFalse(self.admin_adapter.has_change_permission(None))
        self.assertFalse(self.admin_adapter.has_delete_permission(None))

        response = self.client.get(
            reverse("admin:tenants_companymodulestate_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "North")
        self.assertNotContains(response, "South")
        self.assertContains(
            response,
            reverse("admin:tenants_companymodulestate_configure"),
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:tenants_companymodulestate_add")
            ).status_code,
            403,
        )
        history_detail = self.client.get(
            reverse("admin:tenants_companymodulestate_change", args=[revision.pk])
        )
        self.assertEqual(history_detail.status_code, 200)
        self.assertNotContains(history_detail, 'name="_save"')
        self.assertEqual(
            self.client.post(
                reverse(
                    "admin:tenants_companymodulestate_delete", args=[revision.pk]
                ),
                {"post": "yes"},
            ).status_code,
            403,
        )

    def test_configure_action_writes_new_revision_and_audit(self):
        configure_url = reverse("admin:tenants_companymodulestate_configure")
        response = self.client.get(
            configure_url,
            {"company": str(self.company.pk), "module_code": "garage"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "unconfigured")
        self.assertIn("no-store", response["Cache-Control"])

        response = self.client.post(
            configure_url,
            {
                "company": str(self.company.pk),
                "module_code": "garage",
                "state": "enabled",
                "expected_version": "0",
                "reason": "Approved Phase 3 state",
            },
        )

        self.assertEqual(response.status_code, 302)
        revision = CompanyModuleState.objects.get(tenant=self.company)
        self.assertEqual((revision.state, revision.version), ("enabled", 1))
        event = AccountSecurityEvent.objects.get(action="module.configure")
        self.assertEqual(event.company_id, self.company.pk)
        self.assertEqual(event.reason, "Approved Phase 3 state")

    def test_stale_admin_form_returns_conflict_without_mutation(self):
        self.create_revision(company=self.company, actor=self.operator)
        response = self.client.post(
            reverse("admin:tenants_companymodulestate_configure"),
            {
                "company": str(self.company.pk),
                "module_code": "garage",
                "state": "enabled",
                "expected_version": "0",
                "reason": "Stale form",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(CompanyModuleState.objects.count(), 1)
        self.assertFalse(
            AccountSecurityEvent.objects.filter(action="module.configure").exists()
        )

    def test_admin_form_cannot_select_unmanaged_company(self):
        response = self.client.post(
            reverse("admin:tenants_companymodulestate_configure"),
            {
                "company": str(self.other_company.pk),
                "module_code": "garage",
                "state": "enabled",
                "expected_version": "0",
                "reason": "Cross-company attempt",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())

    def test_suspended_company_cannot_be_configured(self):
        self.company.is_active = False
        self.company.save(update_fields=["is_active"])
        configure_url = reverse("admin:tenants_companymodulestate_configure")

        lookup = self.client.get(
            configure_url,
            {"company": str(self.company.pk), "module_code": "garage"},
        )
        self.assertEqual(lookup.status_code, 200)
        self.assertNotContains(lookup, 'name="state"')
        response = self.client.post(
            configure_url,
            {
                "company": str(self.company.pk),
                "module_code": "garage",
                "state": "enabled",
                "expected_version": "0",
                "reason": "Suspended Company attempt",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(CompanyModuleState.objects.exists())
        self.assertFalse(AccountSecurityEvent.objects.exists())
