from importlib import import_module
import re

from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_corrections(apps, schema_editor):
    if apps.get_model('garage', 'GarageCustomerCostPaymentCorrection').objects.using(schema_editor.connection.alias).exists():
        raise IrreversibleError('Garage cost payment correction history exists; retain integrity guards.')


def old_function(name):
    source = import_module('apps.garage.migrations.0022_customer_cost_payment_integrity').FORWARD
    match = re.search(rf'CREATE FUNCTION {name}\(\).*?\$\$;', source, re.DOTALL)
    if match is None:
        raise RuntimeError(f'Original {name} not found')
    return match.group().replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1)


original_payment_guard = old_function('garage_cost_payment_guard')
original_floor = old_function('garage_cost_payment_floor')
original_shape = old_function('garage_cost_payment_shape')
sum_query = '''SELECT COALESCE(SUM(e.amount), 0) INTO paid FROM garage_garagecustomercostpayment p
      JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=NEW.cost_id;'''
if sum_query not in original_payment_guard or sum_query not in original_floor:
    raise RuntimeError('Expected prior cost payment guards changed')

FORWARD = r"""
CREATE FUNCTION garage_cost_net_paid(cid uuid) RETURNS numeric LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT SUM(e.amount) FROM garage_garagecustomercostpayment p JOIN accounting_accountingevent e ON e.id=p.event_id WHERE p.cost_id=cid),0)
       + COALESCE((SELECT SUM(COALESCE(repl.amount,0)-prev.amount) FROM garage_garagecustomercostpaymentcorrection c
          JOIN garage_garagecustomercostpayment p ON p.id=c.payment_id
          JOIN accounting_accountingevent prev ON prev.id=c.previous_event_id
          LEFT JOIN accounting_accountingevent repl ON repl.id=c.replacement_event_id WHERE p.cost_id=cid),0)
$$;
""" + original_payment_guard.replace(sum_query, 'SELECT garage_cost_net_paid(NEW.cost_id) INTO paid;') + '\n' + original_floor.replace(sum_query, 'SELECT garage_cost_net_paid(NEW.cost_id) INTO paid;') + r"""

CREATE FUNCTION garage_cost_payment_correction_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE jid uuid; cid uuid; company_id uuid; branch_id uuid; root_event uuid; rev_company uuid; rev_code text;
        old_event record; reversal record; replacement record; old_account uuid; reverse_account uuid;
        latest integer; last_replacement uuid; new_total numeric; cost_amount numeric;
BEGIN
    SELECT j.id, c.id, j.tenant_id, j.branch_id, p.event_id INTO jid, cid, company_id, branch_id, root_event
      FROM garage_garagecustomercostpayment p JOIN garage_garagecustomercost c ON c.id=p.cost_id
      JOIN garage_garagejob j ON j.id=c.job_id WHERE p.id=NEW.payment_id FOR UPDATE OF j;
    SELECT tenant_id, module_code INTO rev_company, rev_code FROM tenants_companymodulestate WHERE id=NEW.module_revision_id;
    SELECT COALESCE(MAX(version),0) INTO latest FROM garage_garagecustomercostpaymentcorrection WHERE payment_id=NEW.payment_id;
    IF latest>0 THEN SELECT replacement_event_id INTO last_replacement FROM garage_garagecustomercostpaymentcorrection WHERE payment_id=NEW.payment_id AND version=latest; END IF;
    SELECT * INTO old_event FROM accounting_accountingevent WHERE id=NEW.previous_event_id;
    SELECT * INTO reversal FROM accounting_accountingevent WHERE id=NEW.reversal_event_id;
    IF company_id IS NULL OR rev_company IS DISTINCT FROM company_id OR rev_code IS DISTINCT FROM 'garage'
       OR NEW.version <> latest+1 OR (latest=0 AND NEW.previous_event_id IS DISTINCT FROM root_event)
       OR (latest>0 AND (last_replacement IS NULL OR NEW.previous_event_id IS DISTINCT FROM last_replacement))
       OR old_event.tenant_id IS DISTINCT FROM company_id OR old_event.branch_id IS DISTINCT FROM branch_id
       OR old_event.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' OR old_event.effect_sign <> 1
       OR reversal.reversal_of_id IS DISTINCT FROM NEW.previous_event_id OR reversal.actor_id IS DISTINCT FROM NEW.actor_id
       OR reversal.correction_reason IS DISTINCT FROM NEW.reason THEN
        RAISE EXCEPTION 'Garage cost payment correction scope or reversal invalid' USING ERRCODE='23514';
    END IF;
    SELECT account_id INTO old_account FROM accounting_accountmovement WHERE event_id=NEW.previous_event_id;
    SELECT account_id INTO reverse_account FROM accounting_accountmovement WHERE event_id=NEW.reversal_event_id;
    IF old_account IS NULL OR reverse_account IS DISTINCT FROM old_account THEN RAISE EXCEPTION 'Garage cost reversal account invalid' USING ERRCODE='23514'; END IF;
    new_total := garage_cost_net_paid(cid)-old_event.amount;
    IF NEW.replacement_event_id IS NOT NULL THEN
        SELECT * INTO replacement FROM accounting_accountingevent WHERE id=NEW.replacement_event_id;
        IF replacement.replaces_event_id IS DISTINCT FROM NEW.previous_event_id OR replacement.actor_id IS DISTINCT FROM NEW.actor_id
           OR replacement.tenant_id IS DISTINCT FROM company_id OR replacement.branch_id IS DISTINCT FROM branch_id
           OR replacement.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' OR replacement.effect_sign <> 1
           OR replacement.source_reference IS DISTINCT FROM old_event.source_reference OR replacement.correction_reason IS DISTINCT FROM NEW.reason THEN
            RAISE EXCEPTION 'Garage cost replacement invalid' USING ERRCODE='23514';
        END IF;
        new_total := new_total+replacement.amount;
    END IF;
    SELECT COALESCE((SELECT amount FROM garage_garagecustomercostcorrection WHERE cost_id=cid ORDER BY version DESC LIMIT 1),
                    (SELECT amount FROM garage_garagecustomercost WHERE id=cid)) INTO cost_amount;
    IF cost_amount IS NULL OR new_total < 0 OR new_total > cost_amount THEN RAISE EXCEPTION 'Garage cost payment exceeds cost' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_cost_payment_correction_scope BEFORE INSERT ON garage_garagecustomercostpaymentcorrection FOR EACH ROW EXECUTE FUNCTION garage_cost_payment_correction_guard();
CREATE TRIGGER garage_cost_payment_correction_immutable BEFORE UPDATE OR DELETE ON garage_garagecustomercostpaymentcorrection FOR EACH ROW EXECUTE FUNCTION garage_history_retained();

CREATE OR REPLACE FUNCTION garage_cost_payment_shape() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE eid uuid; ev record; originals integer; reversals integer; replacements integer; moves integer; total numeric;
BEGIN
    IF TG_TABLE_NAME='accounting_accountingevent' THEN eid:=NEW.id; ELSE eid:=NEW.event_id; END IF;
    SELECT * INTO ev FROM accounting_accountingevent WHERE id=eid;
    IF ev.event_type IS DISTINCT FROM 'GARAGE_COST_PAYMENT' THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO originals FROM garage_garagecustomercostpayment WHERE event_id=eid;
    SELECT COUNT(*) INTO reversals FROM garage_garagecustomercostpaymentcorrection WHERE reversal_event_id=eid;
    SELECT COUNT(*) INTO replacements FROM garage_garagecustomercostpaymentcorrection WHERE replacement_event_id=eid;
    SELECT COUNT(*),COALESCE(SUM(delta),0) INTO moves,total FROM accounting_accountmovement WHERE event_id=eid AND tenant_id=ev.tenant_id;
    IF originals+reversals+replacements<>1 OR moves<>1 OR total<>-ev.amount*ev.effect_sign
       OR (originals=1 AND (ev.effect_sign<>1 OR ev.reversal_of_id IS NOT NULL OR ev.replaces_event_id IS NOT NULL))
       OR (reversals=1 AND (ev.effect_sign<>-1 OR ev.reversal_of_id IS NULL OR ev.replaces_event_id IS NOT NULL))
       OR (replacements=1 AND (ev.effect_sign<>1 OR ev.replaces_event_id IS NULL OR ev.reversal_of_id IS NOT NULL)) THEN
        RAISE EXCEPTION 'Garage cost payment requires one typed source and exact Cash/Bank movement' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
"""

REVERSE = '\n'.join([
    'DROP TRIGGER garage_cost_payment_correction_immutable ON garage_garagecustomercostpaymentcorrection;',
    'DROP TRIGGER garage_cost_payment_correction_scope ON garage_garagecustomercostpaymentcorrection;',
    'DROP FUNCTION garage_cost_payment_correction_guard();', original_shape, original_payment_guard, original_floor,
    'DROP FUNCTION garage_cost_net_paid(uuid);',
])


class Migration(migrations.Migration):
    dependencies = [('garage', '0023_garagecustomercostpaymentcorrection')]
    operations = [migrations.RunSQL(FORWARD, REVERSE), migrations.RunPython(migrations.RunPython.noop, refuse_reverse_with_corrections)]
