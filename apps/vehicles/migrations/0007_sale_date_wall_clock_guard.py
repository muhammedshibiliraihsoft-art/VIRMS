from django.db import migrations


FORWARD_SQL = r"""
DO $$
DECLARE
    v_definition text;
BEGIN
    SELECT pg_get_functiondef('vehicles_phase5_record_insert_guard()'::regprocedure)
      INTO v_definition;
    IF position('NEW.sold_at > now()' IN v_definition) = 0 THEN
        RAISE EXCEPTION 'Expected Sale date guard was not found';
    END IF;
    EXECUTE replace(
        v_definition,
        'NEW.sold_at > now()',
        'NEW.sold_at > clock_timestamp()'
    );
END;
$$;
"""

REVERSE_SQL = r"""
DO $$
DECLARE
    v_definition text;
BEGIN
    SELECT pg_get_functiondef('vehicles_phase5_record_insert_guard()'::regprocedure)
      INTO v_definition;
    IF position('NEW.sold_at > clock_timestamp()' IN v_definition) = 0 THEN
        RAISE EXCEPTION 'Expected Sale date wall-clock guard was not found';
    END IF;
    EXECUTE replace(
        v_definition,
        'NEW.sold_at > clock_timestamp()',
        'NEW.sold_at > now()'
    );
END;
$$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("vehicles", "0006_vehiclesalereceipt_investment_module_revision"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
