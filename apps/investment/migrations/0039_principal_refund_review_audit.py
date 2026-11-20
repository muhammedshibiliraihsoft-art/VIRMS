from django.db import migrations


FORWARD = """
CREATE FUNCTION principal_refund_review_audit_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM accounts_accountsecurityevent e
    WHERE e.action='investment.capital.recovery.confirm' AND e.company_id=NEW.tenant_id
      AND e.actor_id=NEW.actor_id AND e.reason=NEW.reason
      AND e.metadata->>'operation_id'=NEW.id::text
      AND e.metadata->>'source_version'=NEW.source_version
      AND (e.metadata->>'amount')::numeric=NEW.principal_amount) THEN
  RAISE EXCEPTION 'Principal refund review requires matching Accountant audit' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER principal_refund_review_audit AFTER INSERT ON investment_vehicleprincipalrefundreview
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION principal_refund_review_audit_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0038_mixed_refund_reserve_position")]
    operations = [migrations.RunSQL(
        FORWARD,
        "DROP TRIGGER principal_refund_review_audit ON investment_vehicleprincipalrefundreview; "
        "DROP FUNCTION principal_refund_review_audit_guard();",
    )]
