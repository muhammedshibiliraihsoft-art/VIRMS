from django.db import migrations

FORWARD = """
CREATE FUNCTION virms_scope_end_monotonic_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.effective_until IS NOT NULL AND
    (NEW.effective_until IS NULL OR NEW.effective_until > OLD.effective_until) THEN
  RAISE EXCEPTION 'Authorization interval cannot be expanded after an end is set'
    USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER virms_membership_end_monotonic BEFORE UPDATE OF effective_until ON tenants_tenantmembership FOR EACH ROW EXECUTE FUNCTION virms_scope_end_monotonic_guard();
CREATE TRIGGER virms_assignment_end_monotonic BEFORE UPDATE OF effective_until ON tenants_branchassignment FOR EACH ROW EXECUTE FUNCTION virms_scope_end_monotonic_guard();
CREATE TRIGGER virms_grant_end_monotonic BEFORE UPDATE OF effective_until ON accounts_companyrolegrant FOR EACH ROW EXECUTE FUNCTION virms_scope_end_monotonic_guard();
CREATE TRIGGER virms_role_end_monotonic BEFORE UPDATE OF effective_until ON accounts_roleassignment FOR EACH ROW EXECUTE FUNCTION virms_scope_end_monotonic_guard();
"""

REVERSE = """
DROP TRIGGER virms_membership_end_monotonic ON tenants_tenantmembership;
DROP TRIGGER virms_assignment_end_monotonic ON tenants_branchassignment;
DROP TRIGGER virms_grant_end_monotonic ON accounts_companyrolegrant;
DROP TRIGGER virms_role_end_monotonic ON accounts_roleassignment;
DROP FUNCTION virms_scope_end_monotonic_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounts", "0011_login_state_expiry_idx")]

    operations = [migrations.RunSQL(FORWARD, REVERSE)]
