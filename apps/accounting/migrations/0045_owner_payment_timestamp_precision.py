"""Keep Accounting period source timestamps byte-identical to Python's UTC ISO format."""

from importlib import import_module

from django.db import migrations


PREVIOUS = import_module("apps.accounting.migrations.0044_owner_payment_source_freshness")
OLD_TIMESTAMP = (
    """left(to_json(e.effective_at AT TIME ZONE 'UTC')::text,-1) || '+00:00"'"""
)
# PostgreSQL's JSON timestamp drops trailing fractional zeros. Python's
# datetime.isoformat() keeps all six fractional digits when microseconds are nonzero.
UTC_TIMESTAMP = r"""'"' || to_char(e.effective_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS') ||
        CASE WHEN EXTRACT(MICROSECONDS FROM e.effective_at AT TIME ZONE 'UTC')::bigint % 1000000 = 0
             THEN ''
             ELSE to_char(e.effective_at AT TIME ZONE 'UTC', '.US')
        END || '+00:00"'"""

if PREVIOUS.SOURCE_HASH_SQL.count(OLD_TIMESTAMP) != 1:
    raise RuntimeError("Expected exactly one Accounting event timestamp in the preceding source hash SQL.")


class Migration(migrations.Migration):
    dependencies = [("accounting", "0044_owner_payment_source_freshness")]
    operations = [
        migrations.RunSQL(
            PREVIOUS.SOURCE_HASH_SQL.replace(OLD_TIMESTAMP, UTC_TIMESTAMP, 1),
            reverse_sql=PREVIOUS.SOURCE_HASH_SQL,
        ),
    ]
