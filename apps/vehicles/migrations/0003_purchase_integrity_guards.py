from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION vehicle_purchase_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_company uuid;
    v_branch uuid;
    b_company uuid;
    v_revision_company uuid;
    v_revision_module text;
    v_revision_state text;
    i_company uuid;
    i_revision_company uuid;
    i_revision_module text;
    i_revision_state text;
BEGIN
    SELECT tenant_id, current_branch_id INTO v_company, v_branch
    FROM vehicles_vehicle WHERE id = NEW.vehicle_id;
    SELECT tenant_id INTO b_company FROM tenants_branch WHERE id = NEW.branch_id;
    SELECT tenant_id, module_code, state
      INTO v_revision_company, v_revision_module, v_revision_state
    FROM tenants_companymodulestate WHERE id = NEW.vehicle_module_revision_id;
    IF v_company IS DISTINCT FROM NEW.tenant_id
       OR v_branch IS DISTINCT FROM NEW.branch_id
       OR b_company IS DISTINCT FROM NEW.tenant_id
       OR v_revision_company IS DISTINCT FROM NEW.tenant_id
       OR v_revision_module IS DISTINCT FROM 'vehicle_management'
       OR v_revision_state IS DISTINCT FROM 'enabled'
       OR NEW.purchased_at > clock_timestamp() THEN
        RAISE EXCEPTION 'Vehicle Purchase scope invalid: vehicle company %, vehicle branch %, purchase branch %, branch company %, revision company %, revision module %, revision state %, purchase date %', v_company, v_branch, NEW.branch_id, b_company, v_revision_company, v_revision_module, v_revision_state, NEW.purchased_at
            USING ERRCODE = '23514';
    END IF;
    IF NEW.investor_fund_amount > 0 THEN
        SELECT tenant_id INTO i_company FROM investment_investor WHERE id = NEW.investor_id;
        SELECT tenant_id, module_code, state
          INTO i_revision_company, i_revision_module, i_revision_state
        FROM tenants_companymodulestate WHERE id = NEW.investment_module_revision_id;
        IF i_company IS DISTINCT FROM NEW.tenant_id
           OR i_revision_company IS DISTINCT FROM NEW.tenant_id
           OR i_revision_module IS DISTINCT FROM 'investment'
           OR i_revision_state IS DISTINCT FROM 'enabled' THEN
            RAISE EXCEPTION 'Vehicle Purchase Investor or Investment revision is invalid'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER vehicle_purchase_insert_guard
BEFORE INSERT ON vehicles_vehiclepurchase
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_guard();

CREATE FUNCTION vehicle_purchase_payment_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    p_company uuid;
    p_branch uuid;
    a_company uuid;
    a_active boolean;
    r_company uuid;
    r_module text;
    r_state text;
BEGIN
    SELECT tenant_id, branch_id INTO p_company, p_branch
    FROM vehicles_vehiclepurchase WHERE id = NEW.purchase_id;
    SELECT tenant_id, is_active INTO a_company, a_active
    FROM accounting_accountingaccount WHERE id = NEW.account_id;
    SELECT tenant_id, module_code, state INTO r_company, r_module, r_state
    FROM tenants_companymodulestate WHERE id = NEW.accounting_module_revision_id;
    IF p_company IS DISTINCT FROM NEW.tenant_id
       OR p_branch IS DISTINCT FROM NEW.branch_id
       OR a_company IS DISTINCT FROM NEW.tenant_id
       OR a_active IS DISTINCT FROM TRUE
       OR r_company IS DISTINCT FROM NEW.tenant_id
       OR r_module IS DISTINCT FROM 'accounting'
       OR r_state IS DISTINCT FROM 'enabled'
       OR NEW.effective_at > clock_timestamp() THEN
        RAISE EXCEPTION 'Vehicle Purchase payment scope, account, module or date is invalid'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER vehicle_purchase_payment_insert_guard
BEFORE INSERT ON vehicles_vehiclepurchasepayment
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_payment_guard();

CREATE FUNCTION vehicle_purchase_reject_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Vehicle Purchase and payment history are append only'
        USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER vehicle_purchase_immutable
BEFORE UPDATE OR DELETE ON vehicles_vehiclepurchase
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_reject_mutation();
CREATE TRIGGER vehicle_purchase_payment_immutable
BEFORE UPDATE OR DELETE ON vehicles_vehiclepurchasepayment
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_reject_mutation();

CREATE FUNCTION vehicle_purchase_require_audit()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    ok boolean;
BEGIN
    IF TG_TABLE_NAME = 'vehicles_vehiclepurchase' THEN
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'vehicle.purchase.create'
              AND e.company_id = NEW.tenant_id
              AND e.branch_id = NEW.branch_id
              AND e.resource_id = NEW.id
              AND e.actor_id = NEW.actor_id
              AND e.metadata->>'purchase_id' = NEW.id::text
              AND e.metadata->>'vehicle_id' = NEW.vehicle_id::text
              AND e.metadata->>'purchase_cost' = NEW.purchase_cost::text
              AND e.metadata->>'investor_fund_amount' = NEW.investor_fund_amount::text
              AND e.metadata->>'running_capital_amount' = NEW.running_capital_amount::text
        ) INTO ok;
    ELSE
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'vehicle.purchase.payment'
              AND e.company_id = NEW.tenant_id
              AND e.branch_id = NEW.branch_id
              AND e.resource_id = NEW.purchase_id
              AND e.actor_id = NEW.actor_id
              AND e.metadata->>'purchase_id' = NEW.purchase_id::text
              AND e.metadata->>'payment_id' = NEW.id::text
              AND e.metadata->>'amount' = NEW.amount::text
              AND e.metadata ? 'accounting_event_id'
              AND e.metadata->>'account_id' = NEW.account_id::text
        ) INTO ok;
    END IF;
    IF NOT COALESCE(ok, FALSE) THEN
        RAISE EXCEPTION 'Vehicle Purchase financial mutation requires matching audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER vehicle_purchase_audit_deferred
AFTER INSERT ON vehicles_vehiclepurchase DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_require_audit();
CREATE CONSTRAINT TRIGGER vehicle_purchase_payment_audit_deferred
AFTER INSERT ON vehicles_vehiclepurchasepayment DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION vehicle_purchase_require_audit();
"""


REVERSE_SQL = r"""
DROP TRIGGER vehicle_purchase_payment_audit_deferred ON vehicles_vehiclepurchasepayment;
DROP TRIGGER vehicle_purchase_audit_deferred ON vehicles_vehiclepurchase;
DROP FUNCTION vehicle_purchase_require_audit();
DROP TRIGGER vehicle_purchase_payment_immutable ON vehicles_vehiclepurchasepayment;
DROP TRIGGER vehicle_purchase_immutable ON vehicles_vehiclepurchase;
DROP FUNCTION vehicle_purchase_reject_mutation();
DROP TRIGGER vehicle_purchase_payment_insert_guard ON vehicles_vehiclepurchasepayment;
DROP FUNCTION vehicle_purchase_payment_guard();
DROP TRIGGER vehicle_purchase_insert_guard ON vehicles_vehiclepurchase;
DROP FUNCTION vehicle_purchase_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("vehicles", "0002_vehiclepurchase_vehiclepurchasepayment_and_more"),
        ("accounts", "0012_scope_end_monotonic"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
