from django.db import migrations


GUARD = r"""
CREATE OR REPLACE FUNCTION investor_exit_profit_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; position_company uuid; position_investor uuid;
        v_period_start date; v_period_end date; v_amount_due numeric; v_repaid numeric; v_future_recovered numeric; v_future_applied numeric;
BEGIN
    PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
    SELECT e.tenant_id,e.investor_id INTO exit_company,exit_investor
      FROM investment_investorexitrequest e WHERE e.id=NEW.exit_request_id AND e.status='REQUESTED';
    SELECT r.tenant_id,r.investor_id,r.period_start,r.period_end,r.net_position
      INTO position_company,position_investor,v_period_start,v_period_end,v_amount_due
      FROM investment_investorprofitperiodposition p
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE p.id=NEW.position_id;
    IF exit_company IS DISTINCT FROM NEW.tenant_id OR position_company IS DISTINCT FROM NEW.tenant_id
       OR exit_investor IS DISTINCT FROM position_investor OR NEW.effective_at>clock_timestamp() OR btrim(NEW.reason)=''
       OR NOT EXISTS (SELECT 1 FROM tenants_branch WHERE id=NEW.branch_id AND tenant_id=NEW.tenant_id)
       OR NOT EXISTS (SELECT 1 FROM accounting_accountingaccount WHERE id=NEW.account_id AND tenant_id=NEW.tenant_id AND is_active)
       OR EXISTS (SELECT 1 FROM investment_investorprofitperiodreconciliation n JOIN investment_investorprofitperiodreconciliation c
                  ON c.id=(SELECT reconciliation_id FROM investment_investorprofitperiodposition WHERE id=NEW.position_id)
                  WHERE n.tenant_id=NEW.tenant_id AND n.investor_id=position_investor AND n.period_start=v_period_start AND n.version>c.version) THEN
        RAISE EXCEPTION 'Exit Profit payment requires current same-Company sources' USING ERRCODE='23514';
    END IF;
    SELECT COALESCE(SUM(x.amount),0) INTO v_repaid FROM investment_investorprofitrecoveryreceipt x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO v_future_recovered FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.recoverable_position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO v_future_applied FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.profit_position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    v_repaid := v_repaid + COALESCE((SELECT SUM(x.amount) FROM investment_investorexitprofitpayment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end),0);
    IF NEW.amount>GREATEST(v_amount_due-v_repaid-v_future_recovered+v_future_applied,0) THEN
        RAISE EXCEPTION 'Exit Profit payment exceeds current confirmed payable' USING ERRCODE='23514';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM tenants_companymodulestate m WHERE m.id=NEW.accounting_revision_id
       AND m.tenant_id=NEW.tenant_id AND m.module_code='accounting' AND m.state='enabled') THEN
        RAISE EXCEPTION 'Exit Profit payment requires Accounting enabled' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0045_exit_profit_payment_guards")]
    operations = [migrations.RunSQL(GUARD, reverse_sql=migrations.RunSQL.noop)]
