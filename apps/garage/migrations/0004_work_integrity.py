from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_work(apps, schema_editor):
    if apps.get_model("garage", "GarageWorkEntry").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage work history exists; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION garage_work_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE company_id uuid; current_status text; rev_company uuid; rev_code text;
BEGIN
    SELECT tenant_id, status INTO company_id, current_status FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF company_id IS NULL OR current_status <> 'OPEN' OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage' THEN
        RAISE EXCEPTION 'Garage work requires an open Job and same-Company Garage revision' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_work_scope BEFORE INSERT ON garage_garageworkentry FOR EACH ROW EXECUTE FUNCTION garage_work_scope_guard();
CREATE TRIGGER garage_work_immutable BEFORE UPDATE OR DELETE ON garage_garageworkentry FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""

REVERSE = r"""
DROP TRIGGER garage_work_immutable ON garage_garageworkentry;
DROP TRIGGER garage_work_scope ON garage_garageworkentry;
DROP FUNCTION garage_work_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0003_garageworkentry")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_work), migrations.RunSQL(FORWARD, REVERSE)]
