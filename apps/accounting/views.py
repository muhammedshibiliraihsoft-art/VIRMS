from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, localcontext
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db.models import Case, Count, DecimalField, ExpressionWrapper, F, Q, Subquery, Sum, Value, When
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingApplication,
    AccountingCategory,
    AccountingEvent,
)
from apps.tenants.models import Branch

from . import services
from .policies import AccountingAction, accounting_scope
from .serializers import (
    AccountCreateSerializer,
    AccountingResultQuerySerializer,
    ApplicationReallocationSerializer,
    ArchiveSerializer,
    CategoryCreateSerializer,
    CompanyPeriodConfirmationSerializer,
    OwnerDistributionConfigurationSerializer,
    OwnerDistributionPaymentSerializer,
    EventCorrectionSerializer,
    IncomeExpenseCreateSerializer,
    OpeningBalanceCorrectionSerializer,
    ReceiptPaymentCreateSerializer,
    TransferCreateSerializer,
    TransferCorrectionSerializer,
    TransferReversalSerializer,
    OpeningBalanceCreateSerializer,
    EventFilterSerializer,
    replacement_serializer,
)


COMPANY_TIMEZONE = ZoneInfo("Asia/Kolkata")


class AccountingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Pragma"] = "no-cache"
        response["Vary"] = "Cookie"
        return response

    def scope(
        self,
        request,
        company_id,
        action=AccountingAction.READ,
        *,
        permission_action="accounting.event.read",
        branch_id=None,
        resource=None,
    ):
        return accounting_scope(
            request.user,
            company_id,
            action,
            branch_id=branch_id,
            permission_action=permission_action,
            resource=resource,
        )

    def paginate(self, queryset, serializer):
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(queryset, self.request, view=self)
        data = [serializer(row) for row in page]
        return paginator.get_paginated_response(data)


class AccountingBranchListView(AccountingAPIView):
    """Return only Branch identities available to this Accounting role."""

    def get(self, request, company_id):
        if set(request.query_params) - {"page"}:
            raise ValidationError({"query": "Only the page filter is supported."})
        scope = self.scope(request, company_id)
        queryset = Branch.objects.filter(tenant_id=scope.company.pk)
        if not scope.is_company_wide_reader:
            queryset = queryset.filter(pk__in=scope.allowed_branch_ids)
        queryset = queryset.order_by("name", "id")
        return self.paginate(
            queryset,
            lambda row: {
                "id": str(row.pk),
                "tenant_id": str(row.tenant_id),
                "name": row.name,
            },
        )


def _account_data(account, *, include_balance, balance=None, include_history=False, has_history=False):
    data = {
        "id": str(account.pk),
        "account_type": account.account_type,
        "label": account.label,
        "is_active": account.is_active,
    }
    if include_balance:
        data["current_balance"] = format(balance or Decimal("0.00"), ".2f")
        data["balance_as_of"] = timezone.now().isoformat()
    if include_history:
        data["has_history"] = has_history
    return data


def _event_list_data(event):
    data = services.event_data(event)
    data.update(
        {
            "branch_name": event.branch.name if event.branch_id else None,
            "category_name": event.category.label if event.category_id else None,
        }
    )
    movements = list(event.movements.all())
    if len(movements) == 1:
        data["account_id"] = str(movements[0].account_id)
    elif len(movements) == 2:
        outgoing = next((row for row in movements if row.delta < 0), None)
        incoming = next((row for row in movements if row.delta > 0), None)
        data["from_account_id"] = str(outgoing.account_id) if outgoing else None
        data["to_account_id"] = str(incoming.account_id) if incoming else None
    return data


def _event_detail_data(event):
    data = _event_list_data(event)
    movements = list(
        event.movements.select_related("account").order_by("account_id", "id")
    )
    data["movements"] = [
        {
            "id": str(row.pk),
            "account_id": str(row.account_id),
            "account_label": row.account.label,
            "delta": format(row.delta, ".2f"),
        }
        for row in movements
    ]
    source_apps = list(
        AccountingApplication.objects.filter(source_event=event).order_by("id")
    )
    target_apps = list(
        AccountingApplication.objects.filter(target_event=event).order_by("id")
    )
    applications = {row.pk: row for row in (*source_apps, *target_apps)}
    data["applications"] = [
        {
            "id": str(row.pk),
            "source_event_id": str(row.source_event_id),
            "target_event_id": str(row.target_event_id),
            "amount": format(row.amount, ".2f"),
            "effect_sign": row.effect_sign,
            "reversal_of_id": str(row.reversal_of_id) if row.reversal_of_id else None,
            "recorded_at": row.recorded_at.isoformat(),
            "reason": row.reason,
        }
        for row in sorted(applications.values(), key=lambda row: (row.recorded_at, str(row.pk)))
    ]
    data["reversal_event_ids"] = [
        str(pk)
        for pk in event.reversal_rows.order_by("id").values_list("id", flat=True)
    ]
    data["replacement_event_ids"] = [
        str(pk)
        for pk in event.replacement_rows.order_by("id").values_list("id", flat=True)
    ]
    if (
        event.event_type in (AccountingEvent.EventType.INCOME, AccountingEvent.EventType.EXPENSE)
        and event.effect_sign == 1
        and not AccountingEvent.objects.filter(
            tenant_id=event.tenant_id,
            reversal_of=event,
        ).exists()
        and not AccountingEvent.objects.filter(
            tenant_id=event.tenant_id,
            replaces_event=event,
        ).exists()
    ):
        data["outstanding_amount"] = format(
            event.amount - services._application_total(event), ".2f"
        )
    return data


class AccountListCreateView(AccountingAPIView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page"}:
            raise ValidationError({"query": "Only the page filter is supported."})
        scope = self.scope(request, company_id)
        queryset = AccountingAccount.objects.filter(tenant=scope.company).order_by(
            "account_type", "label", "id"
        )
        include_balance = scope.is_company_accountant or scope.is_company_wide_reader
        include_history = scope.is_company_accountant
        summaries = {}
        if include_balance or include_history:
            summaries = {
                row["account_id"]: row
                for row in AccountMovement.objects.filter(tenant=scope.company)
                .values("account_id")
                .annotate(total=Sum("delta"), movement_count=Count("id"))
            }
        else:
            summaries = {}
        return self.paginate(
            queryset,
            lambda row: _account_data(
                row,
                include_balance=include_balance,
                balance=summaries.get(row.pk, {}).get("total"),
                include_history=include_history,
                has_history=summaries.get(row.pk, {}).get("movement_count", 0) > 0,
            ),
        )

    def post(self, request, company_id):
        serializer = AccountCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_account(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class AccountArchiveView(AccountingAPIView):
    def patch(self, request, company_id, account_id):
        serializer = ArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.archive_account(
            actor=request.user,
            company_id=company_id,
            account_id=account_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
        )
        return Response(result.body, status=result.status)


class CategoryListCreateView(AccountingAPIView):
    def get(self, request, company_id):
        if set(request.query_params) - {"page"}:
            raise ValidationError({"query": "Only the page filter is supported."})
        scope = self.scope(request, company_id)
        queryset = AccountingCategory.objects.filter(tenant=scope.company)
        if not (scope.is_company_accountant or scope.is_company_wide_reader):
            queryset = queryset.filter(is_active=True)
        queryset = queryset.order_by("kind", "label", "id")
        return self.paginate(
            queryset,
            lambda row: {
                "id": str(row.pk),
                "kind": row.kind,
                "label": row.label,
                "is_active": row.is_active,
            },
        )

    def post(self, request, company_id):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.create_category(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class CategoryArchiveView(AccountingAPIView):
    def patch(self, request, company_id, category_id):
        serializer = ArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.archive_category(
            actor=request.user,
            company_id=company_id,
            category_id=category_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
        )
        return Response(result.body, status=result.status)


class EventListView(AccountingAPIView):
    filter_names = {
        "page",
        "event_type",
        "branch_id",
        "category_id",
        "account_id",
        "effective_after",
        "effective_before",
    }

    def get(self, request, company_id):
        unknown = set(request.query_params) - self.filter_names
        if unknown:
            raise ValidationError({"query": f"Unsupported filters: {', '.join(sorted(unknown))}."})
        filter_serializer = EventFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        filters = filter_serializer.validated_data
        branch_id = filters.get("branch_id")
        scope = self.scope(request, company_id, branch_id=branch_id)
        queryset = AccountingEvent.objects.filter(tenant=scope.company).select_related(
            "branch", "category"
        ).prefetch_related("movements")
        if branch_id is None:
            queryset = scope.filter_branch_records(queryset, field="branch_id")
        else:
            queryset = scope.filter_branch_records(
                queryset,
                field="branch_id",
                branch_id=branch_id,
            )
        event_type = filters.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        category_id = filters.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        account_id = filters.get("account_id")
        if account_id:
            queryset = queryset.filter(movements__account_id=account_id).distinct()
        after = filters.get("effective_after")
        before = filters.get("effective_before")
        if after:
            queryset = queryset.filter(effective_at__gte=after)
        if before:
            queryset = queryset.filter(effective_at__lt=before)
        queryset = queryset.order_by("-effective_at", "id")
        return self.paginate(queryset, _event_list_data)


class EventDetailView(AccountingAPIView):
    def get(self, request, company_id, event_id):
        event = AccountingEvent.objects.filter(
            tenant_id=company_id,
            pk=event_id,
        ).select_related("branch", "category", "actor", "module_revision").first()
        if event is None:
            raise NotFound("Accounting event not found.")
        scope = self.scope(request, company_id, resource=event)
        scope.validate_record(event)
        return Response(_event_detail_data(event))


class IncomeListCreateView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = IncomeExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        serializer.validated_data.setdefault("effective_at", None)
        result = services.create_income_or_expense(
            actor=request.user,
            company_id=company_id,
            kind="INCOME",
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class ExpenseListCreateView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = IncomeExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        serializer.validated_data.setdefault("effective_at", None)
        result = services.create_income_or_expense(
            actor=request.user,
            company_id=company_id,
            kind="EXPENSE",
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class ReceiptListCreateView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = ReceiptPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        result = services.create_receipt_or_payment(
            actor=request.user,
            company_id=company_id,
            kind="RECEIPT",
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class PaymentListCreateView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = ReceiptPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        result = services.create_receipt_or_payment(
            actor=request.user,
            company_id=company_id,
            kind="PAYMENT",
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class OpeningBalanceView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = OpeningBalanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        result = services.create_opening_balance(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class TransferView(AccountingAPIView):
    def post(self, request, company_id):
        serializer = TransferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.setdefault("branch_id", None)
        result = services.create_transfer(
            actor=request.user,
            company_id=company_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class EventCorrectionView(AccountingAPIView):
    allowed_event_types = (
        AccountingEvent.EventType.INCOME,
        AccountingEvent.EventType.EXPENSE,
    )
    serializer_class = EventCorrectionSerializer

    def post(self, request, company_id, event_id):
        event = AccountingEvent.objects.filter(
            tenant_id=company_id,
            pk=event_id,
            event_type__in=self.allowed_event_types,
        ).select_related("branch").first()
        if event is None:
            raise NotFound("Accounting event not found.")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        replacement = data.get("replacement")
        if replacement is not None:
            replacement_type = replacement_serializer(event.event_type)
            if replacement_type is None:
                raise ValidationError({"replacement": "Unsupported event type."})
            replacement_serializer_instance = replacement_type(data=replacement)
            replacement_serializer_instance.is_valid(raise_exception=True)
            replacement = replacement_serializer_instance.validated_data
        elif (
            event.event_type == AccountingEvent.EventType.OPENING_BALANCE
            and data["outcome"] == "REVERSE_ONLY"
        ):
            replacement = {"amount": Decimal("0.00")}
        result = services.correct_event(
            actor=request.user,
            company_id=company_id,
            event_id=event_id,
            allowed_event_types=self.allowed_event_types,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            outcome=data["outcome"],
            event_occurred=data["event_occurred"],
            reason=data["reason"],
            replacement=replacement,
        )
        return Response(result.body, status=result.status)


class ReceiptCorrectionView(EventCorrectionView):
    allowed_event_types = (AccountingEvent.EventType.RECEIPT,)


class PaymentCorrectionView(EventCorrectionView):
    allowed_event_types = (AccountingEvent.EventType.PAYMENT,)


class TransferCorrectionView(EventCorrectionView):
    allowed_event_types = (AccountingEvent.EventType.TRANSFER,)
    serializer_class = TransferCorrectionSerializer


class OpeningBalanceCorrectionView(AccountingAPIView):
    def post(self, request, company_id, event_id):
        event = AccountingEvent.objects.filter(
            tenant_id=company_id,
            pk=event_id,
            event_type=AccountingEvent.EventType.OPENING_BALANCE,
        ).first()
        if event is None:
            raise NotFound("Opening Balance event not found.")
        serializer = OpeningBalanceCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.correct_event(
            actor=request.user,
            company_id=company_id,
            event_id=event_id,
            allowed_event_types=(AccountingEvent.EventType.OPENING_BALANCE,),
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            outcome=data["outcome"],
            event_occurred=data["event_occurred"],
            reason=data["reason"],
            replacement={
                "amount": data["replacement_amount"],
                "source_reference": data["source_reference"],
            },
        )
        return Response(result.body, status=result.status)


class TransferReversalView(AccountingAPIView):
    def post(self, request, company_id, event_id):
        event = AccountingEvent.objects.filter(
            tenant_id=company_id,
            pk=event_id,
            event_type=AccountingEvent.EventType.TRANSFER,
        ).first()
        if event is None:
            raise NotFound("Transfer event not found.")
        serializer = TransferReversalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = services.correct_event(
            actor=request.user,
            company_id=company_id,
            event_id=event_id,
            allowed_event_types=(AccountingEvent.EventType.TRANSFER,),
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            outcome=data["outcome"],
            event_occurred=data["event_occurred"],
            reason=data["reason"],
            replacement=None,
        )
        return Response(result.body, status=result.status)


class ApplicationReallocationView(AccountingAPIView):
    def post(self, request, company_id, application_id):
        serializer = ApplicationReallocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.reallocate_application(
            actor=request.user,
            company_id=company_id,
            application_id=application_id,
            key=request.headers.get("Idempotency-Key"),
            path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class AccountingResultView(AccountingAPIView):
    def get(self, request, company_id):
        serializer = AccountingResultQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        branch_id = data.get("branch_id")
        scope = self.scope(
            request,
            company_id,
            AccountingAction.REPORT,
            permission_action="accounting.report.read",
            branch_id=branch_id,
        )
        if not (scope.is_company_accountant or scope.is_company_wide_reader):
            if branch_id is None:
                if len(scope.allowed_branch_ids) != 1:
                    raise ValidationError({"branch_id": "Select one authorized Branch."})
                branch_id = next(iter(scope.allowed_branch_ids))
            elif branch_id not in scope.allowed_branch_ids:
                raise NotFound("Branch not found.")
        local_start, local_end = _period_bounds(data["period"], data["year"], data.get("month"))
        start = local_start.astimezone(datetime_timezone.utc)
        end = local_end.astimezone(datetime_timezone.utc)
        queryset = AccountingEvent.objects.filter(
            tenant=scope.company,
            effective_at__gte=start,
            effective_at__lt=end,
        ).exclude(owner_distribution_payment__isnull=False)
        if branch_id is not None:
            queryset = queryset.filter(branch_id=branch_id)
        elif not (scope.is_company_accountant or scope.is_company_wide_reader):
            raise ValidationError({"branch_id": "Branch scope is required."})
        amount_field = DecimalField(max_digits=38, decimal_places=2)
        net_amount = ExpressionWrapper(
            F("amount") * F("effect_sign"),
            output_field=amount_field,
        )
        from django.contrib.postgres.aggregates import ArrayAgg
        aggregate_kwargs = {
            "income": Sum(
                Case(
                    When(
                        event_type__in=(
                            AccountingEvent.EventType.INCOME,
                            AccountingEvent.EventType.VEHICLE_COMPANY_SHARE,
                        ),
                        then=net_amount,
                    ),
                    default=Value(Decimal("0.00")),
                    output_field=amount_field,
                )
            ),
            "expense": Sum(
                Case(
                    When(event_type=AccountingEvent.EventType.EXPENSE, then=net_amount),
                    default=Value(Decimal("0.00")),
                    output_field=amount_field,
                )
            ),
            "income_event_count": Count("id", filter=Q(event_type__in=(AccountingEvent.EventType.INCOME, AccountingEvent.EventType.VEHICLE_COMPANY_SHARE))),
            "expense_event_count": Count("id", filter=Q(event_type=AccountingEvent.EventType.EXPENSE)),
            "corrected_event_count": Count("id", filter=Q(replaces_event__isnull=False)),
            "reversal_event_count": Count("id", filter=Q(reversal_of__isnull=False)),
        }
        if branch_id is None:
            aggregate_kwargs.update(
                source_ids=ArrayAgg("id", ordering=("id",), default=[]),
                source_types=ArrayAgg("event_type", ordering=("id",), default=[]),
                source_amounts=ArrayAgg("amount", ordering=("id",), default=[]),
                source_signs=ArrayAgg("effect_sign", ordering=("id",), default=[]),
                source_effective_ats=ArrayAgg("effective_at", ordering=("id",), default=[]),
            )
        aggregate_values = queryset.aggregate(**aggregate_kwargs)
        income = aggregate_values["income"] or Decimal("0.00")
        expense = aggregate_values["expense"] or Decimal("0.00")
        # Individual Accounting amounts support 38 digits. The default
        # Decimal context has only 28 digits and silently rounds this result.
        with localcontext() as context:
            context.prec = max(80, len(income.as_tuple().digits) + 2, len(expense.as_tuple().digits) + 2)
            result = income - expense
        from apps.accounting.company_periods import event_source_version_from_rows
        source_version = event_source_version_from_rows(
            ids=aggregate_values["source_ids"], types=aggregate_values["source_types"],
            amounts=aggregate_values["source_amounts"], signs=aggregate_values["source_signs"],
            effective_ats=aggregate_values["source_effective_ats"],
        ) if branch_id is None else None
        movement_rows = AccountMovement.objects.filter(
            tenant=scope.company,
            event__effective_at__gte=start,
            event__effective_at__lt=end,
        ).exclude(event__event_type=AccountingEvent.EventType.OPENING_BALANCE)
        if branch_id is not None:
            movement_rows = movement_rows.filter(event__branch_id=branch_id)
        zero_amount = Value(Decimal("0.00"), output_field=amount_field)
        movement_values = movement_rows.aggregate(
            cash_inflow=Sum(Case(When(delta__gt=0, then=F("delta")), default=zero_amount, output_field=amount_field)),
            cash_outflow=Sum(Case(When(delta__lt=0, then=-F("delta")), default=zero_amount, output_field=amount_field)),
            net_movement=Sum("delta", output_field=amount_field),
            transaction_event_count=Count("event_id", distinct=True),
        )
        receipt_application_sources = AccountingApplication.objects.filter(
            tenant=scope.company,
            source_event__effective_at__gte=start,
            source_event__effective_at__lt=end,
            source_event__event_type=AccountingEvent.EventType.RECEIPT,
            target_event__event_type__in=(AccountingEvent.EventType.INCOME, AccountingEvent.EventType.VEHICLE_COMPANY_SHARE),
        )
        payment_application_sources = AccountingApplication.objects.filter(
            tenant=scope.company,
            source_event__effective_at__gte=start,
            source_event__effective_at__lt=end,
            source_event__event_type=AccountingEvent.EventType.PAYMENT,
            target_event__event_type=AccountingEvent.EventType.EXPENSE,
        )
        if branch_id is not None:
            receipt_application_sources = receipt_application_sources.filter(source_event__branch_id=branch_id)
            payment_application_sources = payment_application_sources.filter(source_event__branch_id=branch_id)
        actual_receipts = AccountMovement.objects.filter(
            tenant=scope.company,
            event_id__in=Subquery(receipt_application_sources.values("source_event_id")),
        ).aggregate(total=Sum("delta", output_field=amount_field))["total"] or Decimal("0.00")
        actual_payments = AccountMovement.objects.filter(
            tenant=scope.company,
            event_id__in=Subquery(payment_application_sources.values("source_event_id")),
        ).aggregate(total=Sum("delta", output_field=amount_field))["total"] or Decimal("0.00")
        reallocation_event_count = AccountingApplication.objects.filter(
            tenant=scope.company,
            recorded_at__gte=start,
            recorded_at__lt=end,
            effect_sign=-1,
        )
        if branch_id is not None:
            reallocation_event_count = reallocation_event_count.filter(source_event__branch_id=branch_id)
        response = Response(
            {
                "period": data["period"],
                "year": data["year"],
                "month": data.get("month"),
                "period_start": local_start.date().isoformat(),
                "period_end": local_end.date().isoformat(),
                "branch_id": str(branch_id) if branch_id else None,
                "timezone": "Asia/Kolkata",
                "starts_at": start.isoformat(),
                "ends_before": end.isoformat(),
                "income_amount": format(income, ".2f"),
                "expense_amount": format(expense, ".2f"),
                "accounting_result_amount": format(result, ".2f"),
                "income_event_count": aggregate_values["income_event_count"],
                "expense_event_count": aggregate_values["expense_event_count"],
                "actual_receipts_amount": format(actual_receipts, ".2f"),
                "actual_payments_amount": format(-actual_payments, ".2f"),
                "transaction_event_count": movement_values["transaction_event_count"],
                "cash_inflow_amount": format(movement_values["cash_inflow"] or Decimal("0.00"), ".2f"),
                "cash_outflow_amount": format(movement_values["cash_outflow"] or Decimal("0.00"), ".2f"),
                "net_movement_amount": format(movement_values["net_movement"] or Decimal("0.00"), ".2f"),
                "corrected_event_count": aggregate_values["corrected_event_count"],
                "reversal_event_count": aggregate_values["reversal_event_count"],
                "reallocation_event_count": reallocation_event_count.count(),
                "source_version": source_version,
                "currency": "INR",
                "scope": "recorded_accounting_events",
            }
        )
        return response


class AccountingMonthlyTrendView(AccountingAPIView):
    """Return eight selected-scope monthly Income/Expense totals for Dashboard."""

    def get(self, request, company_id):
        if set(request.query_params) - {"branch_id"}:
            raise ValidationError({"query": "Only the Branch filter is supported."})
        branch_id = request.query_params.get("branch_id")
        if branch_id is not None:
            try:
                branch_id = UUID(branch_id)
            except (TypeError, ValueError):
                raise ValidationError({"branch_id": "A valid Branch id is required."})
        scope = self.scope(
            request,
            company_id,
            AccountingAction.REPORT,
            permission_action="accounting.report.read",
            branch_id=branch_id,
        )
        if not (scope.is_company_accountant or scope.is_company_wide_reader):
            if branch_id is None:
                if len(scope.allowed_branch_ids) != 1:
                    raise ValidationError({"branch_id": "Select one authorized Branch."})
                branch_id = next(iter(scope.allowed_branch_ids))
            elif branch_id not in scope.allowed_branch_ids:
                raise NotFound("Branch not found.")

        now_local = timezone.localtime(timezone.now(), COMPANY_TIMEZONE)
        month_index = now_local.year * 12 + now_local.month - 1
        first_month_index = month_index - 7
        first_year, first_month_zero = divmod(first_month_index, 12)
        first_local = datetime(first_year, first_month_zero + 1, 1, tzinfo=COMPANY_TIMEZONE)
        next_index = month_index + 1
        next_year, next_month_zero = divmod(next_index, 12)
        after_last_local = datetime(next_year, next_month_zero + 1, 1, tzinfo=COMPANY_TIMEZONE)
        start = first_local.astimezone(datetime_timezone.utc)
        end = after_last_local.astimezone(datetime_timezone.utc)

        events = AccountingEvent.objects.filter(
            tenant=scope.company,
            effective_at__gte=start,
            effective_at__lt=end,
        ).exclude(owner_distribution_payment__isnull=False)
        if branch_id is not None:
            events = events.filter(branch_id=branch_id)
        amount_field = DecimalField(max_digits=38, decimal_places=2)
        net_amount = ExpressionWrapper(F("amount") * F("effect_sign"), output_field=amount_field)
        monthly = events.annotate(month=TruncMonth("effective_at", tzinfo=COMPANY_TIMEZONE)).values("month").annotate(
            income=Sum(Case(
                When(event_type__in=(AccountingEvent.EventType.INCOME, AccountingEvent.EventType.VEHICLE_COMPANY_SHARE), then=net_amount),
                default=Value(Decimal("0.00")), output_field=amount_field,
            )),
            expense=Sum(Case(
                When(event_type=AccountingEvent.EventType.EXPENSE, then=net_amount),
                default=Value(Decimal("0.00")), output_field=amount_field,
            )),
        ).order_by("month")
        values = {
            row["month"].strftime("%Y-%m"): row
            for row in monthly
        }
        points = []
        for offset in range(8):
            current_index = first_month_index + offset
            year, month_zero = divmod(current_index, 12)
            period = f"{year:04d}-{month_zero + 1:02d}"
            row = values.get(period)
            points.append({
                "period": period,
                "label": datetime(year, month_zero + 1, 1).strftime("%b"),
                "income_amount": format((row["income"] if row else None) or Decimal("0.00"), ".2f"),
                "expense_amount": format((row["expense"] if row else None) or Decimal("0.00"), ".2f"),
            })
        return Response({
            "company_id": str(scope.company.pk),
            "branch_id": str(branch_id) if branch_id else None,
            "timezone": "Asia/Kolkata",
            "monthly_trend": points,
        })


class CompanyPeriodConfirmationView(AccountingAPIView):
    def get(self, request, company_id):
        from apps.accounting.company_periods import list_confirmations
        return Response(list_confirmations(actor=request.user, company_id=company_id))

    def post(self, request, company_id):
        serializer = CompanyPeriodConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.accounting.company_periods import confirm_company_period
        result = confirm_company_period(
            actor=request.user, company_id=company_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data,
        )
        return Response(result.body, status=result.status)


class OwnerDistributionConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        from apps.accounts.policy import require_action
        from apps.accounting.models import OwnerDistributionConfiguration
        from apps.tenants.models import Tenant
        company = Tenant.objects.filter(pk=company_id, is_active=True).first()
        if company is None:
            raise NotFound("Company not found.")
        require_action(request.user, "accounting.company_period.read", company=company)
        rows = OwnerDistributionConfiguration.objects.filter(tenant=company).order_by("effective_from", "version")
        return Response([{"id": str(row.pk), "version": row.version,
            "effective_from": row.effective_from.isoformat(), "recipients": row.recipients,
            "actor_id": str(row.actor_id), "reason": row.reason} for row in rows])

    def post(self, request, company_id):
        serializer = OwnerDistributionConfigurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.accounting.company_periods import configure_owner_distribution
        return Response(configure_owner_distribution(actor=request.user, company_id=company_id,
            key=request.headers.get("Idempotency-Key"), path=request.path,
            **serializer.validated_data), status=201)


class OwnerDistributionPaymentView(AccountingAPIView):
    def post(self, request, company_id, confirmation_id):
        serializer = OwnerDistributionPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.accounting.company_periods import pay_owner_distribution
        result = pay_owner_distribution(actor=request.user, company_id=company_id,
            confirmation_id=confirmation_id, key=request.headers.get("Idempotency-Key"),
            path=request.path, **serializer.validated_data)
        return Response(result.body, status=result.status)


def _period_bounds(period, year, month=None):
    if period == "monthly":
        local_start = datetime(year, month, 1, tzinfo=COMPANY_TIMEZONE)
        if month == 12:
            local_end = datetime(year + 1, 1, 1, tzinfo=COMPANY_TIMEZONE)
        else:
            local_end = datetime(year, month + 1, 1, tzinfo=COMPANY_TIMEZONE)
    elif period == "h1":
        local_start = datetime(year, 1, 1, tzinfo=COMPANY_TIMEZONE)
        local_end = datetime(year, 7, 1, tzinfo=COMPANY_TIMEZONE)
    elif period == "h2":
        local_start = datetime(year, 7, 1, tzinfo=COMPANY_TIMEZONE)
        local_end = datetime(year + 1, 1, 1, tzinfo=COMPANY_TIMEZONE)
    else:
        local_start = datetime(year, 1, 1, tzinfo=COMPANY_TIMEZONE)
        local_end = datetime(year + 1, 1, 1, tzinfo=COMPANY_TIMEZONE)
    return local_start, local_end


_UNSET = object()
