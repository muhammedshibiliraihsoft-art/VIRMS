from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_links(apps, schema_editor):
    if apps.get_model("garage", "GarageStockCostLink").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage Stock cost links exist; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION garage_stock_cost_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE job_company uuid; job_branch uuid; job_vehicle uuid; job_status text; job_context text;
        expense_company uuid; expense_branch uuid; expense_vehicle uuid; rev_company uuid; rev_code text;
BEGIN
    SELECT tenant_id, branch_id, vehicle_id, status, context INTO job_company, job_branch, job_vehicle, job_status, job_context
      FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, branch_id, vehicle_id INTO expense_company, expense_branch, expense_vehicle
      FROM vehicles_vehicleexpense WHERE id=NEW.expense_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF job_company IS NULL OR job_status <> 'OPEN' OR job_context <> 'STOCK'
       OR expense_company IS DISTINCT FROM job_company OR expense_branch IS DISTINCT FROM job_branch
       OR expense_vehicle IS DISTINCT FROM job_vehicle OR rev_company IS DISTINCT FROM job_company
       OR rev_code IS DISTINCT FROM 'garage' THEN
        RAISE EXCEPTION 'Garage cost requires open Stock Job and same Company, Branch and Vehicle expense' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_stock_cost_scope BEFORE INSERT ON garage_garagestockcostlink FOR EACH ROW EXECUTE FUNCTION garage_stock_cost_scope_guard();
CREATE TRIGGER garage_stock_cost_immutable BEFORE UPDATE OR DELETE ON garage_garagestockcostlink FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""

REVERSE = r"""
DROP TRIGGER garage_stock_cost_immutable ON garage_garagestockcostlink;
DROP TRIGGER garage_stock_cost_scope ON garage_garagestockcostlink;
DROP FUNCTION garage_stock_cost_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0005_garagestockcostlink")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_links), migrations.RunSQL(FORWARD, REVERSE)]
