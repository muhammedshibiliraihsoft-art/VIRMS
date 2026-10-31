from django.db import migrations

SQL = """
CREATE FUNCTION virms_audit_no_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Audit evidence is append only' USING ERRCODE='23514'; END $$;
CREATE TRIGGER virms_audit_no_mutation BEFORE UPDATE OR DELETE ON accounts_accountsecurityevent
FOR EACH ROW EXECUTE FUNCTION virms_audit_no_mutation();
REVOKE UPDATE, DELETE, TRUNCATE ON accounts_accountsecurityevent FROM PUBLIC;
"""


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_audit_foundation")]
    operations = [migrations.RunSQL(SQL, "DROP TRIGGER virms_audit_no_mutation ON accounts_accountsecurityevent; DROP FUNCTION virms_audit_no_mutation();")]
