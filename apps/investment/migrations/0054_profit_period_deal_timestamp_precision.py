"""Keep Deal payment timestamps byte-identical to Python's UTC ISO format."""

from importlib import import_module

from django.db import migrations


PREVIOUS = import_module("apps.investment.migrations.0053_exit_profit_period_source_parity")
OLD_TIMESTAMP = (
    """trim(both '"' from to_json(p.effective_at AT TIME ZONE 'UTC')::text) || '+00:00'"""
)
# PostgreSQL's JSON timestamp drops trailing zeros. Python datetime.isoformat()
# keeps all six fractional digits when microseconds are nonzero.
UTC_TIMESTAMP = r"""
        to_char(p.effective_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS') ||
        CASE WHEN EXTRACT(MICROSECONDS FROM p.effective_at AT TIME ZONE 'UTC')::bigint % 1000000 = 0
             THEN ''
             ELSE to_char(p.effective_at AT TIME ZONE 'UTC', '.US')
        END || '+00:00'"""

if PREVIOUS.SOURCE_HASH_SQL.count(OLD_TIMESTAMP) != 1:
    raise RuntimeError("Expected exactly one Deal payment timestamp in the preceding source hash SQL.")


class Migration(migrations.Migration):
    dependencies = [("investment", "0053_exit_profit_period_source_parity")]
    operations = [
        migrations.RunSQL(
            PREVIOUS.SOURCE_HASH_SQL.replace(OLD_TIMESTAMP, UTC_TIMESTAMP, 1),
            reverse_sql=PREVIOUS.SOURCE_HASH_SQL,
        ),
    ]
