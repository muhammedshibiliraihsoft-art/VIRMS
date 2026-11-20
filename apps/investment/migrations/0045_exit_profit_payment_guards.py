from django.db import migrations


GUARDS = r"""
CREATE FUNCTION investor_exit_profit_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE exit_company uuid; exit_investor uuid; position_company uuid; position_investor uuid;
        period_start date; period_end date; amount_due numeric; repaid numeric; future_recovered numeric; future_applied numeric;
BEGIN
    PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
    SELECT e.tenant_id,e.investor_id INTO exit_company,exit_investor
      FROM investment_investorexitrequest e WHERE e.id=NEW.exit_request_id AND e.status='REQUESTED';
    SELECT r.tenant_id,r.investor_id,r.period_start,r.period_end,r.net_position
      INTO position_company,position_investor,period_start,period_end,amount_due
      FROM investment_investorprofitperiodposition p
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE p.id=NEW.position_id;
    IF exit_company IS DISTINCT FROM NEW.tenant_id OR position_company IS DISTINCT FROM NEW.tenant_id
       OR exit_investor IS DISTINCT FROM position_investor OR NEW.effective_at>clock_timestamp() OR btrim(NEW.reason)=''
       OR NOT EXISTS (SELECT 1 FROM tenants_branch WHERE id=NEW.branch_id AND tenant_id=NEW.tenant_id)
       OR NOT EXISTS (SELECT 1 FROM accounting_accountingaccount WHERE id=NEW.account_id AND tenant_id=NEW.tenant_id AND is_active)
       OR EXISTS (SELECT 1 FROM investment_investorprofitperiodreconciliation n JOIN investment_investorprofitperiodreconciliation c
                  ON c.id=(SELECT reconciliation_id FROM investment_investorprofitperiodposition WHERE id=NEW.position_id)
                  WHERE n.tenant_id=NEW.tenant_id AND n.investor_id=position_investor AND n.period_start=period_start AND n.version>c.version) THEN
        RAISE EXCEPTION 'Exit Profit payment requires current same-Company sources' USING ERRCODE='23514';
    END IF;
    SELECT COALESCE(SUM(x.amount),0) INTO repaid FROM investment_investorprofitrecoveryreceipt x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=period_start AND r.period_end=period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO future_recovered FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.recoverable_position
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=period_start AND r.period_end=period_end;
    SELECT COALESCE(SUM(x.amount),0) INTO future_applied FROM investment_investorprofitfutureadjustment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.profit_position
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=period_start AND r.period_end=period_end;
    repaid := repaid + COALESCE((SELECT SUM(x.amount) FROM investment_investorexitprofitpayment x
      JOIN investment_investorprofitperiodposition p ON p.id=x.position_id
      JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
      WHERE x.tenant_id=NEW.tenant_id AND r.investor_id=position_investor AND r.period_start=period_start AND r.period_end=period_end),0);
    IF NEW.amount>GREATEST(amount_due-repaid-future_recovered+future_applied,0) THEN
        RAISE EXCEPTION 'Exit Profit payment exceeds current confirmed payable' USING ERRCODE='23514';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM tenants_companymodulestate m WHERE m.id=NEW.accounting_revision_id
       AND m.tenant_id=NEW.tenant_id AND m.module_code='accounting' AND m.state='enabled') THEN
        RAISE EXCEPTION 'Exit Profit payment requires Accounting enabled' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER investor_exit_profit_payment_scope BEFORE INSERT ON investment_investorexitprofitpayment
FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_guard();
CREATE FUNCTION investor_exit_profit_payment_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Exit Profit payments are append-only' USING ERRCODE='23514'; END; $$;
CREATE TRIGGER investor_exit_profit_payment_immutable BEFORE UPDATE OR DELETE ON investment_investorexitprofitpayment
FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_immutable();

CREATE FUNCTION investor_exit_profit_payment_complete() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE pid uuid; payment investment_investorexitprofitpayment%ROWTYPE; event_uuid uuid; ev accounting_accountingevent%ROWTYPE;
BEGIN
    IF TG_TABLE_NAME='investment_investorexitprofitpayment' THEN pid:=NEW.id;
    ELSIF TG_TABLE_NAME='accounting_accountingevent' THEN event_uuid:=NEW.id;
    ELSIF TG_TABLE_NAME='accounting_accountingsourcelink' THEN event_uuid:=NEW.event_id;
    ELSE event_uuid:=NEW.event_id; END IF;
    IF pid IS NULL THEN SELECT investor_exit_profit_payment_id INTO pid FROM accounting_accountingsourcelink WHERE event_id=event_uuid; END IF;
    IF pid IS NULL THEN
        IF event_uuid IS NOT NULL AND EXISTS (SELECT 1 FROM accounting_accountingevent WHERE id=event_uuid AND event_type='INVESTOR_EXIT_PROFIT_PAYMENT') THEN
            RAISE EXCEPTION 'Exit Profit payment requires typed source' USING ERRCODE='23514';
        END IF;
        RETURN NULL;
    END IF;
    SELECT * INTO payment FROM investment_investorexitprofitpayment WHERE id=pid;
    SELECT event_id INTO event_uuid FROM accounting_accountingsourcelink WHERE investor_exit_profit_payment_id=pid;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=event_uuid;
    IF ev.id IS NULL OR ev.tenant_id IS DISTINCT FROM payment.tenant_id OR ev.event_type<>'INVESTOR_EXIT_PROFIT_PAYMENT'
       OR ev.amount IS DISTINCT FROM payment.amount OR ev.actor_id IS DISTINCT FROM payment.actor_id
       OR ev.branch_id IS DISTINCT FROM payment.branch_id OR ev.effective_at IS DISTINCT FROM payment.effective_at
       OR ev.module_revision_id IS DISTINCT FROM payment.accounting_revision_id OR ev.description IS DISTINCT FROM payment.reason
       OR ev.source_reference IS DISTINCT FROM 'INVESTOR-EXIT-PROFIT-'||pid::text OR ev.effect_sign<>-1
       OR (SELECT COUNT(*) FROM accounting_accountmovement WHERE event_id=event_uuid)<>1
       OR NOT EXISTS (SELECT 1 FROM accounting_accountmovement WHERE event_id=event_uuid AND account_id=payment.account_id AND delta=-payment.amount)
       OR EXISTS (SELECT 1 FROM accounting_accountingapplication WHERE source_event_id=event_uuid OR target_event_id=event_uuid)
       OR NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent a WHERE a.action='investment.exit.settlement.profit'
          AND a.company_id=payment.tenant_id AND a.actor_id=payment.actor_id AND a.resource_id=pid
          AND a.metadata->>'accounting_event_id'=event_uuid::text) THEN
        RAISE EXCEPTION 'Exit Profit payment requires one matching cash movement and Accountant audit' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER investor_exit_profit_payment_complete AFTER INSERT ON investment_investorexitprofitpayment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_complete();
CREATE CONSTRAINT TRIGGER investor_exit_profit_event_complete AFTER INSERT ON accounting_accountingevent
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_complete();
CREATE CONSTRAINT TRIGGER investor_exit_profit_link_complete AFTER INSERT ON accounting_accountingsourcelink
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_complete();
CREATE CONSTRAINT TRIGGER investor_exit_profit_movement_complete AFTER INSERT ON accounting_accountmovement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION investor_exit_profit_payment_complete();
"""


def install(apps, schema_editor):
    schema_editor.execute(GUARDS, params=None)


def remove(apps, schema_editor):
    if apps.get_model("investment", "InvestorExitProfitPayment").objects.exists():
        raise RuntimeError("Exit Profit payment history must be preserved.")
    schema_editor.execute("DROP FUNCTION investor_exit_profit_payment_complete() CASCADE; DROP FUNCTION investor_exit_profit_payment_immutable() CASCADE; DROP FUNCTION investor_exit_profit_payment_guard() CASCADE;", params=None)


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0044_investorexitprofitpayment"),
        ("accounting", "0032_accountingsourcelink_investor_exit_profit_payment_and_more"),
    ]

    operations = [migrations.RunPython(install, remove)]
