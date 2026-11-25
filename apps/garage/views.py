from rest_framework import serializers
from decimal import Decimal
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Prefetch, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from apps.garage import services
from apps.garage.models import GarageCustomerCostPayment, GarageCustomerCostPaymentCorrection, GarageCustomerCostRefund, GarageJob, GarageReceiptCorrection, LabourPaymentCorrection
from apps.accounting.models import AccountingApplication
from apps.vehicles.serializers import VehicleExpenseWriteSerializer


class JobSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    vehicle_id = serializers.UUIDField()
    context = serializers.ChoiceField(choices=GarageJob.Context.choices)
    contact_name = serializers.CharField(max_length=160, required=False, allow_blank=True, default="", trim_whitespace=True)
    contact_phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="", trim_whitespace=True)

    def validate(self, attrs):
        if attrs["context"] == GarageJob.Context.EXTERNAL_CUSTOMER and not attrs["contact_name"]:
            raise serializers.ValidationError({"contact_name": "Customer name is required."})
        return attrs


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=GarageJob.Status.choices)
    expected_version = serializers.IntegerField(min_value=0)


class WorkSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=500, trim_whitespace=True)


class StockCostSerializer(serializers.Serializer):
    expense_id = serializers.UUIDField()


class CustomerChargeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.00"))
    expected_version = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="", trim_whitespace=True)


class CustomerReceiptSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=200, trim_whitespace=True)
    effective_at = serializers.DateTimeField(required=False)


class CustomerCostSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=500, trim_whitespace=True)
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))


class CustomerCostCorrectionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    expected_version = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class CustomerCostPaymentSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField(required=False, default=None)


class CustomerCostRefundPreviewSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))


class CustomerCostRefundSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField(required=False, default=None)
    excess_income_category_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    excess_income_description = serializers.CharField(max_length=500, required=False, allow_blank=True, default="", trim_whitespace=True)


class LabourPersonSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="", trim_whitespace=True)


class LabourStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    expected_version = serializers.IntegerField(min_value=0)


class LabourPersonUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160, trim_whitespace=True)
    phone = serializers.CharField(max_length=40, allow_blank=True, trim_whitespace=True)
    expected_updated_at = serializers.DateTimeField()


class LabourPaymentSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="", trim_whitespace=True)


class LabourPaymentReplacementSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=38, decimal_places=2, min_value=Decimal("0.01"))
    effective_at = serializers.DateTimeField()


class LabourPaymentCorrectionSerializer(serializers.Serializer):
    expected_event_id = serializers.UUIDField()
    outcome = serializers.ChoiceField(choices=("REVERSE_ONLY", "REVERSE_AND_REPLACE"))
    reason = serializers.CharField(max_length=500, trim_whitespace=True)
    replacement = LabourPaymentReplacementSerializer(required=False, allow_null=True)

    def validate(self, attrs):
        replacement = attrs.get("replacement")
        if (attrs["outcome"] == "REVERSE_AND_REPLACE") != bool(replacement):
            raise serializers.ValidationError({"replacement": "Provide replacement details only when correcting an actual payment."})
        return attrs


class GarageView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Vary"] = "Cookie"
        return response


class LabourPersonListCreateView(GarageView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        rows = services.list_labour_people(actor=request.user, company_id=company_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.labour_person_data(person) for person in page])

    def post(self, request, company_id):
        serializer = LabourPersonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_labour_person(actor=request.user, company_id=company_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class LabourPersonDetailView(GarageView):
    def patch(self, request, company_id, person_id):
        serializer = LabourPersonUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.update_labour_person(actor=request.user, company_id=company_id, person_id=person_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class LabourStatusView(GarageView):
    def post(self, request, company_id, person_id):
        serializer = LabourStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.change_labour_status(actor=request.user, company_id=company_id, person_id=person_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class LabourPaymentView(GarageView):
    def get(self, request, company_id, person_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        person = services.list_labour_people(actor=request.user, company_id=company_id).filter(pk=person_id).first()
        if person is None:
            raise NotFound("Labour person not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = person.payments.select_related("event").prefetch_related(Prefetch("corrections", queryset=LabourPaymentCorrection.objects.select_related("replacement_event", "previous_event").order_by("-version"), to_attr="ordered_corrections")).order_by("-created_at", "id")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.labour_payment_data(payment) for payment in page])

    def post(self, request, company_id, person_id):
        serializer = LabourPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_labour_payment(actor=request.user, company_id=company_id, person_id=person_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class LabourPaymentCorrectionView(GarageView):
    def get(self, request, company_id, person_id, payment_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        person = services.list_labour_people(actor=request.user, company_id=company_id).filter(pk=person_id).first()
        payment = person.payments.filter(pk=payment_id).first() if person else None
        if payment is None:
            raise NotFound("Labour payment not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = payment.corrections.select_related("previous_event", "replacement_event").order_by("version")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([{"id": str(row.pk), "version": row.version,
            "previous_amount": format(row.previous_event.amount, ".2f"), "replacement_amount": format(row.replacement_event.amount, ".2f") if row.replacement_event else None,
            "reason": row.reason, "actor_id": str(row.actor_id), "created_at": row.created_at.isoformat()} for row in page])

    def post(self, request, company_id, person_id, payment_id):
        serializer = LabourPaymentCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.correct_labour_payment(actor=request.user, company_id=company_id, person_id=person_id, payment_id=payment_id,
            expected_event_id=data["expected_event_id"], outcome=data["outcome"], reason=data["reason"], replacement=data.get("replacement"),
            key=request.headers.get("Idempotency-Key"), path=request.path)
        return Response(result.body, status=result.status)


class JobListCreateView(GarageView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        rows = services.list_jobs(actor=request.user, company_id=company_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.job_data(job) for job in page])

    def post(self, request, company_id):
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_job(actor=request.user, company_id=company_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobDashboardSummaryView(GarageView):
    def get(self, request, company_id):
        if set(request.query_params) - {"branch_id"}:
            raise serializers.ValidationError({"query": "Only the Branch filter is supported."})
        branch_id = request.query_params.get("branch_id")
        if branch_id:
            try:
                from uuid import UUID
                branch_id = str(UUID(branch_id))
            except (TypeError, ValueError):
                raise serializers.ValidationError({"branch_id": "A valid Branch id is required."})
        return Response(services.job_summary(actor=request.user, company_id=company_id, branch_id=branch_id))


class JobStatusView(GarageView):
    def post(self, request, company_id, job_id):
        serializer = StatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.change_status(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobDetailView(GarageView):
    def get(self, request, company_id, job_id):
        if request.query_params:
            raise serializers.ValidationError({"query": "No filters are supported."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        return Response(services.job_detail(job))


class JobWorkView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(job.work_entries.order_by("created_at", "id"), request, view=self)
        return paginator.get_paginated_response([services.work_data(entry) for entry in page])

    def post(self, request, company_id, job_id):
        serializer = WorkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.add_work(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobStatusHistoryView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(job.status_history.order_by("version"), request, view=self)
        return paginator.get_paginated_response([{"version": row.version, "from_status": row.from_status, "to_status": row.to_status, "actor_id": str(row.actor_id), "created_at": row.created_at.isoformat()} for row in page])


class JobStockCostView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(job.stock_cost_links.select_related("expense").prefetch_related("expense__corrections").order_by("created_at", "id"), request, view=self)
        return paginator.get_paginated_response([services.stock_cost_data(link) for link in page])

    def post(self, request, company_id, job_id):
        serializer = StockCostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.link_stock_cost(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobStockCostCreateView(GarageView):
    def post(self, request, company_id, job_id):
        serializer = VehicleExpenseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_stock_cost(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobCustomerChargeView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(job.customer_charges.order_by("-version"), request, view=self)
        return paginator.get_paginated_response([services.charge_data(charge) for charge in page])

    def post(self, request, company_id, job_id):
        serializer = CustomerChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.record_charge(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobCustomerReceiptView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = job.customer_receipts.select_related("event").prefetch_related(Prefetch("corrections", queryset=GarageReceiptCorrection.objects.select_related("replacement_event", "previous_event").order_by("-version"), to_attr="ordered_corrections")).order_by("created_at", "id")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.receipt_data(receipt) for receipt in page])

    def post(self, request, company_id, job_id):
        serializer = CustomerReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.record_receipt(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class GarageReceiptCorrectionView(GarageView):
    def get(self, request, company_id, job_id, receipt_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        receipt = job.customer_receipts.filter(pk=receipt_id).first()
        if receipt is None:
            raise NotFound("Garage receipt not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = receipt.corrections.select_related("previous_event", "replacement_event").order_by("version")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([{"id": str(row.pk), "version": row.version,
            "previous_amount": format(row.previous_event.amount, ".2f"), "replacement_amount": format(row.replacement_event.amount, ".2f") if row.replacement_event else None,
            "reason": row.reason, "actor_id": str(row.actor_id), "created_at": row.created_at.isoformat()} for row in page])

    def post(self, request, company_id, job_id, receipt_id):
        serializer = LabourPaymentCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.correct_receipt(actor=request.user, company_id=company_id, job_id=job_id, receipt_id=receipt_id,
            expected_event_id=data["expected_event_id"], outcome=data["outcome"], reason=data["reason"], replacement=data.get("replacement"),
            key=request.headers.get("Idempotency-Key"), path=request.path)
        return Response(result.body, status=result.status)


class JobCustomerCostView(GarageView):
    def get(self, request, company_id, job_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        amount_field = DecimalField(max_digits=38, decimal_places=2)
        original = GarageCustomerCostPayment.objects.filter(cost_id=OuterRef("pk")).order_by().values("cost_id").annotate(total=Sum("event__amount")).values("total")
        adjustments = GarageCustomerCostPaymentCorrection.objects.filter(payment__cost_id=OuterRef("pk")).order_by().values("payment__cost_id").annotate(
            total=Sum(Coalesce(F("replacement_event__amount"), Value(Decimal("0.00")), output_field=amount_field) - F("previous_event__amount"))).values("total")
        refunds = GarageCustomerCostRefund.objects.filter(cost_id=OuterRef("pk")).order_by().values("cost_id").annotate(total=Sum("applied_amount")).values("total")
        paid = ExpressionWrapper(Coalesce(Subquery(original, output_field=amount_field), Value(Decimal("0.00")), output_field=amount_field) +
                                 Coalesce(Subquery(adjustments, output_field=amount_field), Value(Decimal("0.00")), output_field=amount_field), output_field=amount_field)
        rows = job.customer_costs.annotate(calculated_paid=paid,
            calculated_refunded=Coalesce(Subquery(refunds, output_field=amount_field), Value(Decimal("0.00")), output_field=amount_field)
        ).prefetch_related("corrections").order_by("created_at", "id")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.customer_cost_data(cost) for cost in page])

    def post(self, request, company_id, job_id):
        serializer = CustomerCostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.write_customer_cost(actor=request.user, company_id=company_id, job_id=job_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobCustomerCostRefundPreviewView(GarageView):
    def get(self, request, company_id, job_id, cost_id):
        if set(request.query_params) != {"amount"} or len(request.query_params.getlist("amount")) != 1:
            raise serializers.ValidationError({"query": "Provide one amount only."})
        serializer = CustomerCostRefundPreviewSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(services.preview_customer_cost_refund(actor=request.user, company_id=company_id, job_id=job_id,
            cost_id=cost_id, amount=serializer.validated_data["amount"]))


class JobCustomerCostRefundView(GarageView):
    def get(self, request, company_id, job_id, cost_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        cost = job.customer_costs.filter(pk=cost_id).first()
        if cost is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Customer Job cost not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        applications = AccountingApplication.objects.filter(effect_sign=1).select_related("target_event").order_by("id")
        rows = cost.refunds.select_related("event").prefetch_related(
            Prefetch("event__source_applications", queryset=applications, to_attr="refund_applications")
        ).order_by("created_at", "id")
        page = paginator.paginate_queryset(rows, request, view=self)
        results = []
        for refund in page:
            linked = getattr(refund.event, "refund_applications", [])
            income_event = linked[0].target_event if linked else None
            results.append(services.customer_cost_refund_data(refund, income_event=income_event))
        return paginator.get_paginated_response(results)

    def post(self, request, company_id, job_id, cost_id):
        serializer = CustomerCostRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_customer_cost_refund(
            actor=request.user, company_id=company_id, job_id=job_id, cost_id=cost_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class JobCustomerCostPaymentView(GarageView):
    def get(self, request, company_id, job_id, cost_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        cost = job.customer_costs.filter(pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = cost.payments.select_related("event").prefetch_related(Prefetch("corrections", queryset=GarageCustomerCostPaymentCorrection.objects.select_related("previous_event", "replacement_event").order_by("-version"), to_attr="ordered_corrections")).order_by("created_at", "id")
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([services.customer_cost_payment_data(payment) for payment in page])

    def post(self, request, company_id, job_id, cost_id):
        serializer = CustomerCostPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.pay_customer_cost(actor=request.user, company_id=company_id, job_id=job_id, cost_id=cost_id,
            key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


class JobCustomerCostPaymentCorrectionView(GarageView):
    def get(self, request, company_id, job_id, cost_id, payment_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        payment = GarageCustomerCostPayment.objects.filter(cost__job=job, cost_id=cost_id, pk=payment_id).first()
        if payment is None:
            raise NotFound("Customer Job cost payment not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(payment.corrections.select_related("previous_event", "replacement_event").order_by("version"), request, view=self)
        return paginator.get_paginated_response([{"id": str(row.pk), "version": row.version, "previous_amount": format(row.previous_event.amount, ".2f"),
            "replacement_amount": format(row.replacement_event.amount, ".2f") if row.replacement_event else None,
            "reason": row.reason, "actor_id": str(row.actor_id), "created_at": row.created_at.isoformat()} for row in page])

    def post(self, request, company_id, job_id, cost_id, payment_id):
        serializer = LabourPaymentCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.correct_customer_cost_payment(actor=request.user, company_id=company_id, job_id=job_id, cost_id=cost_id,
            payment_id=payment_id, expected_event_id=data["expected_event_id"], outcome=data["outcome"], reason=data["reason"], replacement=data.get("replacement"),
            key=request.headers.get("Idempotency-Key"), path=request.path)
        return Response(result.body, status=result.status)


class JobCustomerCostCorrectionView(GarageView):
    def get(self, request, company_id, job_id, cost_id):
        if set(request.query_params) - {"page"}:
            raise serializers.ValidationError({"query": "Unsupported query parameter."})
        from rest_framework.exceptions import NotFound
        job = services.get_job(actor=request.user, company_id=company_id, job_id=job_id)
        cost = job.customer_costs.filter(pk=cost_id).first()
        if cost is None:
            raise NotFound("Customer Job cost not found.")
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(cost.corrections.order_by("version"), request, view=self)
        return paginator.get_paginated_response([{"id": str(row.pk), "version": row.version, "amount": format(row.amount, ".2f"), "reason": row.reason, "actor_id": str(row.actor_id), "created_at": row.created_at.isoformat()} for row in page])

    def post(self, request, company_id, job_id, cost_id):
        serializer = CustomerCostCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.write_customer_cost(actor=request.user, company_id=company_id, job_id=job_id, cost_id=cost_id, key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)
