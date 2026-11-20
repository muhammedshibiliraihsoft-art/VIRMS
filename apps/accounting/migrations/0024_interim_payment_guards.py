from importlib import import_module

from django.db import migrations


def _updated_source_guard():
    prior = import_module(
        "apps.accounting.migrations.0022_investor_profit_payment_guards"
    )._updated_source_guard()
    old_count = "                  + (NEW.investor_vehicle_profit_payment_id IS NOT NULL)::integer;"
    new_count = (
        "                  + (NEW.investor_vehicle_profit_payment_id IS NOT NULL)::integer\n"
        "                  + (NEW.investor_interim_payment_id IS NOT NULL)::integer;"
    )
    old_branch = (
        "    ELSIF NEW.investor_vehicle_profit_payment_id IS NOT NULL THEN\n"
        "        SELECT tenant_id, branch_id, amount, actor_id, account_id\n"
        "          INTO s_company, s_branch, s_amount, s_actor, s_account\n"
        "          FROM investment_investorvehicleprofitpayment\n"
        "         WHERE id = NEW.investor_vehicle_profit_payment_id;\n"
        "        expected_type := 'INVESTOR_PROFIT_PAYMENT'; expected_delta := -e_amount;\n"
        "    ELSE\n"
    )
    new_branch = (
        "    ELSIF NEW.investor_vehicle_profit_payment_id IS NOT NULL THEN\n"
        "        SELECT tenant_id, branch_id, amount, actor_id, account_id\n"
        "          INTO s_company, s_branch, s_amount, s_actor, s_account\n"
        "          FROM investment_investorvehicleprofitpayment\n"
        "         WHERE id = NEW.investor_vehicle_profit_payment_id;\n"
        "        expected_type := 'INVESTOR_PROFIT_PAYMENT'; expected_delta := -e_amount;\n"
        "    ELSIF NEW.investor_interim_payment_id IS NOT NULL THEN\n"
        "        SELECT tenant_id, branch_id, amount, actor_id, account_id\n"
        "          INTO s_company, s_branch, s_amount, s_actor, s_account\n"
        "          FROM investment_investorinterimpayment\n"
        "         WHERE id = NEW.investor_interim_payment_id;\n"
        "        expected_type := 'INVESTOR_INTERIM_PAYMENT'; expected_delta := -e_amount;\n"
        "    ELSE\n"
    )
    if prior.count(old_count) != 1 or prior.count(old_branch) != 1:
        raise RuntimeError("Expected prior Accounting typed-source guard structure was not found.")
    return prior.replace(old_count, new_count, 1).replace(old_branch, new_branch, 1)


INTERIM_PAYMENT_GUARDS_SQL = r"""
CREATE FUNCTION investment_interim_payment_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Interim payments are immutable';
END;
$$;

CREATE TRIGGER investment_interim_payment_immutable
BEFORE UPDATE OR DELETE ON investment_investorinterimpayment
FOR EACH ROW EXECUTE FUNCTION investment_interim_payment_immutable();

CREATE FUNCTION investment_interim_payment_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    investor_company uuid;
    config_company uuid;
    config_investor uuid;
    config_effective date;
    branch_company uuid;
    account_company uuid;
    account_active boolean;
    investment_company uuid;
    investment_module text;
    investment_state text;
    accounting_company uuid;
    accounting_module text;
    accounting_state text;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'Investor Interim payments are immutable';
    END IF;

    SELECT tenant_id INTO investor_company
      FROM investment_investor WHERE id = NEW.investor_id;
    SELECT tenant_id, investor_id, effective_date
      INTO config_company, config_investor, config_effective
      FROM investment_investorinterimconfiguration WHERE id = NEW.configuration_id;
    SELECT tenant_id INTO branch_company
      FROM tenants_branch WHERE id = NEW.branch_id;
    SELECT tenant_id, is_active INTO account_company, account_active
      FROM accounting_accountingaccount WHERE id = NEW.account_id;
    SELECT tenant_id, module_code, state
      INTO investment_company, investment_module, investment_state
      FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;
    SELECT tenant_id, module_code, state
      INTO accounting_company, accounting_module, accounting_state
      FROM tenants_companymodulestate WHERE id = NEW.accounting_module_revision_id;

    IF investor_company IS DISTINCT FROM NEW.tenant_id
       OR config_company IS DISTINCT FROM NEW.tenant_id
       OR config_investor IS DISTINCT FROM NEW.investor_id
       OR config_effective IS NULL OR config_effective > NEW.period_month
       OR branch_company IS DISTINCT FROM NEW.tenant_id
       OR account_company IS DISTINCT FROM NEW.tenant_id OR account_active IS DISTINCT FROM TRUE
       OR investment_company IS DISTINCT FROM NEW.tenant_id
       OR investment_module IS DISTINCT FROM 'investment'
       OR investment_state IS DISTINCT FROM 'enabled'
       OR accounting_company IS DISTINCT FROM NEW.tenant_id
       OR accounting_module IS DISTINCT FROM 'accounting'
       OR accounting_state IS DISTINCT FROM 'enabled'
       OR NEW.period_month <> date_trunc('month', NEW.effective_at AT TIME ZONE 'UTC')::date
       OR NEW.effective_at > clock_timestamp()
       OR NEW.amount <= 0
       OR NEW.description = '' OR NEW.description <> BTRIM(NEW.description)
       OR NEW.source_reference = '' OR NEW.source_reference <> BTRIM(NEW.source_reference) THEN
        RAISE EXCEPTION 'Investor Interim payment Company, Branch, month, configuration, account, or module scope is invalid'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER investment_interim_payment_scope
BEFORE INSERT ON investment_investorinterimpayment
FOR EACH ROW EXECUTE FUNCTION investment_interim_payment_scope_guard();

CREATE FUNCTION accounting_assert_investor_interim_payment_shape_v1()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_payment_id uuid;
    v_event_id uuid;
    p_tenant uuid;
    p_investor uuid;
    p_configuration uuid;
    p_branch uuid;
    p_account uuid;
    p_amount numeric;
    p_month date;
    p_effective_at timestamptz;
    p_actor uuid;
    p_investment_revision uuid;
    p_accounting_revision uuid;
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
    investment_tenant uuid;
    investment_module text;
    investment_state text;
    accounting_tenant uuid;
    accounting_module text;
    accounting_state text;
    current_config uuid;
    monthly_limit numeric;
    monthly_total numeric;
    link_count bigint;
    movement_count bigint;
    application_count bigint;
    source_count integer;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorinterimpayment' THEN
        v_payment_id := NEW.id;
    ELSIF TG_TABLE_NAME = 'accounting_accountingsourcelink' THEN
        v_event_id := NEW.event_id;
        v_payment_id := NEW.investor_interim_payment_id;
        IF v_payment_id IS NULL THEN
            IF EXISTS (
                SELECT 1 FROM accounting_accountingevent
                 WHERE id = v_event_id AND event_type = 'INVESTOR_INTERIM_PAYMENT'
            ) THEN
                RAISE EXCEPTION 'Investor Interim event requires its typed Investment source'
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
        SELECT investor_interim_payment_id INTO v_payment_id
          FROM accounting_accountingsourcelink WHERE event_id = v_event_id;
        IF v_payment_id IS NULL THEN
            IF EXISTS (
                SELECT 1 FROM accounting_accountingevent
                 WHERE id = v_event_id AND event_type = 'INVESTOR_INTERIM_PAYMENT'
            ) THEN
                RAISE EXCEPTION 'Investor Interim event requires one typed Investment source'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END IF;
    END IF;

    SELECT tenant_id, investor_id, configuration_id, branch_id, account_id,
           amount, period_month, effective_at, actor_id,
           investment_module_revision_id, accounting_module_revision_id,
           description, source_reference
      INTO p_tenant, p_investor, p_configuration, p_branch, p_account,
           p_amount, p_month, p_effective_at, p_actor,
           p_investment_revision, p_accounting_revision,
           p_description, p_reference
      FROM investment_investorinterimpayment WHERE id = v_payment_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Investor Interim payment source does not exist'
            USING ERRCODE = '23503';
    END IF;

    SELECT COUNT(*) INTO link_count
      FROM accounting_accountingsourcelink
     WHERE investor_interim_payment_id = v_payment_id;
    IF link_count <> 1 THEN
        RAISE EXCEPTION 'Investor Interim payment requires one exclusive Accounting source link'
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
         + (investor_vehicle_profit_payment_id IS NOT NULL)::integer
      INTO v_event_id, source_count
      FROM accounting_accountingsourcelink
     WHERE investor_interim_payment_id = v_payment_id;
    IF source_count <> 0 THEN
        RAISE EXCEPTION 'Investor Interim source link cannot contain another source type'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, branch_id, event_type, amount, effect_sign, actor_id,
           effective_at, module_revision_id, description, source_reference
      INTO e_tenant, e_branch, e_type, e_amount, e_effect, e_actor,
           e_effective_at, e_revision, e_description, e_reference
      FROM accounting_accountingevent WHERE id = v_event_id;
    SELECT COUNT(*) INTO movement_count
      FROM accounting_accountmovement
     WHERE event_id = v_event_id AND tenant_id = p_tenant
       AND account_id = p_account AND delta = -p_amount;
    SELECT COUNT(*) INTO application_count
      FROM accounting_accountingapplication
     WHERE source_event_id = v_event_id OR target_event_id = v_event_id;
    IF movement_count <> 1 OR application_count <> 0 THEN
        RAISE EXCEPTION 'Investor Interim payment requires one Cash/Bank outflow and no Income/Expense application'
            USING ERRCODE = '23514';
    END IF;
    SELECT COUNT(*) INTO link_count FROM accounting_accountmovement WHERE event_id = v_event_id;
    IF link_count <> 1 THEN
        RAISE EXCEPTION 'Investor Interim payment must have exactly one Cash/Bank movement'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, module_code, state
      INTO investment_tenant, investment_module, investment_state
      FROM tenants_companymodulestate WHERE id = p_investment_revision;
    SELECT tenant_id, module_code, state
      INTO accounting_tenant, accounting_module, accounting_state
      FROM tenants_companymodulestate WHERE id = e_revision;

    PERFORM 1 FROM investment_investor
     WHERE id = p_investor AND tenant_id = p_tenant FOR UPDATE;
    SELECT id, amount INTO current_config, monthly_limit
      FROM investment_investorinterimconfiguration
     WHERE tenant_id = p_tenant AND investor_id = p_investor
       AND effective_date <= p_month
     ORDER BY effective_date DESC, id DESC LIMIT 1;
    SELECT COALESCE(SUM(amount), 0) INTO monthly_total
      FROM investment_investorinterimpayment
     WHERE tenant_id = p_tenant AND investor_id = p_investor
       AND period_month = p_month;

    IF current_config IS DISTINCT FROM p_configuration
       OR monthly_limit IS NULL OR monthly_total > monthly_limit
       OR investment_tenant IS DISTINCT FROM p_tenant
       OR investment_module IS DISTINCT FROM 'investment'
       OR investment_state IS DISTINCT FROM 'enabled'
       OR accounting_tenant IS DISTINCT FROM p_tenant
       OR accounting_module IS DISTINCT FROM 'accounting'
       OR accounting_state IS DISTINCT FROM 'enabled'
       OR e_tenant IS DISTINCT FROM p_tenant
       OR e_branch IS DISTINCT FROM p_branch
       OR e_type IS DISTINCT FROM 'INVESTOR_INTERIM_PAYMENT'
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
        RAISE EXCEPTION 'Investor Interim payment, monthly limit, Cash/Bank event, Company, Branch, actor, and modules must match'
            USING ERRCODE = '23514';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = 'investment.interim.payment.create'
           AND event.company_id = p_tenant
           AND event.branch_id = p_branch
           AND event.resource_id = v_payment_id
           AND event.actor_id = p_actor
           AND event.reason = p_description
           AND event.metadata->>'payment_id' = v_payment_id::text
           AND event.metadata->>'investor_id' = p_investor::text
           AND event.metadata->>'configuration_id' = p_configuration::text
           AND event.metadata->>'account_id' = p_account::text
           AND event.metadata->>'period_month' = p_month::text
           AND event.metadata->>'amount' = p_amount::text
           AND event.metadata->>'accounting_event_id' = v_event_id::text
           AND event.metadata->>'cash_movement_created' = 'true'
    ) THEN
        RAISE EXCEPTION 'Investor Interim payment requires matching scoped audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER accounting_interim_payment_event_shape_v1
AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_interim_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_interim_payment_movement_shape_v1
AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_interim_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_interim_payment_link_shape_v1
AFTER INSERT ON accounting_accountingsourcelink DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_interim_payment_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_interim_payment_source_shape_v1
AFTER INSERT ON investment_investorinterimpayment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_investor_interim_payment_shape_v1();
"""


def install_guards(apps, schema_editor):
    schema_editor.execute(_updated_source_guard())
    schema_editor.execute(INTERIM_PAYMENT_GUARDS_SQL)


def remove_guards(apps, schema_editor):
    schema_editor.execute(r"""
        DROP TRIGGER accounting_interim_payment_source_shape_v1
            ON investment_investorinterimpayment;
        DROP TRIGGER accounting_interim_payment_link_shape_v1
            ON accounting_accountingsourcelink;
        DROP TRIGGER accounting_interim_payment_movement_shape_v1
            ON accounting_accountmovement;
        DROP TRIGGER accounting_interim_payment_event_shape_v1
            ON accounting_accountingevent;
        DROP FUNCTION accounting_assert_investor_interim_payment_shape_v1();
        DROP TRIGGER investment_interim_payment_scope
            ON investment_investorinterimpayment;
        DROP FUNCTION investment_interim_payment_scope_guard();
        DROP TRIGGER investment_interim_payment_immutable
            ON investment_investorinterimpayment;
        DROP FUNCTION investment_interim_payment_immutable();
    """)
    schema_editor.execute(
        import_module(
            "apps.accounting.migrations.0022_investor_profit_payment_guards"
        )._updated_source_guard()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0023_investor_interim_accounting_source"),
        ("investment", "0019_investorinterimpayment"),
    ]

    operations = [migrations.RunPython(install_guards, remove_guards)]
