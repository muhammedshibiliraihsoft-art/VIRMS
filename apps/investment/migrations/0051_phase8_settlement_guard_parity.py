from django.db import migrations


FORWARD_SQL = r"""

CREATE OR REPLACE FUNCTION investor_exit_profit_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; position_company uuid; position_investor uuid;
        v_period_start date; v_period_end date; v_amount_due numeric;
        v_profit_paid numeric; v_recovery_received numeric; v_future_applied numeric; v_future_recovered numeric;
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
    IF v_amount_due IS NULL THEN
        RAISE EXCEPTION 'Exit Profit payment requires a current confirmed position' USING ERRCODE='23514';
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
                    WHERE a.tenant_id=NEW.tenant_id AND a.loss_result_id=v.id),0),0)),0)
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
    SELECT COALESCE(SUM(x.amount),0) INTO v_future_recovered FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.recoverable_position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO v_profit_paid FROM investment_investorexitprofitpayment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=v_period_start AND r.period_end=v_period_end;
    IF NEW.amount>GREATEST(v_amount_due-v_profit_paid-v_future_applied+v_recovery_received+v_future_recovered,0) THEN
        RAISE EXCEPTION 'Exit Profit payment exceeds current confirmed payable' USING ERRCODE='23514';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM tenants_companymodulestate m WHERE m.id=NEW.accounting_revision_id
       AND m.tenant_id=NEW.tenant_id AND m.module_code='accounting' AND m.state='enabled') THEN
        RAISE EXCEPTION 'Exit Profit payment requires Accounting enabled' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;


CREATE OR REPLACE FUNCTION investor_exit_loss_application_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; loss_company uuid; loss_investor uuid; loss_version integer;
        loss_amount numeric; used_amount numeric; prior_offsets numeric; module record; fund_available numeric;
BEGIN
    PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
    SELECT tenant_id,investor_id INTO exit_company,exit_investor FROM investment_investorexitrequest
      WHERE id=NEW.exit_request_id AND status='REQUESTED';
    SELECT tenant_id,investor_id,version,abs(investor_share_amount) INTO loss_company,loss_investor,loss_version,loss_amount
      FROM investment_vehicleresultconfirmation WHERE id=NEW.loss_result_id AND result_kind='LOSS';
    PERFORM 1 FROM investment_investor WHERE id=loss_investor AND tenant_id=loss_company FOR UPDATE;
    IF exit_company IS DISTINCT FROM NEW.tenant_id OR loss_company IS DISTINCT FROM NEW.tenant_id
       OR exit_investor IS DISTINCT FROM loss_investor OR NEW.effective_at>clock_timestamp() OR btrim(NEW.reason)=''
       OR NOT EXISTS (SELECT 1 FROM tenants_branch WHERE id=NEW.branch_id AND tenant_id=NEW.tenant_id)
       OR NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation x WHERE x.id=NEW.loss_result_id
                      AND NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation n WHERE n.tenant_id=x.tenant_id AND n.sale_id=x.sale_id AND n.version>x.version)) THEN
        RAISE EXCEPTION 'Exit Loss application requires current same-Company sources' USING ERRCODE='23514';
    END IF;
    IF EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation older
               JOIN investment_investorprofitlossoffset o ON o.loss_result_id=older.id
               WHERE older.tenant_id=NEW.tenant_id AND older.sale_id=(SELECT sale_id FROM investment_vehicleresultconfirmation WHERE id=NEW.loss_result_id)
                 AND older.investor_id=loss_investor AND older.id<>NEW.loss_result_id)
       OR EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation older
                  JOIN investment_investorexitlossapplication a ON a.loss_result_id=older.id
                  WHERE older.tenant_id=NEW.tenant_id AND older.sale_id=(SELECT sale_id FROM investment_vehicleresultconfirmation WHERE id=NEW.loss_result_id)
                    AND older.investor_id=loss_investor AND older.id<>NEW.loss_result_id) THEN
        RAISE EXCEPTION 'Earlier Loss settlement requires review after Vehicle correction' USING ERRCODE='23514';
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

CREATE OR REPLACE FUNCTION investment_assert_profit_loss_offset_bounds()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_investor_id uuid;
    v_tenant_id uuid;
    v_loss_result_id uuid;
    v_profit_result_id uuid;
    v_sale_id uuid;
    loss_share numeric;
    profit_share numeric;
    loss_offset_total numeric;
    exit_loss_total numeric;
    loss_sale_id uuid;
    profit_offset_total numeric;
    profit_payment_total numeric;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorprofitlossoffset' THEN
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_loss_result_id := NEW.loss_result_id;
        v_profit_result_id := NEW.profit_result_id;
    ELSE
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_profit_result_id := NEW.result_confirmation_id;
    END IF;

    PERFORM 1 FROM investment_investor
     WHERE id = v_investor_id AND tenant_id = v_tenant_id
     FOR UPDATE;

    IF v_loss_result_id IS NOT NULL THEN
        SELECT current_loss.investor_share_amount, current_loss.sale_id
          INTO loss_share, loss_sale_id
          FROM investment_vehicleresultconfirmation current_loss
         WHERE current_loss.id = v_loss_result_id AND current_loss.tenant_id = v_tenant_id
           AND current_loss.investor_id = v_investor_id AND current_loss.result_kind = 'LOSS'
           AND NOT EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation newer
                           WHERE newer.tenant_id = v_tenant_id AND newer.sale_id = current_loss.sale_id
                             AND newer.version > current_loss.version);
        SELECT COALESCE(SUM(amount), 0) INTO loss_offset_total
          FROM investment_investorprofitlossoffset
         WHERE tenant_id = v_tenant_id AND investor_id = v_investor_id
           AND loss_result_id = v_loss_result_id;
        SELECT COALESCE(SUM(amount), 0) INTO exit_loss_total
          FROM investment_investorexitlossapplication
         WHERE tenant_id = v_tenant_id AND loss_result_id = v_loss_result_id;
        IF EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation older
                   WHERE older.tenant_id = v_tenant_id AND older.investor_id = v_investor_id
                     AND older.sale_id = loss_sale_id AND older.id <> v_loss_result_id
                     AND (EXISTS (SELECT 1 FROM investment_investorprofitlossoffset o WHERE o.loss_result_id = older.id)
                       OR EXISTS (SELECT 1 FROM investment_investorexitlossapplication a WHERE a.loss_result_id = older.id)))
           OR loss_share IS NULL OR loss_offset_total + exit_loss_total > ABS(loss_share) THEN
            RAISE EXCEPTION 'Investor Loss settlements exceed the current confirmed Loss share or require review'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF v_profit_result_id IS NOT NULL THEN
        SELECT result.investor_share_amount, result.sale_id
          INTO profit_share, v_sale_id
          FROM investment_vehicleresultconfirmation result
         WHERE result.id = v_profit_result_id AND result.tenant_id = v_tenant_id
           AND result.investor_id = v_investor_id AND result.result_kind = 'PROFIT';
        SELECT COALESCE(SUM(loss_offset.amount), 0) INTO profit_offset_total
          FROM investment_investorprofitlossoffset loss_offset
          JOIN investment_vehicleresultconfirmation result
            ON result.id = loss_offset.profit_result_id
         WHERE loss_offset.tenant_id = v_tenant_id AND loss_offset.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        SELECT COALESCE(SUM(payment.amount), 0) INTO profit_payment_total
          FROM investment_investorvehicleprofitpayment payment
          JOIN investment_vehicleresultconfirmation result
            ON result.id = payment.result_confirmation_id
         WHERE payment.tenant_id = v_tenant_id AND payment.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        IF profit_share IS NULL OR profit_offset_total + profit_payment_total > profit_share THEN
            RAISE EXCEPTION 'Investor Loss offsets and Profit payments exceed the confirmed Profit share'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

"""

REVERSE_SQL = r"""

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

CREATE OR REPLACE FUNCTION investment_assert_profit_loss_offset_bounds()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_investor_id uuid;
    v_tenant_id uuid;
    v_loss_result_id uuid;
    v_profit_result_id uuid;
    v_sale_id uuid;
    loss_share numeric;
    profit_share numeric;
    loss_offset_total numeric;
    profit_offset_total numeric;
    profit_payment_total numeric;
BEGIN
    IF TG_TABLE_NAME = 'investment_investorprofitlossoffset' THEN
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_loss_result_id := NEW.loss_result_id;
        v_profit_result_id := NEW.profit_result_id;
    ELSE
        v_investor_id := NEW.investor_id;
        v_tenant_id := NEW.tenant_id;
        v_profit_result_id := NEW.result_confirmation_id;
    END IF;

    PERFORM 1 FROM investment_investor
     WHERE id = v_investor_id AND tenant_id = v_tenant_id
     FOR UPDATE;

    IF v_loss_result_id IS NOT NULL THEN
        SELECT investor_share_amount INTO loss_share
          FROM investment_vehicleresultconfirmation
         WHERE id = v_loss_result_id AND tenant_id = v_tenant_id
           AND investor_id = v_investor_id AND result_kind = 'LOSS';
        SELECT COALESCE(SUM(amount), 0) INTO loss_offset_total
          FROM investment_investorprofitlossoffset
         WHERE tenant_id = v_tenant_id AND investor_id = v_investor_id
           AND loss_result_id = v_loss_result_id;
        IF loss_share IS NULL OR loss_offset_total > ABS(loss_share) THEN
            RAISE EXCEPTION 'Investor Loss offsets exceed the confirmed Loss share'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    IF v_profit_result_id IS NOT NULL THEN
        SELECT result.investor_share_amount, result.sale_id
          INTO profit_share, v_sale_id
          FROM investment_vehicleresultconfirmation result
         WHERE result.id = v_profit_result_id AND result.tenant_id = v_tenant_id
           AND result.investor_id = v_investor_id AND result.result_kind = 'PROFIT';
        SELECT COALESCE(SUM(loss_offset.amount), 0) INTO profit_offset_total
          FROM investment_investorprofitlossoffset loss_offset
          JOIN investment_vehicleresultconfirmation result
            ON result.id = loss_offset.profit_result_id
         WHERE loss_offset.tenant_id = v_tenant_id AND loss_offset.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        SELECT COALESCE(SUM(payment.amount), 0) INTO profit_payment_total
          FROM investment_investorvehicleprofitpayment payment
          JOIN investment_vehicleresultconfirmation result
            ON result.id = payment.result_confirmation_id
         WHERE payment.tenant_id = v_tenant_id AND payment.investor_id = v_investor_id
           AND result.sale_id = v_sale_id;
        IF profit_share IS NULL OR profit_offset_total + profit_payment_total > profit_share THEN
            RAISE EXCEPTION 'Investor Loss offsets and Profit payments exceed the confirmed Profit share'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0050_exit_loss_fund_first_guard")]
    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=REVERSE_SQL)]
