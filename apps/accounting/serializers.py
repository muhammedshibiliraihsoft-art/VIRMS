from decimal import Decimal

from rest_framework import serializers

from apps.accounting.models import AccountingAccount, AccountingCategory, AccountingEvent


class AccountCreateSerializer(serializers.Serializer):
    account_type = serializers.ChoiceField(choices=AccountingAccount.AccountType.choices)
    label = serializers.CharField(max_length=100, trim_whitespace=True)


class CategoryCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=AccountingCategory.Kind.choices)
    label = serializers.CharField(max_length=100, trim_whitespace=True)


class ArchiveSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()

    def validate_is_active(self, value):
        if value:
            raise serializers.ValidationError("Archived records cannot be reactivated.")
        return value


class MoneySerializerField(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 38)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("coerce_to_string", True)
        super().__init__(**kwargs)


class IncomeExpenseCreateSerializer(serializers.Serializer):
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    category_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)
    effective_at = serializers.DateTimeField(required=False)


class ReceiptPaymentCreateSerializer(serializers.Serializer):
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    account_id = serializers.UUIDField()
    target_event_id = serializers.UUIDField()
    effective_at = serializers.DateTimeField()
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)


class OpeningBalanceCreateSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    amount = MoneySerializerField(min_value=Decimal("-999999999999999999999999999999999999.99"))
    effective_at = serializers.DateTimeField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError("Opening balance must be nonzero.")
        return value


class TransferCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    from_account_id = serializers.UUIDField()
    to_account_id = serializers.UUIDField()
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)


class IncomeExpenseReplacementSerializer(serializers.Serializer):
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    category_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)


class CashEventReplacementSerializer(serializers.Serializer):
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    account_id = serializers.UUIDField()
    effective_at = serializers.DateTimeField()
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)


class OpeningBalanceReplacementSerializer(serializers.Serializer):
    amount = MoneySerializerField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    source_reference = serializers.CharField(max_length=200, required=False, allow_blank=True)


class TransferReplacementSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    from_account_id = serializers.UUIDField()
    to_account_id = serializers.UUIDField()
    amount = MoneySerializerField(min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)


class EventCorrectionSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("REVERSE_ONLY", "REVERSE_AND_REPLACE"))
    event_occurred = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    replacement = serializers.DictField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["outcome"] == "REVERSE_AND_REPLACE" and not attrs.get("replacement"):
            raise serializers.ValidationError({"replacement": "A replacement is required."})
        if attrs["event_occurred"] != (attrs["outcome"] == "REVERSE_AND_REPLACE"):
            raise serializers.ValidationError({"outcome": "Outcome must match whether the real event occurred."})
        return attrs


class OpeningBalanceCorrectionSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("REVERSE_ONLY", "REVERSE_AND_REPLACE"))
    event_occurred = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    replacement_amount = MoneySerializerField()
    source_reference = serializers.CharField(max_length=200, trim_whitespace=True)

    def validate(self, attrs):
        reverse_only = attrs["outcome"] == "REVERSE_ONLY"
        if attrs["event_occurred"] == reverse_only:
            raise serializers.ValidationError({"outcome": "Outcome must match whether the real event occurred."})
        if reverse_only and attrs["replacement_amount"] != 0:
            raise serializers.ValidationError({"replacement_amount": "Reverse only must use a zero replacement amount."})
        if not reverse_only and attrs["replacement_amount"] == 0:
            raise serializers.ValidationError({"replacement_amount": "A replacement Opening Balance must be nonzero."})
        return attrs


class TransferReversalSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=("REVERSE_ONLY",))
    event_occurred = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_event_occurred(self, value):
        if value:
            raise serializers.ValidationError("A real Transfer must use the correction resource with a replacement.")
        return value


class TransferCorrectionSerializer(EventCorrectionSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["outcome"] != "REVERSE_AND_REPLACE" or not attrs["event_occurred"]:
            raise serializers.ValidationError({"outcome": "A real Transfer correction requires a same-kind replacement."})
        return attrs


class ApplicationReallocationSerializer(serializers.Serializer):
    target_event_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class AccountingResultQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=("monthly", "h1", "h2", "annual"))
    year = serializers.IntegerField(min_value=1900, max_value=9998)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    branch_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if attrs["period"] == "monthly" and "month" not in attrs:
            raise serializers.ValidationError({"month": "Required for monthly reports."})
        if attrs["period"] != "monthly" and "month" in attrs:
            raise serializers.ValidationError({"month": "Allowed only for monthly reports."})
        return attrs


class EventFilterSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=AccountingEvent.EventType.choices,
        required=False,
    )
    branch_id = serializers.UUIDField(required=False)
    category_id = serializers.UUIDField(required=False)
    account_id = serializers.UUIDField(required=False)
    effective_after = serializers.DateTimeField(required=False)
    effective_before = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if (
            attrs.get("effective_after")
            and attrs.get("effective_before")
            and attrs["effective_before"] <= attrs["effective_after"]
        ):
            raise serializers.ValidationError(
                {"effective_before": "Must be later than effective_after."}
            )
        return attrs


def replacement_serializer(event_type):
    if event_type in (AccountingEvent.EventType.INCOME, AccountingEvent.EventType.EXPENSE):
        return IncomeExpenseReplacementSerializer
    if event_type in (AccountingEvent.EventType.RECEIPT, AccountingEvent.EventType.PAYMENT):
        return CashEventReplacementSerializer
    if event_type == AccountingEvent.EventType.OPENING_BALANCE:
        return OpeningBalanceReplacementSerializer
    if event_type == AccountingEvent.EventType.TRANSFER:
        return TransferReplacementSerializer
    return None
