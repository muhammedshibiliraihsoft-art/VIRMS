from importlib import import_module
from django.db import migrations


previous = import_module("apps.investment.migrations.0033_capital_recovery_review")
OLD = previous.POSITION_OLD.replace(previous.POSITION_CHECK, previous.POSITION_REVIEW)
REVIEW_CHECK = previous.POSITION_REVIEW
NEW_CHECK = """IF running>0 AND EXISTS (SELECT 1 FROM vehicles_vehiclesalecorrection x WHERE x.sale_id=item.sale_id AND x.created_at>item.first_recovery)
           AND NOT EXISTS (SELECT 1 FROM investment_vehicleprincipalrefundreview v
             JOIN vehicles_vehiclesalecorrection c ON c.id=v.sale_correction_id
             WHERE c.sale_id=item.sale_id AND v.tenant_id=company_uuid
               AND c.version=(SELECT MAX(version) FROM vehicles_vehiclesalecorrection WHERE sale_id=item.sale_id))
           AND NOT EXISTS (SELECT 1 FROM investment_vehiclecapitalrecoveryreview v
             JOIN investment_vehiclecapitalrecovery r ON r.id=v.recovery_id
             WHERE r.sale_id=item.sale_id AND v.tenant_id=company_uuid
               AND v.sale_correction_version=(SELECT COALESCE(MAX(version),0) FROM vehicles_vehiclesalecorrection WHERE sale_id=item.sale_id))
           THEN RETURN NULL; END IF;"""
OLD_BRANCH = "        IF running=0 THEN"
NEW_BRANCH = """        IF running>0 THEN
            SELECT v.principal_amount+v.principal_debited_before-principal_refunded INTO reviewed_due
              FROM investment_vehicleprincipalrefundreview v
              JOIN vehicles_vehiclesalecorrection c ON c.id=v.sale_correction_id
              WHERE c.sale_id=item.sale_id AND v.tenant_id=company_uuid
                AND c.version=(SELECT MAX(version) FROM vehicles_vehiclesalecorrection WHERE sale_id=item.sale_id);
            IF reviewed_due IS NOT NULL THEN
                IF reviewed_due<0 OR reviewed_due>GREATEST(received-refunded-sale_price,0) THEN RETURN NULL; END IF;
                principal_due := principal_due+reviewed_due;
            ELSIF received-refunded>sale_price THEN RETURN NULL;
            END IF;
        END IF;
        IF running=0 THEN"""
assert REVIEW_CHECK in OLD and OLD_BRANCH in OLD
NEW = OLD.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1).replace(
    "principal_refunded numeric;", "principal_refunded numeric; reviewed_due numeric;",
).replace(REVIEW_CHECK, NEW_CHECK).replace(OLD_BRANCH, NEW_BRANCH)


class Migration(migrations.Migration):
    dependencies = [("investment", "0037_principal_refund_review")]
    operations = [migrations.RunSQL(
        NEW, OLD.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1),
    )]
