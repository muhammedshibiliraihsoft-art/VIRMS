from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_payments(apps, schema_editor):
    if apps.get_model("garage", "LabourPayment").objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError("Labour payment history exists; integrity guards cannot be reversed.")


FORWARD = r"""
CREATE FUNCTION labour_payment_scope_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p_company uuid; p_branch uuid; p_active boolean; rev_company uuid; rev_code text;
        e_company uuid; e_branch uuid; e_type text; e_actor uuid;
BEGIN
    SELECT tenant_id, branch_id, is_active INTO p_company, p_branch, p_active FROM garage_labourperson WHERE id=NEW.person_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT tenant_id, branch_id, event_type, actor_id INTO e_company, e_branch, e_type, e_actor FROM accounting_accountingevent WHERE id=NEW.event_id;
    IF p_company IS NULL OR p_active IS DISTINCT FROM TRUE OR rev_company IS DISTINCT FROM p_company OR rev_code IS DISTINCT FROM 'labour'
       OR e_company IS DISTINCT FROM p_company OR e_branch IS DISTINCT FROM p_branch OR e_type IS DISTINCT FROM 'LABOUR_PAYMENT' OR e_actor IS DISTINCT FROM NEW.actor_id THEN
        RAISE EXCEPTION 'Labour payment source, Company, Branch or actor mismatch' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER labour_payment_scope BEFORE INSERT ON garage_labourpayment FOR EACH ROW EXECUTE FUNCTION labour_payment_scope_guard();
CREATE TRIGGER labour_payment_immutable BEFORE UPDATE OR DELETE ON garage_labourpayment FOR EACH ROW EXECUTE FUNCTION garage_history_retained();
CREATE FUNCTION labour_payment_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; links integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id; ELSE eid := NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'LABOUR_PAYMENT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO links FROM garage_labourpayment WHERE event_id=eid;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO moves, total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF links <> 1 OR moves <> 1 OR total <> -ev.amount OR ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL THEN
        RAISE EXCEPTION 'Labour payment requires one typed source and exact Cash/Bank outflow' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER labour_payment_event_shape AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION labour_payment_shape();
CREATE CONSTRAINT TRIGGER labour_payment_move_shape AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION labour_payment_shape();
CREATE CONSTRAINT TRIGGER labour_payment_link_shape AFTER INSERT ON garage_labourpayment DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION labour_payment_shape();
"""
REVERSE = r"""
DROP TRIGGER labour_payment_link_shape ON garage_labourpayment;
DROP TRIGGER labour_payment_move_shape ON accounting_accountmovement;
DROP TRIGGER labour_payment_event_shape ON accounting_accountingevent;
DROP FUNCTION labour_payment_shape();
DROP TRIGGER labour_payment_immutable ON garage_labourpayment;
DROP TRIGGER labour_payment_scope ON garage_labourpayment;
DROP FUNCTION labour_payment_scope_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("garage", "0015_labourpayment")]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_payments), migrations.RunSQL(FORWARD, REVERSE)]
