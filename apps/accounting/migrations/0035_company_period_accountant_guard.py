from django.db import migrations


GUARD = r"""
CREATE FUNCTION accounting_company_period_identity_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE year_start date; july_start date; next_year_start date;
BEGIN
    year_start := make_date(EXTRACT(YEAR FROM NEW.period_start)::integer,1,1);
    july_start := make_date(EXTRACT(YEAR FROM NEW.period_start)::integer,7,1);
    next_year_start := make_date(EXTRACT(YEAR FROM NEW.period_start)::integer+1,1,1);
    IF (NEW.period_type='h1' AND (NEW.period_start<>year_start OR NEW.period_end<>july_start))
       OR (NEW.period_type='h2' AND (NEW.period_start<>july_start OR NEW.period_end<>next_year_start))
       OR (NEW.period_type='annual' AND (NEW.period_start<>year_start OR NEW.period_end<>next_year_start))
       OR NOT EXISTS (
          SELECT 1 FROM tenants_tenantmembership m JOIN accounts_companyrolegrant g ON g.membership_id=m.id
          WHERE m.tenant_id=NEW.tenant_id AND m.user_id=NEW.actor_id
            AND m.effective_from<=clock_timestamp() AND (m.effective_until IS NULL OR m.effective_until>clock_timestamp())
            AND g.role='accountant' AND g.branch_id IS NULL
            AND g.effective_from<=clock_timestamp() AND (g.effective_until IS NULL OR g.effective_until>clock_timestamp())
       ) THEN
        RAISE EXCEPTION 'Company period confirmation requires a Company Accountant and canonical period boundaries' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER accounting_company_period_identity_guard BEFORE INSERT ON accounting_companyperiodconfirmation
FOR EACH ROW EXECUTE FUNCTION accounting_company_period_identity_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0034_companyperiodconfirmation_carryforward_source"), ("accounts", "0012_scope_end_monotonic")]
    operations = [migrations.RunSQL(GUARD, reverse_sql="DROP FUNCTION accounting_company_period_identity_guard() CASCADE;")]
