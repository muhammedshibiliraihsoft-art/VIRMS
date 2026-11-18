from importlib import import_module
import re

from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_corrections(apps, schema_editor):
    if apps.get_model('garage', 'GarageReceiptCorrection').objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError('Garage receipt correction history exists; retain integrity guards.')


FORWARD = r"""
CREATE FUNCTION garage_net_received(jid uuid) RETURNS numeric LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT SUM(e.amount) FROM garage_garagecustomerreceipt r JOIN accounting_accountingevent e ON e.id=r.event_id WHERE r.job_id=jid), 0)
       + COALESCE((SELECT SUM(COALESCE(repl.amount, 0) - prev.amount) FROM garage_garagereceiptcorrection c
           JOIN garage_garagecustomerreceipt r ON r.id=c.receipt_id
           JOIN accounting_accountingevent prev ON prev.id=c.previous_event_id
           LEFT JOIN accounting_accountingevent repl ON repl.id=c.replacement_event_id WHERE r.job_id=jid), 0)
$$;
CREATE FUNCTION garage_receipt_correction_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j_id uuid; company_id uuid; branch_id uuid; root_event uuid; rev_company uuid; rev_code text;
        old_event record; reversal record; replacement record; old_account uuid; reverse_account uuid;
        latest integer; last_replacement uuid; charge numeric; new_total numeric;
BEGIN
    SELECT j.id, j.tenant_id, j.branch_id, r.event_id INTO j_id, company_id, branch_id, root_event
      FROM garage_garagecustomerreceipt r JOIN garage_garagejob j ON j.id=r.job_id WHERE r.id=NEW.receipt_id FOR UPDATE OF j;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT COALESCE(MAX(version), 0) INTO latest FROM garage_garagereceiptcorrection WHERE receipt_id=NEW.receipt_id;
    IF latest > 0 THEN SELECT replacement_event_id INTO last_replacement FROM garage_garagereceiptcorrection WHERE receipt_id=NEW.receipt_id AND version=latest; END IF;
    SELECT * INTO old_event FROM accounting_accountingevent WHERE id=NEW.previous_event_id;
    SELECT * INTO reversal FROM accounting_accountingevent WHERE id=NEW.reversal_event_id;
    IF company_id IS NULL OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage'
       OR NEW.version <> latest + 1 OR (latest = 0 AND NEW.previous_event_id IS DISTINCT FROM root_event)
       OR (latest > 0 AND (last_replacement IS NULL OR NEW.previous_event_id IS DISTINCT FROM last_replacement))
       OR old_event.tenant_id IS DISTINCT FROM company_id OR old_event.branch_id IS DISTINCT FROM branch_id
       OR old_event.event_type IS DISTINCT FROM 'GARAGE_RECEIPT' OR old_event.effect_sign <> 1
       OR reversal.reversal_of_id IS DISTINCT FROM NEW.previous_event_id OR reversal.actor_id IS DISTINCT FROM NEW.actor_id
       OR reversal.correction_reason IS DISTINCT FROM NEW.reason THEN
        RAISE EXCEPTION 'Garage receipt correction scope or reversal invalid' USING ERRCODE='23514';
    END IF;
    SELECT account_id INTO old_account FROM accounting_accountmovement WHERE event_id=NEW.previous_event_id;
    SELECT account_id INTO reverse_account FROM accounting_accountmovement WHERE event_id=NEW.reversal_event_id;
    IF old_account IS NULL OR reverse_account IS DISTINCT FROM old_account THEN
        RAISE EXCEPTION 'Garage receipt reversal account invalid' USING ERRCODE='23514';
    END IF;
    new_total := garage_net_received(j_id) - old_event.amount;
    IF NEW.replacement_event_id IS NOT NULL THEN
        SELECT * INTO replacement FROM accounting_accountingevent WHERE id=NEW.replacement_event_id;
        IF replacement.replaces_event_id IS DISTINCT FROM NEW.previous_event_id OR replacement.actor_id IS DISTINCT FROM NEW.actor_id
           OR replacement.tenant_id IS DISTINCT FROM company_id OR replacement.branch_id IS DISTINCT FROM branch_id
           OR replacement.event_type IS DISTINCT FROM 'GARAGE_RECEIPT' OR replacement.effect_sign <> 1
           OR replacement.source_reference IS DISTINCT FROM old_event.source_reference OR replacement.correction_reason IS DISTINCT FROM NEW.reason THEN
            RAISE EXCEPTION 'Garage receipt replacement invalid' USING ERRCODE='23514';
        END IF;
        new_total := new_total + replacement.amount;
    END IF;
    SELECT amount INTO charge FROM garage_garagecustomercharge WHERE job_id=j_id ORDER BY version DESC LIMIT 1;
    IF charge IS NULL OR new_total < 0 OR new_total > charge THEN
        RAISE EXCEPTION 'Garage receipt correction exceeds Job charge' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_receipt_correction_scope BEFORE INSERT ON garage_garagereceiptcorrection FOR EACH ROW EXECUTE FUNCTION garage_receipt_correction_guard();
CREATE TRIGGER garage_receipt_correction_immutable BEFORE UPDATE OR DELETE ON garage_garagereceiptcorrection FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE OR REPLACE FUNCTION garage_receipt_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE j_company uuid; j_branch uuid; j_context text; rev_company uuid; rev_code text;
        e_company uuid; e_branch uuid; e_type text; e_actor uuid; e_amount numeric; e_reference text; charge numeric;
BEGIN
    SELECT tenant_id, branch_id, context INTO j_company, j_branch, j_context FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT tenant_id, branch_id, event_type, actor_id, amount, source_reference INTO e_company, e_branch, e_type, e_actor, e_amount, e_reference FROM accounting_accountingevent WHERE id=NEW.event_id;
    SELECT amount INTO charge FROM garage_garagecustomercharge WHERE job_id=NEW.job_id ORDER BY version DESC LIMIT 1;
    IF j_company IS DISTINCT FROM NEW.tenant_id OR j_context IS DISTINCT FROM 'EXTERNAL_CUSTOMER'
       OR rev_company IS DISTINCT FROM j_company OR rev_code IS DISTINCT FROM 'garage' OR e_company IS DISTINCT FROM j_company
       OR e_branch IS DISTINCT FROM j_branch OR e_type IS DISTINCT FROM 'GARAGE_RECEIPT' OR e_actor IS DISTINCT FROM NEW.actor_id
       OR e_reference IS DISTINCT FROM NEW.reference OR charge IS NULL OR garage_net_received(NEW.job_id) + e_amount > charge THEN
        RAISE EXCEPTION 'Garage receipt scope, source or charge limit invalid' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION garage_charge_receipt_floor() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM 1 FROM garage_garagejob WHERE id=NEW.job_id FOR UPDATE;
    IF NEW.amount < garage_net_received(NEW.job_id) THEN RAISE EXCEPTION 'Garage charge cannot be less than collected amount' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE OR REPLACE FUNCTION garage_assert_receipt_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; originals integer; reversals integer; replacements integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid := NEW.id; ELSE eid := NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'GARAGE_RECEIPT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO originals FROM garage_garagecustomerreceipt WHERE event_id=eid;
    SELECT COUNT(*) INTO reversals FROM garage_garagereceiptcorrection WHERE reversal_event_id=eid;
    SELECT COUNT(*) INTO replacements FROM garage_garagereceiptcorrection WHERE replacement_event_id=eid;
    SELECT COUNT(*), COALESCE(SUM(delta), 0) INTO moves, total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF originals + reversals + replacements <> 1 OR moves <> 1 OR total <> ev.amount * ev.effect_sign
       OR (originals=1 AND (ev.effect_sign <> 1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL))
       OR (reversals=1 AND (ev.effect_sign <> -1 OR ev.reversal_of_id IS NULL OR ev.replaces_event_id IS NOT NULL))
       OR (replacements=1 AND (ev.effect_sign <> 1 OR ev.replaces_event_id IS NULL OR ev.reversal_of_id IS NOT NULL)) THEN
        RAISE EXCEPTION 'Garage receipt requires one typed source and exact Cash/Bank movement' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
"""


def original_guard(name):
    """Restore the exact pre-correction guard when there is no correction history."""
    old_sql = import_module('apps.garage.migrations.0010_receipt_integrity').FORWARD
    match = re.search(rf'CREATE FUNCTION {name}\(\).*?\$\$;', old_sql, flags=re.DOTALL)
    if match is None:
        raise RuntimeError(f'Original Garage integrity guard {name} not found.')
    return match.group(0).replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1)


REVERSE = "\n".join([
    'DROP TRIGGER garage_receipt_correction_immutable ON garage_garagereceiptcorrection;',
    'DROP TRIGGER garage_receipt_correction_scope ON garage_garagereceiptcorrection;',
    'DROP FUNCTION garage_receipt_correction_guard();',
    original_guard('garage_receipt_guard'),
    original_guard('garage_charge_receipt_floor'),
    original_guard('garage_assert_receipt_shape'),
    'DROP FUNCTION garage_net_received(uuid);',
])


class Migration(migrations.Migration):
    dependencies = [('garage', '0019_garagereceiptcorrection')]
    # On reverse, the history check runs before restoring the earlier guards.
    operations = [migrations.RunSQL(FORWARD, REVERSE), migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_corrections)]
