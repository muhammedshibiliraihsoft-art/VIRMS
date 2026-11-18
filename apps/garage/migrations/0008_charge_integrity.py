from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_charges(apps, schema_editor):
    if apps.get_model("garage", "GarageCustomerCharge").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage charge history exists; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION garage_charge_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE company_id uuid; current_status text; job_context text; rev_company uuid; rev_code text; latest integer;
BEGIN
    SELECT tenant_id, status, context INTO company_id, current_status, job_context FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT COALESCE(MAX(version), 0) INTO latest FROM garage_garagecustomercharge WHERE job_id=NEW.job_id;
    IF company_id IS NULL OR current_status <> 'OPEN' OR job_context <> 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage' OR NEW.version <> latest + 1 THEN
        RAISE EXCEPTION 'Garage charge requires open external Job, same Company revision and next version' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_charge_scope BEFORE INSERT ON garage_garagecustomercharge FOR EACH ROW EXECUTE FUNCTION garage_charge_scope_guard();
CREATE TRIGGER garage_charge_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercharge FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""
REVERSE = r"""
DROP TRIGGER garage_charge_immutable ON garage_garagecustomercharge;
DROP TRIGGER garage_charge_scope ON garage_garagecustomercharge;
DROP FUNCTION garage_charge_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0007_garagecustomercharge")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_charges), migrations.RunSQL(FORWARD, REVERSE)]
