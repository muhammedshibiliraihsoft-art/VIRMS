from decimal import Decimal

from django.test import SimpleTestCase

from apps.accounting.finance import calculate_company_period_carryforward


class CompanyPeriodCarryforwardTests(SimpleTestCase):
    def test_losses_accumulate_across_negative_periods(self):
        result = calculate_company_period_carryforward(
            period_result=Decimal("-30.00"), prior_loss=Decimal("70.00")
        )
        self.assertEqual(result.loss_carried_forward, Decimal("100.00"))
        self.assertEqual(result.positive_after_loss, Decimal("0.00"))

    def test_positive_result_reduces_loss_before_positive_balance(self):
        partial = calculate_company_period_carryforward(
            period_result=Decimal("30.00"), prior_loss=Decimal("70.00")
        )
        self.assertEqual(partial.loss_carried_forward, Decimal("40.00"))
        self.assertEqual(partial.positive_after_loss, Decimal("0.00"))
        covered = calculate_company_period_carryforward(
            period_result=Decimal("100.01"), prior_loss=Decimal("70.00")
        )
        self.assertEqual(covered.loss_carried_forward, Decimal("0.00"))
        self.assertEqual(covered.positive_after_loss, Decimal("30.01"))

    def test_supported_large_values_keep_paise(self):
        result = calculate_company_period_carryforward(
            period_result=Decimal("999999999999999999999999999999999999.99"),
            prior_loss=Decimal("0.01"),
        )
        self.assertEqual(result.positive_after_loss, Decimal("999999999999999999999999999999999999.98"))

    def test_negative_prior_loss_and_float_are_rejected(self):
        with self.assertRaises(ValueError):
            calculate_company_period_carryforward(period_result=Decimal("1.00"), prior_loss=Decimal("-1.00"))
        with self.assertRaises(ValueError):
            calculate_company_period_carryforward(period_result=0.1, prior_loss=Decimal("0.00"))
