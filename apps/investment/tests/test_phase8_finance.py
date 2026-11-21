from decimal import Decimal

from django.test import SimpleTestCase

from apps.investment.finance import (
    calculate_vehicle_shares,
    allocate_owner_distribution,
    suggest_vehicle_capital_recovery,
    investor_profit_period_for_date,
    summarize_investor_profit_periods,
    exact_money_difference,
)


class VehicleShareCalculationTests(SimpleTestCase):
    def test_large_vehicle_share_uses_exact_decimal_precision(self):
        result = calculate_vehicle_shares(
            result=Decimal("999999999999999999999999999999999999.99"),
            investor_percentage=Decimal("33.0000"),
        )
        self.assertEqual(result.investor_share, Decimal("330000000000000000000000000000000000.00"))
        self.assertEqual(result.company_share, Decimal("669999999999999999999999999999999999.99"))

    def test_positive_share_rounds_inr_half_up_and_company_gets_exact_remainder(self):
        result = calculate_vehicle_shares(
            result=Decimal("100.01"), investor_percentage=Decimal("33.3333")
        )

        self.assertEqual(result.investor_share, Decimal("33.34"))
        self.assertEqual(result.company_share, Decimal("66.67"))
        self.assertEqual(result.investor_share + result.company_share, Decimal("100.01"))

    def test_negative_result_is_loss_not_negative_profit_payment(self):
        result = calculate_vehicle_shares(
            result=Decimal("-100.01"), investor_percentage=Decimal("33.3333")
        )

        self.assertEqual(result.investor_share, Decimal("-33.34"))
        self.assertEqual(result.company_share, Decimal("-66.67"))
        self.assertEqual(result.investor_share + result.company_share, Decimal("-100.01"))

    def test_company_funded_vehicle_has_no_investor_share(self):
        result = calculate_vehicle_shares(
            result=Decimal("125.50"), investor_percentage=None
        )

        self.assertEqual(result.investor_share, Decimal("0.00"))
        self.assertEqual(result.company_share, Decimal("125.50"))


class VehicleCapitalRecoverySuggestionTests(SimpleTestCase):
    def test_principal_refund_reserve_is_limited_to_fund_money_held(self):
        from apps.investment.finance import calculate_investor_only_refund_reserve

        result = calculate_investor_only_refund_reserve(
            recovered_principal=Decimal("10000.00"), principal_refunded=Decimal("0.00"),
            sale_applied=Decimal("8000.00"), refund_payable=Decimal("4000.00"),
            fund_balance=Decimal("750.00"),
        )
        self.assertEqual(result.principal_refund_due, Decimal("2000.00"))
        self.assertEqual(result.reserve, Decimal("750.00"))
        self.assertEqual(result.uncovered, Decimal("1250.00"))

    def test_principal_refund_debit_reduces_the_pending_principal_obligation(self):
        from apps.investment.finance import calculate_investor_only_refund_reserve

        result = calculate_investor_only_refund_reserve(
            recovered_principal=Decimal("10000.00"), principal_refunded=Decimal("500.00"),
            sale_applied=Decimal("8000.00"), refund_payable=Decimal("3500.00"),
            fund_balance=Decimal("9500.00"),
        )
        self.assertEqual(result.principal_refund_due, Decimal("1500.00"))
        self.assertEqual(result.reserve, Decimal("1500.00"))
        self.assertEqual(result.uncovered, Decimal("0.00"))

    def test_principal_refund_reserve_rejects_invalid_history(self):
        from apps.investment.finance import calculate_investor_only_refund_reserve

        with self.assertRaises(ValueError):
            calculate_investor_only_refund_reserve(
                recovered_principal=Decimal("10.00"), principal_refunded=Decimal("10.01"),
                sale_applied=Decimal("0.00"), refund_payable=Decimal("1.00"),
                fund_balance=Decimal("1.00"),
            )


    def test_supported_large_amounts_preserve_exact_recovery(self):
        result = suggest_vehicle_capital_recovery(
            receipt_amount=Decimal("999999999999999999999999999999999999.99"),
            investor_principal_outstanding=Decimal("700000000000000000000000000000000000.00"),
            running_capital_outstanding=Decimal("300000000000000000000000000000000000.00"),
            mixed_funding=True, sale_fully_collected=True,
        )
        self.assertEqual(result.investor_principal, Decimal("700000000000000000000000000000000000.00"))
        self.assertEqual(result.running_capital, Decimal("299999999999999999999999999999999999.99"))
        self.assertEqual(result.running_capital_remaining, Decimal("0.01"))

    def test_actual_receipt_recovers_investor_principal_before_running_capital(self):
        result = suggest_vehicle_capital_recovery(
            receipt_amount=Decimal("1000.00"),
            investor_principal_outstanding=Decimal("700.00"),
            running_capital_outstanding=Decimal("500.00"),
            mixed_funding=True, sale_fully_collected=True,
        )

        self.assertEqual(result.investor_principal, Decimal("700.00"))
        self.assertEqual(result.running_capital, Decimal("300.00"))
        self.assertEqual(result.remaining_after_capital, Decimal("0.00"))
        self.assertEqual(result.investor_principal_remaining, Decimal("0.00"))
        self.assertEqual(result.running_capital_remaining, Decimal("200.00"))

    def test_receipt_below_investor_principal_does_not_reach_running_capital(self):
        result = suggest_vehicle_capital_recovery(
            receipt_amount=Decimal("250.00"),
            investor_principal_outstanding=Decimal("700.00"),
            running_capital_outstanding=Decimal("500.00"),
            mixed_funding=True, sale_fully_collected=True,
        )

        self.assertEqual(result.investor_principal, Decimal("250.00"))
        self.assertEqual(result.running_capital, Decimal("0.00"))
        self.assertEqual(result.remaining_after_capital, Decimal("0.00"))

    def test_company_funded_vehicle_recovers_running_capital(self):
        result = suggest_vehicle_capital_recovery(
            receipt_amount=Decimal("400.00"),
            investor_principal_outstanding=Decimal("0.00"),
            running_capital_outstanding=Decimal("300.00"),
            mixed_funding=False, sale_fully_collected=True,
        )

        self.assertEqual(result.investor_principal, Decimal("0.00"))
        self.assertEqual(result.running_capital, Decimal("300.00"))
        self.assertEqual(result.remaining_after_capital, Decimal("100.00"))

    def test_negative_money_is_rejected_instead_of_clamped(self):
        with self.assertRaises(ValueError):
            suggest_vehicle_capital_recovery(
                receipt_amount=Decimal("-0.01"),
                investor_principal_outstanding=Decimal("10.00"),
                running_capital_outstanding=Decimal("0.00"),
                mixed_funding=False, sale_fully_collected=True,
            )

    def test_mixed_funding_requires_full_collection_before_suggestion(self):
        with self.assertRaises(ValueError):
            suggest_vehicle_capital_recovery(
                receipt_amount=Decimal("1000.00"),
                investor_principal_outstanding=Decimal("700.00"),
                running_capital_outstanding=Decimal("300.00"),
                mixed_funding=True, sale_fully_collected=False,
            )


class SignedProfitPositionTests(SimpleTestCase):
    def test_profit_payment_reduces_payable_without_being_counted_as_repayment(self):
        from datetime import date, datetime
        from types import SimpleNamespace
        from apps.investment.period_positions import position_data

        position = SimpleNamespace(
            pk="11111111-1111-4111-8111-111111111111", tenant_id="tenant",
            previous_position_id=None, created_at=datetime(2026, 1, 1), reason="confirmed",
            reconciliation=SimpleNamespace(pk="33333333-3333-4333-8333-333333333333", investor_id="investor", period_start=date(2026, 1, 1),
                period_end=date(2026, 7, 1), net_position=Decimal("100.00"), source_version="source"),
        )
        result = position_data(position, is_current=True, recovery_received=Decimal("0.00"),
                               profit_paid=Decimal("40.00"), future_recovered=Decimal("0.00"),
                               future_applied=Decimal("0.00"))
        self.assertEqual(result["kind"], "PAYABLE")
        self.assertEqual(result["amount"], "60.00")
        self.assertEqual(result["recovery_received"], "0.00")
        self.assertEqual(result["profit_paid"], "40.00")

    def test_repayment_can_move_a_recoverable_position_across_zero(self):
        from datetime import date, datetime
        from types import SimpleNamespace
        from apps.investment.period_positions import position_data

        position = SimpleNamespace(
            pk="22222222-2222-4222-8222-222222222222", tenant_id="tenant",
            previous_position_id=None, created_at=datetime(2026, 1, 1), reason="confirmed",
            reconciliation=SimpleNamespace(pk="44444444-4444-4444-8444-444444444444", investor_id="investor", period_start=date(2026, 1, 1),
                period_end=date(2026, 7, 1), net_position=Decimal("-50.00"), source_version="source"),
        )
        result = position_data(position, is_current=True, recovery_received=Decimal("60.00"),
                               profit_paid=Decimal("0.00"), future_recovered=Decimal("0.00"),
                               future_applied=Decimal("0.00"))
        self.assertEqual(result["kind"], "PAYABLE")
        self.assertEqual(result["amount"], "10.00")

    def test_future_recovery_moves_a_signed_position_toward_payable(self):
        from datetime import date, datetime
        from types import SimpleNamespace
        from apps.investment.period_positions import position_data

        position = SimpleNamespace(
            pk="33333333-3333-4333-8333-333333333333", tenant_id="tenant",
            previous_position_id=None, created_at=datetime(2026, 1, 1), reason="confirmed",
            reconciliation=SimpleNamespace(pk="55555555-5555-4555-8555-555555555555", investor_id="investor",
                period_start=date(2026, 1, 1), period_end=date(2026, 7, 1),
                net_position=Decimal("-50.00"), source_version="source"),
        )
        result = position_data(position, is_current=True, recovery_received=Decimal("0.00"),
                               profit_paid=Decimal("0.00"), future_recovered=Decimal("60.00"),
                               future_applied=Decimal("0.00"))
        self.assertEqual(result["kind"], "PAYABLE")
        self.assertEqual(result["amount"], "10.00")
        self.assertEqual(result["future_profit_recovered"], "60.00")


class OwnerDistributionAllocationTests(SimpleTestCase):
    def test_large_supported_amount_preserves_exact_paise(self):
        rows = allocate_owner_distribution(
            amount=Decimal("999999999999999999999999999999999999.99"),
            recipients=[{"id": "owner-a", "percentage": Decimal("100")}],
        )
        self.assertEqual(rows[0].amount, Decimal("999999999999999999999999999999999999.99"))

    def test_rounding_residual_is_distributed_and_total_is_exact(self):
        rows = allocate_owner_distribution(
            amount=Decimal("100.01"),
            recipients=[
                {"id": "owner-a", "percentage": Decimal("33.3333")},
                {"id": "owner-b", "percentage": Decimal("33.3333")},
                {"id": "owner-c", "percentage": Decimal("33.3334")},
            ],
        )

        self.assertEqual(sum(row.amount for row in rows), Decimal("100.01"))
        self.assertTrue(all(row.amount >= 0 for row in rows))
        self.assertEqual([row.recipient_id for row in rows], ["owner-a", "owner-b", "owner-c"])

    def test_equal_paise_tie_uses_configured_recipient_order(self):
        rows = allocate_owner_distribution(
            amount=Decimal("0.01"),
            recipients=[
                {"id": "owner-a", "percentage": Decimal("25.00")},
                {"id": "owner-b", "percentage": Decimal("25.00")},
                {"id": "owner-c", "percentage": Decimal("25.00")},
                {"id": "owner-d", "percentage": Decimal("25.00")},
            ],
        )

        self.assertEqual([row.amount for row in rows], [
            Decimal("0.01"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        ])

    def test_invalid_or_ambiguous_split_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate_owner_distribution(
                amount=Decimal("1.00"),
                recipients=[
                    {"id": "owner-a", "percentage": Decimal("60.00")},
                    {"id": "owner-b", "percentage": Decimal("39.99")},
                ],
            )


class InvestorProfitPeriodTests(SimpleTestCase):
    def test_sale_date_is_assigned_to_each_investors_configured_period(self):
        calendar = [
            {"effective_start": "2026-01-15", "duration_months": 6},
        ]

        first = investor_profit_period_for_date("2026-07-14", calendar)
        second = investor_profit_period_for_date("2026-07-15", calendar)

        self.assertEqual((first.start, first.end), ("2026-01-15", "2026-07-14"))
        self.assertEqual((second.start, second.end), ("2026-07-15", "2027-01-14"))

    def test_calendar_change_starts_a_new_period_without_rewriting_old_period(self):
        calendar = [
            {"effective_start": "2026-01-15", "duration_months": 6},
            {"effective_start": "2026-07-15", "duration_months": 12},
        ]

        old = investor_profit_period_for_date("2026-07-14", calendar)
        new = investor_profit_period_for_date("2026-07-15", calendar)

        self.assertEqual((old.start, old.end), ("2026-01-15", "2026-07-14"))
        self.assertEqual((new.start, new.end), ("2026-07-15", "2027-07-14"))

    def test_date_before_first_calendar_period_is_not_assigned(self):
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        self.assertIsNone(investor_profit_period_for_date("2026-01-14", calendar))

    def test_month_end_periods_clamp_to_the_last_valid_day(self):
        calendar = [{"effective_start": "2024-08-31", "duration_months": 6}]

        period = investor_profit_period_for_date("2025-02-28", calendar)

        self.assertEqual((period.start, period.end), ("2025-02-28", "2025-08-30"))

    def test_latest_calendar_version_at_open_boundary_applies_without_erasing_history(self):
        calendar = [
            {"effective_start": "2026-01-15", "duration_months": 6, "version": 1},
            {"effective_start": "2026-01-15", "duration_months": 12, "version": 2},
        ]

        period = investor_profit_period_for_date("2026-10-01", calendar)

        self.assertEqual((period.start, period.end, period.duration_months),
                         ("2026-01-15", "2027-01-14", 12))

    def test_sale_date_period_sums_profit_and_keeps_loss_separate(self):
        results = [
            {"effective_sale_date": "2026-05-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "1000.00"},
            {"effective_sale_date": "2026-06-01", "status": "CURRENT", "result_kind": "LOSS", "investor_share_amount": "-250.00"},
            {"effective_sale_date": "2026-07-01", "status": "STALE_REVIEW_REQUIRED", "result_kind": "PROFIT", "investor_share_amount": "999.00"},
        ]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        periods, unassigned_count = summarize_investor_profit_periods(results, calendar)

        self.assertEqual(unassigned_count, 1)
        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["period_start"], "2026-01-15")
        self.assertEqual(periods[0]["period_end"], "2026-07-14")
        self.assertEqual(periods[0]["gross_investor_profit"], "1000.00")
        self.assertEqual(periods[0]["investor_loss_share"], "250.00")
        self.assertEqual(periods[0]["status"], "CALCULATED_NOT_RECONCILED")

    def test_confirmed_deal_profit_payments_reduce_the_sale_period_once(self):
        results = [
            {"id": "result-a", "effective_sale_date": "2026-05-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "1000.00"},
            {"id": "result-b", "effective_sale_date": "2026-06-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "500.00"},
        ]
        payments = [
            {"id": "payment-a", "vehicle_result_id": "result-a", "amount": "300.00"},
            {"id": "payment-b", "vehicle_result_id": "result-a", "amount": "200.00"},
        ]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        periods, unassigned_count = summarize_investor_profit_periods(
            results, calendar, deal_profit_payments=payments,
        )

        self.assertEqual(unassigned_count, 0)
        self.assertEqual(periods[0]["gross_investor_profit"], "1500.00")
        self.assertEqual(periods[0]["deal_profit_paid"], "500.00")
        self.assertEqual(periods[0]["calculated_unpaid_profit"], "1000.00")

    def test_large_period_profit_and_payment_preserve_paise(self):
        results = [{
            "id": "result-large", "effective_sale_date": "2026-05-01",
            "status": "CURRENT", "result_kind": "PROFIT",
            "investor_share_amount": "999999999999999999999999999999999999.99",
        }]
        payments = [{"id": "payment-large", "vehicle_result_id": "result-large", "amount": "0.01"}]
        periods, unassigned = summarize_investor_profit_periods(
            results, [{"effective_start": "2026-01-15", "duration_months": 6}],
            deal_profit_payments=payments,
        )
        self.assertEqual(unassigned, 0)
        self.assertEqual(periods[0]["calculated_unpaid_profit"], "999999999999999999999999999999999999.98")
        net = exact_money_difference(Decimal(periods[0]["gross_investor_profit"]), Decimal("0.01"))
        self.assertEqual(net, Decimal("999999999999999999999999999999999999.98"))

    def test_interim_payments_are_separate_paid_facts_for_their_profit_period(self):
        results = [
            {"id": "result-a", "effective_sale_date": "2026-05-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "10000.00"},
        ]
        interim_payments = [
            {"id": "interim-a", "effective_payment_date": "2026-05-03", "amount": "4000.00"},
            {"id": "interim-b", "effective_payment_date": "2026-05-20", "amount": "2000.00"},
            # Idempotent/replayed source rows must not double count.
            {"id": "interim-b", "effective_payment_date": "2026-05-20", "amount": "2000.00"},
        ]
        calendar = [{"effective_start": "2026-01-01", "duration_months": 6}]

        periods, unassigned_count = summarize_investor_profit_periods(
            results, calendar, interim_payments=interim_payments,
        )

        self.assertEqual(unassigned_count, 0)
        self.assertEqual(periods[0]["gross_investor_profit"], "10000.00")
        self.assertEqual(periods[0]["deal_profit_paid"], "0.00")
        self.assertEqual(periods[0]["interim_paid"], "6000.00")
        self.assertEqual(periods[0]["total_paid"], "6000.00")
        self.assertEqual(periods[0]["calculated_unpaid_profit"], "4000.00")
        self.assertEqual(periods[0]["paid_status"], "PARTIALLY_PAID")

    def test_historical_payment_remains_in_period_after_result_becomes_stale(self):
        results = [
            {"id": "result-old", "effective_sale_date": "2026-05-01", "status": "STALE_REVIEW_REQUIRED", "result_kind": "PROFIT", "investor_share_amount": "1000.00"},
        ]
        payments = [{"id": "payment-old", "vehicle_result_id": "result-old", "amount": "800.00"}]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        periods, unassigned_count = summarize_investor_profit_periods(
            results, calendar, deal_profit_payments=payments,
        )

        self.assertEqual(unassigned_count, 1)
        self.assertEqual(periods[0]["gross_investor_profit"], "0.00")
        self.assertEqual(periods[0]["deal_profit_paid"], "800.00")
        self.assertEqual(periods[0]["historical_overpayment"], "800.00")

    def test_loss_reduces_profit_only_when_an_explicit_offset_is_supplied(self):
        results = [
            {"id": "loss", "effective_sale_date": "2026-03-01", "status": "CURRENT", "result_kind": "LOSS", "investor_share_amount": "-250.00"},
            {"id": "profit", "effective_sale_date": "2026-05-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "1000.00"},
        ]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        without_approval, _ = summarize_investor_profit_periods(results, calendar)
        approved_offset, _ = summarize_investor_profit_periods(
            results, calendar,
            loss_offsets=[{"id": "offset-1", "loss_result_id": "loss", "profit_result_id": "profit", "amount": "200.00"}],
        )

        self.assertEqual(without_approval[0]["calculated_unpaid_profit"], "1000.00")
        self.assertEqual(approved_offset[0]["investor_loss_share"], "250.00")
        self.assertEqual(approved_offset[0]["loss_offset_applied"], "200.00")
        self.assertEqual(approved_offset[0]["calculated_unpaid_profit"], "800.00")

    def test_invalidated_loss_offset_does_not_use_current_profit_date_fallback(self):
        results = [
            {"id": "profit", "effective_sale_date": "2026-05-01", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "1000.00"},
        ]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]
        periods, unassigned = summarize_investor_profit_periods(
            results, calendar, loss_offsets=[{
                "id": "offset", "loss_result_id": "stale-loss", "profit_result_id": "profit",
                "effective_sale_date": None, "amount": "200.00", "valid_link": False,
            }],
        )
        self.assertEqual(unassigned, 1)
        self.assertEqual(periods[0]["loss_offset_applied"], "0.00")
        self.assertEqual(periods[0]["calculated_unpaid_profit"], "1000.00")

    def test_result_before_first_fund_credit_is_left_unassigned(self):
        results = [
            {"effective_sale_date": "2026-01-14", "status": "CURRENT", "result_kind": "PROFIT", "investor_share_amount": "500.00"},
        ]
        calendar = [{"effective_start": "2026-01-15", "duration_months": 6}]

        periods, unassigned_count = summarize_investor_profit_periods(results, calendar)

        self.assertEqual(periods, [])
        self.assertEqual(unassigned_count, 1)

