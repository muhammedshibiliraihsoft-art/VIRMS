from django.db import migrations


FORWARD_SQL = r"""
DO $$
DECLARE
    v_definition text;
    v_old text;
    v_new text;
BEGIN
    SELECT pg_get_functiondef('vehicles_phase5_record_insert_guard()'::regprocedure)
      INTO v_definition;

    v_old := 'SELECT tenant_id, branch_id INTO v_company, v_branch
          FROM vehicles_vehiclesale WHERE id = NEW.sale_id FOR UPDATE;';
    v_new := 'SELECT tenant_id, branch_id, sale_price INTO v_company, v_branch, v_current_amount
          FROM vehicles_vehiclesale WHERE id = NEW.sale_id FOR UPDATE;
        SELECT sale_price INTO v_price FROM vehicles_vehiclesalecorrection
         WHERE sale_id = NEW.sale_id ORDER BY version DESC LIMIT 1;
        IF FOUND THEN v_current_amount := v_price; END IF;';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Buyer refund Sale lookup';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);

    v_old := 'NEW.amount <= 0 OR NEW.amount > v_received - v_sale_refunded THEN';
    v_new := 'NEW.amount <= 0 OR NEW.amount > v_received - v_sale_refunded - v_current_amount THEN';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Buyer refund payable check';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);

    v_old := '           OR NEW.sale_price < v_received - v_sale_refunded
           OR NOT vehicles_phase5_revision_enabled(NEW.vehicle_module_revision_id, NEW.tenant_id, ''vehicle_management'')';
    v_new := '           OR NOT vehicles_phase5_revision_enabled(NEW.vehicle_module_revision_id, NEW.tenant_id, ''vehicle_management'')';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Sale correction collected-amount restriction';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);
    EXECUTE v_definition;
END;
$$;
"""

REVERSE_SQL = r"""
DO $$
DECLARE
    v_definition text;
    v_old text;
    v_new text;
BEGIN
    SELECT pg_get_functiondef('vehicles_phase5_record_insert_guard()'::regprocedure)
      INTO v_definition;

    v_old := 'SELECT tenant_id, branch_id, sale_price INTO v_company, v_branch, v_current_amount
          FROM vehicles_vehiclesale WHERE id = NEW.sale_id FOR UPDATE;
        SELECT sale_price INTO v_price FROM vehicles_vehiclesalecorrection
         WHERE sale_id = NEW.sale_id ORDER BY version DESC LIMIT 1;
        IF FOUND THEN v_current_amount := v_price; END IF;';
    v_new := 'SELECT tenant_id, branch_id INTO v_company, v_branch
          FROM vehicles_vehiclesale WHERE id = NEW.sale_id FOR UPDATE;';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Buyer refund current-price lookup';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);

    v_old := 'NEW.amount <= 0 OR NEW.amount > v_received - v_sale_refunded - v_current_amount THEN';
    v_new := 'NEW.amount <= 0 OR NEW.amount > v_received - v_sale_refunded THEN';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Buyer refund payable check';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);

    v_old := '           OR NOT vehicles_phase5_revision_enabled(NEW.vehicle_module_revision_id, NEW.tenant_id, ''vehicle_management'')
           OR NOT vehicles_phase5_revision_enabled(NEW.accounting_module_revision_id, NEW.tenant_id, ''accounting'') THEN
            RAISE EXCEPTION ''Sale correction source, previous price, collected amount or enabled module revisions are invalid''';
    v_new := '           OR NEW.sale_price < v_received - v_sale_refunded
           OR NOT vehicles_phase5_revision_enabled(NEW.vehicle_module_revision_id, NEW.tenant_id, ''vehicle_management'')
           OR NOT vehicles_phase5_revision_enabled(NEW.accounting_module_revision_id, NEW.tenant_id, ''accounting'') THEN
            RAISE EXCEPTION ''Sale correction source, previous price, collected amount or enabled module revisions are invalid''';
    IF length(v_definition) - length(replace(v_definition, v_old, '')) <> length(v_old) THEN
        RAISE EXCEPTION 'Expected exactly one Sale correction guard';
    END IF;
    v_definition := replace(v_definition, v_old, v_new);
    EXECUTE v_definition;
END;
$$;
"""


class Migration(migrations.Migration):
    dependencies = [("vehicles", "0007_sale_date_wall_clock_guard")]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
