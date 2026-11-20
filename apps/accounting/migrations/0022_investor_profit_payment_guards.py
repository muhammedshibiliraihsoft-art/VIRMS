from importlib import import_module

from django.db import migrations


def _updated_source_guard():
    prior = import_module(
        "apps.accounting.migrations.0019_vehicle_company_share_guards"
    ).SOURCE_LINK_GUARD_SQL
    old_count = "                  + (NEW.vehicle_result_confirmation_id IS NOT NULL)::integer;"
    new_count = (
        "                  + (NEW.vehicle_result_confirmation_id IS NOT NULL)::integer\n"
        "                  + (NEW.investor_vehicle_profit_payment_id IS NOT NULL)::integer;"
    )
    old_branch = (
        "    ELSE\n"
        "        SELECT result.tenant_id, sale.branch_id, result.company_share_amount,\n"
    )
    new_branch = (
        "    ELSIF NEW.investor_vehicle_profit_payment_id IS NOT NULL THEN\n"
        "        SELECT tenant_id, branch_id, amount, actor_id, account_id\n"
        "          INTO s_company, s_branch, s_amount, s_actor, s_account\n"
        "          FROM investment_investorvehicleprofitpayment\n"
        "         WHERE id = NEW.investor_vehicle_profit_payment_id;\n"
        "        expected_type := 'INVESTOR_PROFIT_PAYMENT'; expected_delta := -e_amount;\n"
        "    ELSE\n"
        "        SELECT result.tenant_id, sale.branch_id, result.company_share_amount,\n"
    )
    if prior.count(old_count) != 1 or prior.count(old_branch) != 1:
        raise RuntimeError("Expected prior typed source guard structure was not found.")
    return prior.replace(old_count, new_count, 1).replace(old_branch, new_branch, 1)


PROFIT_PAYMENT_SHAPE_SQL = r"""
CREATE FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_payment_id uuid;
    v_event_id uuid;
    p_tenant uuid;
    p_result uuid;
    p_investor uuid;
    p_branch uuid;
    p_account uuid;
    p_amount numeric;
    p_effective_at timestamptz;
    p_actor uuid;
    p_vehicle_revision uuid;
    p_investment_revision uuid;
    p_description text;
    p_reference text;
    e_tenant uuid;
    e_branch uuid;
    e_type text;
    e_amount numeric;
    e_effect integer;
    e_actor uuid;
    e_effective_at timestamptz;
    e_revision uuid;
    e_description text;
    e_reference text;
    result_tenant uuid;
    result_investor uuid;
    result_kind text;
    result_actor uuid;
    sale_branch uuid;
    investment_tenant uuid;
    investment_module text;
    investment_state text;
    vehicle_tenant uuid;
    vehicle_module text;
    vehicle_state text;
    accounting_tenant uuid;
    accounting_module text;
    accounting_state text;
    link_count bigint;
    movement_count bigint;
    application_count bigint;
    source_count integer;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorvehicleprofitpayment' THEN
        v_payment_id := NEW.id;
    ELSIF TG_TABLE_NAME = 'accounting_accountingsourcelink' THEN
        v_event_id := NEW.event_id;
        v_payment_id := NEW.investor_vehicle_profit_payment_id;
        IF v_payment_id IS NULL THEN
            IF EXISTS (
                SELECT 1 FROM accounting_accountingevent
                 WHERE id = v_event_id AND event_type = 'INVESTOR_PROFIT_PAYMENT'
            ) THEN
                RAISE EXCEPTION 'Investor Profit payment event requires its typed Investment source'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END IF;
    ELSIF TG_TABLE_NAME = 'accounting_accountingevent' THEN
        v_event_id := NEW.id;
    ELSE
        v_event_id := NEW.event_id;
    END IF;

    IF v_payment_id IS NULL THEN
        SELECT investor_vehicle_profit_payment_id
          INTO v_payment_id
          FROM accounting_accountingsourcelink
         WHERE event_id = v_event_id;
        IF v_payment_id IS NULL THEN
            IF EXISTS (
                SELECT 1 FROM accounting_accountingevent
                 WHERE id = v_event_id AND event_type = 'INVESTOR_PROFIT_PAYMENT'
            ) THEN
                RAISE EXCEPTION 'Investor Profit payment event requires one typed Investment source'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END IF;
    END IF;

    SELECT tenant_id, result_confirmation_id, investor_id, branch_id, account_id,
           amount, effective_at, actor_id, vehicle_module_revision_id,
           investment_module_revision_id,
           description, source_reference
      INTO p_tenant, p_result, p_investor, p_branch, p_account, p_amount,
           p_effective_at, p_actor, p_vehicle_revision, p_investment_revision,
           p_description, p_reference
      FROM investment_investorvehicleprofitpayment
     WHERE id = v_payment_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Investor Profit payment source does not exist'
            USING ERRCODE = '23503';
    END IF;

    SELECT COUNT(*)
      INTO link_count
      FROM accounting_accountingsourcelink
     WHERE investor_vehicle_profit_payment_id = v_payment_id;
    IF link_count <> 1 THEN
        RAISE EXCEPTION 'Investor Profit payment requires exactly one exclusive Accounting source link'
            USING ERRCODE = '23514';
    END IF;
    SELECT event_id,
           (investor_fund_credit_id IS NOT NULL)::integer
         + (investor_principal_return_id IS NOT NULL)::integer
         + (vehicle_purchase_payment_id IS NOT NULL)::integer
         + (vehicle_expense_payment_id IS NOT NULL)::integer
         + (vehicle_expense_refund_id IS NOT NULL)::integer
         + (vehicle_purchase_refund_id IS NOT NULL)::integer
         + (vehicle_sale_receipt_id IS NOT NULL)::integer
         + (vehicle_sale_refund_id IS NOT NULL)::integer
         + (vehicle_result_confirmation_id IS NOT NULL)::integer
      INTO v_event_id, source_count
      FROM accounting_accountingsourcelink
     WHERE investor_vehicle_profit_payment_id = v_payment_id;
    IF source_count <> 0 THEN
        RAISE EXCEPTION 'Investor Profit payment source link cannot contain another source type'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, branch_id, event_type, amount, effect_sign, actor_id,
           effective_at, module_revision_id, description, source_reference
      INTO e_tenant, e_branch, e_type, e_amount, e_effect, e_actor,
           e_effective_at, e_revision, e_description, e_reference
      FROM accounting_accountingevent
     WHERE id = v_event_id;
    SELECT COUNT(*) INTO movement_count
      FROM accounting_accountmovement
     WHERE event_id = v_event_id AND tenant_id = p_tenant
       AND account_id = p_account AND delta = -p_amount;
    SELECT COUNT(*) INTO application_count
      FROM accounting_accountingapplication
     WHERE source_event_id = v_event_id OR target_event_id = v_event_id;
    IF movement_count <> 1 OR application_count <> 0 THEN
        RAISE EXCEPTION 'Investor Profit payment requires one Cash/Bank outflow and no Income/Expense application'
            USING ERRCODE = '23514';
    END IF;

    SELECT COUNT(*) INTO link_count
      FROM accounting_accountmovement
     WHERE event_id = v_event_id;
    IF link_count <> 1 THEN
        RAISE EXCEPTION 'Investor Profit payment must have exactly one Cash/Bank movement'
            USING ERRCODE = '23514';
    END IF;

    SELECT result.tenant_id, result.investor_id, result.result_kind,
           result.confirmed_by_id, sale.branch_id
      INTO result_tenant, result_investor, result_kind, result_actor, sale_branch
      FROM investment_vehicleresultconfirmation result
      JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
     WHERE result.id = p_result;
    SELECT tenant_id, module_code, state
      INTO investment_tenant, investment_module, investment_state
      FROM tenants_companymodulestate WHERE id = p_investment_revision;
    SELECT tenant_id, module_code, state
      INTO vehicle_tenant, vehicle_module, vehicle_state
      FROM tenants_companymodulestate WHERE id = p_vehicle_revision;
    SELECT tenant_id, module_code, state
      INTO accounting_tenant, accounting_module, accounting_state
      FROM tenants_companymodulestate WHERE id = e_revision;

    IF result_tenant IS DISTINCT FROM p_tenant
       OR result_investor IS DISTINCT FROM p_investor
       OR result_kind IS DISTINCT FROM 'PROFIT'
       OR sale_branch IS DISTINCT FROM p_branch
       OR investment_tenant IS DISTINCT FROM p_tenant
       OR investment_module IS DISTINCT FROM 'investment'
       OR investment_state IS DISTINCT FROM 'enabled'
       OR vehicle_tenant IS DISTINCT FROM p_tenant
       OR vehicle_module IS DISTINCT FROM 'vehicle_management'
       OR vehicle_state IS DISTINCT FROM 'enabled'
       OR accounting_tenant IS DISTINCT FROM p_tenant
       OR accounting_module IS DISTINCT FROM 'accounting'
       OR accounting_state IS DISTINCT FROM 'enabled'
       OR e_tenant IS DISTINCT FROM p_tenant
       OR e_branch IS DISTINCT FROM p_branch
       OR e_type IS DISTINCT FROM 'INVESTOR_PROFIT_PAYMENT'
       OR e_amount IS DISTINCT FROM p_amount
       OR e_effect IS DISTINCT FROM 1
       OR e_actor IS DISTINCT FROM p_actor
       OR e_effective_at IS DISTINCT FROM p_effective_at
       OR e_description IS DISTINCT FROM p_description
       OR e_reference IS DISTINCT FROM p_reference
       OR NOT EXISTS (
            SELECT 1 FROM accounting_accountingaccount
             WHERE id = p_account AND tenant_id = p_tenant AND is_active
       ) THEN
        RAISE EXCEPTION 'Investor Profit payment, verified result, Sale Branch, modules, account, and Accounting event must match'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER accounting_investor_profit_payment_event_shape_v1
AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_investor_profit_payment_movement_shape_v1
AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_investor_profit_payment_link_shape_v1
AFTER INSERT ON accounting_accountingsourcelink DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_investor_profit_payment_source_shape_v1
AFTER INSERT ON investment_investorvehicleprofitpayment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1();
"""


def install_guards(apps, schema_editor):
    schema_editor.execute(_updated_source_guard())
    schema_editor.execute(PROFIT_PAYMENT_SHAPE_SQL)


def remove_guards(apps, schema_editor):
    schema_editor.execute(r"""
        DROP TRIGGER accounting_investor_profit_payment_source_shape_v1
            ON investment_investorvehicleprofitpayment;
        DROP TRIGGER accounting_investor_profit_payment_link_shape_v1
            ON accounting_accountingsourcelink;
        DROP TRIGGER accounting_investor_profit_payment_movement_shape_v1
            ON accounting_accountmovement;
        DROP TRIGGER accounting_investor_profit_payment_event_shape_v1
            ON accounting_accountingevent;
        DROP FUNCTION accounting_assert_investor_vehicle_profit_payment_shape_v1();
    """)
    schema_editor.execute(
        import_module(
            "apps.accounting.migrations.0019_vehicle_company_share_guards"
        ).SOURCE_LINK_GUARD_SQL
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0021_accountingsourcelink_investor_vehicle_profit_payment_and_more"),
        ("investment", "0016_investorvehicleprofitpayment"),
    ]

    operations = [migrations.RunPython(install_guards, remove_guards)]
