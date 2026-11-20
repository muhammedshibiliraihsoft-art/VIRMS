from django.db import migrations


FORWARD = """
CREATE FUNCTION investment_profit_payment_recovery_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE result investment_vehicleresultconfirmation%ROWTYPE;
        investor_capital numeric; company_capital numeric;
        recovered_principal numeric; recovered_company numeric;
        price numeric; collected numeric;
BEGIN
    -- Share the domain mutation's Company serialization for direct SQL writes.
    PERFORM 1 FROM tenants_tenant WHERE id=NEW.tenant_id FOR UPDATE;
    SELECT * INTO result FROM investment_vehicleresultconfirmation
      WHERE id=NEW.result_confirmation_id AND tenant_id=NEW.tenant_id;
    IF NOT FOUND OR result.investor_id IS DISTINCT FROM NEW.investor_id
       OR result.result_kind <> 'PROFIT'
       OR EXISTS (SELECT 1 FROM investment_vehicleresultconfirmation r
          WHERE r.tenant_id=NEW.tenant_id AND r.sale_id=result.sale_id AND r.version>result.version) THEN
        RAISE EXCEPTION 'Profit payment requires the latest same-Investor positive result' USING ERRCODE='23514';
    END IF;
    PERFORM 1 FROM vehicles_vehiclesale WHERE id=result.sale_id FOR UPDATE;
    SELECT
        COALESCE((SELECT c.investor_fund_amount FROM vehicles_vehiclepurchasecorrection c
          WHERE c.purchase_id=p.id ORDER BY c.version DESC,c.id DESC LIMIT 1),p.investor_fund_amount),
        COALESCE((SELECT c.running_capital_amount FROM vehicles_vehiclepurchasecorrection c
          WHERE c.purchase_id=p.id ORDER BY c.version DESC,c.id DESC LIMIT 1),p.running_capital_amount)
      INTO investor_capital,company_capital FROM vehicles_vehiclepurchase p
      WHERE p.id=result.purchase_id AND p.tenant_id=NEW.tenant_id;
    SELECT investor_capital+COALESCE(SUM(COALESCE(
        (SELECT c.investor_fund_amount FROM vehicles_vehicleexpensecorrection c
          WHERE c.expense_id=e.id ORDER BY c.version DESC,c.id DESC LIMIT 1),e.investor_fund_amount)),0),
        company_capital+COALESCE(SUM(COALESCE(
        (SELECT c.running_capital_amount FROM vehicles_vehicleexpensecorrection c
          WHERE c.expense_id=e.id ORDER BY c.version DESC,c.id DESC LIMIT 1),e.running_capital_amount)),0)
      INTO investor_capital,company_capital FROM vehicles_vehicleexpense e
      WHERE e.vehicle_id=result.vehicle_id AND e.tenant_id=NEW.tenant_id;
    SELECT COALESCE(SUM(investor_principal),0),COALESCE(SUM(running_capital),0)
      INTO recovered_principal,recovered_company FROM investment_vehiclecapitalrecovery
      WHERE sale_id=result.sale_id AND tenant_id=NEW.tenant_id;
    SELECT COALESCE((SELECT c.sale_price FROM vehicles_vehiclesalecorrection c
        WHERE c.sale_id=s.id ORDER BY c.version DESC,c.id DESC LIMIT 1),s.sale_price)
      INTO price FROM vehicles_vehiclesale s WHERE s.id=result.sale_id;
    SELECT (SELECT COALESCE(SUM(amount),0) FROM vehicles_vehiclesalereceipt WHERE sale_id=result.sale_id)
        - (SELECT COALESCE(SUM(amount),0) FROM vehicles_vehiclesalerefund WHERE sale_id=result.sale_id)
      INTO collected;
    IF investor_capital IS NULL OR company_capital IS NULL
       OR recovered_principal <> investor_capital OR recovered_company <> company_capital
       OR collected IS DISTINCT FROM price
       OR EXISTS (SELECT 1 FROM vehicles_vehiclesalecorrection c
          WHERE c.sale_id=result.sale_id AND c.created_at>result.created_at)
       OR EXISTS (SELECT 1 FROM vehicles_vehiclepurchasecorrection c
          WHERE c.purchase_id=result.purchase_id AND c.created_at>result.created_at)
       OR EXISTS (SELECT 1 FROM vehicles_vehicleexpense e
          LEFT JOIN vehicles_vehicleexpensecorrection c ON c.expense_id=e.id
          WHERE e.vehicle_id=result.vehicle_id AND (e.created_at>result.created_at OR c.created_at>result.created_at))
       OR EXISTS (SELECT 1 FROM vehicles_vehiclesalereceipt r
          WHERE r.sale_id=result.sale_id AND r.created_at>result.created_at)
       OR EXISTS (SELECT 1 FROM vehicles_vehiclesalerefund r
          WHERE r.sale_id=result.sale_id AND r.created_at>result.created_at)
       OR NOT EXISTS (SELECT 1 FROM investment_vehiclecapitalrecovery r
          WHERE r.tenant_id=NEW.tenant_id AND r.sale_id=result.sale_id
            AND r.investor_id=NEW.investor_id AND r.source_version=result.source_version) THEN
        RAISE EXCEPTION 'Profit payment requires current capital recovery and resolved Buyer balances'
          USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER investment_profit_payment_recovery
BEFORE INSERT ON investment_investorvehicleprofitpayment
FOR EACH ROW EXECUTE FUNCTION investment_profit_payment_recovery_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("investment", "0031_refund_fund_balance_guard")]
    operations = [migrations.RunSQL(
        FORWARD,
        "DROP TRIGGER investment_profit_payment_recovery ON investment_investorvehicleprofitpayment; "
        "DROP FUNCTION investment_profit_payment_recovery_guard();",
    )]
