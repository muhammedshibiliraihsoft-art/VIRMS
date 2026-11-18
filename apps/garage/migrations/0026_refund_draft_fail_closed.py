from django.db import migrations


FORWARD = r"""
CREATE FUNCTION garage_refund_draft_reject() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_TABLE_NAME = 'garage_garagecustomercostrefund' THEN
        RAISE EXCEPTION 'Garage cost refund is not yet implemented' USING ERRCODE='23514';
    END IF;
    IF NEW.event_type = 'GARAGE_COST_REFUND' THEN
        RAISE EXCEPTION 'Garage cost refund is not yet implemented' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER garage_refund_draft_event BEFORE INSERT ON accounting_accountingevent FOR EACH ROW EXECUTE FUNCTION garage_refund_draft_reject();
CREATE TRIGGER garage_refund_draft_link BEFORE INSERT ON garage_garagecustomercostrefund FOR EACH ROW EXECUTE FUNCTION garage_refund_draft_reject();
"""

REVERSE = r"""
DROP TRIGGER garage_refund_draft_link ON garage_garagecustomercostrefund;
DROP TRIGGER garage_refund_draft_event ON accounting_accountingevent;
DROP FUNCTION garage_refund_draft_reject();
"""


class Migration(migrations.Migration):
    dependencies = [('garage', '0025_garagecustomercostrefund')]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
