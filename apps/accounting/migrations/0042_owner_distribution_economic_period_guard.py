from django.db import migrations


GUARD = r"""
CREATE OR REPLACE FUNCTION accounting_owner_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE c_company uuid; c_amount numeric; c_start date; c_end date; c_snapshot jsonb;
        e_company uuid; e_branch uuid; e_actor uuid; e_type text; e_amount numeric; e_effect integer;
        e_category uuid; e_revision uuid; e_source text; acct_company uuid; acct_active boolean;
        branch_company uuid; allocated numeric; paid numeric; movement_count bigint;
BEGIN
 PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
 SELECT tenant_id,distributable_amount,period_start,period_end,owner_allocation_snapshot
   INTO c_company,c_amount,c_start,c_end,c_snapshot
   FROM accounting_companyperiodconfirmation WHERE id=NEW.confirmation_id;
 SELECT tenant_id,branch_id,actor_id,event_type,amount,effect_sign,category_id,module_revision_id,source_reference
   INTO e_company,e_branch,e_actor,e_type,e_amount,e_effect,e_category,e_revision,e_source
   FROM accounting_accountingevent WHERE id=NEW.accounting_event_id;
 SELECT tenant_id,is_active INTO acct_company,acct_active FROM accounting_accountingaccount WHERE id=NEW.account_id;
 SELECT tenant_id INTO branch_company FROM tenants_branch WHERE id=NEW.branch_id;
 SELECT COUNT(*) INTO movement_count FROM accounting_accountmovement WHERE event_id=NEW.accounting_event_id;
 SELECT COALESCE((SELECT (x->>'amount')::numeric FROM jsonb_array_elements(c_snapshot) x WHERE x->>'recipient_id'=NEW.recipient_id::text),0) INTO allocated;
 SELECT COALESCE(SUM(p.amount),0) INTO paid
   FROM accounting_ownerdistributionpayment p
   JOIN accounting_companyperiodconfirmation old ON old.id=p.confirmation_id
   WHERE p.tenant_id=NEW.tenant_id AND old.period_start=c_start AND old.period_end=c_end AND p.recipient_id=NEW.recipient_id;
 IF c_company IS DISTINCT FROM NEW.tenant_id OR e_company IS DISTINCT FROM NEW.tenant_id OR e_branch IS DISTINCT FROM NEW.branch_id
    OR e_actor IS DISTINCT FROM NEW.actor_id OR e_type IS DISTINCT FROM 'OWNER_DISTRIBUTION_PAYMENT' OR e_amount IS DISTINCT FROM NEW.amount
    OR e_effect IS DISTINCT FROM 1 OR e_category IS NOT NULL OR e_revision IS DISTINCT FROM NEW.accounting_revision_id
    OR e_source IS DISTINCT FROM ('OWNER-DISTRIBUTION-'||NEW.id::text) OR acct_company IS DISTINCT FROM NEW.tenant_id
    OR acct_active IS DISTINCT FROM TRUE OR branch_company IS DISTINCT FROM NEW.tenant_id OR NEW.amount<=0 OR NEW.reason=''
    OR NEW.effective_at>clock_timestamp() OR movement_count<>1 THEN
    RAISE EXCEPTION 'Owner distribution payment and Accounting source scope do not match' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS (SELECT 1 FROM tenants_companymodulestate r WHERE r.id=NEW.accounting_revision_id AND r.tenant_id=NEW.tenant_id AND r.module_code='accounting' AND r.state='enabled') THEN
    RAISE EXCEPTION 'Owner payment requires Accounting ON' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS (SELECT 1 FROM tenants_tenantmembership m JOIN accounts_companyrolegrant g ON g.membership_id=m.id
    WHERE m.tenant_id=NEW.tenant_id AND m.user_id=NEW.actor_id AND m.effective_from<=clock_timestamp()
      AND (m.effective_until IS NULL OR m.effective_until>clock_timestamp()) AND g.role='accountant'
      AND (g.branch_id IS NULL OR g.branch_id=NEW.branch_id) AND g.effective_from<=clock_timestamp()
      AND (g.effective_until IS NULL OR g.effective_until>clock_timestamp())) THEN
    RAISE EXCEPTION 'Owner distribution payment requires an authorized Company or Branch Accountant' USING ERRCODE='23514';
 END IF;
 IF allocated<=0 OR paid>allocated OR NEW.amount>allocated-paid THEN RAISE EXCEPTION 'Owner payment exceeds the remaining confirmed allocation' USING ERRCODE='23514'; END IF;
 IF NOT EXISTS (SELECT 1 FROM accounting_accountmovement m WHERE m.event_id=NEW.accounting_event_id AND m.tenant_id=NEW.tenant_id AND m.account_id=NEW.account_id AND m.delta=-NEW.amount) THEN
    RAISE EXCEPTION 'Owner distribution payment requires the exact Cash/Bank outflow' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END; $$;
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0041_owner_distribution_event_guards")]
    operations = [migrations.RunSQL(GUARD, reverse_sql=migrations.RunSQL.noop)]
