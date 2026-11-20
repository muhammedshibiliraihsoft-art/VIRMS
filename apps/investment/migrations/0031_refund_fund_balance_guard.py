from django.db import migrations


FORWARD = """
CREATE FUNCTION principal_refund_fund_balance_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF investment_credit_gross_available(NEW.fund_credit_id) < 0 THEN
        RAISE EXCEPTION 'Principal refund cannot overdraw a Fund lot' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END; $$;
CREATE CONSTRAINT TRIGGER principal_refund_fund_balance
AFTER INSERT ON investment_vehicleprincipalrefunddebit
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION principal_refund_fund_balance_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0030_vehicle_capital_recovery")]
    operations = [migrations.RunSQL(
        FORWARD,
        "DROP TRIGGER principal_refund_fund_balance ON investment_vehicleprincipalrefunddebit; "
        "DROP FUNCTION principal_refund_fund_balance_guard();",
    )]
