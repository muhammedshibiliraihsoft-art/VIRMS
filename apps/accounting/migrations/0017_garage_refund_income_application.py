from django.db import migrations


FORWARD_SQL = r"""
CREATE OR REPLACE FUNCTION accounting_application_insert_guard()
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
    SELECT tenant_id, event_type, effect_sign
      INTO target_company, target_type, target_effect
      FROM accounting_accountingevent WHERE id = NEW.target_event_id;
    IF source_company IS DISTINCT FROM NEW.tenant_id
       OR target_company IS DISTINCT FROM NEW.tenant_id
       OR NOT ((source_type IN ('RECEIPT', 'VEHICLE_REFUND_IN', 'GARAGE_COST_REFUND') AND target_type = 'INCOME')
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
"""


REVERSE_SQL = r"""
CREATE OR REPLACE FUNCTION accounting_application_insert_guard()
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
    SELECT tenant_id, event_type, effect_sign
      INTO target_company, target_type, target_effect
      FROM accounting_accountingevent WHERE id = NEW.target_event_id;
    IF source_company IS DISTINCT FROM NEW.tenant_id
       OR target_company IS DISTINCT FROM NEW.tenant_id
       OR NOT ((source_type IN ('RECEIPT', 'VEHICLE_REFUND_IN') AND target_type = 'INCOME')
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
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0016_remove_accountingevent_acct_event_type_ck_and_more"),
        ("garage", "0026_refund_draft_fail_closed"),
    ]

    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
