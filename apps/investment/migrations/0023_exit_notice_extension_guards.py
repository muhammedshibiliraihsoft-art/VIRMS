from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investment_exit_request_notice_origin_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'Exit notice origin is immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER investment_exit_notice_origin_immutable BEFORE UPDATE ON investment_investorexitrequest
FOR EACH ROW EXECUTE FUNCTION investment_exit_request_notice_origin_immutable();
CREATE FUNCTION investment_exit_extension_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE r_company uuid; r_status text; r_created timestamptz;
        v_company uuid; v_module text; prior_deadline timestamptz; prior_version integer;
BEGIN
    SELECT tenant_id, status, created_at INTO r_company, r_status, r_created
      FROM investment_investorexitrequest WHERE id = NEW.exit_request_id FOR UPDATE;
    SELECT tenant_id, module_code INTO v_company, v_module
      FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;
    SELECT deadline, version INTO prior_deadline, prior_version
      FROM investment_investorexitnoticeextension WHERE exit_request_id = NEW.exit_request_id
      ORDER BY version DESC LIMIT 1;
    IF prior_version IS NULL THEN
        prior_version := 0;
        prior_deadline := (r_created AT TIME ZONE 'UTC' + interval '3 months') AT TIME ZONE 'UTC';
    END IF;
    IF r_company IS DISTINCT FROM NEW.tenant_id OR v_company IS DISTINCT FROM NEW.tenant_id
       OR v_module IS DISTINCT FROM 'investment' OR r_status NOT IN ('REQUESTED', 'CANCELLATION_PENDING')
       OR NEW.version <> prior_version + 1 OR NEW.previous_deadline IS DISTINCT FROM prior_deadline
       OR NEW.deadline <= prior_deadline THEN
        RAISE EXCEPTION 'Invalid Exit notice extension source or ordering' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE FUNCTION investment_exit_extension_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Exit notice extensions are retained' USING ERRCODE = '23514'; END; $$;
CREATE FUNCTION investment_exit_extension_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent e
                   WHERE e.action = 'investment.exit.notice.extend' AND e.company_id = NEW.tenant_id
                     AND e.resource_id = NEW.id AND e.actor_id = NEW.actor_id AND e.reason = NEW.reason
                     AND e.metadata->>'exit_request_id' = NEW.exit_request_id::text
                     AND e.metadata->>'extension_id' = NEW.id::text) THEN
        RAISE EXCEPTION 'Exit notice extension requires audit evidence' USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE TRIGGER investment_exit_ext_guard BEFORE INSERT ON investment_investorexitnoticeextension
FOR EACH ROW EXECUTE FUNCTION investment_exit_extension_guard();
CREATE TRIGGER investment_exit_ext_immutable BEFORE UPDATE OR DELETE ON investment_investorexitnoticeextension
FOR EACH ROW EXECUTE FUNCTION investment_exit_extension_immutable();
CREATE CONSTRAINT TRIGGER investment_exit_ext_audit AFTER INSERT ON investment_investorexitnoticeextension
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION investment_exit_extension_audit();
"""

REVERSE_SQL = r"""
DROP TRIGGER investment_exit_ext_audit ON investment_investorexitnoticeextension;
DROP TRIGGER investment_exit_ext_immutable ON investment_investorexitnoticeextension;
DROP TRIGGER investment_exit_ext_guard ON investment_investorexitnoticeextension;
DROP FUNCTION investment_exit_extension_audit();
DROP FUNCTION investment_exit_extension_immutable();
DROP FUNCTION investment_exit_extension_guard();
DROP TRIGGER investment_exit_notice_origin_immutable ON investment_investorexitrequest;
DROP FUNCTION investment_exit_request_notice_origin_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0022_exit_notice_extension")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
