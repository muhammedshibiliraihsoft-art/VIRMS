from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_garage_data(apps, schema_editor):
    if apps.get_model("garage", "GarageJob").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage Job history exists; do not reverse its integrity guards.")


FORWARD = r"""
CREATE FUNCTION garage_job_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE vehicle_company uuid; vehicle_branch uuid; branch_company uuid;
        revision_company uuid; revision_code text;
BEGIN
    SELECT tenant_id, current_branch_id INTO vehicle_company, vehicle_branch FROM vehicles_vehicle WHERE id=NEW.vehicle_id;
    SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id=NEW.branch_id;
    SELECT tenant_id, module_code INTO revision_company, revision_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF vehicle_company IS DISTINCT FROM NEW.tenant_id OR branch_company IS DISTINCT FROM NEW.tenant_id
       OR revision_company IS DISTINCT FROM NEW.tenant_id OR revision_code IS DISTINCT FROM 'garage' THEN
        RAISE EXCEPTION 'Garage Job Company, Branch, Vehicle or revision mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'OPEN' OR NEW.status_version <> 0 OR vehicle_branch IS DISTINCT FROM NEW.branch_id THEN
            RAISE EXCEPTION 'New Garage Job must be OPEN at Vehicle current Branch' USING ERRCODE='23514';
        END IF;
    ELSE
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.branch_id IS DISTINCT FROM OLD.branch_id
           OR NEW.vehicle_id IS DISTINCT FROM OLD.vehicle_id OR NEW.context IS DISTINCT FROM OLD.context
           OR NEW.created_by_id IS DISTINCT FROM OLD.created_by_id OR NEW.module_revision_id IS DISTINCT FROM OLD.module_revision_id THEN
            RAISE EXCEPTION 'Garage Job source identity is immutable' USING ERRCODE='23514';
        END IF;
        IF (NEW.status IS DISTINCT FROM OLD.status OR NEW.status_version IS DISTINCT FROM OLD.status_version) AND
          (NEW.status = OLD.status OR NEW.status_version <> OLD.status_version + 1 OR NOT EXISTS (
            SELECT 1 FROM garage_garagejobstatuschange s WHERE s.job_id=NEW.id
            AND s.from_status=OLD.status AND s.to_status=NEW.status
            AND s.version=NEW.status_version
        )) THEN
            RAISE EXCEPTION 'Garage status change requires history' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_job_scope BEFORE INSERT OR UPDATE ON garage_garagejob FOR EACH ROW EXECUTE FUNCTION garage_job_scope_guard();
CREATE FUNCTION garage_status_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE company_id uuid; current_status text; current_version integer; rev_company uuid; rev_code text;
BEGIN
    SELECT tenant_id, status, status_version INTO company_id, current_status, current_version FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF company_id IS NULL OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage'
       OR current_status IS DISTINCT FROM NEW.from_status OR NEW.version <> current_version + 1 THEN
        RAISE EXCEPTION 'Garage status history scope or previous state mismatch' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_status_scope BEFORE INSERT ON garage_garagejobstatuschange FOR EACH ROW EXECUTE FUNCTION garage_status_scope_guard();
CREATE FUNCTION garage_history_retained() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Garage history is retained' USING ERRCODE='23514'; END; $$;
CREATE TRIGGER garage_job_no_delete BEFORE DELETE ON garage_garagejob FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
CREATE TRIGGER garage_status_immutable BEFORE UPDATE OR DELETE ON garage_garagejobstatuschange FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""

REVERSE = r"""
DROP TRIGGER garage_status_immutable ON garage_garagejobstatuschange;
DROP TRIGGER garage_job_no_delete ON garage_garagejob;
DROP FUNCTION garage_history_retained();
DROP TRIGGER garage_status_scope ON garage_garagejobstatuschange;
DROP FUNCTION garage_status_scope_guard();
DROP TRIGGER garage_job_scope ON garage_garagejob;
DROP FUNCTION garage_job_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0001_initial")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_garage_data), migrations.RunSQL(FORWARD, REVERSE)]
