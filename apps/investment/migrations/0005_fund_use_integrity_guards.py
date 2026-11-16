from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION investor_fund_use_insert_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    i_company uuid;
    p_company uuid;
    p_branch uuid;
    p_investor uuid;
    p_fund_amount numeric;
    p_revision_company uuid;
    p_revision_module text;
    p_revision_state text;
BEGIN
    SELECT tenant_id, module_code, state
      INTO p_revision_company, p_revision_module, p_revision_state
    FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
    IF p_revision_company IS DISTINCT FROM NEW.tenant_id
       OR p_revision_module IS DISTINCT FROM 'investment'
       OR p_revision_state IS DISTINCT FROM 'enabled' THEN
        RAISE EXCEPTION 'Investor Fund use requires an enabled same-Company Investment revision'
            USING ERRCODE = '23514';
    END IF;

    IF NEW.purchase_id IS NOT NULL THEN
        SELECT tenant_id, branch_id, investor_id, investor_fund_amount
          INTO p_company, p_branch, p_investor, p_fund_amount
        FROM vehicles_vehiclepurchase WHERE id = NEW.purchase_id;
        IF p_fund_amount IS DISTINCT FROM NEW.amount
           OR p_investor IS DISTINCT FROM NEW.investor_id THEN
            RAISE EXCEPTION 'Investor Fund use must exactly match the Purchase allocation'
                USING ERRCODE = '23514';
        END IF;
    ELSE
        SELECT tenant_id, branch_id, investor_id, investor_fund_amount
          INTO p_company, p_branch, p_investor, p_fund_amount
        FROM vehicles_vehicleexpense WHERE id = NEW.expense_id;
        IF p_fund_amount IS DISTINCT FROM NEW.amount
           OR p_investor IS DISTINCT FROM NEW.investor_id THEN
            RAISE EXCEPTION 'Investor Fund use must exactly match the Vehicle Expense allocation'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    SELECT tenant_id INTO i_company FROM investment_investor WHERE id = NEW.investor_id;
    IF p_company IS DISTINCT FROM NEW.tenant_id
       OR p_branch IS DISTINCT FROM NEW.branch_id
       OR p_investor IS DISTINCT FROM NEW.investor_id
       OR i_company IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION 'Investor Fund use source, Investor, Branch and Company must match'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER investor_fund_use_insert_guard
BEFORE INSERT ON investment_investorfunduse
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_insert_guard();

CREATE FUNCTION investor_fund_use_allocation_insert_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    u_company uuid;
    u_investor uuid;
    c_company uuid;
    c_investor uuid;
BEGIN
    SELECT tenant_id, investor_id INTO u_company, u_investor
    FROM investment_investorfunduse WHERE id = NEW.fund_use_id;
    SELECT tenant_id, investor_id INTO c_company, c_investor
    FROM investment_investorfundcredit WHERE id = NEW.credit_id;
    IF u_company IS DISTINCT FROM NEW.tenant_id
       OR c_company IS DISTINCT FROM NEW.tenant_id
       OR u_investor IS DISTINCT FROM c_investor THEN
        RAISE EXCEPTION 'Fund-use allocation must link same-Company, same-Investor records'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER investor_fund_use_allocation_insert_guard
BEFORE INSERT ON investment_investorfunduseallocation
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_allocation_insert_guard();

CREATE FUNCTION investor_fund_use_reject_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor Fund use history is append only'
        USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER investor_fund_use_immutable
BEFORE UPDATE OR DELETE ON investment_investorfunduse
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_reject_mutation();
CREATE TRIGGER investor_fund_use_allocation_immutable
BEFORE UPDATE OR DELETE ON investment_investorfunduseallocation
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_reject_mutation();

CREATE FUNCTION investor_fund_use_assert_complete()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    use_id uuid;
    expected_amount numeric;
    allocation_count bigint;
    allocation_total numeric;
    v_company_id uuid;
    v_actor_id uuid;
    v_branch_id uuid;
    purchase_id uuid;
    expense_id uuid;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorfunduse' THEN
        use_id := NEW.id;
    ELSE
        use_id := NEW.fund_use_id;
    END IF;
    SELECT u.tenant_id, u.amount, u.actor_id, u.branch_id, u.purchase_id, u.expense_id
      INTO v_company_id, expected_amount, v_actor_id, v_branch_id, purchase_id, expense_id
    FROM investment_investorfunduse u WHERE u.id = use_id;
    SELECT COUNT(*), COALESCE(SUM(amount), 0)
      INTO allocation_count, allocation_total
    FROM investment_investorfunduseallocation
    WHERE fund_use_id = use_id AND tenant_id = v_company_id;
    IF allocation_count = 0 OR allocation_total IS DISTINCT FROM expected_amount THEN
        RAISE EXCEPTION 'Investor Fund use must be fully allocated to its source credits'
            USING ERRCODE = '23514';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent e
        WHERE e.action = CASE WHEN purchase_id IS NOT NULL
                              THEN 'vehicle.purchase.create'
                              ELSE 'vehicle.expense.create' END
          AND e.company_id = v_company_id
          AND e.branch_id = v_branch_id
          AND e.resource_id = COALESCE(purchase_id, expense_id)
          AND e.actor_id = v_actor_id
    ) THEN
        RAISE EXCEPTION 'Investor Fund use requires a matching Vehicle source audit event'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER investor_fund_use_complete_deferred
AFTER INSERT ON investment_investorfunduse DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_assert_complete();
CREATE CONSTRAINT TRIGGER investor_fund_use_allocation_complete_deferred
AFTER INSERT ON investment_investorfunduseallocation DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investor_fund_use_assert_complete();
"""


REVERSE_SQL = r"""
DROP TRIGGER investor_fund_use_allocation_complete_deferred ON investment_investorfunduseallocation;
DROP TRIGGER investor_fund_use_complete_deferred ON investment_investorfunduse;
DROP FUNCTION investor_fund_use_assert_complete();
DROP TRIGGER investor_fund_use_allocation_immutable ON investment_investorfunduseallocation;
DROP TRIGGER investor_fund_use_immutable ON investment_investorfunduse;
DROP FUNCTION investor_fund_use_reject_mutation();
DROP TRIGGER investor_fund_use_allocation_insert_guard ON investment_investorfunduseallocation;
DROP FUNCTION investor_fund_use_allocation_insert_guard();
DROP TRIGGER investor_fund_use_insert_guard ON investment_investorfunduse;
DROP FUNCTION investor_fund_use_insert_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0004_investorfunduse_expense_investorfunduse_investor_and_more"),
        ("accounts", "0012_scope_end_monotonic"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
