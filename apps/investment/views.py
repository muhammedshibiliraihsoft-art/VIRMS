from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.investment import services
from apps.investment.models import Investor
from apps.tenants.models import Branch

from .serializers import (
    FundCreditCorrectionCreateSerializer,
    FundLedgerQuerySerializer,
    FundMovementCreateSerializer,
    InvestorInterimCreateSerializer,
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
