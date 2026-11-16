from django.db import migrations, models


FORWARD_SQL = r"""
DO $$
DECLARE definition text;
BEGIN
    SELECT pg_get_functiondef('vehicle_expense_guard()'::regprocedure) INTO definition;
    IF position('IF NEW.investor_fund_amount > 0 THEN' in definition) = 0 THEN
        RAISE EXCEPTION 'Expected Vehicle Expense Investor guard not found';
    END IF;
    definition := replace(definition, 'IF NEW.investor_fund_amount > 0 THEN', 'IF NEW.investor_id IS NOT NULL THEN');
    EXECUTE definition;
END $$;
"""
REVERSE_SQL = r"""
DO $$
DECLARE definition text;
BEGIN
    IF EXISTS (SELECT 1 FROM vehicles_vehicleexpense WHERE investor_id IS NOT NULL AND investor_fund_amount = 0) THEN
        RAISE EXCEPTION 'Investor-linked Expense history exists; guard cannot be reversed';
    END IF;
    SELECT pg_get_functiondef('vehicle_expense_guard()'::regprocedure) INTO definition;
    definition := replace(definition, 'IF NEW.investor_id IS NOT NULL THEN', 'IF NEW.investor_fund_amount > 0 THEN');
    EXECUTE definition;
END $$;
"""

class Migration(migrations.Migration):
    dependencies = [("vehicles", "0008_sale_refund_payable_guard")]
    operations = [
        migrations.RemoveConstraint(model_name="vehicleexpense", name="vehicle_expense_investor_ck"),
        migrations.AddConstraint(model_name="vehicleexpense", constraint=models.CheckConstraint(
            condition=(models.Q(investor_fund_amount=0, investor__isnull=True, investment_module_revision__isnull=True)
                       | models.Q(investor_fund_amount__gte=0, investor__isnull=False, investment_module_revision__isnull=False)),
            name="vehicle_expense_investor_ck")),
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
    ]
