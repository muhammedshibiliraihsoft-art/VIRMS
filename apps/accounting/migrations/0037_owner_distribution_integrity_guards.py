from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION accounting_owner_split_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE actor_kind text; expected_owners integer; recipient_count integer; percentage_total numeric;
BEGIN
 SELECT account_kind INTO actor_kind FROM accounts_user WHERE id=NEW.actor_id;
 IF actor_kind IS DISTINCT FROM 'platform'
    OR NOT EXISTS (SELECT 1 FROM accounts_roleassignment r WHERE r.user_id=NEW.actor_id AND r.role='back_office' AND r.effective_from<=clock_timestamp() AND (r.effective_until IS NULL OR r.effective_until>clock_timestamp()))
    OR EXISTS (SELECT 1 FROM accounts_roleassignment r WHERE r.user_id=NEW.actor_id AND r.role<>'back_office')
    OR EXISTS (SELECT 1 FROM accounts_companyrolegrant g JOIN tenants_tenantmembership m ON m.id=g.membership_id WHERE m.user_id=NEW.actor_id)
    OR jsonb_typeof(NEW.recipients)<>'array' OR jsonb_array_length(NEW.recipients)=0
    OR EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.recipients) x WHERE NOT (x ? 'id' AND x ? 'percentage') OR (x->>'percentage')::numeric<0 OR (x->>'percentage')::numeric>100)
    OR (SELECT COUNT(DISTINCT x->>'id') FROM jsonb_array_elements(NEW.recipients) x)<>jsonb_array_length(NEW.recipients)
    OR (SELECT COALESCE(SUM((x->>'percentage')::numeric),0) FROM jsonb_array_elements(NEW.recipients) x)<>100 THEN
   RAISE EXCEPTION 'Owner split must be immutable Platform Back Office configuration with unique recipients totaling 100 percent' USING ERRCODE='23514';
 END IF;
 SELECT COUNT(*) INTO expected_owners FROM accounts_companyrolegrant g JOIN tenants_tenantmembership m ON m.id=g.membership_id JOIN accounts_user u ON u.id=m.user_id
 WHERE m.tenant_id=NEW.tenant_id AND g.role='owner' AND g.branch_id IS NULL AND u.is_active
   AND m.effective_from <= (NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata') AND (m.effective_until IS NULL OR m.effective_until>(NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata'))
   AND g.effective_from <= (NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata') AND (g.effective_until IS NULL OR g.effective_until>(NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata'));
 SELECT COUNT(*) INTO recipient_count FROM jsonb_array_elements(NEW.recipients) x JOIN accounts_user u ON u.id=(x->>'id')::uuid
 WHERE EXISTS (SELECT 1 FROM accounts_companyrolegrant g JOIN tenants_tenantmembership m ON m.id=g.membership_id
   WHERE m.tenant_id=NEW.tenant_id AND m.user_id=u.id AND g.role='owner' AND g.branch_id IS NULL
     AND m.effective_from <= (NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata') AND (m.effective_until IS NULL OR m.effective_until>(NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata'))
     AND g.effective_from <= (NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata') AND (g.effective_until IS NULL OR g.effective_until>(NEW.effective_from::timestamp AT TIME ZONE 'Asia/Kolkata')));
 IF expected_owners<>jsonb_array_length(NEW.recipients) OR recipient_count<>expected_owners THEN RAISE EXCEPTION 'Owner split recipients must match the Company Owners effective on that date' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE FUNCTION accounting_owner_split_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Owner split configuration is append-only' USING ERRCODE='23514'; END; $$;
CREATE FUNCTION accounting_owner_split_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent e WHERE e.action='accounting.owner_split.configure' AND e.company_id=NEW.tenant_id AND e.resource_type='accounting.owner_split' AND e.resource_id=NEW.id AND e.actor_id=NEW.actor_id AND e.reason=NEW.reason AND e.metadata->>'configuration_id'=NEW.id::text AND e.metadata->>'version'=NEW.version::text AND e.metadata->>'effective_from'=NEW.effective_from::text) THEN
   RAISE EXCEPTION 'Owner split configuration requires matching audit evidence' USING ERRCODE='23514';
 END IF; RETURN NULL;
END; $$;
CREATE TRIGGER accounting_owner_split_scope BEFORE INSERT ON accounting_ownerdistributionconfiguration FOR EACH ROW EXECUTE FUNCTION accounting_owner_split_guard();
CREATE TRIGGER accounting_owner_split_immutable_guard BEFORE UPDATE OR DELETE ON accounting_ownerdistributionconfiguration FOR EACH ROW EXECUTE FUNCTION accounting_owner_split_immutable();
CREATE CONSTRAINT TRIGGER accounting_owner_split_audit AFTER INSERT ON accounting_ownerdistributionconfiguration DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION accounting_owner_split_audit_guard();

CREATE FUNCTION accounting_period_owner_split_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE allocations_total numeric; allocation_count integer; config_recipients jsonb;
BEGIN
 IF NEW.distributable_amount=0 THEN
   IF NEW.owner_split_configuration_id IS NOT NULL OR jsonb_array_length(NEW.owner_allocation_snapshot)<>0 THEN RAISE EXCEPTION 'Zero distribution cannot carry Owner allocations' USING ERRCODE='23514'; END IF;
   RETURN NEW;
 END IF;
 SELECT recipients INTO config_recipients FROM accounting_ownerdistributionconfiguration c WHERE c.id=NEW.owner_split_configuration_id AND c.tenant_id=NEW.tenant_id AND c.effective_from<=NEW.period_start;
 IF config_recipients IS NULL OR jsonb_typeof(NEW.owner_allocation_snapshot)<>'array' OR jsonb_array_length(NEW.owner_allocation_snapshot)=0
    OR EXISTS (SELECT 1 FROM jsonb_array_elements(config_recipients) c WHERE NOT EXISTS (SELECT 1 FROM jsonb_array_elements(NEW.owner_allocation_snapshot) a WHERE a->>'recipient_id'=c->>'id' AND (a->>'percentage')::numeric=(c->>'percentage')::numeric))
    OR (SELECT COUNT(*) FROM jsonb_array_elements(config_recipients))<>(SELECT COUNT(*) FROM jsonb_array_elements(NEW.owner_allocation_snapshot)) THEN
   RAISE EXCEPTION 'Positive distribution requires an exact effective Owner split snapshot' USING ERRCODE='23514';
 END IF;
 SELECT COALESCE(SUM((a->>'amount')::numeric),0),COUNT(*) INTO allocations_total,allocation_count FROM jsonb_array_elements(NEW.owner_allocation_snapshot) a;
 IF allocations_total<>NEW.distributable_amount OR allocation_count=0 THEN RAISE EXCEPTION 'Owner allocations must equal the confirmed distributable amount' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER accounting_period_owner_split_scope BEFORE INSERT ON accounting_companyperiodconfirmation FOR EACH ROW EXECUTE FUNCTION accounting_period_owner_split_guard();
"""

REVERSE_SQL = r"""
DROP TRIGGER accounting_period_owner_split_scope ON accounting_companyperiodconfirmation;
DROP FUNCTION accounting_period_owner_split_guard();
DROP TRIGGER accounting_owner_split_audit ON accounting_ownerdistributionconfiguration;
DROP TRIGGER accounting_owner_split_immutable_guard ON accounting_ownerdistributionconfiguration;
DROP TRIGGER accounting_owner_split_scope ON accounting_ownerdistributionconfiguration;
DROP FUNCTION accounting_owner_split_audit_guard();
DROP FUNCTION accounting_owner_split_immutable();
DROP FUNCTION accounting_owner_split_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0036_owner_distribution_configuration"), ("accounts", "0012_scope_end_monotonic")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
