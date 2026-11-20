from decimal import Decimal

from rest_framework import serializers


class InvestorWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120, trim_whitespace=True)


class InvestorPortalBindingSerializer(serializers.Serializer):
    account_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    login_id = serializers.CharField(max_length=150, required=False, trim_whitespace=True)

    def validate(self, attrs):
        if bool(attrs.get("account_id")) == bool(attrs.get("login_id")):
            raise serializers.ValidationError("Provide exactly one of account_id or login_id.")
        return attrs


class InvestorPortalBindingRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class InvestorExitRequestSerializer(serializers.Serializer):
    terms_accepted = serializers.BooleanField()

    def validate_terms_accepted(self, value):
        if value is not True:
            raise serializers.ValidationError("You must accept the Exit request terms.")
        return value


class InvestorExitCancellationRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, trim_whitespace=True)


class InvestorExitCancellationReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, trim_whitespace=True)


class InvestorExitNoticeExtensionSerializer(serializers.Serializer):
    deadline = serializers.DateTimeField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True, min_length=3)


class InvestorExitPrincipalPaymentSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=200, trim_whitespace=True, min_length=3)
    effective_at = serializers.DateTimeField()
    expected_source_version = serializers.RegexField(r"^[0-9a-f]{64}$")
    reason = serializers.CharField(max_length=500, trim_whitespace=True, min_length=3)


class InvestorExitLossApplicationSerializer(serializers.Serializer):
    loss_result_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField(required=False)
    source = serializers.ChoiceField(choices=("AVAILABLE_FUND", "DIRECT_RECEIPT"))
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()
    expected_source_version = serializers.RegexField(r"^[0-9a-f]{64}$")
    reason = serializers.CharField(max_length=500, trim_whitespace=True, min_length=3)

    def validate(self, attrs):
        if (attrs["source"] == "DIRECT_RECEIPT") != ("account_id" in attrs):
            raise serializers.ValidationError({"account_id": "Select a Cash/Bank account only for a direct receipt."})
        return attrs


class InvestorExitProfitPaymentSerializer(serializers.Serializer):
    position_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()
    expected_source_version = serializers.RegexField(r"^[0-9a-f]{64}$")
    reason = serializers.CharField(max_length=500, trim_whitespace=True, min_length=3)


class InvestorExitSettlementCloseSerializer(serializers.Serializer):
    expected_source_version = serializers.RegexField(r"^[0-9a-f]{64}$")
    reason = serializers.CharField(max_length=500, trim_whitespace=True, min_length=3)


class InvestorListQuerySerializer(serializers.Serializer):
    branch_id = serializers.UUIDField(required=False)


class InvestorInterimCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=16, decimal_places=2, min_value=Decimal("0.00")
    )
    effective_date = serializers.DateField()


class InvestorInterimPaymentCreateSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.01")
    )
    effective_at = serializers.DateTimeField()


class InvestorInterimPaymentQuerySerializer(serializers.Serializer):
    period_month = serializers.DateField()
    branch_id = serializers.UUIDField(required=False)

    def validate_period_month(self, value):
        if value.day != 1:
            raise serializers.ValidationError("Use the first day of the payment month.")
        return value


class InvestorProfitCalendarConfigurationSerializer(serializers.Serializer):
    effective_start = serializers.DateField()
    duration_months = serializers.IntegerField(min_value=1, max_value=32767)


class InvestorProfitShareAgreementSerializer(serializers.Serializer):
    share_percentage = serializers.DecimalField(
        max_digits=7, decimal_places=4,
        min_value=Decimal("0.0000"), max_value=Decimal("100.0000"),
    )
    effective_at = serializers.DateTimeField()


class VehicleResultConfirmationSerializer(serializers.Serializer):
    expected_source_version = serializers.RegexField(r"^[0-9a-f]{64}$")
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    investor_loss_amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False)
    company_loss_amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False)

    def validate_reason(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("A reason of at least 3 characters is required.")
        return value


class VehiclePrincipalRefundReviewSerializer(serializers.Serializer):
    principal_amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0"))
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class VehicleCapitalRecoverySerializer(serializers.Serializer):
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class InvestorVehicleProfitPaymentSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.01")
    )
    effective_at = serializers.DateTimeField(required=False)
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True, trim_whitespace=True,
    )


class InvestorProfitLossOffsetSerializer(serializers.Serializer):
    profit_result_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.01")
    )
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("A reason of at least 3 characters is required.")
        return value


class InvestorProfitFutureAdjustmentSerializer(serializers.Serializer):
    profit_position_id = serializers.UUIDField()
    profit_result_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    expected_profit_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class InvestorProfitRecoveryReceiptSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField(required=False)
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class InvestorProfitPositionSerializer(serializers.Serializer):
    reconciliation_id = serializers.UUIDField()
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$")
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class InvestorProfitPeriodReconciliationSerializer(serializers.Serializer):
    period_start = serializers.DateField()
    expected_source_version = serializers.RegexField(regex=r"^[0-9a-f]{64}$", max_length=64)
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("A reason of at least 3 characters is required.")
        return value


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
