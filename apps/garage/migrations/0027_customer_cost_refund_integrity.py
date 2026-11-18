from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


FORWARD_SQL = r"""
DROP TRIGGER garage_refund_draft_link ON garage_garagecustomercostrefund;
DROP TRIGGER garage_refund_draft_event ON accounting_accountingevent;
DROP FUNCTION garage_refund_draft_reject();

DROP TRIGGER garage_cost_payment_floor ON garage_garagecustomercostcorrection;

CREATE OR REPLACE FUNCTION garage_cost_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    j_company uuid; j_branch uuid; j_context text; rev_company uuid; rev_code text;
    ev record; cost_amount numeric; gross_paid numeric; corrections numeric; prior_refunds numeric; net_paid numeric;
BEGIN
    SELECT j.tenant_id, j.branch_id, j.context INTO j_company, j_branch, j_context
      FROM garage_garagecustomercost c JOIN garage_garagejob j ON j.id=c.job_id
     WHERE c.id=NEW.cost_id FOR UPDATE OF j;
    SELECT tenant_id, module_code INTO rev_company, rev_code
      FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=NEW.event_id;
    SELECT COALESCE((SELECT amount FROM garage_garagecustomercostcorrection
                      WHERE cost_id=NEW.cost_id ORDER BY version DESC LIMIT 1),
                    (SELECT amount FROM garage_garagecustomercost WHERE id=NEW.cost_id))
      INTO cost_amount;
    SELECT COALESCE(SUM(e.amount), 0) INTO gross_paid
      FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(COALESCE(replacement.amount, 0)-previous.amount), 0)
      INTO corrections
      FROM garage_garagecustomercostpaymentcorrection c
      JOIN garage_garagecustomercostpayment p ON p.id=c.payment_id
      JOIN accounting_accountingevent previous ON previous.id=c.previous_event_id
      LEFT JOIN accounting_accountingevent replacement ON replacement.id=c.replacement_event_id
     WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(applied_amount), 0) INTO prior_refunds
      FROM garage_garagecustomercostrefund WHERE cost_id=NEW.cost_id;
    IF j_company IS NULL OR j_context IS DISTINCT FROM 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'garage'
       OR ev.tenant_id IS DISTINCT FROM j_company OR ev.branch_id IS DISTINCT FROM j_branch
       OR ev.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' OR ev.actor_id IS DISTINCT FROM NEW.actor_id
       OR cost_amount IS NULL OR ev.amount <= 0 THEN
        RAISE EXCEPTION 'Garage cost payment scope is invalid' USING ERRCODE='23514';
    END IF;
    SELECT tenant_id, module_code INTO rev_company, rev_code
      FROM tenants_companymodulestate WHERE id=ev.module_revision_id;
    IF rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'accounting' THEN
        RAISE EXCEPTION 'Garage cost payment requires a same-Company Accounting revision' USING ERRCODE='23514';
    END IF;
    net_paid := gross_paid + corrections - prior_refunds;
    IF net_paid < 0 OR net_paid + ev.amount > cost_amount THEN
        RAISE EXCEPTION 'Garage cost payment exceeds the net payable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;

CREATE OR REPLACE FUNCTION garage_cost_payment_floor() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE jid uuid; gross_paid numeric; corrections numeric; refunds numeric; net_paid numeric;
BEGIN
    SELECT job_id INTO jid FROM garage_garagecustomercost WHERE id=NEW.cost_id;
    PERFORM 1 FROM garage_garagejob WHERE id=jid FOR UPDATE;
    SELECT COALESCE(SUM(e.amount), 0) INTO gross_paid
      FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(COALESCE(replacement.amount, 0)-previous.amount), 0)
      INTO corrections
      FROM garage_garagecustomercostpaymentcorrection c
      JOIN garage_garagecustomercostpayment p ON p.id=c.payment_id
      JOIN accounting_accountingevent previous ON previous.id=c.previous_event_id
      LEFT JOIN accounting_accountingevent replacement ON replacement.id=c.replacement_event_id
     WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(applied_amount), 0) INTO refunds
      FROM garage_garagecustomercostrefund WHERE cost_id=NEW.cost_id;
    net_paid := gross_paid + corrections - refunds;
    IF NEW.amount < net_paid THEN
        RAISE EXCEPTION 'Garage cost cannot be reduced below net payments after refunds' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_cost_payment_floor BEFORE INSERT ON garage_garagecustomercostcorrection
    FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_floor();

CREATE FUNCTION garage_customer_cost_refund_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    j_company uuid; j_branch uuid; j_context text; rev_company uuid; rev_code text;
    ev record; gross_paid numeric; corrections numeric; paid numeric; prior_refunds numeric;
BEGIN
    SELECT j.tenant_id, j.branch_id, j.context INTO j_company, j_branch, j_context
      FROM garage_garagecustomercost c JOIN garage_garagejob j ON j.id=c.job_id
     WHERE c.id=NEW.cost_id FOR UPDATE OF j;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=NEW.event_id;
    SELECT tenant_id, module_code INTO rev_company, rev_code
      FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT COALESCE(SUM(e.amount), 0) INTO gross_paid
      FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(COALESCE(replacement.amount, 0)-previous.amount), 0)
      INTO corrections
      FROM garage_garagecustomercostpaymentcorrection c
      JOIN garage_garagecustomercostpayment p ON p.id=c.payment_id
      JOIN accounting_accountingevent previous ON previous.id=c.previous_event_id
      LEFT JOIN accounting_accountingevent replacement ON replacement.id=c.replacement_event_id
     WHERE p.cost_id=NEW.cost_id;
    SELECT COALESCE(SUM(applied_amount), 0) INTO prior_refunds
      FROM garage_garagecustomercostrefund WHERE cost_id=NEW.cost_id;
    paid := gross_paid + corrections;
    IF j_company IS NULL OR j_context IS DISTINCT FROM 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'garage'
       OR ev.tenant_id IS DISTINCT FROM j_company OR ev.branch_id IS DISTINCT FROM j_branch
       OR ev.event_type IS DISTINCT FROM 'GARAGE_COST_REFUND' OR ev.actor_id IS DISTINCT FROM NEW.actor_id
       OR ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL
       OR ev.category_id IS NOT NULL OR ev.amount <= 0
       OR NEW.applied_amount < 0 OR NEW.applied_amount > ev.amount
       OR prior_refunds + NEW.applied_amount > paid THEN
        RAISE EXCEPTION 'Garage customer cost refund scope or applied amount is invalid' USING ERRCODE='23514';
    END IF;
    SELECT tenant_id, module_code INTO rev_company, rev_code
      FROM tenants_companymodulestate WHERE id=ev.module_revision_id;
    IF rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'accounting' THEN
        RAISE EXCEPTION 'Garage customer cost refund requires a same-Company Accounting revision' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_customer_cost_refund_scope BEFORE INSERT ON garage_garagecustomercostrefund
    FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_refund_guard();
CREATE TRIGGER garage_customer_cost_refund_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercostrefund
    FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE FUNCTION garage_customer_cost_refund_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    eid uuid; ev record; refund_count bigint; applied numeric; movement_count bigint; movement_total numeric;
    app_count bigint; app_total numeric; app_valid_count bigint; excess numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id;
    ELSIF TG_TABLE_NAME='accounting_accountmovement' THEN eid := NEW.event_id;
    ELSIF TG_TABLE_NAME='accounting_accountingapplication' THEN eid := NEW.source_event_id;
    ELSE eid := NEW.event_id;
    END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF NOT FOUND OR ev.event_type IS DISTINCT FROM 'GARAGE_COST_REFUND' THEN RETURN NULL; END IF;
    SELECT COUNT(*), COALESCE(MAX(applied_amount), 0) INTO refund_count, applied
      FROM garage_garagecustomercostrefund WHERE event_id=eid;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO movement_count, movement_total
      FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF refund_count <> 1 OR movement_count <> 1 OR movement_total <> ev.amount
       OR ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL
       OR applied < 0 OR applied > ev.amount THEN
        RAISE EXCEPTION 'Garage cost refund requires one typed source and one exact Cash/Bank inflow' USING ERRCODE='23514';
    END IF;
    excess := ev.amount - applied;
    SELECT COUNT(*), COALESCE(SUM(a.amount*a.effect_sign), 0),
           COUNT(*) FILTER (WHERE a.tenant_id=ev.tenant_id
             AND a.effect_sign=1 AND a.reversal_of_id IS NULL
             AND a.actor_id=(SELECT actor_id FROM garage_garagecustomercostrefund WHERE event_id=eid)
             AND a.module_revision_id=ev.module_revision_id
             AND t.tenant_id=ev.tenant_id AND t.branch_id=ev.branch_id
             AND t.event_type='INCOME' AND t.amount=excess AND t.effect_sign=1
             AND t.reversal_of_id IS NULL AND t.replaces_event_id IS NULL
             AND t.effective_at=ev.effective_at
             AND cat.tenant_id=ev.tenant_id AND cat.kind='INCOME')
      INTO app_count, app_total, app_valid_count
      FROM accounting_accountingapplication a
      JOIN accounting_accountingevent t ON t.id=a.target_event_id
      LEFT JOIN accounting_accountingcategory cat ON cat.id=t.category_id
     WHERE a.source_event_id=eid;
    IF (excess = 0 AND app_count <> 0)
       OR (excess > 0 AND (app_count <> 1 OR app_valid_count <> 1 OR app_total <> excess)) THEN
        RAISE EXCEPTION 'Garage cost refund excess must link exactly to one matching Company Income event' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER garage_cost_refund_event_shape AFTER INSERT ON accounting_accountingevent
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_refund_shape();
CREATE CONSTRAINT TRIGGER garage_cost_refund_move_shape AFTER INSERT ON accounting_accountmovement
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_refund_shape();
CREATE CONSTRAINT TRIGGER garage_cost_refund_link_shape AFTER INSERT ON garage_garagecustomercostrefund
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_refund_shape();
CREATE CONSTRAINT TRIGGER garage_cost_refund_application_shape AFTER INSERT ON accounting_accountingapplication
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_customer_cost_refund_shape();
"""


REVERSE_SQL = r"""
DROP TRIGGER garage_cost_refund_application_shape ON accounting_accountingapplication;
DROP TRIGGER garage_cost_refund_link_shape ON garage_garagecustomercostrefund;
DROP TRIGGER garage_cost_refund_move_shape ON accounting_accountmovement;
DROP TRIGGER garage_cost_refund_event_shape ON accounting_accountingevent;
DROP FUNCTION garage_customer_cost_refund_shape();
DROP TRIGGER garage_customer_cost_refund_immutable ON garage_garagecustomercostrefund;
DROP TRIGGER garage_customer_cost_refund_scope ON garage_garagecustomercostrefund;
DROP FUNCTION garage_customer_cost_refund_guard();

CREATE FUNCTION garage_refund_draft_reject() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_TABLE_NAME='garage_garagecustomercostrefund' THEN
        RAISE EXCEPTION 'Garage cost refund is not yet implemented' USING ERRCODE='23514';
    END IF;
    IF NEW.event_type='GARAGE_COST_REFUND' THEN
        RAISE EXCEPTION 'Garage cost refund is not yet implemented' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_refund_draft_event BEFORE INSERT ON accounting_accountingevent
    FOR EACH ROW EXECUTE FUNCTION garage_refund_draft_reject();
CREATE TRIGGER garage_refund_draft_link BEFORE INSERT ON garage_garagecustomercostrefund
    FOR EACH ROW EXECUTE FUNCTION garage_refund_draft_reject();

DROP TRIGGER garage_cost_payment_floor ON garage_garagecustomercostcorrection;
CREATE OR REPLACE FUNCTION garage_cost_payment_floor() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE jid uuid; paid numeric;
BEGIN
    SELECT job_id INTO jid FROM garage_garagecustomercost WHERE id=NEW.cost_id;
    PERFORM 1 FROM garage_garagejob WHERE id=jid FOR UPDATE;
    SELECT COALESCE(SUM(e.amount), 0) INTO paid FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    IF NEW.amount < paid THEN RAISE EXCEPTION 'Garage cost cannot be reduced below paid amount' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_cost_payment_floor BEFORE INSERT ON garage_garagecustomercostcorrection
    FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_floor();

CREATE OR REPLACE FUNCTION garage_cost_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j_id uuid; j_company uuid; j_branch uuid; j_context text; rev_company uuid; rev_code text;
        ev record; cost_amount numeric; paid numeric;
BEGIN
    SELECT j.id, j.tenant_id, j.branch_id, j.context INTO j_id, j_company, j_branch, j_context
      FROM garage_garagecustomercost c JOIN garage_garagejob j ON j.id=c.job_id
      WHERE c.id=NEW.cost_id FOR UPDATE OF j;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=NEW.event_id;
    SELECT COALESCE((SELECT amount FROM garage_garagecustomercostcorrection WHERE cost_id=NEW.cost_id ORDER BY version DESC LIMIT 1),
                    (SELECT amount FROM garage_garagecustomercost WHERE id=NEW.cost_id)) INTO cost_amount;
    SELECT COALESCE(SUM(e.amount), 0) INTO paid FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    IF j_company IS NULL OR j_context IS DISTINCT FROM 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'garage'
       OR ev.tenant_id IS DISTINCT FROM j_company OR ev.branch_id IS DISTINCT FROM j_branch
       OR ev.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' OR ev.actor_id IS DISTINCT FROM NEW.actor_id
       OR cost_amount IS NULL OR paid + ev.amount > cost_amount THEN
        RAISE EXCEPTION 'Garage cost payment scope or payable limit invalid' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;

"""


def refuse_reverse_with_refunds(apps, schema_editor):
    model = apps.get_model("garage", "GarageCustomerCostRefund")
    if model.objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage customer cost refund history exists; retain its integrity guards.")


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0017_garage_refund_income_application"),
        ("garage", "0026_refund_draft_fail_closed"),
    ]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
        migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_refunds),
    ]
