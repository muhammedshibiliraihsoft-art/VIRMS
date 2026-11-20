from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investment_profit_calendar_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    investor_company uuid;
    revision_company uuid;
    revision_module text;
    revision_state text;
    expected_version integer;
BEGIN
    SELECT tenant_id INTO investor_company
      FROM investment_investor WHERE id = NEW.investor_id;
    SELECT tenant_id, module_code, state
      INTO revision_company, revision_module, revision_state
      FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
    SELECT COALESCE(MAX(version), 0) + 1 INTO expected_version
      FROM investment_investorprofitcalendarconfiguration
     WHERE investor_id = NEW.investor_id
       AND effective_start = NEW.effective_start;
    IF investor_company IS DISTINCT FROM NEW.tenant_id
       OR revision_company IS DISTINCT FROM NEW.tenant_id
       OR revision_module IS DISTINCT FROM 'investment'
       OR revision_state IS DISTINCT FROM 'enabled'
       OR NEW.version IS DISTINCT FROM expected_version THEN
        RAISE EXCEPTION 'Investor Profit calendar Company, module revision, or version is invalid'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE FUNCTION investment_profit_calendar_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Profit calendar versions are immutable'
        USING ERRCODE = '23514';
END;
$$;

CREATE FUNCTION investment_profit_calendar_audit_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = 'investor.profit_calendar.configure'
           AND event.company_id = NEW.tenant_id
           AND event.resource_type = 'investment.investor'
           AND event.resource_id = NEW.investor_id
           AND event.actor_id = NEW.actor_id
           AND event.metadata->>'calendar_id' = NEW.id::text
           AND event.metadata->>'investor_id' = NEW.investor_id::text
           AND event.metadata->>'effective_start' = NEW.effective_start::text
           AND event.metadata->>'duration_months' = NEW.duration_months::text
           AND event.metadata->>'version' = NEW.version::text
    ) THEN
        RAISE EXCEPTION 'Investor Profit calendar configuration requires matching audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER investment_profit_calendar_scope
BEFORE INSERT ON investment_investorprofitcalendarconfiguration
FOR EACH ROW EXECUTE FUNCTION investment_profit_calendar_scope_guard();
CREATE TRIGGER investment_profit_calendar_immutable
BEFORE UPDATE OR DELETE ON investment_investorprofitcalendarconfiguration
FOR EACH ROW EXECUTE FUNCTION investment_profit_calendar_immutable();
CREATE CONSTRAINT TRIGGER investment_profit_calendar_audit
AFTER INSERT ON investment_investorprofitcalendarconfiguration
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_profit_calendar_audit_guard();
"""


REVERSE_SQL = r"""
DROP TRIGGER investment_profit_calendar_audit ON investment_investorprofitcalendarconfiguration;
DROP TRIGGER investment_profit_calendar_immutable ON investment_investorprofitcalendarconfiguration;
DROP TRIGGER investment_profit_calendar_scope ON investment_investorprofitcalendarconfiguration;
DROP FUNCTION investment_profit_calendar_audit_guard();
DROP FUNCTION investment_profit_calendar_immutable();
DROP FUNCTION investment_profit_calendar_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0013_investorprofitcalendarconfiguration"),
        ("accounts", "0012_scope_end_monotonic"),
        ("tenants", "0003_company_module_state"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
