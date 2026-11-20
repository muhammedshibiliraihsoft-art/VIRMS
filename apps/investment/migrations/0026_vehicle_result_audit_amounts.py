from django.db import migrations


FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION investment_vehicle_result_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = 'investment.vehicle_result.confirm'
           AND event.company_id = NEW.tenant_id AND event.resource_id = NEW.id
           AND event.actor_id = NEW.confirmed_by_id AND event.reason = NEW.reason
           AND event.metadata->>'result_id' = NEW.id::text
           AND event.metadata->>'vehicle_id' = NEW.vehicle_id::text
           AND event.metadata->>'source_version' = NEW.source_version
           AND event.metadata->>'result_kind' = NEW.result_kind
           AND (event.metadata->>'result_amount')::numeric = NEW.result_amount
           AND (event.metadata->>'investor_share_amount')::numeric = NEW.investor_share_amount
           AND (event.metadata->>'company_share_amount')::numeric = NEW.company_share_amount
    ) THEN
        RAISE EXCEPTION 'Vehicle result confirmation requires matching amount audit evidence' USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END; $$;
"""

REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION investment_vehicle_result_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM accounts_accountsecurityevent event
         WHERE event.action = 'investment.vehicle_result.confirm'
           AND event.company_id = NEW.tenant_id AND event.resource_id = NEW.id
           AND event.actor_id = NEW.confirmed_by_id AND event.reason = NEW.reason
           AND event.metadata->>'result_id' = NEW.id::text
           AND event.metadata->>'vehicle_id' = NEW.vehicle_id::text
           AND event.metadata->>'source_version' = NEW.source_version
    ) THEN
        RAISE EXCEPTION 'Vehicle result confirmation requires matching audit evidence' USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END; $$;
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0025_result_kind_sign_guard")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
