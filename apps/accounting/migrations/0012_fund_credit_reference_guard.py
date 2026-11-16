from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r"""
CREATE TABLE accounting_fund_credit_reference_key (
    credit_id uuid PRIMARY KEY REFERENCES investment_investorfundcredit(id),
    tenant_id uuid NOT NULL REFERENCES tenants_tenant(id),
    account_id uuid NOT NULL REFERENCES accounting_accountingaccount(id),
    normalized_reference text NOT NULL,
    CONSTRAINT fund_credit_reference_uq UNIQUE (tenant_id, account_id, normalized_reference)
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM investment_investorfundcredit c
        LEFT JOIN accounting_accountingsourcelink l ON l.investor_fund_credit_id = c.id
        LEFT JOIN accounting_accountmovement m ON m.event_id = l.event_id
        GROUP BY c.id HAVING count(m.id) <> 1
    ) THEN
        RAISE EXCEPTION 'Fund credit reference migration requires exactly one linked account movement per credit';
    END IF;
END $$;

INSERT INTO accounting_fund_credit_reference_key (credit_id, tenant_id, account_id, normalized_reference)
SELECT c.id, c.tenant_id, m.account_id, lower(btrim(c.reference))
FROM investment_investorfundcredit c
JOIN accounting_accountingsourcelink l ON l.investor_fund_credit_id = c.id
JOIN accounting_accountmovement m ON m.event_id = l.event_id;

CREATE FUNCTION accounting_fund_credit_reference_insert() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.investor_fund_credit_id IS NOT NULL THEN
        INSERT INTO accounting_fund_credit_reference_key (credit_id, tenant_id, account_id, normalized_reference)
        SELECT c.id, c.tenant_id, m.account_id, lower(btrim(c.reference))
        FROM investment_investorfundcredit c
        JOIN accounting_accountmovement m ON m.event_id = NEW.event_id
        WHERE c.id = NEW.investor_fund_credit_id AND m.tenant_id = c.tenant_id;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Fund credit requires its Accounting movement before the source link' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE FUNCTION accounting_fund_credit_reference_validate() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM investment_investorfundcredit c
        JOIN accounting_accountingsourcelink l ON l.investor_fund_credit_id = c.id
        JOIN accounting_accountmovement m ON m.event_id = l.event_id
        WHERE c.id = NEW.credit_id AND c.tenant_id = NEW.tenant_id
          AND m.tenant_id = NEW.tenant_id AND m.account_id = NEW.account_id
          AND NEW.normalized_reference = lower(btrim(c.reference))
    ) THEN
        RAISE EXCEPTION 'Fund credit reference key must match its linked movement' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER accounting_fund_credit_reference_validate_guard
BEFORE INSERT ON accounting_fund_credit_reference_key
FOR EACH ROW EXECUTE FUNCTION accounting_fund_credit_reference_validate();
CREATE TRIGGER accounting_fund_credit_reference_guard
AFTER INSERT ON accounting_accountingsourcelink
FOR EACH ROW EXECUTE FUNCTION accounting_fund_credit_reference_insert();
CREATE TRIGGER accounting_fund_credit_reference_immutable
BEFORE UPDATE OR DELETE ON accounting_fund_credit_reference_key
FOR EACH ROW EXECUTE FUNCTION accounting_reject_history_mutation();
"""

REVERSE_SQL = r"""
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM accounting_fund_credit_reference_key) THEN
        RAISE EXCEPTION 'Fund credit reference history exists; this guard cannot be reversed';
    END IF;
END $$;
DROP TRIGGER accounting_fund_credit_reference_immutable ON accounting_fund_credit_reference_key;
DROP TRIGGER accounting_fund_credit_reference_guard ON accounting_accountingsourcelink;
DROP FUNCTION accounting_fund_credit_reference_insert();
DROP TRIGGER accounting_fund_credit_reference_validate_guard ON accounting_fund_credit_reference_key;
DROP FUNCTION accounting_fund_credit_reference_validate();
DROP TABLE accounting_fund_credit_reference_key;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0011_vehicle_refund_income_applications"),
        ("investment", "0007_fund_credit_attribution_correction"),
    ]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
        state_operations=[migrations.CreateModel(
            name="FundCreditReferenceKey",
            fields=[
                ("credit", models.OneToOneField(primary_key=True, serialize=False, on_delete=django.db.models.deletion.PROTECT, related_name="reference_key", to="investment.investorfundcredit")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="tenants.tenant")),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="accounting.accountingaccount")),
                ("normalized_reference", models.TextField()),
            ],
            options={"db_table": "accounting_fund_credit_reference_key", "constraints": [models.UniqueConstraint(fields=("tenant", "account", "normalized_reference"), name="fund_credit_reference_uq")]},
        )],
    )]
