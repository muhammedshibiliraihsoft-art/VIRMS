from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_costs(apps, schema_editor):
    if apps.get_model("garage", "GarageCustomerCost").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage customer costs exist; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION garage_customer_cost_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE job_id uuid; company_id uuid; current_status text; job_context text; rev_company uuid; rev_code text; latest integer;
BEGIN
    IF TG_TABLE_NAME = 'garage_garagecustomercost' THEN job_id := NEW.job_id;
    ELSE SELECT c.job_id INTO job_id FROM garage_garagecustomercost c WHERE c.id=NEW.cost_id; END IF;
    SELECT tenant_id, status, context INTO company_id, current_status, job_context FROM garage_garagejob WHERE id=job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF company_id IS NULL OR current_status <> 'OPEN' OR job_context <> 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage' THEN
        RAISE EXCEPTION 'Garage customer cost requires an open external Job and matching Company revision' USING ERRCODE='23514';
    END IF;
    IF TG_TABLE_NAME = 'garage_garagecustomercostcorrection' THEN
        SELECT COALESCE(MAX(version), 0) INTO latest FROM garage_garagecustomercostcorrection WHERE cost_id=NEW.cost_id;
        IF NEW.version <> latest + 1 THEN RAISE EXCEPTION 'Garage cost correction version invalid' USING ERRCODE='23514'; END IF;
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_customer_cost_scope BEFORE INSERT ON garage_garagecustomercost FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_guard();
CREATE TRIGGER garage_customer_cost_correction_scope BEFORE INSERT ON garage_garagecustomercostcorrection FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_guard();
CREATE TRIGGER garage_customer_cost_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercost FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
CREATE TRIGGER garage_customer_cost_correction_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercostcorrection FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""
REVERSE = r"""
DROP TRIGGER garage_customer_cost_correction_immutable ON garage_garagecustomercostcorrection;
DROP TRIGGER garage_customer_cost_immutable ON garage_garagecustomercost;
DROP TRIGGER garage_customer_cost_correction_scope ON garage_garagecustomercostcorrection;
DROP TRIGGER garage_customer_cost_scope ON garage_garagecustomercost;
DROP FUNCTION garage_customer_cost_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0011_garagecustomercost_garagecustomercostcorrection_and_more")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_costs), migrations.RunSQL(FORWARD, REVERSE)]
