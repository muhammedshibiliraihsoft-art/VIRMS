from decimal import Decimal

from rest_framework import serializers


class VehicleWriteSerializer(serializers.Serializer):
    registration = serializers.CharField(max_length=40, trim_whitespace=True)
    model = serializers.CharField(max_length=160, trim_whitespace=True)
    branch_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not attrs.get("registration", "").strip():
            raise serializers.ValidationError({"registration": "A registration number is required."})
        if not attrs.get("model", "").strip():
            raise serializers.ValidationError({"model": "A model/description is required."})
        return attrs


class VehicleListQuerySerializer(serializers.Serializer):
    branch_id = serializers.UUIDField(required=False)
    vehicle_id = serializers.UUIDField(required=False)
    search = serializers.CharField(max_length=80, required=False, allow_blank=False)


class VehicleRegisterQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    branch_id = serializers.UUIDField(required=False)
    search = serializers.CharField(max_length=80, required=False, allow_blank=False)
    context = serializers.ChoiceField(choices=("all", "stock", "customer"), required=False, default="all")
    status = serializers.ChoiceField(
        choices=("all", "in_work", "sold", "purchased", "customer_vehicles"),
        required=False,
        default="all",
    )


class VehicleBranchMoveSerializer(serializers.Serializer):
    to_branch_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if not value:
            raise serializers.ValidationError("A reason is required.")
        return value


class VehiclePurchaseWriteSerializer(serializers.Serializer):
    vehicle_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    purchase_cost = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.00"))
    seller_name = serializers.CharField(max_length=160, trim_whitespace=True)
    seller_phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    investor_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    investor_fund_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False, default=Decimal("0.00")
    )
    running_capital_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    purchased_at = serializers.DateTimeField(required=False)
    initial_payment_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False, default="0.00"
    )
    initial_payment_account_id = serializers.UUIDField(required=False, allow_null=True)
    initial_payment_effective_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if not attrs.get("seller_name", "").strip():
            raise serializers.ValidationError({"seller_name": "Seller name is required."})
        if attrs["purchase_cost"] <= 0:
            raise serializers.ValidationError({"purchase_cost": "Purchase cost must be greater than zero."})
        if attrs.get("running_capital_amount") is None:
            attrs["running_capital_amount"] = attrs["purchase_cost"] - attrs["investor_fund_amount"]
        return attrs


class VehiclePurchasePaymentSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.00"))
    effective_at = serializers.DateTimeField(required=False)
    reference = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment must be greater than zero.")
        return value


class VehicleExpenseWriteSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    investor_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    investor_fund_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False
    )
    running_capital_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    effective_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if not attrs.get("description", "").strip():
            raise serializers.ValidationError({"description": "A description is required."})
        fund = attrs.get("investor_fund_amount")
        running = attrs.get("running_capital_amount")
        if fund is not None and running is not None and attrs["amount"] != fund + running:
            raise serializers.ValidationError({"running_capital_amount": "Fund and Company amounts must equal the full Vehicle Expense."})
        return attrs


class VehicleExpensePaymentSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=200, trim_whitespace=True)
    effective_at = serializers.DateTimeField(required=False)

    def validate_reference(self, value):
        if not value.strip():
            raise serializers.ValidationError("A bank transaction ID or cash voucher number is required.")
        return value.strip()


class VehicleExpenseRefundSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    excess_income_category_id = serializers.UUIDField(required=False, allow_null=True)
    excess_income_description = serializers.CharField(max_length=500, required=False, allow_blank=True, trim_whitespace=True)
    effective_at = serializers.DateTimeField(required=False)


class VehiclePurchaseRefundSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField(required=False)


class VehiclePurchaseCorrectionSerializer(serializers.Serializer):
    purchase_cost = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("A correction reason is required.")
        return value.strip()


class VehicleSaleWriteSerializer(serializers.Serializer):
    vehicle_id = serializers.UUIDField()
    branch_id = serializers.UUIDField()
    sale_price = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    buyer_name = serializers.CharField(max_length=160, trim_whitespace=True)
    buyer_phone = serializers.CharField(max_length=40, trim_whitespace=True)
    sold_at = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        if not attrs.get("buyer_name", "").strip():
            raise serializers.ValidationError({"buyer_name": "Buyer name is required."})
        if not attrs.get("buyer_phone", "").strip():
            raise serializers.ValidationError({"buyer_phone": "Buyer phone is required."})
        return attrs


class VehicleSaleReceiptSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=200, trim_whitespace=True)
    effective_at = serializers.DateTimeField(required=False)

    def validate_reference(self, value):
        if not value.strip():
            raise serializers.ValidationError("A bank transaction ID or cash voucher number is required.")
        return value.strip()


class VehicleSaleRefundSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    investor_principal_amount = serializers.DecimalField(
        max_digits=38, decimal_places=2, min_value=Decimal("0.00"), required=False,
    )
    effective_at = serializers.DateTimeField(required=False)


class VehicleSaleCorrectionSerializer(serializers.Serializer):
    sale_price = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("A correction reason is required.")
        return value.strip()


class VehicleExpenseCorrectionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reason = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_reason(self, value):
        if not value.strip():
            raise serializers.ValidationError("A correction reason is required.")
        return value.strip()
