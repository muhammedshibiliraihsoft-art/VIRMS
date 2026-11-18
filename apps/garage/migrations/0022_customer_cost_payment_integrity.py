from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_payments(apps, schema_editor):
    if apps.get_model('garage', 'GarageCustomerCostPayment').objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError('Garage cost payment history exists; retain integrity guards.')


FORWARD = r"""
CREATE FUNCTION garage_cost_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE TRIGGER garage_cost_payment_scope BEFORE INSERT ON garage_garagecustomercostpayment FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_guard();
CREATE TRIGGER garage_cost_payment_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercostpayment FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE FUNCTION garage_cost_payment_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; links integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id; ELSE eid := NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO links FROM garage_garagecustomercostpayment WHERE event_id=eid;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO moves, total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF links <> 1 OR moves <> 1 OR total <> -ev.amount OR ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL THEN
        RAISE EXCEPTION 'Garage cost payment requires one typed source and exact Cash/Bank outflow' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER garage_cost_payment_event_shape AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_shape();
CREATE CONSTRAINT TRIGGER garage_cost_payment_move_shape AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_shape();
CREATE CONSTRAINT TRIGGER garage_cost_payment_link_shape AFTER INSERT ON garage_garagecustomercostpayment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_shape();

CREATE FUNCTION garage_cost_payment_floor() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE jid uuid; paid numeric;
BEGIN
    SELECT job_id INTO jid FROM garage_garagecustomercost WHERE id=NEW.cost_id;
    PERFORM 1 FROM garage_garagejob WHERE id=jid FOR UPDATE;
    SELECT COALESCE(SUM(e.amount), 0) INTO paid FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;
    IF NEW.amount < paid THEN RAISE EXCEPTION 'Garage cost cannot be reduced below paid amount' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_cost_payment_floor BEFORE INSERT ON garage_garagecustomercostcorrection FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_floor();
"""

REVERSE = r"""
DROP TRIGGER garage_cost_payment_floor ON garage_garagecustomercostcorrection;
DROP FUNCTION garage_cost_payment_floor();
DROP TRIGGER garage_cost_payment_link_shape ON garage_garagecustomercostpayment;
DROP TRIGGER garage_cost_payment_move_shape ON accounting_accountmovement;
DROP TRIGGER garage_cost_payment_event_shape ON accounting_accountingevent;
DROP FUNCTION garage_cost_payment_shape();
DROP TRIGGER garage_cost_payment_immutable ON garage_garagecustomercostpayment;
DROP TRIGGER garage_cost_payment_scope ON garage_garagecustomercostpayment;
DROP FUNCTION garage_cost_payment_guard();
"""


class Migration(migrations.Migration):
    dependencies = [('garage', '0021_garagecustomercostpayment')]
    operations = [migrations.RunSQL(FORWARD, REVERSE), migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_payments)]
