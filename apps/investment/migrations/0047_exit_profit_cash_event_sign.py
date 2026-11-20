from django.db import migrations


COMPLETE = r"""
CREATE OR REPLACE FUNCTION investor_exit_profit_payment_complete() RETURNS trigger LANGUAGE plpgsql AS $$
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
       OR ev.source_reference IS DISTINCT FROM 'INVESTOR-EXIT-PROFIT-'||pid::text OR ev.effect_sign<>1
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
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0046_exit_profit_payment_guard_variables")]
    operations = [migrations.RunSQL(COMPLETE, reverse_sql=migrations.RunSQL.noop)]
