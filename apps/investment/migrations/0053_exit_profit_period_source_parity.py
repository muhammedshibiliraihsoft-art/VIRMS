"""Recompute the confirmed Investor period source hash at the DB payout boundary."""

from importlib import import_module

from django.db import migrations


PREVIOUS = import_module("apps.investment.migrations.0052_exit_profit_calendar_source_guard")

SOURCE_HASH_SQL = r"""
CREATE OR REPLACE FUNCTION investment_canonical_source_json(value jsonb)
RETURNS text LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    key text;
    element jsonb;
    parts text[] := ARRAY[]::text[];
BEGIN
    IF jsonb_typeof(value) = 'object' THEN
        FOR key IN SELECT jsonb_object_keys(value) ORDER BY 1 LOOP
            parts := array_append(parts, to_json(key)::text || ':' || investment_canonical_source_json(value -> key));
        END LOOP;
        RETURN '{' || array_to_string(parts, ',') || '}';
    ELSIF jsonb_typeof(value) = 'array' THEN
        FOR element IN SELECT a.value FROM jsonb_array_elements(value) WITH ORDINALITY AS a(value, n) ORDER BY a.n LOOP
            parts := array_append(parts, investment_canonical_source_json(element));
        END LOOP;
        RETURN '[' || array_to_string(parts, ',') || ']';
    END IF;
    RETURN value::text;
END;
$$;

CREATE OR REPLACE FUNCTION investment_profit_period_source_version(reconciliation_id uuid)
RETURNS text LANGUAGE sql STABLE AS $$
WITH target AS (
    SELECT r.* FROM investment_investorprofitperiodreconciliation r WHERE r.id=reconciliation_id
), current_results AS (
    SELECT DISTINCT ON (v.sale_id) v.id,v.sale_id,v.vehicle_id,v.created_at,v.investor_id,v.source_version,
           v.result_kind,v.investor_share_amount,
           (s.sold_at AT TIME ZONE 'Asia/Kolkata')::date AS sale_date
    FROM investment_vehicleresultconfirmation v
    JOIN vehicles_vehiclesale s ON s.id=v.sale_id
    JOIN vehicles_vehiclepurchase p ON p.id=v.purchase_id
    JOIN target t ON t.tenant_id=v.tenant_id AND t.investor_id=v.investor_id
    WHERE p.investor_id=t.investor_id AND p.investor_fund_amount>0
    ORDER BY v.sale_id,v.version DESC,v.id DESC
), stale_results AS (
    SELECT 1 FROM current_results v JOIN target t ON v.sale_date BETWEEN t.period_start AND t.period_end WHERE
      EXISTS (SELECT 1 FROM vehicles_vehiclebranchmovement c WHERE c.vehicle_id=v.vehicle_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehiclesalecorrection c WHERE c.sale_id=v.sale_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehiclesalereceipt c WHERE c.sale_id=v.sale_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehiclesalerefund c WHERE c.sale_id=v.sale_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehiclepurchasecorrection c JOIN vehicles_vehiclepurchase p ON p.id=c.purchase_id
                 WHERE p.vehicle_id=v.vehicle_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehicleexpense c WHERE c.vehicle_id=v.vehicle_id AND c.created_at>v.created_at)
      OR EXISTS (SELECT 1 FROM vehicles_vehicleexpensecorrection c JOIN vehicles_vehicleexpense e ON e.id=c.expense_id
                 WHERE e.vehicle_id=v.vehicle_id AND c.created_at>v.created_at)
), sources AS (
    SELECT 'VEHICLE_RESULT'::text AS kind,v.id::text AS source_id,
      jsonb_build_object('kind','VEHICLE_RESULT','id',v.id::text,
        'source_version',v.source_version,'sale_date',v.sale_date::text,
        'result_kind',v.result_kind,'investor_share_amount',v.investor_share_amount::text) AS item
    FROM current_results v JOIN target t ON v.sale_date BETWEEN t.period_start AND t.period_end
    UNION ALL
    SELECT 'DEAL_PROFIT_PAYMENT',p.id::text,
      jsonb_build_object('kind','DEAL_PROFIT_PAYMENT','id',p.id::text,
        'result_id',COALESCE(CASE WHEN v.result_kind='PROFIT' THEN v.id END,p.result_confirmation_id)::text,
        'amount',p.amount::text,
        'effective_at',trim(both '"' from to_json(p.effective_at AT TIME ZONE 'UTC')::text) || '+00:00')
    FROM investment_investorvehicleprofitpayment p
    JOIN investment_vehicleresultconfirmation original ON original.id=p.result_confirmation_id
    JOIN current_results v ON v.sale_id=original.sale_id
    JOIN target t ON t.tenant_id=p.tenant_id AND t.investor_id=p.investor_id
    WHERE v.sale_date BETWEEN t.period_start AND t.period_end
    UNION ALL
    SELECT 'INTERIM_PAYMENT',p.id::text,
      jsonb_build_object('kind','INTERIM_PAYMENT','id',p.id::text,
        'amount',p.amount::text,
        'effective_payment_date',(p.effective_at AT TIME ZONE 'Asia/Kolkata')::date::text)
    FROM investment_investorinterimpayment p
    JOIN target t ON t.tenant_id=p.tenant_id AND t.investor_id=p.investor_id
    WHERE (p.effective_at AT TIME ZONE 'Asia/Kolkata')::date BETWEEN t.period_start AND t.period_end
    UNION ALL
    SELECT 'LOSS_OFFSET',o.id::text,
      jsonb_build_object('kind','LOSS_OFFSET','id',o.id::text,
        'loss_result_id',o.loss_result_id::text,'profit_result_id',o.profit_result_id::text,
        'amount',o.amount::text)
    FROM investment_investorprofitlossoffset o
    JOIN investment_vehicleresultconfirmation profit ON profit.id=o.profit_result_id
    JOIN current_results v ON v.id=profit.id
    JOIN target t ON t.tenant_id=o.tenant_id AND t.investor_id=o.investor_id
    WHERE v.sale_date BETWEEN t.period_start AND t.period_end
)
SELECT CASE WHEN EXISTS (SELECT 1 FROM stale_results) THEN NULL ELSE encode(sha256(convert_to(investment_canonical_source_json(
  jsonb_build_object('period_start',t.period_start::text,'period_end',t.period_end::text,
    'duration_months',t.duration_months,'sources',
    COALESCE((SELECT jsonb_agg(item ORDER BY kind,source_id) FROM sources),'[]'::jsonb))
), 'UTF8')), 'hex') END FROM target t;
$$;
"""

FRESHNESS_GUARD = r"""
    IF v_amount_due IS NOT NULL AND (
       SELECT r.source_version IS DISTINCT FROM investment_profit_period_source_version(r.id)
       FROM investment_investorprofitperiodposition p
       JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
       WHERE p.id=NEW.position_id
    ) THEN
       RAISE EXCEPTION 'Exit Profit payment requires current same-Company sources' USING ERRCODE='23514';
    END IF;
"""

ANCHOR = "    IF v_amount_due IS NULL THEN\n"
FORWARD_SQL = SOURCE_HASH_SQL + PREVIOUS.FORWARD_SQL.replace(ANCHOR, FRESHNESS_GUARD + ANCHOR, 1)
REVERSE_SQL = PREVIOUS.FORWARD_SQL + "DROP FUNCTION investment_profit_period_source_version(uuid); DROP FUNCTION investment_canonical_source_json(jsonb);"


class Migration(migrations.Migration):
    dependencies = [("investment", "0052_exit_profit_calendar_source_guard")]
    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=REVERSE_SQL)]
