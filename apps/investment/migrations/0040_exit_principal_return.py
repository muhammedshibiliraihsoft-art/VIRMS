from importlib import import_module

from django.db import migrations, models
import django.db.models.deletion


def audit_function(*, allow_exit):
    source = import_module("apps.investment.migrations.0002_integrity_guards").FORWARD_SQL
    start = source.index("CREATE FUNCTION investment_require_audit()")
    end = source.index("CREATE CONSTRAINT TRIGGER investor_create_audit_deferred", start)
    function_sql = source[start:end].strip()
    target = "WHERE e.action = 'investment.fund.principal_return'\n              AND e.company_id = NEW.tenant_id"
    replacement = (
        "WHERE (e.action = 'investment.fund.principal_return' OR "
        "(NEW.exit_request_id IS NOT NULL AND e.action = 'investment.exit.settlement.principal'))\n"
        "              AND e.company_id = NEW.tenant_id"
    ) if allow_exit else target
    if function_sql.count(target) != 1:
        raise RuntimeError("Unexpected Investment principal-return audit guard layout.")
    function_sql = function_sql.replace(target, replacement, 1)
    return function_sql.replace("CREATE FUNCTION investment_require_audit()", "CREATE OR REPLACE FUNCTION investment_require_audit()", 1)


def install(apps, schema_editor):
    schema_editor.execute("""
        CREATE FUNCTION investment_exit_principal_return_guard() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE request_company uuid; request_investor uuid; request_status text;
        BEGIN
            IF NEW.exit_request_id IS NULL THEN RETURN NEW; END IF;
            SELECT tenant_id, investor_id, status INTO request_company, request_investor, request_status
              FROM investment_investorexitrequest WHERE id=NEW.exit_request_id;
            IF request_company IS DISTINCT FROM NEW.tenant_id
               OR request_investor IS DISTINCT FROM NEW.investor_id
               OR request_status IS DISTINCT FROM 'REQUESTED' THEN
                RAISE EXCEPTION 'Exit principal return requires its open same-Company Investor request'
                    USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$;
        CREATE TRIGGER investment_exit_principal_return_scope
        BEFORE INSERT ON investment_investorprincipalreturn
        FOR EACH ROW EXECUTE FUNCTION investment_exit_principal_return_guard();
    """, params=None)
    schema_editor.execute(audit_function(allow_exit=True), params=None)


def uninstall(apps, schema_editor):
    if apps.get_model("investment", "InvestorPrincipalReturn").objects.filter(exit_request__isnull=False).exists():
        raise RuntimeError("Exit principal return history must be preserved.")
    schema_editor.execute("DROP TRIGGER investment_exit_principal_return_scope ON investment_investorprincipalreturn; DROP FUNCTION investment_exit_principal_return_guard();", params=None)
    schema_editor.execute(audit_function(allow_exit=False), params=None)


class Migration(migrations.Migration):
    dependencies = [("investment", "0039_principal_refund_review_audit")]
    operations = [
        migrations.AddField(
            model_name="investorprincipalreturn",
            name="exit_request",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="principal_returns", to="investment.investorexitrequest"),
        ),
        migrations.RunPython(install, uninstall),
    ]
