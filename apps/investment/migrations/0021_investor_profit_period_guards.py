from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investment_profit_period_reconciliation_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Profit period reconciliations are append-only'
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER investment_profit_period_reconciliation_immutable
BEFORE UPDATE OR DELETE ON investment_investorprofitperiodreconciliation
FOR EACH ROW EXECUTE FUNCTION investment_profit_period_reconciliation_immutable();

CREATE FUNCTION investment_profit_period_reconciliation_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    investor_company uuid;
    latest_version integer;
    latest_id uuid;
    previous_net numeric;
    revision_company uuid;
    revision_module text;
    revision_state text;
    expected_adjustment numeric;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'Investor Profit period reconciliations are append-only'
            USING ERRCODE = '23514';
    END IF;

    PERFORM 1 FROM investment_investor
     WHERE id = NEW.investor_id AND tenant_id = NEW.tenant_id
     FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation Company scope is invalid'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.source_version !~ '^[0-9a-f]{64}$'
       OR NEW.reason <> BTRIM(NEW.reason)
       OR NEW.reason = ''
       OR NEW.confirmed_at > clock_timestamp() THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation metadata is invalid'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, module_code, state
      INTO revision_company, revision_module, revision_state
      FROM tenants_companymodulestate
     WHERE id = NEW.investment_module_revision_id;
    IF revision_company IS DISTINCT FROM NEW.tenant_id
       OR revision_module IS DISTINCT FROM 'investment'
       OR revision_state IS DISTINCT FROM 'enabled' THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation Investment revision is invalid'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, module_code, state
      INTO revision_company, revision_module, revision_state
      FROM tenants_companymodulestate
     WHERE id = NEW.vehicle_module_revision_id;
    IF revision_company IS DISTINCT FROM NEW.tenant_id
       OR revision_module IS DISTINCT FROM 'vehicle_management'
       OR revision_state IS DISTINCT FROM 'enabled' THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation Vehicle revision is invalid'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, module_code, state
      INTO revision_company, revision_module, revision_state
      FROM tenants_companymodulestate
     WHERE id = NEW.accounting_module_revision_id;
    IF revision_company IS DISTINCT FROM NEW.tenant_id
       OR revision_module IS DISTINCT FROM 'accounting'
       OR revision_state IS DISTINCT FROM 'enabled' THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation Accounting revision is invalid'
            USING ERRCODE = '23514';
    END IF;

    SELECT version, id, net_position
      INTO latest_version, latest_id, previous_net
      FROM investment_investorprofitperiodreconciliation
     WHERE tenant_id = NEW.tenant_id
       AND investor_id = NEW.investor_id
       AND period_start = NEW.period_start
       AND period_end = NEW.period_end
     ORDER BY version DESC, id DESC
     LIMIT 1;
    IF NOT FOUND THEN
        latest_version := 0;
        latest_id := NULL;
        previous_net := NULL;
    END IF;

    IF NEW.version <> latest_version + 1
       OR NEW.previous_reconciliation_id IS DISTINCT FROM latest_id THEN
        RAISE EXCEPTION 'Investor Profit period reconciliation version is not the next audited version'
            USING ERRCODE = '23514';
    END IF;

    IF latest_id IS NULL THEN
        expected_adjustment := 0;
    ELSE
        expected_adjustment := NEW.net_position - previous_net;
    END IF;
    IF NEW.restatement_adjustment IS DISTINCT FROM expected_adjustment THEN
        RAISE EXCEPTION 'Investor Profit period restatement adjustment does not reconcile'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER investment_profit_period_reconciliation_scope
BEFORE INSERT ON investment_investorprofitperiodreconciliation
FOR EACH ROW EXECUTE FUNCTION investment_profit_period_reconciliation_scope_guard();
"""


REVERSE_SQL = r"""
DROP TRIGGER IF EXISTS investment_profit_period_reconciliation_scope
    ON investment_investorprofitperiodreconciliation;
DROP TRIGGER IF EXISTS investment_profit_period_reconciliation_immutable
    ON investment_investorprofitperiodreconciliation;
DROP FUNCTION IF EXISTS investment_profit_period_reconciliation_scope_guard();
DROP FUNCTION IF EXISTS investment_profit_period_reconciliation_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0020_investor_profit_period_reconciliation"),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]
