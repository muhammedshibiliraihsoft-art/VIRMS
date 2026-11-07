from django.db import migrations
from django.db.migrations.exceptions import IrreversibleError


def refuse_reverse_with_accounting_data(apps, schema_editor):
    model_names = (
        "AccountingAccount",
        "AccountingCategory",
        "AccountingEvent",
        "AccountingApplication",
        "AccountMovement",
        "AccountingIdempotencyRecord",
    )
    for model_name in model_names:
        model = apps.get_model("accounting", model_name)
        if model.objects.using(schema_editor.connection.alias).exists():
            raise IrreversibleError(
                "Company Accounting data exists; roll back application code "
                "without reversing Accounting migrations."
            )


FORWARD_SQL = """
CREATE FUNCTION accounting_reject_history_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Accounting history is append only'
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER accounting_event_immutable
BEFORE UPDATE OR DELETE ON accounting_accountingevent
FOR EACH ROW EXECUTE FUNCTION accounting_reject_history_mutation();
CREATE TRIGGER accounting_application_immutable
BEFORE UPDATE OR DELETE ON accounting_accountingapplication
FOR EACH ROW EXECUTE FUNCTION accounting_reject_history_mutation();
CREATE TRIGGER accounting_movement_immutable
BEFORE UPDATE OR DELETE ON accounting_accountmovement
FOR EACH ROW EXECUTE FUNCTION accounting_reject_history_mutation();
CREATE TRIGGER accounting_idempotency_immutable
BEFORE UPDATE OR DELETE ON accounting_accountingidempotencyrecord
FOR EACH ROW EXECUTE FUNCTION accounting_reject_history_mutation();

REVOKE UPDATE, DELETE, TRUNCATE ON accounting_accountingevent FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON accounting_accountingapplication FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON accounting_accountmovement FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON accounting_accountingidempotencyrecord FROM PUBLIC;

CREATE FUNCTION accounting_archive_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    current_balance numeric;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Accounting catalogue records cannot be deleted'
            USING ERRCODE = '23514';
    END IF;
    IF TG_TABLE_NAME = 'accounting_accountingaccount' THEN
        IF OLD.account_type IS DISTINCT FROM NEW.account_type THEN
            RAISE EXCEPTION 'Accounting account identity cannot be changed'
                USING ERRCODE = '23514';
        END IF;
    ELSE
        IF OLD.kind IS DISTINCT FROM NEW.kind THEN
            RAISE EXCEPTION 'Accounting category identity cannot be changed'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF OLD.tenant_id <> NEW.tenant_id
       OR OLD.created_by_id <> NEW.created_by_id
       OR OLD.label <> NEW.label
       OR OLD.normalized_label <> NEW.normalized_label
       OR OLD.updated_at <> NEW.updated_at AND NEW.is_active = OLD.is_active
       OR OLD.is_active IS DISTINCT FROM TRUE
       OR NEW.is_active IS DISTINCT FROM FALSE
       OR OLD.archived_at IS NOT NULL
       OR NEW.archived_at IS NULL
       OR OLD.archived_by_id IS NOT NULL
       OR NEW.archived_by_id IS NULL
       OR NEW.archived_at < OLD.created_at THEN
        RAISE EXCEPTION 'Accounting catalogue records may only be archived once'
            USING ERRCODE = '23514';
    END IF;
    IF TG_TABLE_NAME = 'accounting_accountingaccount' THEN
        PERFORM id FROM tenants_tenant WHERE id = OLD.tenant_id FOR UPDATE;
        IF EXISTS (
            SELECT 1 FROM accounting_accountmovement WHERE account_id = OLD.id
        ) THEN
            RAISE EXCEPTION 'An account with history cannot be archived'
                USING ERRCODE = '23514';
        END IF;
        SELECT COALESCE(SUM(delta), 0) INTO current_balance
        FROM accounting_accountmovement WHERE account_id = OLD.id;
        IF current_balance <> 0 THEN
            RAISE EXCEPTION 'An account with a nonzero balance cannot be archived'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER accounting_account_archive_guard
BEFORE UPDATE OR DELETE ON accounting_accountingaccount
FOR EACH ROW EXECUTE FUNCTION accounting_archive_guard();
CREATE TRIGGER accounting_category_archive_guard
BEFORE UPDATE OR DELETE ON accounting_accountingcategory
FOR EACH ROW EXECUTE FUNCTION accounting_archive_guard();
"""

REVERSE_SQL = """
DROP TRIGGER accounting_category_archive_guard ON accounting_accountingcategory;
DROP TRIGGER accounting_account_archive_guard ON accounting_accountingaccount;
DROP FUNCTION accounting_archive_guard();
DROP TRIGGER accounting_idempotency_immutable ON accounting_accountingidempotencyrecord;
DROP TRIGGER accounting_movement_immutable ON accounting_accountmovement;
DROP TRIGGER accounting_application_immutable ON accounting_accountingapplication;
DROP TRIGGER accounting_event_immutable ON accounting_accountingevent;
DROP FUNCTION accounting_reject_history_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0001_initial")]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=refuse_reverse_with_accounting_data,
        ),
    ]
