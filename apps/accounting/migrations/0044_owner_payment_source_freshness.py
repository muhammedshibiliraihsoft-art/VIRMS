"""Reject direct Owner payouts against a stale period source or Owner split."""

from importlib import import_module

from django.db import migrations


PREVIOUS = import_module("apps.accounting.migrations.0043_owner_payment_latest_confirmation_guard")

SOURCE_HASH_SQL = r"""
CREATE OR REPLACE FUNCTION accounting_period_event_source_version(
    company_id uuid, start_at timestamptz, end_at timestamptz, pending_payment_event_id uuid
) RETURNS text LANGUAGE sql STABLE AS $$
  SELECT encode(sha256(convert_to('[' || COALESCE(string_agg(
    '[' || to_json(e.id::text)::text || ',' || to_json(e.event_type)::text || ',' ||
    to_json(e.amount::text)::text || ',' || e.effect_sign::text || ',' ||
    left(to_json(e.effective_at AT TIME ZONE 'UTC')::text,-1) || '+00:00"' || ']', ',' ORDER BY e.id
  ), '') || ']', 'UTF8')), 'hex')
  FROM accounting_accountingevent e
  WHERE e.tenant_id=company_id AND e.effective_at>=start_at AND e.effective_at<end_at
    AND e.id IS DISTINCT FROM pending_payment_event_id
    AND NOT EXISTS (SELECT 1 FROM accounting_ownerdistributionpayment p WHERE p.accounting_event_id=e.id);
$$;

CREATE OR REPLACE FUNCTION accounting_period_confirmation_current(
    confirmation_id uuid, pending_payment_event_id uuid
) RETURNS boolean LANGUAGE plpgsql STABLE AS $$
DECLARE c record; predecessor_id uuid; split_id uuid;
BEGIN
  SELECT * INTO c FROM accounting_companyperiodconfirmation WHERE id=confirmation_id;
  IF NOT FOUND THEN RETURN false; END IF;
  IF EXISTS (SELECT 1 FROM accounting_companyperiodconfirmation newer
             WHERE newer.tenant_id=c.tenant_id AND newer.period_start=c.period_start
               AND newer.period_end=c.period_end AND newer.version>c.version) THEN
    RETURN false;
  END IF;
  IF c.source_version IS DISTINCT FROM accounting_period_event_source_version(
      c.tenant_id, c.period_start::timestamp AT TIME ZONE 'Asia/Kolkata',
      c.period_end::timestamp AT TIME ZONE 'Asia/Kolkata', pending_payment_event_id) THEN
    RETURN false;
  END IF;
  SELECT id INTO split_id FROM accounting_ownerdistributionconfiguration
    WHERE tenant_id=c.tenant_id AND effective_from<=c.period_start
    ORDER BY effective_from DESC,version DESC LIMIT 1;
  IF c.owner_split_configuration_id IS DISTINCT FROM
      (CASE WHEN c.distributable_amount>0 THEN split_id ELSE NULL END) THEN
    RETURN false;
  END IF;
  SELECT id INTO predecessor_id FROM accounting_companyperiodconfirmation prior
    WHERE prior.tenant_id=c.tenant_id AND prior.period_end<=c.period_start
      AND (prior.period_start,prior.period_end)<>(c.period_start,c.period_end)
    ORDER BY prior.period_end DESC,prior.version DESC LIMIT 1;
  IF c.carryforward_source_id IS DISTINCT FROM predecessor_id THEN RETURN false; END IF;
  RETURN predecessor_id IS NULL OR accounting_period_confirmation_current(predecessor_id,pending_payment_event_id);
END; $$;
"""

FRESHNESS_GUARD = r"""
 IF NOT accounting_period_confirmation_current(NEW.confirmation_id,NEW.accounting_event_id) THEN
    RAISE EXCEPTION 'Owner payment requires current Company period sources' USING ERRCODE='23514';
 END IF;
"""

ANCHOR = " SELECT COALESCE(SUM(p.amount),0) INTO paid\n"
FORWARD_SQL = SOURCE_HASH_SQL + PREVIOUS.FORWARD_SQL.replace(ANCHOR, FRESHNESS_GUARD + ANCHOR, 1)
REVERSE_SQL = PREVIOUS.FORWARD_SQL + "DROP FUNCTION accounting_period_confirmation_current(uuid,uuid); DROP FUNCTION accounting_period_event_source_version(uuid,timestamptz,timestamptz,uuid);"


class Migration(migrations.Migration):
    dependencies = [("accounting", "0043_owner_payment_latest_confirmation_guard")]
    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=REVERSE_SQL)]
