"""Reject Exit Profit payouts when the confirmed period calendar changed."""

from importlib import import_module

from django.db import migrations


PREVIOUS = import_module("apps.investment.migrations.0051_phase8_settlement_guard_parity")

CALENDAR_GUARD = r"""
    IF v_amount_due IS NOT NULL AND EXISTS (
        SELECT 1 FROM investment_investorprofitperiodposition p
        JOIN investment_investorprofitperiodreconciliation r ON r.id=p.reconciliation_id
        LEFT JOIN LATERAL (
            SELECT candidate.effective_start,candidate.duration_months
            FROM (
                SELECT c.effective_start,c.duration_months,1 AS priority,c.version,c.id
                FROM investment_investorprofitcalendarconfiguration c
                WHERE c.tenant_id=r.tenant_id AND c.investor_id=r.investor_id
                  AND c.effective_start<=r.period_start
                UNION ALL
                SELECT (fc.effective_at AT TIME ZONE 'Asia/Kolkata')::date,6,0,1,fc.id
                FROM investment_investorfundcredit fc
                LEFT JOIN LATERAL (
                    SELECT cc.to_investor_id FROM investment_investorfundcreditcorrection cc
                    WHERE cc.credit_id=fc.id ORDER BY cc.version DESC,cc.id DESC LIMIT 1
                ) owner ON TRUE
                WHERE fc.tenant_id=r.tenant_id
                  AND COALESCE(owner.to_investor_id,fc.investor_id)=r.investor_id
                  AND NOT EXISTS (
                    SELECT 1 FROM investment_investorprofitcalendarconfiguration c
                    WHERE c.tenant_id=r.tenant_id AND c.investor_id=r.investor_id
                  )
            ) candidate
            ORDER BY candidate.priority DESC,
                     CASE WHEN candidate.priority=0 THEN candidate.effective_start END ASC,
                     CASE WHEN candidate.priority=1 THEN candidate.effective_start END DESC,
                     candidate.version DESC,candidate.id DESC LIMIT 1
        ) calendar ON TRUE
        WHERE p.id=NEW.position_id AND (
            calendar.effective_start IS NULL
            OR r.duration_months<>calendar.duration_months
            OR r.period_start<> (
                calendar.effective_start + make_interval(months => (
                    ((extract(year from r.period_start)::integer-extract(year from calendar.effective_start)::integer)*12
                     +extract(month from r.period_start)::integer-extract(month from calendar.effective_start)::integer)
                    /calendar.duration_months)*calendar.duration_months
                ))::date
            OR r.period_end<> (
                calendar.effective_start + make_interval(months => (
                    (((extract(year from r.period_start)::integer-extract(year from calendar.effective_start)::integer)*12
                     +extract(month from r.period_start)::integer-extract(month from calendar.effective_start)::integer)
                    /calendar.duration_months)+1)*calendar.duration_months
                ))::date-1
        )
    ) THEN
        RAISE EXCEPTION 'Exit Profit payment requires current same-Company sources' USING ERRCODE='23514';
    END IF;
"""

ANCHOR = "    IF v_amount_due IS NULL THEN\n"
FORWARD_SQL = PREVIOUS.FORWARD_SQL.replace(ANCHOR, CALENDAR_GUARD + ANCHOR, 1)


class Migration(migrations.Migration):
    dependencies = [("investment", "0051_phase8_settlement_guard_parity")]
    operations = [migrations.RunSQL(FORWARD_SQL, reverse_sql=PREVIOUS.FORWARD_SQL)]
