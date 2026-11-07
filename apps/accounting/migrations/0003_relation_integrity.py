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
CREATE FUNCTION accounting_event_insert_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    revision_company uuid;
    revision_module text;
    related_company uuid;
    related_kind text;
    related_type text;
    related_amount numeric;
    related_branch uuid;
    related_category uuid;
    related_effect integer;
    related_effective timestamptz;
    related_description text;
    related_source text;
BEGIN
    SELECT tenant_id, module_code INTO revision_company, revision_module
    FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
    IF revision_company IS DISTINCT FROM NEW.tenant_id OR revision_module <> 'accounting' THEN
        RAISE EXCEPTION 'Accounting event requires a same-Company Accounting revision'
            USING ERRCODE = '23514';
    END IF;
    IF NEW.branch_id IS NOT NULL THEN
        SELECT tenant_id INTO related_company FROM tenants_branch WHERE id = NEW.branch_id;
        IF related_company IS DISTINCT FROM NEW.tenant_id THEN
            RAISE EXCEPTION 'Accounting event Branch belongs to another Company'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF NEW.category_id IS NOT NULL THEN
        SELECT tenant_id, kind INTO related_company, related_kind
        FROM accounting_accountingcategory WHERE id = NEW.category_id;
        IF related_company IS DISTINCT FROM NEW.tenant_id
           OR related_kind IS DISTINCT FROM NEW.event_type THEN
            RAISE EXCEPTION 'Accounting event category scope or kind is invalid'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF NEW.reversal_of_id IS NOT NULL THEN
        SELECT tenant_id, event_type, amount, branch_id, category_id, effect_sign,
               effective_at, description, source_reference
          INTO related_company, related_type, related_amount, related_branch,
               related_category, related_effect, related_effective,
               related_description, related_source
        FROM accounting_accountingevent WHERE id = NEW.reversal_of_id;
        IF related_company IS DISTINCT FROM NEW.tenant_id
           OR related_type IS DISTINCT FROM NEW.event_type
           OR related_amount IS DISTINCT FROM NEW.amount
           OR related_branch IS DISTINCT FROM NEW.branch_id
           OR related_category IS DISTINCT FROM NEW.category_id
           OR related_effective IS DISTINCT FROM NEW.effective_at
           OR related_description IS DISTINCT FROM NEW.description
           OR related_source IS DISTINCT FROM NEW.source_reference
           OR related_effect <> 1
           OR NEW.effect_sign <> -1
           OR NEW.replaces_event_id IS NOT NULL
           OR NEW.correction_reason = '' THEN
            RAISE EXCEPTION 'Accounting event reversal does not match its immutable original'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF NEW.replaces_event_id IS NOT NULL THEN
        SELECT tenant_id, event_type, effect_sign INTO related_company, related_type, related_effect
        FROM accounting_accountingevent WHERE id = NEW.replaces_event_id;
        IF related_company IS DISTINCT FROM NEW.tenant_id
           OR related_type IS DISTINCT FROM NEW.event_type
           OR related_effect <> 1
           OR NEW.effect_sign <> 1
           OR NEW.reversal_of_id IS NOT NULL
           OR NEW.correction_reason = '' THEN
            RAISE EXCEPTION 'Accounting event replacement has an invalid predecessor'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER accounting_event_insert_guard
BEFORE INSERT ON accounting_accountingevent
FOR EACH ROW EXECUTE FUNCTION accounting_event_insert_guard();

CREATE FUNCTION accounting_application_insert_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    source_company uuid;
    target_company uuid;
    source_type text;
    target_type text;
    source_effect integer;
    source_reversal uuid;
    target_effect integer;
    original_source uuid;
    original_target uuid;
    original_amount numeric;
    original_effect integer;
BEGIN
    SELECT tenant_id, event_type, effect_sign, reversal_of_id
      INTO source_company, source_type, source_effect, source_reversal
    FROM accounting_accountingevent WHERE id = NEW.source_event_id;
    SELECT tenant_id, event_type, effect_sign INTO target_company, target_type, target_effect
    FROM accounting_accountingevent WHERE id = NEW.target_event_id;
    IF source_company IS DISTINCT FROM NEW.tenant_id
       OR target_company IS DISTINCT FROM NEW.tenant_id
       OR NOT ((source_type = 'RECEIPT' AND target_type = 'INCOME')
            OR (source_type = 'PAYMENT' AND target_type = 'EXPENSE'))
       OR source_effect <> 1
       OR source_reversal IS NOT NULL
       OR target_effect <> 1 THEN
        RAISE EXCEPTION 'Accounting application scope or event kinds are invalid'
            USING ERRCODE = '23514';
    END IF;
    IF NEW.module_revision_id IS NOT NULL THEN
        SELECT tenant_id, module_code INTO source_company, source_type
        FROM tenants_companymodulestate WHERE id = NEW.module_revision_id;
        IF source_company IS DISTINCT FROM NEW.tenant_id OR source_type <> 'accounting' THEN
            RAISE EXCEPTION 'Accounting application requires a same-Company Accounting revision'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF NEW.reversal_of_id IS NOT NULL THEN
        SELECT source_event_id, target_event_id, amount, effect_sign
          INTO original_source, original_target, original_amount, original_effect
        FROM accounting_accountingapplication WHERE id = NEW.reversal_of_id;
        IF original_source IS DISTINCT FROM NEW.source_event_id
           OR original_target IS DISTINCT FROM NEW.target_event_id
           OR original_amount IS DISTINCT FROM NEW.amount
           OR original_effect <> 1
           OR NEW.effect_sign <> -1
           OR NEW.reason = '' THEN
            RAISE EXCEPTION 'Accounting application reversal does not match its original'
                USING ERRCODE = '23514';
        END IF;
    ELSIF NEW.effect_sign <> 1 THEN
        RAISE EXCEPTION 'Accounting application reversal link is required'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER accounting_application_insert_guard
BEFORE INSERT ON accounting_accountingapplication
FOR EACH ROW EXECUTE FUNCTION accounting_application_insert_guard();

CREATE FUNCTION accounting_movement_insert_guard()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    event_company uuid;
    account_company uuid;
    v_event_type text;
BEGIN
    SELECT tenant_id, event_type INTO event_company, v_event_type
    FROM accounting_accountingevent WHERE id = NEW.event_id;
    SELECT tenant_id INTO account_company
    FROM accounting_accountingaccount WHERE id = NEW.account_id;
    IF event_company IS DISTINCT FROM NEW.tenant_id
       OR account_company IS DISTINCT FROM NEW.tenant_id
       OR v_event_type IN ('INCOME', 'EXPENSE') THEN
        RAISE EXCEPTION 'Accounting movement Company or event kind is invalid'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER accounting_movement_insert_guard
BEFORE INSERT ON accounting_accountmovement
FOR EACH ROW EXECUTE FUNCTION accounting_movement_insert_guard();

CREATE FUNCTION accounting_assert_event_shape()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_event_id uuid;
    v_source_id uuid;
    v_kind text;
    v_event_amount numeric;
    v_event_effect integer;
    v_event_reversal uuid;
    v_movement_count bigint;
    v_movement_sum numeric;
    v_positive_movement_count bigint;
    v_negative_movement_count bigint;
    v_application_total numeric;
    v_active_application_count bigint;
    v_active_target_count bigint;
BEGIN
    IF TG_TABLE_NAME = 'accounting_accountingevent' THEN
        v_event_id := NEW.id;
        v_source_id := NEW.id;
    ELSIF TG_TABLE_NAME = 'accounting_accountmovement' THEN
        v_event_id := NEW.event_id;
        v_source_id := NEW.event_id;
    ELSE
        v_source_id := NEW.source_event_id;
        v_event_id := NEW.source_event_id;
    END IF;
    SELECT event_type, amount, effect_sign, reversal_of_id
      INTO v_kind, v_event_amount, v_event_effect, v_event_reversal
    FROM accounting_accountingevent WHERE id = v_event_id;
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    IF v_kind IN ('RECEIPT', 'PAYMENT', 'OPENING_BALANCE', 'TRANSFER') THEN
        SELECT COUNT(*), COALESCE(SUM(delta), 0),
               COUNT(*) FILTER (WHERE delta > 0), COUNT(*) FILTER (WHERE delta < 0)
          INTO v_movement_count, v_movement_sum, v_positive_movement_count, v_negative_movement_count
        FROM accounting_accountmovement WHERE event_id = v_event_id;
        IF v_kind IN ('RECEIPT', 'PAYMENT', 'OPENING_BALANCE') AND v_movement_count <> 1 THEN
            RAISE EXCEPTION 'Accounting cash event requires exactly one movement'
                USING ERRCODE = '23514';
        END IF;
        IF v_kind = 'RECEIPT' AND v_movement_sum <> v_event_amount * v_event_effect THEN
            RAISE EXCEPTION 'Receipt movement does not match its event amount'
                USING ERRCODE = '23514';
        END IF;
        IF v_kind = 'PAYMENT' AND v_movement_sum <> -v_event_amount * v_event_effect THEN
            RAISE EXCEPTION 'Payment movement does not match its event amount'
                USING ERRCODE = '23514';
        END IF;
        IF v_kind = 'OPENING_BALANCE' AND v_event_reversal IS NOT NULL THEN
            IF NOT EXISTS (
                SELECT 1
                FROM accounting_accountmovement original_move
                JOIN accounting_accountmovement reversal_move
                  ON reversal_move.event_id = v_event_id
                 AND reversal_move.account_id = original_move.account_id
                WHERE original_move.event_id = v_event_reversal
                  AND reversal_move.delta = -original_move.delta
            ) THEN
                RAISE EXCEPTION 'Opening Balance reversal movement does not negate its original'
                    USING ERRCODE = '23514';
            END IF;
        ELSIF v_kind = 'OPENING_BALANCE' AND abs(v_movement_sum) <> v_event_amount THEN
            RAISE EXCEPTION 'Opening Balance movement magnitude does not match its event amount'
                USING ERRCODE = '23514';
        END IF;
        IF v_kind = 'TRANSFER' AND (
            v_movement_count <> 2 OR v_movement_sum <> 0
            OR v_positive_movement_count <> 1 OR v_negative_movement_count <> 1
            OR abs((SELECT delta FROM accounting_accountmovement WHERE event_id = v_event_id AND delta > 0)) <> v_event_amount
            OR abs((SELECT delta FROM accounting_accountmovement WHERE event_id = v_event_id AND delta < 0)) <> v_event_amount
        ) THEN
            RAISE EXCEPTION 'Transfer requires two equal and opposite account movements'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF v_kind IN ('RECEIPT', 'PAYMENT') AND v_event_effect = 1 THEN
        SELECT COALESCE(SUM(amount * effect_sign), 0)
          INTO v_application_total
        FROM accounting_accountingapplication WHERE source_event_id = v_source_id;
        SELECT COUNT(*), COUNT(DISTINCT active.target_event_id)
          INTO v_active_application_count, v_active_target_count
        FROM accounting_accountingapplication active
        WHERE active.source_event_id = v_source_id
          AND active.effect_sign = 1
          AND NOT EXISTS (
              SELECT 1 FROM accounting_accountingapplication reverse
              WHERE reverse.reversal_of_id = active.id
          );
        IF EXISTS (
            SELECT 1 FROM accounting_accountingevent WHERE reversal_of_id = v_source_id
        ) THEN
            IF v_application_total <> 0 OR v_active_application_count <> 0 THEN
                RAISE EXCEPTION 'Reversed cash event retains an active application'
                    USING ERRCODE = '23514';
            END IF;
        ELSIF v_application_total <> v_event_amount
           OR v_active_application_count <> 1
           OR v_active_target_count <> 1 THEN
            RAISE EXCEPTION 'Receipt/Payment requires one full application to one target'
                USING ERRCODE = '23514';
        END IF;
    ELSIF v_kind IN ('RECEIPT', 'PAYMENT') AND v_event_effect = -1 THEN
        -- Reversing a real cash event must also reverse its application in the
        -- same transaction. The immutable cash movement itself remains present.
        SELECT COALESCE(SUM(amount * effect_sign), 0)
          INTO v_application_total
        FROM accounting_accountingapplication
        WHERE source_event_id = v_event_reversal;
        SELECT COUNT(*)
          INTO v_active_application_count
        FROM accounting_accountingapplication active
        WHERE active.source_event_id = v_event_reversal
          AND active.effect_sign = 1
          AND NOT EXISTS (
              SELECT 1 FROM accounting_accountingapplication reverse
              WHERE reverse.reversal_of_id = active.id
          );
        IF v_application_total <> 0 OR v_active_application_count <> 0 THEN
            RAISE EXCEPTION 'Cash event reversal retains an active application'
                USING ERRCODE = '23514';
        END IF;
    ELSIF v_kind IN ('INCOME', 'EXPENSE') AND v_event_effect = -1 THEN
        -- An Income/Expense target cannot be reversed while any actual Receipt
        -- or Payment is still applied to it. Reallocation/reversal rows must be
        -- appended atomically with the target correction.
        SELECT COUNT(*)
          INTO v_active_application_count
        FROM accounting_accountingapplication active
        WHERE active.target_event_id = v_event_reversal
          AND active.effect_sign = 1
          AND NOT EXISTS (
              SELECT 1 FROM accounting_accountingapplication reverse
              WHERE reverse.reversal_of_id = active.id
          );
        IF v_active_application_count <> 0 THEN
            RAISE EXCEPTION 'Income/Expense reversal retains an active cash application'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER accounting_event_shape_deferred
AFTER INSERT ON accounting_accountingevent
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION accounting_assert_event_shape();
CREATE CONSTRAINT TRIGGER accounting_movement_shape_deferred
AFTER INSERT ON accounting_accountmovement
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION accounting_assert_event_shape();
CREATE CONSTRAINT TRIGGER accounting_application_shape_deferred
AFTER INSERT ON accounting_accountingapplication
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION accounting_assert_event_shape();
"""

REVERSE_SQL = """
DROP TRIGGER accounting_application_shape_deferred ON accounting_accountingapplication;
DROP TRIGGER accounting_movement_shape_deferred ON accounting_accountmovement;
DROP TRIGGER accounting_event_shape_deferred ON accounting_accountingevent;
DROP FUNCTION accounting_assert_event_shape();
DROP TRIGGER accounting_movement_insert_guard ON accounting_accountmovement;
DROP FUNCTION accounting_movement_insert_guard();
DROP TRIGGER accounting_application_insert_guard ON accounting_accountingapplication;
DROP FUNCTION accounting_application_insert_guard();
DROP TRIGGER accounting_event_insert_guard ON accounting_accountingevent;
DROP FUNCTION accounting_event_insert_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("accounting", "0002_history_and_archive_guards")]

    operations = [
        migrations.RunSQL(FORWARD_SQL, REVERSE_SQL),
        migrations.RunPython(
            migrations.RunPython.noop,
            reverse_code=refuse_reverse_with_accounting_data,
        ),
    ]
