from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce

from apps.vehicles import services
from apps.vehicles.models import VehicleExpenseCorrection

from .serializers import (
    VehicleBranchMoveSerializer,
    VehicleListQuerySerializer,
    VehiclePurchasePaymentSerializer,
    VehiclePurchaseWriteSerializer,
    VehicleExpensePaymentSerializer,
    VehicleExpenseRefundSerializer,
    VehicleExpenseWriteSerializer,
    VehicleExpenseCorrectionSerializer,
    VehiclePurchaseRefundSerializer,
    VehiclePurchaseCorrectionSerializer,
    VehicleSaleCorrectionSerializer,
    VehicleSaleReceiptSerializer,
    VehicleSaleRefundSerializer,
    VehicleSaleWriteSerializer,
    VehicleWriteSerializer,
)


def _query(query_params):
    serializer = VehicleListQuerySerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class VehicleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Pragma"] = "no-cache"
        response["Vary"] = "Cookie"
        return response

    def paginate(self, rows, serializer):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(rows, self.request, view=self)
        return paginator.get_paginated_response([serializer(row) for row in page])


class VehicleListCreateView(VehicleAPIView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page", "branch_id", "search"}:
            raise ValidationError({"query": "Unsupported query parameter."})
        filters = _query(request.query_params)
        rows = services.list_vehicles(
            actor=request.user, company_id=company_id, **filters
        )
        return self.paginate(rows, services._vehicle_data)

    def post(self, request, company_id):
        serializer = VehicleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "branch_id" not in data:
            raise ValidationError({"branch_id": "A Branch is required."})
        result = services.create_vehicle(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            branch_id=data["branch_id"],
            registration=data["registration"],
            model=data["model"],
        )
        return Response(result.body, status=result.status)


class VehicleDetailView(VehicleAPIView):
    def get(self, request, company_id, vehicle_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(
            services.get_vehicle(
                actor=request.user, company_id=company_id, vehicle_id=vehicle_id
            )
        )

    def patch(self, request, company_id, vehicle_id):
        serializer = VehicleWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if "branch_id" in values:
            raise ValidationError({"branch_id": "Use the Branch movement endpoint."})
        if not values:
            raise ValidationError({"detail": "At least one Vehicle field is required."})
        result = services.update_vehicle(
            actor=request.user,
            company_id=company_id,
            vehicle_id=vehicle_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            values=values,
        )
        return Response(result.body, status=result.status)


class VehicleBranchMovementView(VehicleAPIView):
    def post(self, request, company_id, vehicle_id):
        serializer = VehicleBranchMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.move_vehicle(
            actor=request.user,
            company_id=company_id,
            vehicle_id=vehicle_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehiclePurchaseListCreateView(VehicleAPIView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page", "branch_id", "vehicle_id"}:
            raise ValidationError({"query": "Unsupported query parameter."})
        branch_id = request.query_params.get("branch_id")
        vehicle_id = request.query_params.get("vehicle_id")
        if branch_id:
            serializer = VehicleListQuerySerializer(data={"branch_id": branch_id})
            serializer.is_valid(raise_exception=True)
            branch_id = serializer.validated_data["branch_id"]
        if vehicle_id:
            serializer = VehicleListQuerySerializer(data={"vehicle_id": vehicle_id})
            serializer.is_valid(raise_exception=True)
            vehicle_id = serializer.validated_data["vehicle_id"]
        rows = services.list_purchases(
            actor=request.user, company_id=company_id, branch_id=branch_id, vehicle_id=vehicle_id
        )
        return self.paginate(rows, services._purchase_data)

    def post(self, request, company_id):
        serializer = VehiclePurchaseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.create_purchase(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **data,
        )
        return Response(result.body, status=result.status)


class VehiclePurchaseDetailView(VehicleAPIView):
    def get(self, request, company_id, purchase_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(
            services.get_purchase(
                actor=request.user, company_id=company_id, purchase_id=purchase_id
            )
        )


class VehiclePurchaseInstallmentView(VehicleAPIView):
    def post(self, request, company_id, purchase_id):
        serializer = VehiclePurchasePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_purchase_installment(
            actor=request.user,
            company_id=company_id,
            purchase_id=purchase_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehiclePurchaseRefundView(VehicleAPIView):
    def post(self, request, company_id, purchase_id):
        serializer = VehiclePurchaseRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_purchase_refund(
            actor=request.user, company_id=company_id, purchase_id=purchase_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehiclePurchaseCorrectionView(VehicleAPIView):
    def post(self, request, company_id, purchase_id):
        serializer = VehiclePurchaseCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.correct_purchase(
            actor=request.user, company_id=company_id, purchase_id=purchase_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleExpenseListCreateView(VehicleAPIView):
    def get(self, request, company_id, vehicle_id):
        if set(request.query_params) - {"page", "branch_id"}:
            raise ValidationError({"query": "Unsupported query parameter."})
        branch_id = request.query_params.get("branch_id")
        if branch_id:
            branch_id = _query({"branch_id": branch_id})["branch_id"]
        rows = services.list_expenses(
            actor=request.user, company_id=company_id,
            vehicle_id=vehicle_id, branch_id=branch_id,
        )
        current_capital = VehicleExpenseCorrection.objects.filter(
            expense_id=OuterRef("pk")
        ).order_by("-version", "-id").values("running_capital_amount")[:1]
        total = rows.order_by().aggregate(
            total=Sum(Coalesce(Subquery(current_capital), "running_capital_amount"))
        )["total"]
        response = self.paginate(rows, services._expense_data)
        response.data["running_capital_total"] = format(total or 0, ".2f")
        return response

    def post(self, request, company_id, vehicle_id):
        serializer = VehicleExpenseWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_vehicle_expense(
            actor=request.user,
            company_id=company_id,
            vehicle_id=vehicle_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleExpenseDetailView(VehicleAPIView):
    def get(self, request, company_id, expense_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.get_expense(
            actor=request.user, company_id=company_id, expense_id=expense_id
        ))


class VehicleExpenseInstallmentView(VehicleAPIView):
    def post(self, request, company_id, expense_id):
        serializer = VehicleExpensePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_expense_installment(
            actor=request.user, company_id=company_id, expense_id=expense_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleExpenseRefundView(VehicleAPIView):
    def post(self, request, company_id, expense_id):
        serializer = VehicleExpenseRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_expense_refund(
            actor=request.user, company_id=company_id, expense_id=expense_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleExpenseCorrectionView(VehicleAPIView):
    def post(self, request, company_id, expense_id):
        serializer = VehicleExpenseCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.correct_vehicle_expense(
            actor=request.user, company_id=company_id, expense_id=expense_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleSaleListCreateView(VehicleAPIView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page", "branch_id"}:
            raise ValidationError({"query": "Unsupported query parameter."})
        branch_id = request.query_params.get("branch_id")
        if branch_id:
            branch_id = _query({"branch_id": branch_id})["branch_id"]
        return self.paginate(
            services.list_sales(actor=request.user, company_id=company_id, branch_id=branch_id),
            services._sale_data,
        )

    def post(self, request, company_id):
        serializer = VehicleSaleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_sale(
            actor=request.user, company_id=company_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleSaleDetailView(VehicleAPIView):
    def get(self, request, company_id, sale_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.get_sale(actor=request.user, company_id=company_id, sale_id=sale_id))


class VehicleSaleReceiptView(VehicleAPIView):
    def post(self, request, company_id, sale_id):
        serializer = VehicleSaleReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_sale_receipt(
            actor=request.user, company_id=company_id, sale_id=sale_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleSaleRefundView(VehicleAPIView):
    def post(self, request, company_id, sale_id):
        serializer = VehicleSaleRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_sale_refund(
            actor=request.user, company_id=company_id, sale_id=sale_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleSaleCorrectionView(VehicleAPIView):
    def post(self, request, company_id, sale_id):
        serializer = VehicleSaleCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.correct_sale(
            actor=request.user, company_id=company_id, sale_id=sale_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehiclePaymentAccountPreferenceView(VehicleAPIView):
    def get(self, request, company_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.get_payment_account_preference(actor=request.user, company_id=company_id))
