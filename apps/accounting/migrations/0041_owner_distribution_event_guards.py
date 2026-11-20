from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION accounting_owner_distribution_event_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE event_uuid uuid; v_event_type text; v_event_amount numeric; v_event_effect integer; movement_count bigint; movement_sum numeric; payment_count bigint;
BEGIN
 IF TG_TABLE_NAME='accounting_accountingevent' THEN event_uuid:=NEW.id;
 ELSIF TG_TABLE_NAME='accounting_accountmovement' THEN event_uuid:=NEW.event_id;
 ELSE event_uuid:=NEW.accounting_event_id;
 END IF;
 SELECT e.event_type,e.amount,e.effect_sign INTO v_event_type,v_event_amount,v_event_effect FROM accounting_accountingevent e WHERE e.id=event_uuid;
 IF NOT FOUND THEN RETURN NULL; END IF;
 IF v_event_type<>'OWNER_DISTRIBUTION_PAYMENT' THEN RETURN NULL; END IF;
 SELECT COUNT(*),COALESCE(SUM(delta),0) INTO movement_count,movement_sum FROM accounting_accountmovement WHERE event_id=event_uuid;
 SELECT COUNT(*) INTO payment_count FROM accounting_ownerdistributionpayment WHERE accounting_event_id=event_uuid;
 IF v_event_effect<>1 OR movement_count<>1 OR movement_sum<>-v_event_amount OR payment_count<>1 THEN
   RAISE EXCEPTION 'Owner distribution event requires one matching payment record and exact cash outflow' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER accounting_owner_distribution_event_shape AFTER INSERT ON accounting_accountingevent DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION accounting_owner_distribution_event_guard();
CREATE CONSTRAINT TRIGGER accounting_owner_distribution_movement_shape AFTER INSERT ON accounting_accountmovement DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION accounting_owner_distribution_event_guard();
"""

REVERSE_SQL = r"""
DROP TRIGGER accounting_owner_distribution_movement_shape ON accounting_accountmovement;
DROP TRIGGER accounting_owner_distribution_event_shape ON accounting_accountingevent;
DROP FUNCTION accounting_owner_distribution_event_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0040_remove_accountingevent_acct_event_type_ck_and_more")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
