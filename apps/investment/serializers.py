from decimal import Decimal

from rest_framework import serializers


class InvestorWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class InvestorListQuerySerializer(serializers.Serializer):
    branch_id = serializers.UUIDField(required=False)


class InvestorInterimCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=16, decimal_places=2, min_value=Decimal("0.00")
    )
    effective_date = serializers.DateField()


class FundLedgerQuerySerializer(serializers.Serializer):
    investor_id = serializers.UUIDField(required=False)
    branch_id = serializers.UUIDField(required=False)


class FundMovementCreateSerializer(serializers.Serializer):
    investor_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.01")
    )
    reference = serializers.CharField(max_length=200, trim_whitespace=True)
    effective_at = serializers.DateTimeField()

    def validate_reference(self, value):
        if not value:
            raise serializers.ValidationError("A source reference is required.")
        return value


class FundCreditCorrectionCreateSerializer(serializers.Serializer):
    to_investor_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if not value:
            raise serializers.ValidationError("A correction reason is required.")
        return value
