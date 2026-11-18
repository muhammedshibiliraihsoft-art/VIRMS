from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_people(apps, schema_editor):
    if apps.get_model("garage", "LabourPerson").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Labour records exist; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION labour_person_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE branch_company uuid; revision_company uuid; revision_code text;
BEGIN
    SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id=NEW.branch_id;
    SELECT tenant_id, module_code INTO revision_company, revision_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF branch_company IS DISTINCT FROM NEW.tenant_id OR revision_company IS DISTINCT FROM NEW.tenant_id OR revision_code IS DISTINCT FROM 'labour' THEN
        RAISE EXCEPTION 'Labour person Company, Branch or revision mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP='INSERT' THEN
        IF NEW.is_active IS DISTINCT FROM TRUE OR NEW.status_version <> 0 THEN
            RAISE EXCEPTION 'New Labour person must be active' USING ERRCODE='23514';
        END IF;
    ELSE
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id OR NEW.branch_id IS DISTINCT FROM OLD.branch_id
           OR NEW.created_by_id IS DISTINCT FROM OLD.created_by_id OR NEW.module_revision_id IS DISTINCT FROM OLD.module_revision_id THEN
            RAISE EXCEPTION 'Labour source identity is immutable' USING ERRCODE='23514';
        END IF;
        IF (NEW.is_active IS DISTINCT FROM OLD.is_active OR NEW.status_version IS DISTINCT FROM OLD.status_version) AND
          (NEW.is_active = OLD.is_active OR NEW.status_version <> OLD.status_version + 1 OR NOT EXISTS (
            SELECT 1 FROM garage_labourstatuschange s WHERE s.person_id=NEW.id AND s.version=NEW.status_version AND s.is_active=NEW.is_active
          )) THEN RAISE EXCEPTION 'Labour status change requires history' USING ERRCODE='23514'; END IF;
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER labour_person_scope BEFORE INSERT OR UPDATE ON garage_labourperson FOR EACH ROW EXECUTE FUNCTION labour_person_scope_guard();
CREATE FUNCTION labour_status_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE company_id uuid; current_status boolean; current_version integer; rev_company uuid; rev_code text;
BEGIN
    SELECT tenant_id, is_active, status_version INTO company_id, current_status, current_version FROM garage_labourperson WHERE id=NEW.person_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    IF company_id IS NULL OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'labour'
       OR NEW.is_active IS NOT DISTINCT FROM current_status OR NEW.version <> current_version + 1 THEN
        RAISE EXCEPTION 'Labour status history scope or version mismatch' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER labour_status_scope BEFORE INSERT ON garage_labourstatuschange FOR EACH ROW EXECUTE FUNCTION labour_status_scope_guard();
CREATE TRIGGER labour_person_no_delete BEFORE DELETE ON garage_labourperson FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
CREATE TRIGGER labour_status_immutable BEFORE UPDATE OR DELETE ON garage_labourstatuschange FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
"""
REVERSE = r"""
DROP TRIGGER labour_status_immutable ON garage_labourstatuschange;
DROP TRIGGER labour_person_no_delete ON garage_labourperson;
DROP TRIGGER labour_status_scope ON garage_labourstatuschange;
DROP FUNCTION labour_status_scope_guard();
DROP TRIGGER labour_person_scope ON garage_labourperson;
DROP FUNCTION labour_person_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0013_labourperson_labourstatuschange_and_more")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_people), migrations.RunSQL(FORWARD, REVERSE)]
