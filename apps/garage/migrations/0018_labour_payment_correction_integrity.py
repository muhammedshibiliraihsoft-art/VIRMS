from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_corrections(apps, schema_editor):
    if apps.get_model('garage', 'LabourPaymentCorrection').objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError('Labour payment correction history exists; retain integrity guards.')


FORWARD = r"""
CREATE FUNCTION labour_payment_correction_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p_company uuid; p_branch uuid; root_event uuid; rev_company uuid; rev_code text;
        old_event record; reversal record; replacement record; old_account uuid; reverse_account uuid; latest integer; last_replacement uuid;
BEGIN
    SELECT p.tenant_id, p.branch_id, pay.event_id INTO p_company, p_branch, root_event
      FROM garage_labourpayment pay JOIN garage_labourperson p ON p.id=pay.person_id
      WHERE pay.id=NEW.payment_id FOR UPDATE OF p;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT COALESCE(MAX(version), 0) INTO latest FROM garage_labourpaymentcorrection WHERE payment_id=NEW.payment_id;
    IF latest > 0 THEN SELECT replacement_event_id INTO last_replacement FROM garage_labourpaymentcorrection WHERE payment_id=NEW.payment_id AND version=latest; END IF;
    SELECT * INTO old_event FROM accounting_accountingevent WHERE id=NEW.previous_event_id;
    SELECT * INTO reversal FROM accounting_accountingevent WHERE id=NEW.reversal_event_id;
    IF p_company IS NULL OR rev_company IS DISTINCT FROM p_company OR rev_code IS DISTINCT FROM 'labour'
       OR NEW.version <> latest + 1 OR (latest = 0 AND NEW.previous_event_id IS DISTINCT FROM root_event)
       OR (latest > 0 AND (last_replacement IS NULL OR NEW.previous_event_id IS DISTINCT FROM last_replacement))
       OR old_event.tenant_id IS DISTINCT FROM p_company OR old_event.branch_id IS DISTINCT FROM p_branch
       OR old_event.event_type IS DISTINCT FROM 'LABOUR_PAYMENT' OR old_event.effect_sign <> 1
       OR reversal.reversal_of_id IS DISTINCT FROM NEW.previous_event_id OR reversal.actor_id IS DISTINCT FROM NEW.actor_id
       OR reversal.correction_reason IS DISTINCT FROM NEW.reason THEN
        RAISE EXCEPTION 'Labour correction scope or reversal invalid' USING ERRCODE='23514';
    END IF;
    SELECT account_id INTO old_account FROM accounting_accountmovement WHERE event_id=NEW.previous_event_id;
    SELECT account_id INTO reverse_account FROM accounting_accountmovement WHERE event_id=NEW.reversal_event_id;
    IF old_account IS NULL OR reverse_account IS DISTINCT FROM old_account THEN
        RAISE EXCEPTION 'Labour correction reversal account invalid' USING ERRCODE='23514';
    END IF;
    IF NEW.replacement_event_id IS NOT NULL THEN
        SELECT * INTO replacement FROM accounting_accountingevent WHERE id=NEW.replacement_event_id;
        IF replacement.replaces_event_id IS DISTINCT FROM NEW.previous_event_id OR replacement.actor_id IS DISTINCT FROM NEW.actor_id
           OR replacement.tenant_id IS DISTINCT FROM p_company OR replacement.branch_id IS DISTINCT FROM p_branch
           OR replacement.event_type IS DISTINCT FROM 'LABOUR_PAYMENT' OR replacement.effect_sign <> 1
           OR replacement.correction_reason IS DISTINCT FROM NEW.reason THEN
            RAISE EXCEPTION 'Labour correction replacement invalid' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER labour_correction_scope BEFORE INSERT ON garage_labourpaymentcorrection FOR EACH ROW EXECUTE FUNCTION labour_payment_correction_guard();
CREATE TRIGGER labour_correction_immutable BEFORE UPDATE OR DELETE ON garage_labourpaymentcorrection FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE OR REPLACE FUNCTION labour_payment_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; links integer; originals integer; reversals integer; replacements integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id; ELSE eid := NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'LABOUR_PAYMENT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO originals FROM garage_labourpayment WHERE event_id=eid;
    SELECT COUNT(*) INTO reversals FROM garage_labourpaymentcorrection WHERE reversal_event_id=eid;
    SELECT COUNT(*) INTO replacements FROM garage_labourpaymentcorrection WHERE replacement_event_id=eid;
    links := originals + reversals + replacements;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO moves, total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF links <> 1 OR moves <> 1 OR total <> -ev.amount * ev.effect_sign
       OR (originals=1 AND (ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL))
       OR (reversals=1 AND (ev.effect_sign <> -1 OR ev.reversal_of_id IS NULL OR ev.replaces_event_id IS NOT NULL))
       OR (replacements=1 AND (ev.effect_sign <> 1 OR ev.replaces_event_id IS NULL OR ev.reversal_of_id IS NOT NULL)) THEN
        RAISE EXCEPTION 'Labour payment requires one typed source and exact Cash/Bank movement' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
"""

REVERSE = r"""
DROP TRIGGER labour_correction_immutable ON garage_labourpaymentcorrection;
DROP TRIGGER labour_correction_scope ON garage_labourpaymentcorrection;
DROP FUNCTION labour_payment_correction_guard();
CREATE OR REPLACE FUNCTION labour_payment_shape() RETURNS trigger LANGUAGE plpgsql AS $$
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
"""


class Migration(migrations.Migration):
    dependencies = [('garage', '0017_labourpaymentcorrection')]
    operations = [migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_corrections), migrations.RunSQL(FORWARD, REVERSE)]
