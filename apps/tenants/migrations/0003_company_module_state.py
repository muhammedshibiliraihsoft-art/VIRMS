import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError


COMPANY_MODULE_CODES = [
    "accounting",
    "investment",
    "garage",
    "investor_portal",
    "vehicle_management",
    "vehicle_expense_management",
    "sales_receivables",
    "media_vehicle_publication",
    "public_vehicle_access",
    "labour",
    "reports_dashboard",
    "audit_corrections",
    "gst_tax_invoice",
    "owner_ai_assistant",
]

IMMUTABILITY_SQL = """
CREATE FUNCTION tenants_reject_module_state_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Company module-state history is append only'
        USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER tenants_module_state_no_update_delete
BEFORE UPDATE OR DELETE ON tenants_companymodulestate
FOR EACH ROW EXECUTE FUNCTION tenants_reject_module_state_mutation();
REVOKE UPDATE, DELETE, TRUNCATE ON tenants_companymodulestate FROM PUBLIC;
"""

DROP_IMMUTABILITY_SQL = """
DROP TRIGGER tenants_module_state_no_update_delete ON tenants_companymodulestate;
DROP FUNCTION tenants_reject_module_state_mutation();
"""


def refuse_reverse_with_module_history(apps, schema_editor):
    CompanyModuleState = apps.get_model("tenants", "CompanyModuleState")
    if CompanyModuleState.objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError(
            "Company module-state history exists; roll back application code "
            "without reversing this migration."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0002_platform_scope"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyModuleState",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "module_code",
                    models.CharField(
                        choices=[
                            ("accounting", "Accounting"),
                            ("investment", "Investment"),
                            ("garage", "Garage"),
                            ("investor_portal", "Investor Portal"),
                            ("vehicle_management", "Vehicle Management"),
                            (
                                "vehicle_expense_management",
                                "Vehicle Expense Management",
                            ),
                            ("sales_receivables", "Sales and Receivables"),
                            (
                                "media_vehicle_publication",
                                "Media / Vehicle Publication",
                            ),
                            ("public_vehicle_access", "Public Vehicle Access"),
                            ("labour", "Labour"),
                            ("reports_dashboard", "Reports and Dashboard"),
                            ("audit_corrections", "Audit and Corrections"),
                            ("gst_tax_invoice", "GST / Tax / Invoice capability"),
                            ("owner_ai_assistant", "Owner AI Assistant"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[("enabled", "Enabled"), ("disabled", "Disabled")],
                        max_length=8,
                    ),
                ),
                ("version", models.PositiveIntegerField()),
                ("effective_from", models.DateTimeField()),
                (
                    "changed_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="company_module_state_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="module_states",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={"ordering": ["tenant_id", "module_code", "version"]},
        ),
        migrations.AddConstraint(
            model_name="companymodulestate",
            constraint=models.UniqueConstraint(
                fields=("tenant", "module_code", "version"),
                name="company_module_rev_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="companymodulestate",
            constraint=models.CheckConstraint(
                condition=models.Q(("version__gte", 1)),
                name="company_module_rev_version_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="companymodulestate",
            constraint=models.CheckConstraint(
                condition=models.Q(("module_code__in", COMPANY_MODULE_CODES)),
                name="company_module_rev_code_ck",
            ),
        ),
        migrations.AddConstraint(
            model_name="companymodulestate",
            constraint=models.CheckConstraint(
                condition=models.Q(("state__in", ["enabled", "disabled"])),
                name="company_module_rev_state_ck",
            ),
        ),
        migrations.RunSQL(IMMUTABILITY_SQL, DROP_IMMUTABILITY_SQL),
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=refuse_reverse_with_module_history,
        ),
    ]
