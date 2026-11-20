from django.db import migrations


FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION investment_exit_extension_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent e
                   JOIN investment_investorexitrequest r ON r.id = NEW.exit_request_id
                   WHERE e.action = 'investment.exit.notice.extend' AND e.company_id = NEW.tenant_id
                     AND e.resource_id = NEW.id AND e.actor_id = NEW.actor_id AND e.reason = NEW.reason
                     AND e.metadata->>'exit_request_id' = NEW.exit_request_id::text
                     AND e.metadata->>'extension_id' = NEW.id::text
                     AND e.metadata->>'investor_id' = r.investor_id::text
                     AND e.metadata->>'version' = NEW.version::text
                     AND (e.metadata->>'previous_deadline')::timestamptz = NEW.previous_deadline
                     AND (e.metadata->>'deadline')::timestamptz = NEW.deadline) THEN
        RAISE EXCEPTION 'Exit notice extension requires matching audit evidence' USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END; $$;
"""

REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION investment_exit_extension_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent e
                   WHERE e.action = 'investment.exit.notice.extend' AND e.company_id = NEW.tenant_id
                     AND e.resource_id = NEW.id AND e.actor_id = NEW.actor_id AND e.reason = NEW.reason
                     AND e.metadata->>'exit_request_id' = NEW.exit_request_id::text
                     AND e.metadata->>'extension_id' = NEW.id::text) THEN
        RAISE EXCEPTION 'Exit notice extension requires audit evidence' USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END; $$;
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0023_exit_notice_extension_guards")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
