from django.db import migrations


FORWARD_SQL = r"""
DROP TRIGGER accounting_capital_source_insert_guard ON accounting_accountingsourcelink;
DROP TRIGGER accounting_capital_event_shape_deferred ON accounting_accountingevent;
DROP TRIGGER accounting_capital_movement_shape_deferred ON accounting_accountmovement;
DROP TRIGGER accounting_capital_source_shape_deferred ON accounting_accountingsourcelink;
DROP TRIGGER accounting_fund_credit_source_shape_deferred ON investment_investorfundcredit;
DROP TRIGGER accounting_principal_return_source_shape_deferred ON investment_investorprincipalreturn;

CREATE FUNCTION accounting_source_insert_guard_v2()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    e_company uuid;
    e_branch uuid;
    e_type text;
    e_amount numeric;
    e_effect integer;
    e_category uuid;
    e_reversal uuid;
    e_replacement uuid;
    s_company uuid;
    s_branch uuid;
    s_amount numeric;
    s_actor uuid;
    s_account uuid;
    source_count integer;
BEGIN
    SELECT tenant_id, branch_id, event_type, amount, effect_sign, category_id,
           reversal_of_id, replaces_event_id
      INTO e_company, e_branch, e_type, e_amount, e_effect, e_category,
           e_reversal, e_replacement
    FROM accounting_accountingevent WHERE id = NEW.event_id;

    source_count := (NEW.investor_fund_credit_id IS NOT NULL)::integer
                  + (NEW.investor_principal_return_id IS NOT NULL)::integer
                  + (NEW.vehicle_purchase_payment_id IS NOT NULL)::integer;
    IF source_count <> 1
       OR e_company IS DISTINCT FROM NEW.tenant_id
       OR e_effect <> 1
       OR e_category IS NOT NULL
       OR e_reversal IS NOT NULL
       OR e_replacement IS NOT NULL THEN
        RAISE EXCEPTION 'Typed source link requires one same-Company current unclassified event'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.vehicle_purchase_payment_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id, account_id
          INTO s_company, s_branch, s_amount, s_actor, s_account
        FROM vehicles_vehiclepurchasepayment WHERE id = NEW.vehicle_purchase_payment_id;
        IF e_type IS DISTINCT FROM 'VEHICLE_PAYMENT' THEN
            RAISE EXCEPTION 'Vehicle Purchase payment must link to a Vehicle Payment event'
                USING ERRCODE = '23514';
        END IF;
    ELSIF NEW.investor_fund_credit_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, amount, actor_id
          INTO s_company, s_branch, s_amount, s_actor
        FROM investment_investorfundcredit WHERE id = NEW.investor_fund_credit_id;
        IF e_type IS DISTINCT FROM 'CAPITAL_INFLOW' THEN
            RAISE EXCEPTION 'Fund credit must link to a Capital Inflow event'
                USING ERRCODE = '23514';
        END IF;
    ELSE
        SELECT tenant_id, branch_id, amount, actor_id
          INTO s_company, s_branch, s_amount, s_actor
        FROM investment_investorprincipalreturn WHERE id = NEW.investor_principal_return_id;
        IF e_type IS DISTINCT FROM 'CAPITAL_OUTFLOW' THEN
            RAISE EXCEPTION 'Principal return must link to a Capital Outflow event'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF s_company IS DISTINCT FROM NEW.tenant_id
       OR s_branch IS DISTINCT FROM e_branch
       OR s_amount IS DISTINCT FROM e_amount
       OR s_actor IS DISTINCT FROM (SELECT actor_id FROM accounting_accountingevent WHERE id = NEW.event_id) THEN
        RAISE EXCEPTION 'Typed source and Accounting event Company/Branch/amount/actor must match'
            USING ERRCODE = '23514';
    END IF;
    IF NEW.vehicle_purchase_payment_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM accounting_accountmovement
        WHERE event_id = NEW.event_id AND account_id = s_account AND delta = -e_amount
    ) THEN
        RAISE EXCEPTION 'Vehicle Purchase payment event must move the exact amount from its selected account'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER accounting_source_insert_guard_v2
BEFORE INSERT ON accounting_accountingsourcelink
FOR EACH ROW EXECUTE FUNCTION accounting_source_insert_guard_v2();

CREATE FUNCTION accounting_assert_source_shape_v2()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_event_id uuid;
    v_event_type text;
    v_amount numeric;
    v_tenant uuid;
    v_branch uuid;
    v_actor uuid;
    v_movement_count bigint;
    v_movement_total numeric;
    v_link_count bigint;
    v_credit_count bigint;
    v_return_count bigint;
    v_payment_count bigint;
    v_source_amount numeric;
    v_source_tenant uuid;
    v_source_branch uuid;
    v_source_actor uuid;
    v_source_account uuid;
BEGIN
    IF TG_TABLE_NAME = 'accounting_accountingevent' THEN
        v_event_id := NEW.id;
    ELSIF TG_TABLE_NAME = 'accounting_accountmovement' THEN
        v_event_id := NEW.event_id;
    ELSIF TG_TABLE_NAME = 'accounting_accountingsourcelink' THEN
        v_event_id := NEW.event_id;
    ELSIF TG_TABLE_NAME = 'investment_investorfundcredit' THEN
        SELECT event_id INTO v_event_id FROM accounting_accountingsourcelink
        WHERE investor_fund_credit_id = NEW.id;
    ELSIF TG_TABLE_NAME = 'investment_investorprincipalreturn' THEN
        SELECT event_id INTO v_event_id FROM accounting_accountingsourcelink
        WHERE investor_principal_return_id = NEW.id;
    ELSE
        SELECT event_id INTO v_event_id FROM accounting_accountingsourcelink
        WHERE vehicle_purchase_payment_id = NEW.id;
    END IF;

    IF v_event_id IS NULL THEN
        IF TG_TABLE_NAME IN ('investment_investorfundcredit',
                             'investment_investorprincipalreturn',
                             'vehicles_vehiclepurchasepayment') THEN
            RAISE EXCEPTION 'Cash source requires one linked typed Accounting event'
                USING ERRCODE = '23514';
        END IF;
        RETURN NULL;
    END IF;

    SELECT tenant_id, branch_id, event_type, amount, actor_id
      INTO v_tenant, v_branch, v_event_type, v_amount, v_actor
    FROM accounting_accountingevent WHERE id = v_event_id;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    IF v_event_type NOT IN ('CAPITAL_INFLOW', 'CAPITAL_OUTFLOW', 'VEHICLE_PAYMENT') THEN
        IF TG_TABLE_NAME = 'accounting_accountingsourcelink' THEN
            IF NEW.investor_fund_credit_id IS NOT NULL
               OR NEW.investor_principal_return_id IS NOT NULL
               OR NEW.vehicle_purchase_payment_id IS NOT NULL THEN
                RAISE EXCEPTION 'Typed source link cannot reference an unrelated Accounting event'
                    USING ERRCODE = '23514';
            END IF;
        END IF;
        RETURN NULL;
    END IF;

    SELECT COUNT(*), COALESCE(SUM(delta), 0)
      INTO v_movement_count, v_movement_total
    FROM accounting_accountmovement WHERE event_id = v_event_id;
    SELECT COUNT(*), COUNT(investor_fund_credit_id),
           COUNT(investor_principal_return_id), COUNT(vehicle_purchase_payment_id)
      INTO v_link_count, v_credit_count, v_return_count, v_payment_count
    FROM accounting_accountingsourcelink WHERE event_id = v_event_id;
    IF v_movement_count <> 1 OR v_link_count <> 1 THEN
        RAISE EXCEPTION 'Source event requires exactly one typed link and one Cash/Bank movement'
            USING ERRCODE = '23514';
    END IF;

    IF v_event_type = 'CAPITAL_INFLOW' THEN
        IF v_credit_count <> 1 OR v_return_count <> 0 OR v_payment_count <> 0
           OR v_movement_total <> v_amount THEN
            RAISE EXCEPTION 'Capital Inflow source or movement does not reconcile'
                USING ERRCODE = '23514';
        END IF;
        SELECT tenant_id, branch_id, amount, actor_id
          INTO v_source_tenant, v_source_branch, v_source_amount, v_source_actor
        FROM investment_investorfundcredit
        WHERE id = (SELECT investor_fund_credit_id FROM accounting_accountingsourcelink WHERE event_id = v_event_id);
    ELSIF v_event_type = 'CAPITAL_OUTFLOW' THEN
        IF v_credit_count <> 0 OR v_return_count <> 1 OR v_payment_count <> 0
           OR v_movement_total <> -v_amount THEN
            RAISE EXCEPTION 'Capital Outflow source or movement does not reconcile'
                USING ERRCODE = '23514';
        END IF;
        SELECT tenant_id, branch_id, amount, actor_id
          INTO v_source_tenant, v_source_branch, v_source_amount, v_source_actor
        FROM investment_investorprincipalreturn
        WHERE id = (SELECT investor_principal_return_id FROM accounting_accountingsourcelink WHERE event_id = v_event_id);
    ELSE
        IF v_credit_count <> 0 OR v_return_count <> 0 OR v_payment_count <> 1
           OR v_movement_total <> -v_amount THEN
            RAISE EXCEPTION 'Vehicle Payment source or movement does not reconcile'
                USING ERRCODE = '23514';
        END IF;
        SELECT p.tenant_id, p.branch_id, p.amount, p.actor_id, p.account_id
          INTO v_source_tenant, v_source_branch, v_source_amount, v_source_actor, v_source_account
        FROM vehicles_vehiclepurchasepayment p
        WHERE p.id = (SELECT vehicle_purchase_payment_id FROM accounting_accountingsourcelink WHERE event_id = v_event_id);
        IF NOT EXISTS (
            SELECT 1 FROM accounting_accountmovement
            WHERE event_id = v_event_id AND account_id = v_source_account AND delta = -v_amount
        ) THEN
            RAISE EXCEPTION 'Vehicle Payment must use the selected Cash/Bank account'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF v_source_tenant IS DISTINCT FROM v_tenant
       OR v_source_branch IS DISTINCT FROM v_branch
       OR v_source_amount IS DISTINCT FROM v_amount
       OR v_source_actor IS DISTINCT FROM v_actor THEN
        RAISE EXCEPTION 'Source and Accounting event do not reconcile'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER accounting_source_event_shape_v2
AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
CREATE CONSTRAINT TRIGGER accounting_source_movement_shape_v2
AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
CREATE CONSTRAINT TRIGGER accounting_source_link_shape_v2
AFTER INSERT ON accounting_accountingsourcelink DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
CREATE CONSTRAINT TRIGGER accounting_fund_credit_source_shape_v2
AFTER INSERT ON investment_investorfundcredit DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
CREATE CONSTRAINT TRIGGER accounting_principal_return_source_shape_v2
AFTER INSERT ON investment_investorprincipalreturn DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
CREATE CONSTRAINT TRIGGER accounting_vehicle_payment_source_shape_v2
AFTER INSERT ON vehicles_vehiclepurchasepayment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_source_shape_v2();
"""


REVERSE_SQL = r"""
DROP TRIGGER accounting_vehicle_payment_source_shape_v2 ON vehicles_vehiclepurchasepayment;
DROP TRIGGER accounting_principal_return_source_shape_v2 ON investment_investorprincipalreturn;
DROP TRIGGER accounting_fund_credit_source_shape_v2 ON investment_investorfundcredit;
DROP TRIGGER accounting_source_link_shape_v2 ON accounting_accountingsourcelink;
DROP TRIGGER accounting_source_movement_shape_v2 ON accounting_accountmovement;
DROP TRIGGER accounting_source_event_shape_v2 ON accounting_accountingevent;
DROP FUNCTION accounting_assert_source_shape_v2();
DROP TRIGGER accounting_source_insert_guard_v2 ON accounting_accountingsourcelink;
DROP FUNCTION accounting_source_insert_guard_v2();

CREATE TRIGGER accounting_capital_source_insert_guard
BEFORE INSERT ON accounting_accountingsourcelink
FOR EACH ROW EXECUTE FUNCTION accounting_capital_source_guard();
CREATE CONSTRAINT TRIGGER accounting_capital_event_shape_deferred
AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_capital_shape();
CREATE CONSTRAINT TRIGGER accounting_capital_movement_shape_deferred
AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_capital_shape();
CREATE CONSTRAINT TRIGGER accounting_capital_source_shape_deferred
AFTER INSERT ON accounting_accountingsourcelink DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_capital_shape();
CREATE CONSTRAINT TRIGGER accounting_fund_credit_source_shape_deferred
AFTER INSERT ON investment_investorfundcredit DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_capital_shape();
CREATE CONSTRAINT TRIGGER accounting_principal_return_source_shape_deferred
AFTER INSERT ON investment_investorprincipalreturn DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION accounting_assert_capital_shape();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0007_accountingsourcelink_vehicle_purchase_payment_and_more"),
        ("vehicles", "0002_vehiclepurchase_vehiclepurchasepayment_and_more"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
