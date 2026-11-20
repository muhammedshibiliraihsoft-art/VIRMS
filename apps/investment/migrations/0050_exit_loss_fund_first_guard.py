from django.db import migrations


GUARD = r"""
CREATE OR REPLACE FUNCTION investor_exit_loss_application_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; loss_company uuid; loss_investor uuid; loss_version integer;
        loss_amount numeric; used_amount numeric; prior_offsets numeric; module record; fund_available numeric;
BEGIN
    PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
    SELECT tenant_id,investor_id INTO exit_company,exit_investor FROM investment_investorexitrequest
      WHERE id=NEW.exit_request_id AND status='REQUESTED';
    SELECT tenant_id,investor_id,version,abs(investor_share_amount) INTO loss_company,loss_investor,loss_version,loss_amount
      FROM investment_vehicleresultconfirmation WHERE id=NEW.loss_result_id AND result_kind='LOSS';
    IF exit_company IS DISTINCT FROM NEW.tenant_id OR loss_company IS DISTINCT FROM NEW.tenant_id
       OR exit_investor IS DISTINCT FROM loss_investor OR NEW.effective_at>clock_timestamp() OR btrim(NEW.reason)=''
       OR NOT EXISTS (SELECT 1 FROM tenants_branch WHERE id=NEW.branch_id AND tenant_id=NEW.tenant_id)
       OR NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation x WHERE x.id=NEW.loss_result_id
                      AND NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation n WHERE n.tenant_id=x.tenant_id AND n.sale_id=x.sale_id AND n.version>x.version)) THEN
        RAISE EXCEPTION 'Exit Loss application requires current same-Company sources' USING ERRCODE='23514';
    END IF;
    SELECT COALESCE(SUM(x.amount),0) INTO prior_offsets FROM investment_investorprofitlossoffset x
      WHERE x.tenant_id=NEW.tenant_id AND x.loss_result_id=NEW.loss_result_id;
    SELECT COALESCE(SUM(x.amount),0) INTO used_amount FROM investment_investorexitlossapplication x
      WHERE x.tenant_id=NEW.tenant_id AND x.loss_result_id=NEW.loss_result_id;
    IF NEW.amount+used_amount>GREATEST(loss_amount-prior_offsets,0) THEN
        RAISE EXCEPTION 'Exit Loss application exceeds confirmed current Loss' USING ERRCODE='23514';
    END IF;
    FOR module IN SELECT * FROM (VALUES (NEW.accounting_revision_id,'accounting')) AS m(id,code)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM tenants_companymodulestate s WHERE s.id=module.id AND s.tenant_id=NEW.tenant_id
          AND s.module_code=module.code AND s.state='enabled') THEN
            RAISE EXCEPTION 'Exit Loss application requires Accounting enabled' USING ERRCODE='23514';
        END IF;
    END LOOP;
    IF NEW.source='DIRECT_RECEIPT' THEN
        IF NOT EXISTS (SELECT 1 FROM accounting_accountingaccount
                       WHERE id=NEW.account_id AND tenant_id=NEW.tenant_id AND is_active) THEN
            RAISE EXCEPTION 'Exit Loss receipt requires an active same-Company account' USING ERRCODE='23514';
        END IF;
        IF EXISTS (SELECT 1 FROM investment_investorfundcredit c
                   WHERE c.tenant_id=NEW.tenant_id
                     AND COALESCE((SELECT x.to_investor_id FROM investment_investorfundcreditcorrection x
                                   WHERE x.credit_id=c.id ORDER BY x.version DESC,x.id DESC LIMIT 1), c.investor_id)=exit_investor
                     AND investment_credit_available(c.id) IS NULL) THEN
            RAISE EXCEPTION 'Exit Loss direct receipt requires Fund source review' USING ERRCODE='23514';
        END IF;
        SELECT COALESCE(SUM(investment_credit_available(c.id)),0) INTO fund_available
          FROM investment_investorfundcredit c
          WHERE c.tenant_id=NEW.tenant_id
            AND COALESCE((SELECT x.to_investor_id FROM investment_investorfundcreditcorrection x
                          WHERE x.credit_id=c.id ORDER BY x.version DESC,x.id DESC LIMIT 1), c.investor_id)=exit_investor;
        IF fund_available>0 THEN
            RAISE EXCEPTION 'Exit Loss must use eligible Available Fund before direct receipt' USING ERRCODE='23514';
        END IF;
    END IF;
    IF NEW.source='AVAILABLE_FUND' AND NEW.account_id IS NOT NULL OR NEW.source='DIRECT_RECEIPT' AND NEW.account_id IS NULL THEN
        RAISE EXCEPTION 'Exit Loss source and account do not match' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0049_signed_exit_profit_settlement_guards")]
    operations = [migrations.RunSQL(GUARD, reverse_sql=migrations.RunSQL.noop)]
