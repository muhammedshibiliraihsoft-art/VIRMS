from django.db import migrations


FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION investment_profit_loss_offset_scope_guard()
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

"""

REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION investment_profit_loss_offset_scope_guard()
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

"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0028_loss_suggestion_guards")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
