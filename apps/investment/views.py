from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.investment import portal, services
from apps.investment.models import Investor, InvestorExitRequest
from apps.accounts.policy import require_action
from apps.tenants.models import Tenant
from rest_framework.exceptions import NotFound
from apps.tenants.models import Branch

from .serializers import (
    FundCreditCorrectionCreateSerializer,
    FundLedgerQuerySerializer,
    FundMovementCreateSerializer,
    InvestorInterimCreateSerializer,
    InvestorInterimPaymentCreateSerializer,
    InvestorInterimPaymentQuerySerializer,
    InvestorExitCancellationRequestSerializer,
    InvestorExitCancellationReviewSerializer,
    InvestorExitNoticeExtensionSerializer,
    InvestorExitPrincipalPaymentSerializer,
    InvestorExitLossApplicationSerializer,
    InvestorExitProfitPaymentSerializer,
    InvestorExitSettlementCloseSerializer,
    InvestorExitRequestSerializer,
    InvestorPortalBindingSerializer,
    InvestorPortalBindingRevokeSerializer,
    InvestorProfitCalendarConfigurationSerializer,
    InvestorProfitPeriodReconciliationSerializer,
    InvestorVehicleProfitPaymentSerializer,
    InvestorProfitLossOffsetSerializer,
    InvestorProfitShareAgreementSerializer,
    InvestorWriteSerializer,
)


def _query(serializer_class, query_params):
    serializer = serializer_class(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _reject_unknown(query_params, allowed):
    if set(query_params) - set(allowed):
        raise ValidationError({"query": "Unsupported query parameter."})


def _investor_data(row):
    return services._investor_data(row)


def _config_data(row):
    return {
        "id": str(row.pk),
        "investor_id": str(row.investor_id),
        "amount": format(row.amount, ".2f"),
        "effective_date": row.effective_date.isoformat(),
        "recorded_at": row.created_at.isoformat(),
        "actor_id": str(row.actor_id),
    }


class InvestmentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Pragma"] = "no-cache"
        response["Vary"] = "Cookie"
        return response

    def paginate(self, queryset, serializer):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, self.request, view=self)
        return paginator.get_paginated_response([serializer(row) for row in page])


class InvestorPortalSelfView(InvestmentAPIView):
    def get(self, request, company_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(portal.self_profile(actor=request.user, company_id=company_id))


class InvestorPortalFundHistoryView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page"})
        queryset = portal.self_fund_history(actor=request.user, company_id=company_id)
        return self.paginate(queryset, portal.fund_history_activity_data)


class InvestorPortalInterimPaymentHistoryView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page"})
        queryset = portal.self_interim_payment_history(
            actor=request.user, company_id=company_id,
        )
        return self.paginate(queryset, portal.interim_payment_activity_data)


class InvestorPortalExitRequestView(InvestmentAPIView):
    def post(self, request, company_id):
        serializer = InvestorExitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.submit_exit_request(
            actor=request.user, company_id=company_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
        )
        return Response(result.body, status=result.status)


class InvestorPortalExitCancellationRequestView(InvestmentAPIView):
    def post(self, request, company_id, exit_request_id):
        serializer = InvestorExitCancellationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.request_exit_cancellation(
            actor=request.user, company_id=company_id, exit_request_id=exit_request_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorExitCancellationReviewView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitCancellationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.review_exit_cancellation(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorExitNoticeExtensionView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitNoticeExtensionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.extend_exit_notice(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorExitSettlementPositionView(InvestmentAPIView):
    def get(self, request, company_id, investor_id, exit_request_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        from apps.investment.exit_settlement import exit_settlement_position

        return Response(exit_settlement_position(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id,
        ))


class InvestorExitSettlementCloseView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitSettlementCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.investment.exit_settlement import close_exit_settlement
        result = close_exit_settlement(actor=request.user, company_id=company_id,
            investor_id=investor_id, exit_request_id=exit_request_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data)
        return Response(result.body, status=result.status)


class InvestorExitPrincipalPaymentView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitPrincipalPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.investment.exit_settlement import record_exit_principal_payment

        result = record_exit_principal_payment(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorExitLossApplicationView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitLossApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.investment.exit_settlement import record_exit_loss_application

        data = dict(serializer.validated_data)
        data.setdefault("account_id", None)
        result = record_exit_loss_application(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **data,
        )
        return Response(result.body, status=result.status)


class InvestorExitProfitPaymentView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, exit_request_id):
        serializer = InvestorExitProfitPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.investment.exit_settlement import record_exit_profit_payment

        result = record_exit_profit_payment(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            exit_request_id=exit_request_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorExitRequestListView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        _reject_unknown(request.query_params, {"page"})
        company = Tenant.objects.filter(pk=company_id, is_active=True).first()
        if company is None:
            raise NotFound("Company not found.")
        require_action(request.user, "investment.exit.notice.extend", company=company)
        if not Investor.objects.filter(tenant=company, pk=investor_id, is_active=True).exists():
            raise NotFound("Investor not found.")
        rows = InvestorExitRequest.objects.filter(tenant=company, investor_id=investor_id).order_by("-created_at", "-id")
        return self.paginate(rows, portal._exit_request_data)


class InvestorPortalBindingView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        return Response(portal.get_binding(
            actor=request.user, company_id=company_id, investor_id=investor_id,
        ))

    def post(self, request, company_id, investor_id):
        serializer = InvestorPortalBindingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.bind_account(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorPortalBindingRevokeView(InvestmentAPIView):
    def post(self, request, company_id, binding_id):
        serializer = InvestorPortalBindingRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = portal.revoke_binding(
            actor=request.user, company_id=company_id, binding_id=binding_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitShareAgreementView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.list_profit_share_agreements(
            actor=request.user, company_id=company_id, investor_id=investor_id,
        ))

    def post(self, request, company_id, investor_id):
        serializer = InvestorProfitShareAgreementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_profit_share_agreement(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class Phase5BranchListView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page"})
        company, scope, _ = services.read_scope(actor=request.user, company_id=company_id, action="investment.fund.read")
        branches = Branch.objects.filter(tenant=company)
        if not scope.is_company_reader:
            branches = branches.filter(pk__in=scope.allowed_branch_ids)
        return self.paginate(branches.order_by("name", "id"), lambda branch: {
            "id": str(branch.pk), "tenant_id": str(branch.tenant_id), "name": branch.name,
        })


class InvestorListCreateView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page"})
        queryset = services.list_investors(actor=request.user, company_id=company_id)
        return self.paginate(queryset, _investor_data)

    def post(self, request, company_id):
        serializer = InvestorWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_investor(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorDetailView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        investor = services.get_investor(
            actor=request.user, company_id=company_id, investor_id=investor_id
        )
        return Response(_investor_data(investor))

    def patch(self, request, company_id, investor_id):
        serializer = InvestorWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data:
            raise ValidationError({"detail": "At least one profile field is required."})
        result = services.update_investor(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            values=serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorInterimConfigurationView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        _reject_unknown(request.query_params, {"page"})
        queryset = services.list_interim_configurations(
            actor=request.user, company_id=company_id, investor_id=investor_id
        )
        return self.paginate(queryset, _config_data)

    def post(self, request, company_id, investor_id):
        serializer = InvestorInterimCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_interim_configuration(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorInterimPaymentView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        _reject_unknown(request.query_params, {"period_month", "branch_id", "page"})
        filters = _query(InvestorInterimPaymentQuerySerializer, request.query_params)
        queryset = services.list_interim_payments(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            **filters,
        )
        return self.paginate(queryset, services._interim_payment_data)

    def post(self, request, company_id, investor_id):
        serializer = InvestorInterimPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_interim_payment(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitCalendarConfigurationView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.list_profit_calendar_configurations(
            actor=request.user, company_id=company_id, investor_id=investor_id,
        ))

    def post(self, request, company_id, investor_id):
        serializer = InvestorProfitCalendarConfigurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.configure_profit_calendar(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitPeriodProjectionView(InvestmentAPIView):
    def get(self, request, company_id, investor_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.list_investor_profit_period_projection(
            actor=request.user, company_id=company_id, investor_id=investor_id,
        ))


class InvestorProfitFutureAdjustmentView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, position_id):
        from .serializers import InvestorProfitFutureAdjustmentSerializer
        from .period_positions import adjust_against_future_profit
        serializer = InvestorProfitFutureAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = adjust_against_future_profit(
            actor=request.user, company_id=company_id, investor_id=investor_id, position_id=position_id,
            key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitRecoveryReceiptView(InvestmentAPIView):
    def post(self, request, company_id, investor_id, position_id):
        from .serializers import InvestorProfitRecoveryReceiptSerializer
        from .period_positions import receive_period_repayment
        serializer = InvestorProfitRecoveryReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = receive_period_repayment(
            actor=request.user, company_id=company_id, investor_id=investor_id, position_id=position_id,
            key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitPositionView(InvestmentAPIView):
    def post(self, request, company_id, investor_id):
        from .serializers import InvestorProfitPositionSerializer
        from .period_positions import confirm_period_position
        serializer = InvestorProfitPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = confirm_period_position(
            actor=request.user, company_id=company_id, investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitPeriodReconciliationView(InvestmentAPIView):
    def post(self, request, company_id, investor_id):
        serializer = InvestorProfitPeriodReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.reconcile_investor_profit_period(
            actor=request.user,
            company_id=company_id,
            investor_id=investor_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehiclePrincipalRefundReviewView(InvestmentAPIView):
    def post(self, request, company_id, sale_id):
        from .serializers import VehiclePrincipalRefundReviewSerializer
        from .refund_reviews import confirm_principal_refund_review
        serializer = VehiclePrincipalRefundReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = confirm_principal_refund_review(
            actor=request.user, company_id=company_id, sale_id=sale_id,
            key=request.headers.get("Idempotency-Key"), path=request.path, **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class VehicleCapitalRecoveryView(InvestmentAPIView):
    def post(self, request, company_id, sale_id):
        from .serializers import VehicleCapitalRecoverySerializer
        serializer = VehicleCapitalRecoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_vehicle_capital_recovery(
            actor=request.user, company_id=company_id, sale_id=sale_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorVehicleProfitPaymentView(InvestmentAPIView):
    def post(self, request, company_id, result_confirmation_id):
        serializer = InvestorVehicleProfitPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_vehicle_profit_payment(
            actor=request.user,
            company_id=company_id,
            result_confirmation_id=result_confirmation_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class InvestorProfitLossOffsetView(InvestmentAPIView):
    def get(self, request, company_id, loss_result_id):
        if request.query_params:
            raise ValidationError({"query": "No filters are supported."})
        return Response(services.list_profit_loss_offset_targets(
            actor=request.user,
            company_id=company_id,
            loss_result_id=loss_result_id,
        ))

    def post(self, request, company_id, loss_result_id):
        serializer = InvestorProfitLossOffsetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_profit_loss_offset(
            actor=request.user,
            company_id=company_id,
            loss_result_id=loss_result_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class FundCreditListCreateView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page", "branch_id", "investor_id"})
        filters = _query(FundLedgerQuerySerializer, request.query_params)
        queryset = services.list_fund_credits(
            actor=request.user, company_id=company_id, **filters
        )
        return self.paginate(queryset, services._credit_data)

    def post(self, request, company_id):
        serializer = FundMovementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_fund_credit(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class FundCreditCorrectionCreateView(InvestmentAPIView):
    def post(self, request, company_id, credit_id):
        serializer = FundCreditCorrectionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.correct_fund_credit_investor(
            actor=request.user,
            company_id=company_id,
            credit_id=credit_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class FundSummaryView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"investor_id", "branch_id"})
        filters = _query(FundLedgerQuerySerializer, request.query_params)
        return Response(
            services.fund_summary(actor=request.user, company_id=company_id, **filters)
        )


class PrincipalReturnListCreateView(InvestmentAPIView):
    def get(self, request, company_id):
        _reject_unknown(request.query_params, {"page", "branch_id", "investor_id"})
        filters = _query(FundLedgerQuerySerializer, request.query_params)
        queryset = services.list_principal_returns(
            actor=request.user, company_id=company_id, **filters
        )
        return self.paginate(queryset, services._return_data)

    def post(self, request, company_id):
        serializer = FundMovementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_principal_return(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)
