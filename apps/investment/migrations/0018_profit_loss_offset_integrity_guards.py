from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investment_profit_loss_offset_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Profit/Loss offsets and Profit payments are append-only'
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER investment_profit_loss_offset_immutable
BEFORE UPDATE OR DELETE ON investment_investorprofitlossoffset
FOR EACH ROW EXECUTE FUNCTION investment_profit_loss_offset_immutable();
CREATE TRIGGER investment_vehicle_profit_payment_immutable
BEFORE UPDATE OR DELETE ON investment_investorvehicleprofitpayment
FOR EACH ROW EXECUTE FUNCTION investment_profit_loss_offset_immutable();

CREATE FUNCTION investment_profit_loss_offset_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    loss_company uuid;
    loss_investor uuid;
    loss_kind text;
    loss_share numeric;
    loss_vehicle uuid;
    loss_branch uuid;
    loss_sold_at timestamptz;
    loss_latest integer;
    profit_company uuid;
    profit_investor uuid;
    profit_kind text;
    profit_share numeric;
    profit_vehicle uuid;
    profit_branch uuid;
    profit_sold_at timestamptz;
    profit_latest integer;
    investor_company uuid;
    branch_company uuid;
    vehicle_revision_company uuid;
    vehicle_revision_module text;
    vehicle_revision_state text;
    investment_revision_company uuid;
    investment_revision_module text;
    investment_revision_state text;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'Investor Profit/Loss offsets are append-only'
            USING ERRCODE = '23514';
    END IF;

    SELECT result.tenant_id, result.investor_id, result.result_kind,
           result.investor_share_amount, result.vehicle_id, sale.branch_id,
           sale.sold_at,
           (SELECT MAX(latest.version)
              FROM investment_vehicleresultconfirmation latest
             WHERE latest.tenant_id = result.tenant_id
               AND latest.vehicle_id = result.vehicle_id)
      INTO loss_company, loss_investor, loss_kind, loss_share, loss_vehicle,
           loss_branch, loss_sold_at, loss_latest
      FROM investment_vehicleresultconfirmation result
      JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
     WHERE result.id = NEW.loss_result_id;

    SELECT result.tenant_id, result.investor_id, result.result_kind,
           result.investor_share_amount, result.vehicle_id, sale.branch_id,
           sale.sold_at,
           (SELECT MAX(latest.version)
              FROM investment_vehicleresultconfirmation latest
             WHERE latest.tenant_id = result.tenant_id
               AND latest.vehicle_id = result.vehicle_id)
      INTO profit_company, profit_investor, profit_kind, profit_share,
           profit_vehicle, profit_branch, profit_sold_at, profit_latest
      FROM investment_vehicleresultconfirmation result
      JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
     WHERE result.id = NEW.profit_result_id;

    SELECT tenant_id INTO investor_company
      FROM investment_investor WHERE id = NEW.investor_id;
    SELECT tenant_id INTO branch_company
      FROM tenants_branch WHERE id = NEW.branch_id;
    SELECT tenant_id, module_code, state
      INTO vehicle_revision_company, vehicle_revision_module, vehicle_revision_state
      FROM tenants_companymodulestate WHERE id = NEW.vehicle_module_revision_id;
    SELECT tenant_id, module_code, state
      INTO investment_revision_company, investment_revision_module, investment_revision_state
      FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;

    IF loss_company IS DISTINCT FROM NEW.tenant_id
       OR profit_company IS DISTINCT FROM NEW.tenant_id
       OR investor_company IS DISTINCT FROM NEW.tenant_id
       OR branch_company IS DISTINCT FROM NEW.tenant_id
       OR loss_investor IS DISTINCT FROM NEW.investor_id
       OR profit_investor IS DISTINCT FROM NEW.investor_id
       OR loss_kind IS DISTINCT FROM 'LOSS'
       OR profit_kind IS DISTINCT FROM 'PROFIT'
       OR loss_share IS NULL OR loss_share >= 0
       OR profit_share IS NULL OR profit_share <= 0
       OR loss_vehicle IS NOT DISTINCT FROM profit_vehicle
       OR loss_sold_at::date >= profit_sold_at::date
       OR loss_latest IS DISTINCT FROM (
            SELECT version FROM investment_vehicleresultconfirmation
             WHERE id = NEW.loss_result_id
       )
       OR profit_latest IS DISTINCT FROM (
            SELECT version FROM investment_vehicleresultconfirmation
             WHERE id = NEW.profit_result_id
       )
       OR profit_branch IS DISTINCT FROM NEW.branch_id
       OR vehicle_revision_company IS DISTINCT FROM NEW.tenant_id
       OR vehicle_revision_module IS DISTINCT FROM 'vehicle_management'
       OR vehicle_revision_state IS DISTINCT FROM 'enabled'
       OR investment_revision_company IS DISTINCT FROM NEW.tenant_id
       OR investment_revision_module IS DISTINCT FROM 'investment'
       OR investment_revision_state IS DISTINCT FROM 'enabled'
       OR NEW.effective_at > clock_timestamp()
       OR NEW.reason <> BTRIM(NEW.reason)
       OR NEW.reason = '' THEN
        RAISE EXCEPTION 'Investor Profit/Loss offset source, date, Branch, Company, or module scope is invalid'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER investment_profit_loss_offset_scope
BEFORE INSERT ON investment_investorprofitlossoffset
FOR EACH ROW EXECUTE FUNCTION investment_profit_loss_offset_scope_guard();

CREATE FUNCTION investment_assert_profit_loss_offset_bounds()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_investor_id uuid;
    v_tenant_id uuid;
    v_loss_result_id uuid;
    v_profit_result_id uuid;
    v_sale_id uuid;
    loss_share numeric;
    profit_share numeric;
    loss_offset_total numeric;
    profit_offset_total numeric;
    profit_payment_total numeric;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorprofitlossoffset' THEN
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_loss_result_id := NEW.loss_result_id;
        v_profit_result_id := NEW.profit_result_id;
    ELSE
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_profit_result_id := NEW.result_confirmation_id;
    END IF;

    PERFORM 1 FROM investment_investor
     WHERE id = v_investor_id AND tenant_id = v_tenant_id
     FOR UPDATE;

    IF v_loss_result_id IS NOT NULL THEN
        SELECT investor_share_amount INTO loss_share
          FROM investment_vehicleresultconfirmation
         WHERE id = v_loss_result_id AND tenant_id = v_tenant_id
           AND investor_id = v_investor_id AND result_kind = 'LOSS';
        SELECT COALESCE(SUM(amount), 0) INTO loss_offset_total
          FROM investment_investorprofitlossoffset
         WHERE tenant_id = v_tenant_id AND investor_id = v_investor_id
           AND loss_result_id = v_loss_result_id;
        IF loss_share IS NULL OR loss_offset_total > ABS(loss_share) THEN
            RAISE EXCEPTION 'Investor Loss offsets exceed the confirmed Loss share'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF v_profit_result_id IS NOT NULL THEN
        SELECT result.investor_share_amount, result.sale_id
          INTO profit_share, v_sale_id
          FROM investment_vehicleresultconfirmation result
         WHERE result.id = v_profit_result_id AND result.tenant_id = v_tenant_id
           AND result.investor_id = v_investor_id AND result.result_kind = 'PROFIT';
        SELECT COALESCE(SUM(loss_offset.amount), 0) INTO profit_offset_total
          FROM investment_investorprofitlossoffset loss_offset
          JOIN investment_vehicleresultconfirmation result
            ON result.id = loss_offset.profit_result_id
         WHERE loss_offset.tenant_id = v_tenant_id AND loss_offset.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        SELECT COALESCE(SUM(payment.amount), 0) INTO profit_payment_total
          FROM investment_investorvehicleprofitpayment payment
          JOIN investment_vehicleresultconfirmation result
            ON result.id = payment.result_confirmation_id
         WHERE payment.tenant_id = v_tenant_id AND payment.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        IF profit_share IS NULL OR profit_offset_total + profit_payment_total > profit_share THEN
            RAISE EXCEPTION 'Investor Loss offsets and Profit payments exceed the confirmed Profit share'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER investment_profit_loss_offset_bounds
AFTER INSERT ON investment_investorprofitlossoffset
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_assert_profit_loss_offset_bounds();
CREATE CONSTRAINT TRIGGER investment_vehicle_profit_payment_bounds
AFTER INSERT ON investment_investorvehicleprofitpayment
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_assert_profit_loss_offset_bounds();

CREATE FUNCTION investment_profit_loss_offset_audit_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    loss_branch uuid;
    profit_branch uuid;
    expected_action text;
BEGIN
    SELECT sale.branch_id INTO loss_branch
      FROM investment_vehicleresultconfirmation result
      JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
     WHERE result.id = NEW.loss_result_id;
    SELECT sale.branch_id INTO profit_branch
      FROM investment_vehicleresultconfirmation result
      JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
     WHERE result.id = NEW.profit_result_id;
    expected_action := CASE WHEN loss_branch = profit_branch
        THEN 'investment.profit.loss_offset.create'
        ELSE 'investment.profit.loss_offset.cross' END;

    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = expected_action
           AND event.company_id = NEW.tenant_id
           AND event.branch_id = profit_branch
           AND event.resource_id = NEW.id
           AND event.actor_id = NEW.actor_id
           AND event.reason = NEW.reason
           AND event.metadata->>'offset_id' = NEW.id::text
           AND event.metadata->>'investor_id' = NEW.investor_id::text
           AND event.metadata->>'loss_result_id' = NEW.loss_result_id::text
           AND event.metadata->>'profit_result_id' = NEW.profit_result_id::text
           AND event.metadata->>'amount' = NEW.amount::text
           AND event.metadata->>'cash_movement_created' = 'false'
    ) THEN
        RAISE EXCEPTION 'Investor Profit/Loss offset requires matching scoped audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER investment_profit_loss_offset_audit
AFTER INSERT ON investment_investorprofitlossoffset
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_profit_loss_offset_audit_guard();
"""


REVERSE_SQL = r"""
DROP TRIGGER investment_profit_loss_offset_audit ON investment_investorprofitlossoffset;
DROP FUNCTION investment_profit_loss_offset_audit_guard();
DROP TRIGGER investment_vehicle_profit_payment_bounds ON investment_investorvehicleprofitpayment;
DROP TRIGGER investment_profit_loss_offset_bounds ON investment_investorprofitlossoffset;
DROP FUNCTION investment_assert_profit_loss_offset_bounds();
DROP TRIGGER investment_profit_loss_offset_scope ON investment_investorprofitlossoffset;
DROP FUNCTION investment_profit_loss_offset_scope_guard();
DROP TRIGGER investment_vehicle_profit_payment_immutable ON investment_investorvehicleprofitpayment;
DROP TRIGGER investment_profit_loss_offset_immutable ON investment_investorprofitlossoffset;
DROP FUNCTION investment_profit_loss_offset_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0022_investor_profit_payment_guards"),
        ("investment", "0017_investor_profit_loss_offset"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
