from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_receipts(apps, schema_editor):
    if apps.get_model("garage", "GarageCustomerReceipt").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Garage receipt history exists; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION garage_receipt_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j_company uuid; j_branch uuid; j_context text; rev_company uuid; rev_code text;
        e_company uuid; e_branch uuid; e_type text; e_actor uuid; e_amount numeric; e_reference text;
        charge numeric; collected numeric;
BEGIN
    SELECT tenant_id, branch_id, context INTO j_company, j_branch, j_context FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT tenant_id, branch_id, event_type, actor_id, amount, source_reference
      INTO e_company, e_branch, e_type, e_actor, e_amount, e_reference FROM accounting_accountingevent WHERE id=NEW.event_id;
    SELECT amount INTO charge FROM garage_garagecustomercharge WHERE job_id=NEW.job_id ORDER BY version DESC LIMIT 1;
    SELECT COALESCE(SUM(e.amount), 0) INTO collected FROM garage_garagecustomerreceipt r JOIN accounting_accountingevent e ON e.id=r.event_id WHERE r.job_id=NEW.job_id;
    IF j_company IS DISTINCT FROM NEW.tenant_id OR j_context IS DISTINCT FROM 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'garage'
       OR e_company IS DISTINCT FROM j_company OR e_branch IS DISTINCT FROM j_branch
       OR e_type IS DISTINCT FROM 'GARAGE_RECEIPT' OR e_actor IS DISTINCT FROM NEW.actor_id
       OR e_reference IS DISTINCT FROM NEW.reference OR charge IS NULL OR collected + e_amount > charge THEN
        RAISE EXCEPTION 'Garage receipt scope, source or charge limit invalid' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_receipt_scope BEFORE INSERT ON garage_garagecustomerreceipt FOR EACH ROW EXECUTE FUNCTION garage_receipt_guard();
CREATE TRIGGER garage_receipt_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomerreceipt FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE FUNCTION garage_charge_receipt_floor() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE collected numeric;
BEGIN
    PERFORM 1 FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT COALESCE(SUM(e.amount), 0) INTO collected FROM garage_garagecustomerreceipt r JOIN accounting_accountingevent e ON e.id=r.event_id WHERE r.job_id=NEW.job_id;
    IF NEW.amount < collected THEN RAISE EXCEPTION 'Garage charge cannot be less than collected amount' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_charge_floor BEFORE INSERT ON garage_garagecustomercharge FOR EACH ROW EXECUTE FUNCTION garage_charge_receipt_floor();

CREATE FUNCTION garage_assert_receipt_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; links integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id;
    ELSE eid := NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'GARAGE_RECEIPT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO links FROM garage_garagecustomerreceipt WHERE event_id=eid;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO moves, total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF links <> 1 OR moves <> 1 OR total <> ev.amount OR ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL THEN
        RAISE EXCEPTION 'Garage receipt requires exactly one typed Job link and matching Cash/Bank movement' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER garage_receipt_event_shape AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_assert_receipt_shape();
CREATE CONSTRAINT TRIGGER garage_receipt_move_shape AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_assert_receipt_shape();
CREATE CONSTRAINT TRIGGER garage_receipt_link_shape AFTER INSERT ON garage_garagecustomerreceipt DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION garage_assert_receipt_shape();
"""
REVERSE = r"""
DROP TRIGGER garage_receipt_link_shape ON garage_garagecustomerreceipt;
DROP TRIGGER garage_receipt_move_shape ON accounting_accountmovement;
DROP TRIGGER garage_receipt_event_shape ON accounting_accountingevent;
DROP FUNCTION garage_assert_receipt_shape();
DROP TRIGGER garage_charge_floor ON garage_garagecustomercharge;
DROP FUNCTION garage_charge_receipt_floor();
DROP TRIGGER garage_receipt_immutable ON garage_garagecustomerreceipt;
DROP TRIGGER garage_receipt_scope ON garage_garagecustomerreceipt;
DROP FUNCTION garage_receipt_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0009_garagecustomerreceipt")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_receipts), migrations.RunSQL(FORWARD, REVERSE)]
