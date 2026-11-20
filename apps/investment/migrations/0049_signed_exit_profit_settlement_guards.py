from django.db import migrations


GUARD = r"""
CREATE OR REPLACE FUNCTION investor_exit_profit_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; position_company uuid; position_investor uuid;
        v_period_start date; v_period_end date; v_amount_due numeric;
        v_profit_paid numeric; v_recovery_received numeric; v_future_applied numeric;
        v_principal_available numeric; v_loss_due numeric;
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
                  WHERE n.tenant_id=NEW.tenant_id AND n.investor_id=position_investor AND n.period_start=v_period_start AND n.period_end=v_period_end AND n.version>c.version) THEN
        RAISE EXCEPTION 'Exit Profit payment requires current same-Company sources' USING ERRCODE='23514';
    END IF;
    IF v_amount_due IS NULL OR v_amount_due<=0 THEN
        RAISE EXCEPTION 'Exit Profit payment requires a current payable position' USING ERRCODE='23514';
    END IF;
    IF EXISTS (
        SELECT 1 FROM investment_investorfundcredit c
        WHERE c.tenant_id=NEW.tenant_id
          AND COALESCE((SELECT x.to_investor_id FROM investment_investorfundcreditcorrection x
                        WHERE x.credit_id=c.id ORDER BY x.version DESC,x.id DESC LIMIT 1), c.investor_id)=position_investor
          AND investment_credit_available(c.id) IS NULL
    ) THEN
        RAISE EXCEPTION 'Exit Profit payment requires Fund source review' USING ERRCODE='23514';
    END IF;
    SELECT COALESCE(SUM(investment_credit_available(c.id)),0) INTO v_principal_available
      FROM investment_investorfundcredit c
      WHERE c.tenant_id=NEW.tenant_id
        AND COALESCE((SELECT x.to_investor_id FROM investment_investorfundcreditcorrection x
                      WHERE x.credit_id=c.id ORDER BY x.version DESC,x.id DESC LIMIT 1), c.investor_id)=position_investor;
    SELECT COALESCE(SUM(GREATEST(ABS(v.investor_share_amount)
        - COALESCE((SELECT SUM(o.amount) FROM investment_investorprofitlossoffset o WHERE o.tenant_id=NEW.tenant_id AND o.loss_result_id=v.id),0)
        - COALESCE((SELECT SUM(a.amount) FROM investment_investorexitlossapplication a
                    WHERE a.tenant_id=NEW.tenant_id AND a.exit_request_id=NEW.exit_request_id
                      AND a.loss_result_id=v.id),0),0)),0)
      INTO v_loss_due
      FROM investment_vehicleresultconfirmation v
      WHERE v.tenant_id=NEW.tenant_id AND v.investor_id=position_investor AND v.result_kind='LOSS'
        AND NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation newer
                        WHERE newer.tenant_id=v.tenant_id AND newer.sale_id=v.sale_id AND newer.version>v.version);
    IF v_principal_available>0 OR v_loss_due>0 THEN
        RAISE EXCEPTION 'Exit Profit payment requires Principal and confirmed Loss settlement first' USING ERRCODE='23514';
    END IF;
    SELECT COALESCE(SUM(x.amount),0) INTO v_recovery_received FROM investment_investorprofitrecoveryreceipt x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO v_future_applied FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.profit_position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO v_profit_paid FROM investment_investorexitprofitpayment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    IF NEW.amount>GREATEST(v_amount_due-v_profit_paid-v_future_applied,0) THEN
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
    dependencies = [("investment", "0048_investorexitsettlementclosure_and_more")]
    operations = [migrations.RunSQL(GUARD, reverse_sql=migrations.RunSQL.noop)]
