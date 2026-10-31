from django.db import migrations

SQL = """
CREATE FUNCTION virms_scope_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE col text;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Scope history cannot be deleted' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' THEN
  FOREACH col IN ARRAY TG_ARGV LOOP
   IF (to_jsonb(NEW)->col) IS DISTINCT FROM (to_jsonb(OLD)->col) THEN
    RAISE EXCEPTION 'Immutable scope identity' USING ERRCODE='23514';
   END IF;
  END LOOP;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER virms_company_history BEFORE UPDATE OR DELETE ON tenants_tenant FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id');
CREATE TRIGGER virms_branch_history BEFORE UPDATE OR DELETE ON tenants_branch FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id','tenant_id');
CREATE TRIGGER virms_membership_history BEFORE UPDATE OR DELETE ON tenants_tenantmembership FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id','user_id','tenant_id','effective_from');
CREATE TRIGGER virms_assignment_history BEFORE UPDATE OR DELETE ON tenants_branchassignment FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id','membership_id','branch_id','effective_from');
CREATE TRIGGER virms_grant_history BEFORE UPDATE OR DELETE ON accounts_companyrolegrant FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id','membership_id','branch_id','role','effective_from');
CREATE TRIGGER virms_role_history BEFORE UPDATE OR DELETE ON accounts_roleassignment FOR EACH ROW EXECUTE FUNCTION virms_scope_history_guard('id','user_id','role','effective_from');
CREATE FUNCTION virms_branch_company_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE member_company uuid; branch_company uuid;
BEGIN
 SELECT tenant_id INTO member_company FROM tenants_tenantmembership WHERE id=NEW.membership_id;
 IF NEW.branch_id IS NOT NULL THEN
  SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id=NEW.branch_id;
  IF member_company IS DISTINCT FROM branch_company THEN
   RAISE EXCEPTION 'Company/Branch mismatch' USING ERRCODE='23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER virms_assignment_company BEFORE INSERT OR UPDATE ON tenants_branchassignment FOR EACH ROW EXECUTE FUNCTION virms_branch_company_guard();
CREATE TRIGGER virms_grant_company BEFORE INSERT OR UPDATE ON accounts_companyrolegrant FOR EACH ROW EXECUTE FUNCTION virms_branch_company_guard();
"""
REVERSE = """
DROP TRIGGER virms_assignment_company ON tenants_branchassignment;
DROP TRIGGER virms_grant_company ON accounts_companyrolegrant;
DROP FUNCTION virms_branch_company_guard();
DROP TRIGGER virms_company_history ON tenants_tenant;
DROP TRIGGER virms_branch_history ON tenants_branch;
DROP TRIGGER virms_membership_history ON tenants_tenantmembership;
DROP TRIGGER virms_assignment_history ON tenants_branchassignment;
DROP TRIGGER virms_grant_history ON accounts_companyrolegrant;
DROP TRIGGER virms_role_history ON accounts_roleassignment;
DROP FUNCTION virms_scope_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_platform_scope"), ("tenants", "0002_platform_scope")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
