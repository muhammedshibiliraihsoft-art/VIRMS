from django.db import migrations, models


def classify_existing_superusers(apps, schema_editor):
    user = apps.get_model("accounts", "User")
    user.objects.using(schema_editor.connection.alias).filter(is_superuser=True).update(
        account_kind="platform"
    )


SQL = """
DO $$ BEGIN
 IF EXISTS (
  SELECT 1 FROM tenants_tenantmembership m
  JOIN accounts_user u ON u.id=m.user_id
  WHERE u.account_kind='company'
  GROUP BY m.user_id HAVING count(DISTINCT m.tenant_id)>1
 ) THEN
  RAISE EXCEPTION 'Existing multi-Company business accounts require reviewed mapping'
   USING ERRCODE='23514';
 END IF;
END $$;
CREATE FUNCTION virms_one_company_account_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE kind text;
BEGIN
 SELECT account_kind INTO kind FROM accounts_user WHERE id=NEW.user_id FOR UPDATE;
 IF kind='company' AND EXISTS (
  SELECT 1 FROM tenants_tenantmembership
  WHERE user_id=NEW.user_id AND tenant_id<>NEW.tenant_id
 ) THEN
  RAISE EXCEPTION 'Company account cannot join another Company'
   USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER virms_one_company_membership
 BEFORE INSERT OR UPDATE OF user_id, tenant_id ON tenants_tenantmembership
 FOR EACH ROW EXECUTE FUNCTION virms_one_company_account_guard();
CREATE FUNCTION virms_account_kind_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.account_kind IS DISTINCT FROM OLD.account_kind THEN
  RAISE EXCEPTION 'Account kind is immutable' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER virms_account_kind_immutable BEFORE UPDATE OF account_kind
 ON accounts_user FOR EACH ROW EXECUTE FUNCTION virms_account_kind_guard();
"""
REVERSE = """
DROP TRIGGER virms_account_kind_immutable ON accounts_user;
DROP FUNCTION virms_account_kind_guard();
DROP TRIGGER virms_one_company_membership ON tenants_tenantmembership;
DROP FUNCTION virms_one_company_account_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_session_activity"),
        ("tenants", "0002_platform_scope"),
    ]
    operations = [
        migrations.AddField(
            model_name="user",
            name="account_kind",
            field=models.CharField(
                choices=[("company", "Company"), ("platform", "Platform")],
                default="company",
                max_length=8,
            ),
        ),
        migrations.RunPython(classify_existing_superusers, migrations.RunPython.noop),
        migrations.RunSQL(SQL, REVERSE),
    ]
