from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_investment_data(apps, schema_editor):
    for model_name in (
        "Investor",
        "InvestorInterimConfiguration",
        "InvestorFundCredit",
        "InvestorPrincipalReturn",
        "InvestorPrincipalReturnAllocation",
        "InvestmentIdempotencyRecord",
    ):
        model = apps.get_model("investment", model_name)
        if model.objects.using(schema_editor.connection.alias).exists():
            raise IrreversibleError(
                "Investment history exists; roll back application code without reversing Phase 5 migrations."
            )


FORWARD_SQL = r"""
CREATE FUNCTION investment_reject_history_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investment financial/configuration history is append only'
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER investor_interim_immutable
BEFORE UPDATE OR DELETE ON investment_investorinterimconfiguration
FOR EACH ROW EXECUTE FUNCTION investment_reject_history_mutation();
CREATE TRIGGER investor_credit_immutable
BEFORE UPDATE OR DELETE ON investment_investorfundcredit
FOR EACH ROW EXECUTE FUNCTION investment_reject_history_mutation();
CREATE TRIGGER investor_return_immutable
BEFORE UPDATE OR DELETE ON investment_investorprincipalreturn
FOR EACH ROW EXECUTE FUNCTION investment_reject_history_mutation();
CREATE TRIGGER investor_return_allocation_immutable
BEFORE UPDATE OR DELETE ON investment_investorprincipalreturnallocation
FOR EACH ROW EXECUTE FUNCTION investment_reject_history_mutation();
CREATE TRIGGER investment_idempotency_immutable
BEFORE UPDATE OR DELETE ON investment_investmentidempotencyrecord
FOR EACH ROW EXECUTE FUNCTION investment_reject_history_mutation();

CREATE FUNCTION investment_scope_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    investor_company uuid;
    branch_company uuid;
    revision_company uuid;
    revision_module text;
    return_company uuid;
    return_investor uuid;
    return_branch uuid;
    credit_company uuid;
    credit_investor uuid;
    credit_branch uuid;
BEGIN
    IF TG_TABLE_NAME = 'investment_investor' THEN
        IF TG_OP = 'UPDATE' AND (
            NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
            OR NEW.created_by_id IS DISTINCT FROM OLD.created_by_id
            OR NEW.is_active IS DISTINCT FROM OLD.is_active
        ) THEN
            RAISE EXCEPTION 'Investor Company, creator and active status are immutable in this phase'
                USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    ELSIF TG_TABLE_NAME = 'investment_investorinterimconfiguration' THEN
        SELECT tenant_id INTO investor_company FROM investment_investor WHERE id = NEW.investor_id;
        SELECT tenant_id, module_code INTO revision_company, revision_module
        FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
        IF investor_company IS DISTINCT FROM NEW.tenant_id
           OR revision_company IS DISTINCT FROM NEW.tenant_id
           OR revision_module IS DISTINCT FROM 'investment' THEN
            RAISE EXCEPTION 'Interim configuration Company or module revision is invalid'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'investment_investorfundcredit' THEN
        SELECT tenant_id INTO investor_company FROM investment_investor WHERE id = NEW.investor_id;
        SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id = NEW.branch_id;
        SELECT tenant_id, module_code INTO revision_company, revision_module
        FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
        IF investor_company IS DISTINCT FROM NEW.tenant_id
           OR branch_company IS DISTINCT FROM NEW.tenant_id
           OR revision_company IS DISTINCT FROM NEW.tenant_id
           OR revision_module IS DISTINCT FROM 'investment' THEN
            RAISE EXCEPTION 'Fund credit Company, Branch or module revision is invalid'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'investment_investorprincipalreturn' THEN
        SELECT tenant_id INTO investor_company FROM investment_investor WHERE id = NEW.investor_id;
        SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id = NEW.branch_id;
        SELECT tenant_id, module_code INTO revision_company, revision_module
        FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
        IF investor_company IS DISTINCT FROM NEW.tenant_id
           OR branch_company IS DISTINCT FROM NEW.tenant_id
           OR revision_company IS DISTINCT FROM NEW.tenant_id
           OR revision_module IS DISTINCT FROM 'investment' THEN
            RAISE EXCEPTION 'Principal return Company, Branch or module revision is invalid'
                USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'investment_investorprincipalreturnallocation' THEN
        PERFORM id FROM investment_investorfundcredit WHERE id = NEW.credit_id FOR UPDATE;
        SELECT tenant_id, investor_id, branch_id
          INTO return_company, return_investor, return_branch
        FROM investment_investorprincipalreturn WHERE id = NEW.principal_return_id;
        SELECT tenant_id, investor_id, branch_id
          INTO credit_company, credit_investor, credit_branch
        FROM investment_investorfundcredit WHERE id = NEW.credit_id;
        IF return_company IS DISTINCT FROM NEW.tenant_id
           OR credit_company IS DISTINCT FROM NEW.tenant_id
           OR return_investor IS DISTINCT FROM credit_investor
           OR return_branch IS DISTINCT FROM credit_branch THEN
            RAISE EXCEPTION 'Return allocation must use its Investor and source Branch credit'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER investor_scope_insert_update_guard
BEFORE INSERT OR UPDATE ON investment_investor
FOR EACH ROW EXECUTE FUNCTION investment_scope_guard();
CREATE TRIGGER interim_scope_insert_guard
BEFORE INSERT ON investment_investorinterimconfiguration
FOR EACH ROW EXECUTE FUNCTION investment_scope_guard();
CREATE TRIGGER fund_credit_scope_insert_guard
BEFORE INSERT ON investment_investorfundcredit
FOR EACH ROW EXECUTE FUNCTION investment_scope_guard();
CREATE TRIGGER principal_return_scope_insert_guard
BEFORE INSERT ON investment_investorprincipalreturn
FOR EACH ROW EXECUTE FUNCTION investment_scope_guard();
CREATE TRIGGER return_allocation_scope_insert_guard
BEFORE INSERT ON investment_investorprincipalreturnallocation
FOR EACH ROW EXECUTE FUNCTION investment_scope_guard();

CREATE FUNCTION investment_require_audit()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    ok boolean;
BEGIN
    IF TG_TABLE_NAME = 'investment_investor' AND TG_OP = 'INSERT' THEN
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'investor.profile.create'
              AND e.company_id = NEW.tenant_id
              AND e.resource_id = NEW.id
              AND e.actor_id = NEW.created_by_id
              AND e.metadata->>'investor_id' = NEW.id::text
              AND e.metadata->>'new_name' = NEW.name
        ) INTO ok;
    ELSIF TG_TABLE_NAME = 'investment_investor' THEN
        IF TG_OP = 'UPDATE' AND OLD.name IS DISTINCT FROM NEW.name THEN
            SELECT EXISTS (
                SELECT 1 FROM accounts_accountsecurityevent e
                WHERE e.action = 'investor.profile.update'
                  AND e.company_id = NEW.tenant_id
                  AND e.resource_id = NEW.id
                  AND e.actor_id = NEW.updated_by_id
                  AND e.metadata->>'investor_id' = NEW.id::text
                  AND e.metadata->>'old_name' = OLD.name
                  AND e.metadata->>'new_name' = NEW.name
            ) INTO ok;
        ELSE
            RETURN NULL;
        END IF;
    ELSIF TG_TABLE_NAME = 'investment_investorinterimconfiguration' THEN
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'investor.interim.configure'
              AND e.company_id = NEW.tenant_id
              AND e.resource_id = NEW.id
              AND e.actor_id = NEW.actor_id
              AND e.metadata->>'investor_id' = NEW.investor_id::text
              AND e.metadata->>'amount' = NEW.amount::text
        ) INTO ok;
    ELSIF TG_TABLE_NAME = 'investment_investorfundcredit' THEN
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'investment.fund.credit'
              AND e.company_id = NEW.tenant_id
              AND e.branch_id = NEW.branch_id
              AND e.resource_id = NEW.id
              AND e.actor_id = NEW.actor_id
              AND e.metadata->>'investor_id' = NEW.investor_id::text
              AND e.metadata->>'amount' = NEW.amount::text
        ) INTO ok;
    ELSIF TG_TABLE_NAME = 'investment_investorprincipalreturn' THEN
        SELECT EXISTS (
            SELECT 1 FROM accounts_accountsecurityevent e
            WHERE e.action = 'investment.fund.principal_return'
              AND e.company_id = NEW.tenant_id
              AND e.branch_id = NEW.branch_id
              AND e.resource_id = NEW.id
              AND e.actor_id = NEW.actor_id
              AND e.metadata->>'investor_id' = NEW.investor_id::text
              AND e.metadata->>'amount' = NEW.amount::text
        ) INTO ok;
    ELSE
        RETURN NULL;
    END IF;
    IF NOT COALESCE(ok, FALSE) THEN
        RAISE EXCEPTION 'Investor/configuration/capital mutation requires matching immutable audit evidence'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER investor_create_audit_deferred
AFTER INSERT ON investment_investor DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_require_audit();
CREATE CONSTRAINT TRIGGER investor_update_audit_deferred
AFTER UPDATE ON investment_investor DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_require_audit();
CREATE CONSTRAINT TRIGGER interim_audit_deferred
AFTER INSERT ON investment_investorinterimconfiguration DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_require_audit();
CREATE CONSTRAINT TRIGGER fund_credit_audit_deferred
AFTER INSERT ON investment_investorfundcredit DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_require_audit();
CREATE CONSTRAINT TRIGGER principal_return_audit_deferred
AFTER INSERT ON investment_investorprincipalreturn DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_require_audit();

CREATE FUNCTION investment_assert_return_shape()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_return_id uuid;
    v_return_amount numeric;
    v_allocation_total numeric;
    v_allocation_count bigint;
    v_credit_id uuid;
    v_credit_amount numeric;
    v_credited numeric;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorprincipalreturn' THEN
        v_return_id := NEW.id;
    ELSE
        v_return_id := NEW.principal_return_id;
    END IF;
    SELECT amount INTO v_return_amount
    FROM investment_investorprincipalreturn WHERE id = v_return_id;
    SELECT COALESCE(SUM(amount), 0), COUNT(*)
      INTO v_allocation_total, v_allocation_count
    FROM investment_investorprincipalreturnallocation
    WHERE principal_return_id = v_return_id;
    IF v_allocation_count = 0 OR v_allocation_total <> v_return_amount THEN
        RAISE EXCEPTION 'Principal return must be fully allocated to source Fund credits'
            USING ERRCODE = '23514';
    END IF;
    FOR v_credit_id IN
        SELECT DISTINCT allocation.credit_id
        FROM investment_investorprincipalreturnallocation allocation
        WHERE allocation.principal_return_id = v_return_id
        ORDER BY allocation.credit_id
    LOOP
        PERFORM credit.id FROM investment_investorfundcredit credit
        WHERE credit.id = v_credit_id FOR UPDATE;
        SELECT credit.amount INTO v_credit_amount
        FROM investment_investorfundcredit credit WHERE credit.id = v_credit_id;
        SELECT COALESCE(SUM(allocation.amount), 0) INTO v_credited
        FROM investment_investorprincipalreturnallocation allocation
        WHERE allocation.credit_id = v_credit_id;
        IF v_credited > v_credit_amount THEN
            RAISE EXCEPTION 'Principal returns cannot exceed their source Fund credit'
                USING ERRCODE = '23514';
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER investor_return_shape_deferred
AFTER INSERT ON investment_investorprincipalreturn DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_assert_return_shape();
CREATE CONSTRAINT TRIGGER investor_return_allocation_shape_deferred
AFTER INSERT ON investment_investorprincipalreturnallocation DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION investment_assert_return_shape();

CREATE FUNCTION investment_reject_investor_delete()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Investor identity cannot be deleted'
        USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER investor_no_delete BEFORE DELETE ON investment_investor
FOR EACH ROW EXECUTE FUNCTION investment_reject_investor_delete();
"""

REVERSE_SQL = r"""
DROP TRIGGER investor_no_delete ON investment_investor;
DROP FUNCTION investment_reject_investor_delete();
DROP TRIGGER investor_return_allocation_shape_deferred ON investment_investorprincipalreturnallocation;
DROP TRIGGER investor_return_shape_deferred ON investment_investorprincipalreturn;
DROP FUNCTION investment_assert_return_shape();
DROP TRIGGER principal_return_audit_deferred ON investment_investorprincipalreturn;
DROP TRIGGER fund_credit_audit_deferred ON investment_investorfundcredit;
DROP TRIGGER interim_audit_deferred ON investment_investorinterimconfiguration;
DROP TRIGGER investor_update_audit_deferred ON investment_investor;
DROP TRIGGER investor_create_audit_deferred ON investment_investor;
DROP FUNCTION investment_require_audit();
DROP TRIGGER return_allocation_scope_insert_guard ON investment_investorprincipalreturnallocation;
DROP TRIGGER principal_return_scope_insert_guard ON investment_investorprincipalreturn;
DROP TRIGGER fund_credit_scope_insert_guard ON investment_investorfundcredit;
DROP TRIGGER interim_scope_insert_guard ON investment_investorinterimconfiguration;
DROP TRIGGER investor_scope_insert_update_guard ON investment_investor;
DROP FUNCTION investment_scope_guard();
DROP TRIGGER investment_idempotency_immutable ON investment_investmentidempotencyrecord;
DROP TRIGGER investor_return_allocation_immutable ON investment_investorprincipalreturnallocation;
DROP TRIGGER investor_return_immutable ON investment_investorprincipalreturn;
DROP TRIGGER investor_credit_immutable ON investment_investorfundcredit;
DROP TRIGGER investor_interim_immutable ON investment_investorinterimconfiguration;
DROP FUNCTION investment_reject_history_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0001_initial")]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=refuse_reverse_with_investment_data,
        ),
    ]
