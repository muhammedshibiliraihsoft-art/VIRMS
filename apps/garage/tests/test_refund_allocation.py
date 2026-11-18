from decimal import Decimal
from unittest import TestCase

from apps.garage.refund_allocation import split_customer_cost_refund


class CustomerCostRefundAllocationTests(TestCase):
    def test_refund_is_split_against_remaining_net_payments(self):
        self.assertEqual(split_customer_cost_refund(Decimal('2000.00'), Decimal('2000.00'), Decimal('500.00')), (Decimal('1500.00'), Decimal('500.00')))
        self.assertEqual(split_customer_cost_refund(Decimal('20.00'), Decimal('0.00'), Decimal('0.00')), (Decimal('0.00'), Decimal('20.00')))
        self.assertEqual(split_customer_cost_refund(Decimal('10.00'), Decimal('50.00'), Decimal('0.00')), (Decimal('10.00'), Decimal('0.00')))
        self.assertEqual(split_customer_cost_refund(Decimal('999999999999999999999999999999999999.99'), Decimal('1.00'), Decimal('0.00')), (Decimal('1.00'), Decimal('999999999999999999999999999999999998.99')))

    def test_rejects_invalid_or_fractional_paise_amounts(self):
        for values in [('0', '10', '0'), ('1', '10', '11'), ('1.001', '10', '0'), ('NaN', '10', '0')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                split_customer_cost_refund(*(Decimal(value) for value in values))
