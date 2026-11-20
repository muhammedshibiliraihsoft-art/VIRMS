from importlib import import_module

from django.db import migrations


SOURCE_LINK_GUARD_SQL = r"""
CREATE OR REPLACE FUNCTION accounting_source_insert_guard_v4()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    e_company uuid;
    e_branch uuid;
    e_type text;
    e_amount numeric;
    e_actor uuid;
    e_category uuid;
    e_effect integer;
    e_reversal uuid;
    e_replacement uuid;
    e_effective_at timestamptz;
    e_module_revision uuid;
    s_company uuid;
    s_branch uuid;
    s_amount numeric;
    s_actor uuid;
    s_account uuid;
    s_effective_at timestamptz;
    s_result_kind text;
    expected_delta numeric;
    expected_type text;
    source_count integer;
    revision_company uuid;
    revision_module text;
    revision_state text;
BEGIN
    source_count := (NEW.investor_fund_credit_id IS NOT NULL)::integer
                  + (NEW.investor_principal_return_id IS NOT NULL)::integer
                  + (NEW.vehicle_purchase_payment_id IS NOT NULL)::integer
                  + (NEW.vehicle_expense_payment_id IS NOT NULL)::integer
                  + (NEW.vehicle_expense_refund_id IS NOT NULL)::integer
                  + (NEW.vehicle_purchase_refund_id IS NOT NULL)::integer
                  + (NEW.vehicle_sale_receipt_id IS NOT NULL)::integer
                  + (NEW.vehicle_sale_refund_id IS NOT NULL)::integer
                  + (NEW.vehicle_result_confirmation_id IS NOT NULL)::integer;
    SELECT tenant_id, branch_id, event_type, amount, actor_id, category_id,
           effect_sign, reversal_of_id, replaces_event_id, effective_at, module_revision_id
      INTO e_company, e_branch, e_type, e_amount, e_actor, e_category,
           e_effect, e_reversal, e_replacement, e_effective_at, e_module_revision
      FROM accounting_accountingevent WHERE id = NEW.event_id;

    IF source_count <> 1 OR e_company IS DISTINCT FROM NEW.tenant_id
       OR e_effect <> 1 OR e_category IS NOT NULL
       OR e_reversal IS NOT NULL OR e_replacement IS NOT NULL THEN
        RAISE EXCEPTION 'Typed source link requires one same-Company current unclassified event'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.investor_fund_credit_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id INTO s_company, s_branch, s_amount, s_actor
          FROM investment_investorfundcredit WHERE id = NEW.investor_fund_credit_id;
        expected_type := 'CAPITAL_INFLOW'; expected_delta := e_amount;
    ELSIF NEW.investor_principal_return_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id INTO s_company, s_branch, s_amount, s_actor
          FROM investment_investorprincipalreturn WHERE id = NEW.investor_principal_return_id;
        expected_type := 'CAPITAL_OUTFLOW'; expected_delta := -e_amount;
    ELSIF NEW.vehicle_purchase_payment_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehiclepurchasepayment WHERE id = NEW.vehicle_purchase_payment_id;
        expected_type := 'VEHICLE_PAYMENT'; expected_delta := -e_amount;
    ELSIF NEW.vehicle_expense_payment_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehicleexpensepayment WHERE id = NEW.vehicle_expense_payment_id;
        expected_type := 'VEHICLE_PAYMENT'; expected_delta := -e_amount;
    ELSIF NEW.vehicle_expense_refund_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehicleexpenserefund WHERE id = NEW.vehicle_expense_refund_id;
        expected_type := 'VEHICLE_REFUND_IN'; expected_delta := e_amount;
    ELSIF NEW.vehicle_purchase_refund_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehiclepurchaserefund WHERE id = NEW.vehicle_purchase_refund_id;
        expected_type := 'PURCHASE_REFUND_IN'; expected_delta := e_amount;
    ELSIF NEW.vehicle_sale_receipt_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehiclesalereceipt WHERE id = NEW.vehicle_sale_receipt_id;
        expected_type := 'VEHICLE_SALE_RECEIPT'; expected_delta := e_amount;
    ELSIF NEW.vehicle_sale_refund_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
          FROM vehicles_vehiclesalerefund WHERE id = NEW.vehicle_sale_refund_id;
        expected_type := 'VEHICLE_SALE_REFUND'; expected_delta := -e_amount;
    ELSE
        SELECT result.tenant_id, sale.branch_id, result.company_share_amount,
               result.confirmed_by_id, sale.sold_at, result.result_kind
          INTO s_company, s_branch, s_amount, s_actor, s_effective_at, s_result_kind
          FROM investment_vehicleresultconfirmation result
          JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
         WHERE result.id = NEW.vehicle_result_confirmation_id;
        expected_type := 'VEHICLE_COMPANY_SHARE';
        expected_delta := NULL;
        SELECT tenant_id, module_code, state
          INTO revision_company, revision_module, revision_state
          FROM tenants_companymodulestate WHERE id = e_module_revision;
        IF revision_company IS DISTINCT FROM NEW.tenant_id
           OR revision_module IS DISTINCT FROM 'accounting'
           OR revision_state IS DISTINCT FROM 'enabled'
           OR s_result_kind IS DISTINCT FROM 'PROFIT'
           OR s_amount <= 0
           OR s_effective_at IS DISTINCT FROM e_effective_at THEN
            RAISE EXCEPTION 'Vehicle Company Share requires a positive verified result, Sale date, and enabled Accounting revision'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF e_type IS DISTINCT FROM expected_type
       OR s_company IS DISTINCT FROM NEW.tenant_id
       OR s_branch IS DISTINCT FROM e_branch
       OR s_amount IS DISTINCT FROM e_amount
       OR s_actor IS DISTINCT FROM e_actor THEN
        RAISE EXCEPTION 'Typed source and Accounting event Company/Branch/amount/actor/type must match'
            USING ERRCODE = '23514';
    END IF;
    IF s_account IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM accounting_accountmovement
         WHERE event_id = NEW.event_id AND tenant_id = NEW.tenant_id
           AND account_id = s_account AND delta = expected_delta
    ) THEN
        RAISE EXCEPTION 'Vehicle Cash/Bank source must use its selected account and exact signed amount'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
"""


COMPANY_SHARE_SHAPE_SQL = r"""
CREATE FUNCTION accounting_assert_vehicle_company_share_shape_v1()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_event_id uuid;
    v_tenant uuid;
    v_branch uuid;
    v_type text;
    v_amount numeric;
    v_effect integer;
    v_reversal uuid;
    v_category uuid;
    v_effective_at timestamptz;
    v_actor uuid;
    v_revision uuid;
    v_link_count bigint;
    v_result_id uuid;
    v_source_count integer;
    v_movement_count bigint;
    v_result_tenant uuid;
    v_result_vehicle uuid;
    v_result_sale uuid;
    v_result_share numeric;
    v_result_kind text;
    v_result_actor uuid;
    v_result_revision uuid;
    v_sale_branch uuid;
    v_sale_date timestamptz;
    v_revision_tenant uuid;
    v_revision_module text;
    v_revision_state text;
    v_original_tenant uuid;
    v_original_branch uuid;
    v_original_type text;
    v_original_amount numeric;
    v_original_effect integer;
    v_original_date timestamptz;
    v_original_result uuid;
    v_positive_count bigint;
BEGIN
    IF TG_TABLE_NAME = 'investment_vehicleresultconfirmation' THEN
        IF NEW.accounting_module_revision_id IS NULL THEN
            RAISE EXCEPTION 'Vehicle result confirmation requires its Accounting module revision'
                USING ERRCODE = '23514';
        END IF;
        SELECT tenant_id, module_code, state
          INTO v_revision_tenant, v_revision_module, v_revision_state
          FROM tenants_companymodulestate WHERE id = NEW.accounting_module_revision_id;
        IF v_revision_tenant IS DISTINCT FROM NEW.tenant_id
           OR v_revision_module IS DISTINCT FROM 'accounting'
           OR v_revision_state IS DISTINCT FROM 'enabled' THEN
            RAISE EXCEPTION 'Vehicle result confirmation requires an enabled same-Company Accounting revision'
                USING ERRCODE = '23514';
        END IF;
        IF NEW.result_kind = 'PROFIT' AND NEW.company_share_amount > 0 AND NOT EXISTS (
            SELECT 1
              FROM accounting_accountingsourcelink link
              JOIN accounting_accountingevent event ON event.id = link.event_id
             WHERE link.vehicle_result_confirmation_id = NEW.id
               AND event.event_type = 'VEHICLE_COMPANY_SHARE'
               AND event.effect_sign = 1
               AND event.amount = NEW.company_share_amount
               AND event.actor_id = NEW.confirmed_by_id
               AND event.module_revision_id = NEW.accounting_module_revision_id
        ) THEN
            RAISE EXCEPTION 'Positive Vehicle result confirmation requires linked Company Share recognition'
                USING ERRCODE = '23514';
        END IF;
        RETURN NULL;
    END IF;

    IF TG_TABLE_NAME = 'accounting_accountingevent' THEN
        v_event_id := NEW.id;
    ELSIF TG_TABLE_NAME = 'accounting_accountmovement' THEN
        v_event_id := NEW.event_id;
    ELSE
        v_event_id := NEW.event_id;
    END IF;

    SELECT tenant_id, branch_id, event_type, amount, effect_sign,
           reversal_of_id, category_id, effective_at, actor_id, module_revision_id
      INTO v_tenant, v_branch, v_type, v_amount, v_effect, v_reversal,
           v_category, v_effective_at, v_actor, v_revision
      FROM accounting_accountingevent WHERE id = v_event_id;
    IF NOT FOUND THEN RETURN NULL; END IF;

    IF v_type <> 'VEHICLE_COMPANY_SHARE' THEN
        IF EXISTS (
            SELECT 1 FROM accounting_accountingsourcelink
             WHERE event_id = v_event_id AND vehicle_result_confirmation_id IS NOT NULL
        ) THEN
            RAISE EXCEPTION 'Vehicle result source may only link a Vehicle Company Share event'
                USING ERRCODE = '23514';
        END IF;
        RETURN NULL;
    END IF;

    SELECT COUNT(*), COUNT(vehicle_result_confirmation_id),
           (COUNT(investor_fund_credit_id) + COUNT(investor_principal_return_id)
            + COUNT(vehicle_purchase_payment_id) + COUNT(vehicle_expense_payment_id)
            + COUNT(vehicle_expense_refund_id) + COUNT(vehicle_purchase_refund_id)
            + COUNT(vehicle_sale_receipt_id) + COUNT(vehicle_sale_refund_id))
      INTO v_link_count, v_positive_count, v_source_count
      FROM accounting_accountingsourcelink WHERE event_id = v_event_id;
    SELECT COUNT(*) INTO v_movement_count
      FROM accounting_accountmovement WHERE event_id = v_event_id;
    IF v_category IS NOT NULL OR v_movement_count <> 0 THEN
        RAISE EXCEPTION 'Vehicle Company Share is unclassified source Income with no cash movement'
            USING ERRCODE = '23514';
    END IF;

    SELECT tenant_id, module_code, state
      INTO v_revision_tenant, v_revision_module, v_revision_state
      FROM tenants_companymodulestate WHERE id = v_revision;
    IF v_revision_tenant IS DISTINCT FROM v_tenant
       OR v_revision_module IS DISTINCT FROM 'accounting'
       OR v_revision_state IS DISTINCT FROM 'enabled' THEN
        RAISE EXCEPTION 'Vehicle Company Share requires an enabled same-Company Accounting revision'
            USING ERRCODE = '23514';
    END IF;

    IF v_effect = 1 AND v_reversal IS NULL THEN
        IF v_link_count <> 1 OR v_positive_count <> 1 OR v_source_count <> 0 THEN
            RAISE EXCEPTION 'Positive Vehicle Company Share requires exactly one typed result source'
                USING ERRCODE = '23514';
        END IF;
        SELECT vehicle_result_confirmation_id INTO v_result_id
          FROM accounting_accountingsourcelink WHERE event_id = v_event_id;
        SELECT result.tenant_id, result.vehicle_id, result.sale_id,
               result.company_share_amount, result.result_kind,
               result.confirmed_by_id, result.accounting_module_revision_id,
               sale.branch_id, sale.sold_at
          INTO v_result_tenant, v_result_vehicle, v_result_sale,
               v_result_share, v_result_kind, v_result_actor, v_result_revision,
               v_sale_branch, v_sale_date
          FROM investment_vehicleresultconfirmation result
          JOIN vehicles_vehiclesale sale ON sale.id = result.sale_id
         WHERE result.id = v_result_id;
        IF v_result_tenant IS DISTINCT FROM v_tenant
           OR v_result_kind IS DISTINCT FROM 'PROFIT'
           OR v_result_share IS DISTINCT FROM v_amount
           OR v_result_share <= 0
           OR v_result_actor IS DISTINCT FROM v_actor
           OR v_result_revision IS DISTINCT FROM v_revision
           OR v_sale_branch IS DISTINCT FROM v_branch
           OR v_sale_date IS DISTINCT FROM v_effective_at THEN
            RAISE EXCEPTION 'Vehicle Company Share must match its verified result, Sale, Branch, amount, actor, and Accounting revision'
                USING ERRCODE = '23514';
        END IF;
        SELECT COUNT(*) INTO v_positive_count
          FROM accounting_accountingsourcelink link
          JOIN accounting_accountingevent event ON event.id = link.event_id
         WHERE link.vehicle_result_confirmation_id = v_result_id
           AND event.event_type = 'VEHICLE_COMPANY_SHARE'
           AND event.effect_sign = 1;
        IF v_positive_count <> 1 THEN
            RAISE EXCEPTION 'A Vehicle result may have only one positive Company Share recognition'
                USING ERRCODE = '23514';
        END IF;
    ELSIF v_effect = -1 AND v_reversal IS NOT NULL THEN
        IF v_link_count <> 0 OR v_positive_count <> 0 OR v_source_count <> 0 OR v_amount <= 0 THEN
            RAISE EXCEPTION 'Vehicle Company Share reversal cannot have another source link or movement'
                USING ERRCODE = '23514';
        END IF;
        SELECT tenant_id, branch_id, event_type, amount, effect_sign, effective_at
          INTO v_original_tenant, v_original_branch, v_original_type,
               v_original_amount, v_original_effect, v_original_date
          FROM accounting_accountingevent WHERE id = v_reversal;
        IF v_original_tenant IS DISTINCT FROM v_tenant
           OR v_original_branch IS DISTINCT FROM v_branch
           OR v_original_type IS DISTINCT FROM 'VEHICLE_COMPANY_SHARE'
           OR v_original_amount IS DISTINCT FROM v_amount
           OR v_original_effect IS DISTINCT FROM 1
           OR v_original_date IS DISTINCT FROM v_effective_at
           OR NOT EXISTS (
                SELECT 1 FROM accounting_accountingsourcelink
                 WHERE event_id = v_reversal AND vehicle_result_confirmation_id IS NOT NULL
           ) THEN
            RAISE EXCEPTION 'Vehicle Company Share reversal must match an original typed recognition'
                USING ERRCODE = '23514';
        END IF;
    ELSE
        RAISE EXCEPTION 'Vehicle Company Share event must be a current recognition or an audited reversal'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER accounting_vehicle_company_share_event_shape_v1
AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_vehicle_company_share_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_vehicle_company_share_movement_shape_v1
AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_vehicle_company_share_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_vehicle_company_share_link_shape_v1
AFTER INSERT ON accounting_accountingsourcelink DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_vehicle_company_share_shape_v1();
CREATE CONSTRAINT TRIGGER accounting_vehicle_company_share_confirmation_shape_v1
AFTER INSERT ON investment_vehicleresultconfirmation DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_vehicle_company_share_shape_v1();
"""


def install_guards(apps, schema_editor):
    schema_editor.execute(SOURCE_LINK_GUARD_SQL)
    schema_editor.execute(COMPANY_SHARE_SHAPE_SQL)


def restore_guards(apps, schema_editor):
    schema_editor.execute(r"""
        DROP TRIGGER accounting_vehicle_company_share_confirmation_shape_v1 ON investment_vehicleresultconfirmation;
        DROP TRIGGER accounting_vehicle_company_share_link_shape_v1 ON accounting_accountingsourcelink;
        DROP TRIGGER accounting_vehicle_company_share_movement_shape_v1 ON accounting_accountmovement;
        DROP TRIGGER accounting_vehicle_company_share_event_shape_v1 ON accounting_accountingevent;
        DROP FUNCTION accounting_assert_vehicle_company_share_shape_v1();
    """)
    previous = import_module(
        "apps.accounting.migrations.0010_remove_accountingevent_acct_event_type_ck_and_more"
    ).PHASE5_SOURCE_GUARDS_SQL
    start = previous.index("CREATE FUNCTION accounting_source_insert_guard_v4()")
    end = previous.index("\nCREATE FUNCTION accounting_phase5_vehicle_source_shape_v1()", start)
    previous_guard = previous[start:end].split(
        "\nCREATE TRIGGER accounting_source_insert_guard_v4", 1
    )[0].replace("CREATE FUNCTION accounting_source_insert_guard_v4()", "CREATE OR REPLACE FUNCTION accounting_source_insert_guard_v4()", 1)
    schema_editor.execute(previous_guard)


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0018_company_share_recognition"),
        ("investment", "0015_company_share_recognition"),
    ]

    operations = [
        migrations.RunPython(install_guards, restore_guards),
    ]
