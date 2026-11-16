import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connection
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.accounts.locks import locked_users
from apps.accounts.models import User
from apps.accounting.models import (
    AccountMovement,
    AccountingAccount,
    AccountingApplication,
    AccountingCategory,
    AccountingEvent,
    AccountingIdempotencyRecord,
    AccountingSourceLink,
    normalize_label,
)
from apps.tenants.models import Branch, CompanyModuleCode, CompanyModuleState, Tenant

from .policies import (
    AccountingAction,
    accounting_scope,
    lock_accounting_module_revision,
)


class AccountingConflict(APIException):
    status_code = 409
    default_code = "accounting_conflict"

    def __init__(self, detail, *, code="accounting_conflict"):
        super().__init__({"detail": detail, "code": code}, code=code)


@dataclass(frozen=True)
class MutationResult:
    status: int
    body: dict


def _latest_revision(company_id):
    return (
        CompanyModuleState.objects.filter(
            tenant_id=company_id,
            module_code=CompanyModuleCode.ACCOUNTING,
        )
        .order_by("-version", "-id")
        .first()
    )


def _revision_version(revision):
    return revision.version if revision else 0


def _raise_module_state_changed():
    raise AccountingConflict(
        "Accounting module state changed while this request was being prepared. Reload and retry.",
        code="ACCOUNTING_MODULE_STATE_CHANGED",
    )


def _raise_module_disabled():
    raise PermissionDenied("Accounting module is not enabled.")


def _mutation(
    *,
    actor,
    company_id,
    method,
    path,
    key,
    body,
    permission_action,
    role_action,
    operation,
    branch_id=None,
    resource=None,
    allow_off=False,
):
    if not key or len(key) > 128:
        raise ValidationError({"Idempotency-Key": "A key of 1 to 128 characters is required."})
    canonical_body = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    request_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()

    try:
        with locked_users(actor.pk) as users:
            locked_actor = users[actor.pk]
            if (
                actor.auth_epoch != locked_actor.auth_epoch
                or actor.password != locked_actor.password
            ):
                raise PermissionDenied("Authentication changed.")
            observed_revision = _latest_revision(company_id)
            company = Tenant.objects.select_for_update().filter(pk=company_id).first()
            if company is None or not company.is_active:
                raise NotFound("Company not found.")
            current_revision = _latest_revision(company.pk)
            if _revision_version(observed_revision) != _revision_version(current_revision):
                _raise_module_state_changed()

            scope = accounting_scope(
                locked_actor,
                company.pk,
                role_action,
                branch_id=branch_id,
                permission_action=permission_action,
                resource=resource,
            )
            idem = AccountingIdempotencyRecord.objects.filter(
                tenant=company,
                actor=locked_actor,
                key=key,
            ).first()
            if idem is not None:
                if (
                    idem.method != method
                    or idem.path != path
                    or idem.request_hash != request_hash
                ):
                    raise AccountingConflict(
                        "Idempotency-Key was already used for a different request.",
                        code="IDEMPOTENCY_KEY_REUSED",
                    )
                return MutationResult(idem.response_status, idem.response_body)

            if (current_revision is None or current_revision.state != CompanyModuleState.State.ENABLED) and not allow_off:
                _raise_module_disabled()
            revision = lock_accounting_module_revision(scope)
            if _revision_version(revision) != _revision_version(current_revision):
                _raise_module_state_changed()
            result = operation(scope, revision, locked_actor)
            AccountingIdempotencyRecord.objects.create(
                tenant=company,
                actor=locked_actor,
                key=key,
                method=method,
                path=path,
                request_hash=request_hash,
                response_status=result.status,
                response_body=result.body,
            )
            return result
    except IntegrityError as exc:
        constraint = getattr(
            getattr(getattr(exc, "__cause__", None), "diag", None),
            "constraint_name",
            None,
        )
        if constraint == "acct_idem_scope_key_uq":
            idem = AccountingIdempotencyRecord.objects.filter(
                tenant_id=company_id,
                actor_id=actor.pk,
                key=key,
            ).first()
            if idem and idem.method == method and idem.path == path and idem.request_hash == request_hash:
                return MutationResult(idem.response_status, idem.response_body)
            raise AccountingConflict(
                "Idempotency-Key was already used for a different request.",
                code="IDEMPOTENCY_KEY_REUSED",
            ) from exc
        raise


def _require_enabled(revision):
    if revision is None or revision.state != CompanyModuleState.State.ENABLED:
        _raise_module_disabled()


def _require_off_target(event, revision):
    if (
        revision is None
        or revision.state != CompanyModuleState.State.DISABLED
        or event.module_revision_id is None
        or event.module_revision.module_code != CompanyModuleCode.ACCOUNTING
        or event.module_revision.tenant_id != event.tenant_id
        or event.module_revision.version >= revision.version
        or event.recorded_at >= revision.effective_from
    ):
        raise PermissionDenied(
            "Accounting is OFF; this action is limited to records entered before the OFF transition."
        )


def _ensure_current_event(event):
    if event.effect_sign != 1 or event.reversal_of_id is not None:
        raise AccountingConflict("Only the current event can be corrected.", code="ACCOUNTING_EVENT_NOT_CURRENT")
    if AccountingEvent.objects.filter(reversal_of=event).exists() or AccountingEvent.objects.filter(
        replaces_event=event
    ).exists():
        raise AccountingConflict("Only the current event can be corrected.", code="ACCOUNTING_EVENT_NOT_CURRENT")


def _event_row(
    *,
    tenant,
    branch,
    event_type,
    amount,
    actor,
    revision,
    description,
    source_reference,
    effective_at=None,
    category=None,
    effect_sign=1,
    reversal_of=None,
    replaces_event=None,
    correction_reason="",
):
    return AccountingEvent.objects.create(
        tenant=tenant,
        branch=branch,
        event_type=event_type,
        amount=amount,
        currency="INR",
        effect_sign=effect_sign,
        reversal_of=reversal_of,
        replaces_event=replaces_event,
        correction_reason=correction_reason,
        effective_at=effective_at or timezone.now(),
        actor=actor,
        module_revision=revision,
        category=category,
        description=description.strip(),
        source_reference=source_reference.strip(),
    )


def record_capital_movement(
    *,
    tenant,
    branch,
    account_id,
    amount,
    actor,
    accounting_revision,
    event_type,
    source_record,
    description,
    source_reference,
    effective_at,
):
    """Append one real cash movement for an Investment capital source.

    The caller owns the outer transaction and has already locked/rechecked the
    Company and all required module revisions. PostgreSQL deferred triggers
    verify that the source, event and single signed movement agree at commit.
    """
    from apps.investment.models import InvestorFundCredit, InvestorPrincipalReturn

    if not connection.in_atomic_block:
        raise RuntimeError("Capital movements must be part of an outer transaction.")
    expected_source = {
        AccountingEvent.EventType.CAPITAL_INFLOW: InvestorFundCredit,
        AccountingEvent.EventType.CAPITAL_OUTFLOW: InvestorPrincipalReturn,
    }.get(event_type)
    if expected_source is None or not isinstance(source_record, expected_source):
        raise ValidationError("Capital event type does not match its typed source record.")
    if (
        source_record.tenant_id != tenant.pk
        or source_record.branch_id != getattr(branch, "pk", None)
        or source_record.amount != Decimal(amount)
    ):
        raise ValidationError("Capital source scope or amount does not match.")
    if (
        accounting_revision is None
        or accounting_revision.tenant_id != tenant.pk
        or accounting_revision.module_code != CompanyModuleCode.ACCOUNTING
        or accounting_revision.state != CompanyModuleState.State.ENABLED
    ):
        _raise_module_disabled()
    if branch is None or branch.tenant_id != tenant.pk:
        raise ValidationError({"branch_id": "A same-Company source Branch is required."})
    account = _get_account(tenant, account_id)
    event = _event_row(
        tenant=tenant,
        branch=branch,
        event_type=event_type,
        amount=Decimal(amount),
        actor=actor,
        revision=accounting_revision,
        description=description,
        source_reference=source_reference,
        effective_at=effective_at,
    )
    delta = Decimal(amount) if event_type == AccountingEvent.EventType.CAPITAL_INFLOW else -Decimal(amount)
    movement = AccountMovement.objects.create(
        tenant=tenant,
        event=event,
        account=account,
        delta=delta,
    )
    source_fields = (
        {"investor_fund_credit": source_record}
        if event_type == AccountingEvent.EventType.CAPITAL_INFLOW
        else {"investor_principal_return": source_record}
    )
    AccountingSourceLink.objects.create(
        tenant=tenant,
        event=event,
        **source_fields,
    )
    data = event_data(event)
    data.update({"account_id": str(account.pk), "movement_id": str(movement.pk)})
    return event, movement, data


def event_data(event):
    return {
        "id": str(event.pk),
        "company_id": str(event.tenant_id),
        "branch_id": str(event.branch_id) if event.branch_id else None,
        "event_type": event.event_type,
        "amount": format(event.amount, ".2f"),
        "currency": event.currency,
        "category_id": str(event.category_id) if event.category_id else None,
        "description": event.description,
        "source_reference": event.source_reference,
        "effective_at": event.effective_at.isoformat(),
        "recorded_at": event.recorded_at.isoformat(),
        "actor_id": str(event.actor_id),
        "effect_sign": event.effect_sign,
        "reversal_of_id": str(event.reversal_of_id) if event.reversal_of_id else None,
        "replaces_event_id": str(event.replaces_event_id) if event.replaces_event_id else None,
    }


def _get_branch(company, branch_id, *, allow_company_wide):
    if branch_id is None:
        if allow_company_wide:
            return None
        raise ValidationError({"branch_id": "A Branch is required."})
    branch = Branch.objects.filter(pk=branch_id, tenant=company).first()
    if branch is None:
        raise NotFound("Branch not found.")
    return branch


def _get_category(company, category_id, kind):
    category = AccountingCategory.objects.filter(
        pk=category_id,
        tenant=company,
        kind=kind,
        is_active=True,
    ).first()
    if category is None:
        raise NotFound("Accounting category not found.")
    return category


def _get_account(company, account_id, *, active=True):
    queryset = AccountingAccount.objects.filter(tenant=company, pk=account_id)
    if active:
        queryset = queryset.filter(is_active=True)
    account = queryset.select_for_update().first()
    if account is None:
        raise NotFound("Accounting account not found.")
    return account


def create_account(*, actor, company_id, key, path, account_type, label):
    body = {"account_type": account_type, "label": label}

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        if account_type not in AccountingAccount.AccountType.values:
            raise ValidationError({"account_type": "Unsupported account type."})
        if not label.strip():
            raise ValidationError({"label": "A nonempty account label is required."})
        account = AccountingAccount.objects.create(
            tenant=scope.company,
            account_type=account_type,
            label=label.strip(),
            created_by=locked_actor,
        )
        return MutationResult(
            201,
            {
                "id": str(account.pk),
                "account_type": account.account_type,
                "label": account.label,
                "is_active": True,
                "current_balance": "0.00",
                "balance_as_of": timezone.now().isoformat(),
                "has_history": False,
            },
        )

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.account.manage",
        role_action=AccountingAction.MANAGE,
        operation=operation,
    )


def archive_account(*, actor, company_id, account_id, key, path):
    body = {"is_active": False}

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        account = _get_account(scope.company, account_id, active=True)
        movement_qs = AccountMovement.objects.filter(account=account)
        total = movement_qs.aggregate(total=Sum("delta"))["total"] or Decimal("0.00")
        if total != 0:
            raise AccountingConflict(
                "An account must have a zero balance before it can be archived.",
                code="ACCOUNT_BALANCE_NONZERO",
            )
        if movement_qs.exists():
            raise AccountingConflict(
                "An account with any historical movement cannot be archived, even at zero balance.",
                code="ACCOUNT_HISTORY_PRESENT",
            )
        account.is_active = False
        account.archived_at = timezone.now()
        account.archived_by = locked_actor
        account.save()
        return MutationResult(200, {"id": str(account.pk), "is_active": False})

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="PATCH",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.account.manage",
        role_action=AccountingAction.MANAGE,
        operation=operation,
    )


def create_category(*, actor, company_id, key, path, kind, label):
    body = {"kind": kind, "label": label}

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        if kind not in AccountingCategory.Kind.values:
            raise ValidationError({"kind": "Unsupported category kind."})
        normalized = normalize_label(label)
        if not normalized:
            raise ValidationError({"label": "A nonempty category label is required."})
        if AccountingCategory.objects.filter(
            tenant=scope.company,
            kind=kind,
            normalized_label=normalized,
            is_active=True,
        ).exists():
            raise AccountingConflict(
                "An active category with this name already exists.",
                code="ACCOUNTING_CATEGORY_DUPLICATE",
            )
        category = AccountingCategory.objects.create(
            tenant=scope.company,
            kind=kind,
            label=" ".join(label.split()),
            created_by=locked_actor,
        )
        return MutationResult(
            201,
            {"id": str(category.pk), "kind": category.kind, "label": category.label, "is_active": True},
        )

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.category.manage",
        role_action=AccountingAction.MANAGE,
        operation=operation,
    )


def archive_category(*, actor, company_id, category_id, key, path):
    body = {"is_active": False}

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        category = AccountingCategory.objects.select_for_update().filter(
            tenant=scope.company,
            pk=category_id,
            is_active=True,
        ).first()
        if category is None:
            raise NotFound("Accounting category not found.")
        category.is_active = False
        category.archived_at = timezone.now()
        category.archived_by = locked_actor
        category.save()
        return MutationResult(200, {"id": str(category.pk), "is_active": False})

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="PATCH",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.category.manage",
        role_action=AccountingAction.MANAGE,
        operation=operation,
    )


def create_income_or_expense(
    *, actor, company_id, kind, branch_id, category_id, amount, description, source_reference, effective_at, key, path
):
    event_type = AccountingEvent.EventType.INCOME if kind == "INCOME" else AccountingEvent.EventType.EXPENSE
    permission_action = "accounting.income.create" if kind == "INCOME" else "accounting.expense.create"
    role_action = AccountingAction.POST
    body = {
        "event_type": event_type,
        "branch_id": str(branch_id) if branch_id else None,
        "category_id": str(category_id),
        "amount": format(Decimal(amount), ".2f"),
        "description": description,
        "source_reference": source_reference,
        "effective_at": effective_at.isoformat() if effective_at else None,
    }

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        branch = _get_branch(scope.company, branch_id, allow_company_wide=True)
        scope.validate_write_branch(branch.pk if branch else None, allow_company_wide=True)
        category = _get_category(scope.company, category_id, kind)
        if not description.strip() or not source_reference.strip():
            raise ValidationError("Description and source reference are required.")
        event = _event_row(
            tenant=scope.company,
            branch=branch,
            event_type=event_type,
            amount=Decimal(amount),
            actor=locked_actor,
            revision=revision,
            category=category,
            description=description,
            source_reference=source_reference,
            effective_at=effective_at,
        )
        return MutationResult(201, event_data(event))

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action=permission_action,
        role_action=role_action,
        branch_id=branch_id,
        operation=operation,
    )


def _application_total(target_event):
    rows = list(
        AccountingApplication.objects.filter(
            tenant_id=target_event.tenant_id,
            target_event=target_event,
            effect_sign=1,
        ).order_by("id")
    )
    reversed_ids = set(
        AccountingApplication.objects.filter(reversal_of__in=rows).values_list(
            "reversal_of_id", flat=True
        )
    )
    return sum(
        (row.amount for row in rows if row.pk not in reversed_ids),
        Decimal("0.00"),
    )


def _active_source_application(source_event):
    rows = list(
        AccountingApplication.objects.filter(
            tenant_id=source_event.tenant_id,
            source_event=source_event,
            effect_sign=1,
        ).order_by("id")
    )
    reversed_ids = set(
        AccountingApplication.objects.filter(reversal_of__in=rows).values_list(
            "reversal_of_id", flat=True
        )
    )
    active = [row for row in rows if row.pk not in reversed_ids]
    return active[0] if active else None


def _ensure_target_current(target):
    _ensure_current_event(target)
    if target.event_type not in (AccountingEvent.EventType.INCOME, AccountingEvent.EventType.EXPENSE):
        raise ValidationError({"target_event_id": "Target must be a current Income or Expense."})


def create_receipt_or_payment(
    *, actor, company_id, kind, branch_id, account_id, target_event_id, amount, effective_at, description, source_reference, key, path
):
    event_type = AccountingEvent.EventType.RECEIPT if kind == "RECEIPT" else AccountingEvent.EventType.PAYMENT
    target_type = AccountingEvent.EventType.INCOME if kind == "RECEIPT" else AccountingEvent.EventType.EXPENSE
    permission_action = "accounting.receipt.create" if kind == "RECEIPT" else "accounting.payment.create"
    target_preview = AccountingEvent.objects.filter(
        tenant_id=company_id,
        pk=target_event_id,
    ).select_related("module_revision", "branch").first()
    if target_preview is None:
        raise NotFound("Accounting target not found.")
    body = {
        "event_type": event_type,
        "branch_id": str(branch_id) if branch_id else None,
        "account_id": str(account_id),
        "target_event_id": str(target_event_id),
        "amount": format(Decimal(amount), ".2f"),
        "effective_at": effective_at.isoformat(),
        "description": description,
        "source_reference": source_reference,
    }

    def operation(scope, revision, locked_actor):
        target = AccountingEvent.objects.select_for_update(of=("self",)).select_related(
            "module_revision", "branch"
        ).filter(tenant=scope.company, pk=target_event_id).first()
        if target is None:
            raise NotFound("Accounting target not found.")
        scope.validate_record(target)
        _ensure_target_current(target)
        if target.event_type != target_type:
            raise ValidationError({"target_event_id": "Receipt/Payment target kind does not match."})
        if revision.state == CompanyModuleState.State.DISABLED:
            _require_off_target(target, revision)
        else:
            _require_enabled(revision)
        if effective_at > timezone.now():
            raise ValidationError({"effective_at": "Actual Receipt/Payment cannot be future-dated."})
        branch = _get_branch(scope.company, branch_id, allow_company_wide=True)
        scope.validate_write_branch(branch.pk if branch else None, allow_company_wide=True)
        account = _get_account(scope.company, account_id)
        outstanding = target.amount - _application_total(target)
        if Decimal(amount) > outstanding:
            raise AccountingConflict(
                "Amount exceeds the current outstanding Income/Expense.",
                code="ACCOUNTING_TARGET_BALANCE_EXCEEDED",
            )
        if Decimal(amount) <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})
        event = _event_row(
            tenant=scope.company,
            branch=branch,
            event_type=event_type,
            amount=Decimal(amount),
            actor=locked_actor,
            revision=revision,
            description=description,
            source_reference=source_reference,
            effective_at=effective_at,
        )
        delta = Decimal(amount) if kind == "RECEIPT" else -Decimal(amount)
        AccountMovement.objects.create(
            tenant=scope.company,
            event=event,
            account=account,
            delta=delta,
        )
        application = AccountingApplication.objects.create(
            tenant=scope.company,
            source_event=event,
            target_event=target,
            amount=Decimal(amount),
            actor=locked_actor,
            module_revision=revision,
        )
        data = event_data(event)
        data["account_id"] = str(account.pk)
        data["application_ids"] = [str(application.pk)]
        return MutationResult(201, data)

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action=permission_action,
        role_action=AccountingAction.POST,
        branch_id=branch_id,
        resource=target_preview,
        operation=operation,
        allow_off=True,
    )


def create_opening_balance(*, actor, company_id, account_id, branch_id, amount, effective_at, reason, source_reference, key, path):
    body = {
        "account_id": str(account_id),
        "branch_id": str(branch_id) if branch_id else None,
        "amount": format(Decimal(amount), ".2f"),
        "effective_at": effective_at.isoformat(),
        "reason": reason,
        "source_reference": source_reference,
    }

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        if Decimal(amount) == 0:
            raise ValidationError({"amount": "Opening balance must be nonzero."})
        if not reason.strip() or not source_reference.strip():
            raise ValidationError("Reason and source reference are required.")
        account = _get_account(scope.company, account_id)
        if AccountMovement.objects.filter(account=account).exists():
            raise AccountingConflict(
                "Opening balance must be the first movement for the account.",
                code="OPENING_BALANCE_ALREADY_ESTABLISHED",
            )
        branch = _get_branch(scope.company, branch_id, allow_company_wide=True)
        scope.validate_write_branch(branch.pk if branch else None, allow_company_wide=True)
        event = _event_row(
            tenant=scope.company,
            branch=branch,
            event_type=AccountingEvent.EventType.OPENING_BALANCE,
            amount=abs(Decimal(amount)),
            actor=locked_actor,
            revision=revision,
            description=reason,
            source_reference=source_reference,
            effective_at=effective_at,
        )
        movement = AccountMovement.objects.create(
            tenant=scope.company,
            event=event,
            account=account,
            delta=Decimal(amount),
        )
        data = event_data(event)
        data.update({"account_id": str(account.pk), "movement_id": str(movement.pk), "opening_amount": format(Decimal(amount), ".2f")})
        return MutationResult(201, data)

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.opening_balance.create",
        role_action=AccountingAction.MANAGE,
        branch_id=branch_id,
        operation=operation,
    )


def create_transfer(*, actor, company_id, branch_id, from_account_id, to_account_id, amount, effective_at, reason, source_reference, key, path):
    body = {
        "branch_id": str(branch_id) if branch_id else None,
        "from_account_id": str(from_account_id),
        "to_account_id": str(to_account_id),
        "amount": format(Decimal(amount), ".2f"),
        "effective_at": effective_at.isoformat(),
        "reason": reason,
        "source_reference": source_reference,
    }

    def operation(scope, revision, locked_actor):
        _require_enabled(revision)
        if Decimal(amount) <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})
        if from_account_id == to_account_id:
            raise ValidationError({"to_account_id": "Transfer accounts must be different."})
        if effective_at > timezone.now():
            raise ValidationError({"effective_at": "Actual Transfer cannot be future-dated."})
        branch = _get_branch(scope.company, branch_id, allow_company_wide=True)
        scope.validate_write_branch(branch.pk if branch else None, allow_company_wide=True)
        accounts = list(
            AccountingAccount.objects.select_for_update()
            .filter(tenant=scope.company, pk__in=(from_account_id, to_account_id), is_active=True)
            .order_by("id")
        )
        if len(accounts) != 2:
            raise NotFound("Accounting account not found.")
        accounts_by_id = {str(account.pk): account for account in accounts}
        source = accounts_by_id.get(str(from_account_id))
        destination = accounts_by_id.get(str(to_account_id))
        if source is None or destination is None:
            raise NotFound("Accounting account not found.")
        event = _event_row(
            tenant=scope.company,
            branch=branch,
            event_type=AccountingEvent.EventType.TRANSFER,
            amount=Decimal(amount),
            actor=locked_actor,
            revision=revision,
            description=reason,
            source_reference=source_reference,
            effective_at=effective_at,
        )
        movements = [
            AccountMovement(tenant=scope.company, event=event, account=source, delta=-Decimal(amount)),
            AccountMovement(tenant=scope.company, event=event, account=destination, delta=Decimal(amount)),
        ]
        AccountMovement.objects.bulk_create(movements)
        data = event_data(event)
        data.update({"from_account_id": str(source.pk), "to_account_id": str(destination.pk)})
        return MutationResult(201, data)

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.transfer.create",
        role_action=AccountingAction.MANAGE,
        branch_id=branch_id,
        operation=operation,
    )


def _active_applications_for_target(target_event):
    rows = list(
        AccountingApplication.objects.select_for_update()
        .filter(tenant_id=target_event.tenant_id, target_event=target_event, effect_sign=1)
        .order_by("id")
    )
    reversed_ids = set(
        AccountingApplication.objects.filter(reversal_of__in=rows).values_list(
            "reversal_of_id", flat=True
        )
    )
    return [row for row in rows if row.pk not in reversed_ids]


def _reverse_application(application, *, actor, revision, reason):
    return AccountingApplication.objects.create(
        tenant_id=application.tenant_id,
        source_event=application.source_event,
        target_event=application.target_event,
        amount=application.amount,
        effect_sign=-1,
        reversal_of=application,
        actor=actor,
        module_revision=revision,
        reason=reason,
    )


def _reverse_event(event, *, actor, revision, reason):
    reversal = _event_row(
        tenant=event.tenant,
        branch=event.branch,
        event_type=event.event_type,
        amount=event.amount,
        actor=actor,
        revision=revision,
        category=event.category,
        description=event.description,
        source_reference=event.source_reference,
        effective_at=event.effective_at,
        effect_sign=-1,
        reversal_of=event,
        correction_reason=reason,
    )
    old_movements = list(
        AccountMovement.objects.select_for_update()
        .filter(event=event)
        .select_related("account")
        .order_by("account_id", "id")
    )
    for movement in old_movements:
        AccountMovement.objects.create(
            tenant_id=event.tenant_id,
            event=reversal,
            account=movement.account,
            delta=-movement.delta,
        )
    return reversal, old_movements


def _replacement_event(event, *, actor, revision, reason, branch, values):
    values = values or {}
    replacement_type = event.event_type
    replacement = None
    created_movements = []
    target_application = None

    if replacement_type in (AccountingEvent.EventType.INCOME, AccountingEvent.EventType.EXPENSE):
        kind = replacement_type
        category = _get_category(event.tenant, values["category_id"], kind)
        amount = Decimal(values["amount"])
        if amount <= 0:
            raise ValidationError({"replacement.amount": "Amount must be greater than zero."})
        applications = _active_applications_for_target(event)
        applied = sum((row.amount for row in applications), Decimal("0.00"))
        if amount < applied:
            raise AccountingConflict(
                "Replacement Income/Expense cannot cover its existing actual applications.",
                code="ACCOUNTING_TARGET_BALANCE_EXCEEDED",
            )
        replacement = _event_row(
            tenant=event.tenant,
            branch=branch,
            event_type=event.event_type,
            amount=amount,
            actor=actor,
            revision=revision,
            category=category,
            description=values["description"],
            source_reference=values["source_reference"],
            effective_at=event.effective_at,
            replaces_event=event,
            correction_reason=reason,
        )
        for application in applications:
            _reverse_application(application, actor=actor, revision=revision, reason=reason)
            AccountingApplication.objects.create(
                tenant_id=event.tenant_id,
                source_event=application.source_event,
                target_event=replacement,
                amount=application.amount,
                actor=actor,
                module_revision=revision,
                reason=reason,
            )
    elif replacement_type in (AccountingEvent.EventType.RECEIPT, AccountingEvent.EventType.PAYMENT):
        amount = Decimal(values["amount"])
        effective_at = values["effective_at"]
        if amount <= 0:
            raise ValidationError({"replacement.amount": "Amount must be greater than zero."})
        if effective_at > timezone.now():
            raise ValidationError({"replacement.effective_at": "Actual Receipt/Payment cannot be future-dated."})
        account = _get_account(event.tenant, values["account_id"])
        branch = _get_branch(event.tenant, values.get("branch_id"), allow_company_wide=True)
        active = _active_applications_for_source(event)
        if len(active) != 1:
            raise AccountingConflict(
                "Cash-event correction requires exactly one active Income/Expense application.",
                code="ACCOUNTING_APPLICATION_STATE_INVALID",
            )
        target_application = active[0]
        target = target_application.target_event
        available = target.amount - _application_total(target) + target_application.amount
        if amount > available:
            raise AccountingConflict(
                "Replacement amount exceeds the current outstanding Income/Expense.",
                code="ACCOUNTING_TARGET_BALANCE_EXCEEDED",
            )
        replacement = _event_row(
            tenant=event.tenant,
            branch=branch,
            event_type=event.event_type,
            amount=amount,
            actor=actor,
            revision=revision,
            description=values["description"],
            source_reference=values["source_reference"],
            effective_at=effective_at,
            replaces_event=event,
            correction_reason=reason,
        )
        old_movements = list(
            AccountMovement.objects.select_for_update()
            .filter(event=event)
            .select_related("account")
            .order_by("account_id", "id")
        )
        if len(old_movements) != 1:
            raise AccountingConflict(
                "Cash event movement history is incomplete.",
                code="ACCOUNTING_MOVEMENT_STATE_INVALID",
            )
        movement_delta = amount if event.event_type == AccountingEvent.EventType.RECEIPT else -amount
        _reverse_application(target_application, actor=actor, revision=revision, reason=reason)
        AccountMovement.objects.create(
            tenant_id=event.tenant_id,
            event=replacement,
            account=account,
            delta=movement_delta,
        )
        AccountingApplication.objects.create(
            tenant_id=event.tenant_id,
            source_event=replacement,
            target_event=target,
            amount=amount,
            actor=actor,
            module_revision=revision,
            reason=reason,
        )
    elif replacement_type == AccountingEvent.EventType.OPENING_BALANCE:
        signed_amount = Decimal(values["amount"])
        if signed_amount == 0:
            return None, created_movements
        movements = list(
            AccountMovement.objects.select_for_update()
            .filter(event=event)
            .select_related("account")
            .order_by("account_id", "id")
        )
        if len(movements) != 1:
            raise AccountingConflict(
                "Opening Balance movement history is incomplete.",
                code="ACCOUNTING_MOVEMENT_STATE_INVALID",
            )
        account = movements[0].account
        replacement = _event_row(
            tenant=event.tenant,
            branch=event.branch,
            event_type=event.event_type,
            amount=abs(signed_amount),
            actor=actor,
            revision=revision,
            description=values.get("description") or reason,
            source_reference=values.get("source_reference") or event.source_reference,
            effective_at=event.effective_at,
            replaces_event=event,
            correction_reason=reason,
        )
        created_movements.append(
            AccountMovement.objects.create(
                tenant_id=event.tenant_id,
                event=replacement,
                account=account,
                delta=signed_amount,
            )
        )
    elif replacement_type == AccountingEvent.EventType.TRANSFER:
        amount = Decimal(values["amount"])
        effective_at = values["effective_at"]
        if amount <= 0:
            raise ValidationError({"replacement.amount": "Amount must be greater than zero."})
        if effective_at > timezone.now():
            raise ValidationError({"replacement.effective_at": "Transfer cannot be future-dated."})
        if values["from_account_id"] == values["to_account_id"]:
            raise ValidationError({"replacement.to_account_id": "Transfer accounts must be different."})
        accounts = list(
            AccountingAccount.objects.select_for_update()
            .filter(
                tenant=event.tenant,
                pk__in=(values["from_account_id"], values["to_account_id"]),
                is_active=True,
            )
            .order_by("id")
        )
        if len(accounts) != 2:
            raise NotFound("Accounting account not found.")
        by_id = {str(row.pk): row for row in accounts}
        source = by_id.get(str(values["from_account_id"]))
        destination = by_id.get(str(values["to_account_id"]))
        if source is None or destination is None:
            raise NotFound("Accounting account not found.")
        replacement = _event_row(
            tenant=event.tenant,
            branch=branch,
            event_type=event.event_type,
            amount=amount,
            actor=actor,
            revision=revision,
            description=values["description"],
            source_reference=values["source_reference"],
            effective_at=effective_at,
            replaces_event=event,
            correction_reason=reason,
        )
        created_movements = [
            AccountMovement.objects.create(
                tenant_id=event.tenant_id,
                event=replacement,
                account=source,
                delta=-amount,
            ),
            AccountMovement.objects.create(
                tenant_id=event.tenant_id,
                event=replacement,
                account=destination,
                delta=amount,
            ),
        ]
    return replacement, created_movements


def _active_applications_for_source(source_event):
    rows = list(
        AccountingApplication.objects.select_for_update()
        .filter(tenant_id=source_event.tenant_id, source_event=source_event, effect_sign=1)
        .select_related("target_event", "target_event__module_revision")
        .order_by("id")
    )
    reversed_ids = set(
        AccountingApplication.objects.filter(reversal_of__in=rows).values_list(
            "reversal_of_id", flat=True
        )
    )
    return [row for row in rows if row.pk not in reversed_ids]


def correct_event(
    *, actor, company_id, event_id, allowed_event_types, outcome, event_occurred, reason, replacement, key, path
):
    preview = AccountingEvent.objects.filter(
        tenant_id=company_id,
        pk=event_id,
    ).select_related("branch", "category", "module_revision").first()
    if preview is None:
        raise NotFound("Accounting event not found.")
    body = {
        "outcome": outcome,
        "event_occurred": event_occurred,
        "reason": reason,
        "replacement": replacement,
    }
    branch_id = preview.branch_id

    def operation(scope, revision, locked_actor):
        event = AccountingEvent.objects.select_for_update(of=("self",)).select_related(
            "branch", "category", "module_revision", "tenant"
        ).filter(tenant=scope.company, pk=event_id).first()
        if event is None:
            raise NotFound("Accounting event not found.")
        scope.validate_record(event)
        if event.event_type not in allowed_event_types:
            raise NotFound("Accounting event not found for this correction resource.")
        _ensure_current_event(event)
        if revision.state == CompanyModuleState.State.DISABLED:
            _require_off_target(event, revision)
        else:
            _require_enabled(revision)
        if not reason.strip():
            raise ValidationError({"reason": "A correction reason is required."})
        if outcome not in {"REVERSE_ONLY", "REVERSE_AND_REPLACE"}:
            raise ValidationError({"outcome": "Unsupported correction outcome."})
        if event_occurred and outcome != "REVERSE_AND_REPLACE":
            raise AccountingConflict(
                "A real event must be corrected with a same-kind replacement.",
                code="REVERSAL_REPLACEMENT_REQUIRED",
            )
        if not event_occurred and outcome != "REVERSE_ONLY":
            raise AccountingConflict(
                "A false or duplicate event must be reversed without a replacement.",
                code="REPLACEMENT_NOT_ALLOWED",
            )

        active_target_apps = []
        active_source_apps = []
        if event.event_type in (AccountingEvent.EventType.INCOME, AccountingEvent.EventType.EXPENSE):
            active_target_apps = _active_applications_for_target(event)
            for application in active_target_apps:
                scope.validate_record(application.source_event)
            if revision.state == CompanyModuleState.State.DISABLED:
                for application in active_target_apps:
                    _require_off_target(application.source_event, revision)
        elif event.event_type in (AccountingEvent.EventType.RECEIPT, AccountingEvent.EventType.PAYMENT):
            active_source_apps = _active_applications_for_source(event)
            for application in active_source_apps:
                scope.validate_record(application.target_event)
            if revision.state == CompanyModuleState.State.DISABLED:
                for application in active_source_apps:
                    _require_off_target(application.target_event, revision)

        if outcome == "REVERSE_ONLY" and active_target_apps:
            raise AccountingConflict(
                "Reallocate active Receipt/Payment applications before reversing this Income/Expense only.",
                code="ACCOUNTING_APPLICATIONS_MUST_BE_RESOLVED",
            )
        if outcome == "REVERSE_ONLY" and event.event_type in (
            AccountingEvent.EventType.RECEIPT,
            AccountingEvent.EventType.PAYMENT,
        ):
            if len(active_source_apps) != 1:
                raise AccountingConflict(
                    "Cash-event correction requires exactly one active Income/Expense application.",
                    code="ACCOUNTING_APPLICATION_STATE_INVALID",
                )
            for application in active_source_apps:
                _reverse_application(
                    application,
                    actor=locked_actor,
                    revision=revision,
                    reason=reason.strip(),
                )
        if replacement is None and outcome == "REVERSE_AND_REPLACE":
            raise ValidationError({"replacement": "A same-kind replacement is required."})
        opening_reverse_zero = (
            event.event_type == AccountingEvent.EventType.OPENING_BALANCE
            and outcome == "REVERSE_ONLY"
            and replacement is not None
            and Decimal(replacement.get("amount", "-1")) == 0
        )
        if replacement is not None and outcome == "REVERSE_ONLY" and not opening_reverse_zero:
            raise ValidationError({"replacement": "Replacement fields are not allowed for reverse-only."})

        new_branch = event.branch
        if replacement is not None and event.event_type in (
            AccountingEvent.EventType.INCOME,
            AccountingEvent.EventType.EXPENSE,
            AccountingEvent.EventType.TRANSFER,
        ):
            new_branch = _get_branch(
                scope.company,
                replacement.get("branch_id", event.branch_id),
                allow_company_wide=True,
            )
            scope.validate_replacement_branch(
                new_branch.pk if new_branch else None,
                original_record=event,
                allow_company_wide=True,
            )
        elif replacement is not None and event.event_type in (
            AccountingEvent.EventType.RECEIPT,
            AccountingEvent.EventType.PAYMENT,
        ):
            new_branch = _get_branch(
                scope.company,
                replacement.get("branch_id", event.branch_id),
                allow_company_wide=True,
            )
            scope.validate_replacement_branch(
                new_branch.pk if new_branch else None,
                original_record=event,
                allow_company_wide=True,
            )

        reversal, old_movements = _reverse_event(
            event,
            actor=locked_actor,
            revision=revision,
            reason=reason.strip(),
        )
        replacement_event = None
        if outcome == "REVERSE_AND_REPLACE":
            replacement_event, _ = _replacement_event(
                event,
                actor=locked_actor,
                revision=revision,
                reason=reason.strip(),
                branch=new_branch,
                values=replacement,
            )
            if replacement_event is None:
                raise ValidationError({"replacement.amount": "Replacement amount must be nonzero."})
        result = {
            "original_event_id": str(event.pk),
            "reversal_event_id": str(reversal.pk),
            "replacement_event_id": str(replacement_event.pk) if replacement_event else None,
        }
        return MutationResult(201, result)

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.event.correct",
        role_action=AccountingAction.CORRECT,
        branch_id=branch_id,
        resource=preview,
        operation=operation,
        allow_off=True,
    )


def reallocate_application(*, actor, company_id, application_id, target_event_id, reason, key, path):
    preview = AccountingApplication.objects.filter(
        tenant_id=company_id,
        pk=application_id,
    ).select_related("source_event", "target_event", "target_event__module_revision").first()
    if preview is None:
        raise NotFound("Accounting application not found.")
    body = {"target_event_id": str(target_event_id), "reason": reason}

    def operation(scope, revision, locked_actor):
        application = AccountingApplication.objects.select_for_update().select_related(
            "source_event__module_revision",
            "target_event__module_revision",
        ).filter(tenant=scope.company, pk=application_id).first()
        if application is None or application.effect_sign != 1:
            raise NotFound("Accounting application not found.")
        scope.validate_record(application.source_event)
        scope.validate_record(application.target_event)
        active = _active_applications_for_source(application.source_event)
        if application.pk not in {row.pk for row in active}:
            raise AccountingConflict(
                "Only an active application can be reallocated.",
                code="ACCOUNTING_APPLICATION_NOT_CURRENT",
            )
        target = AccountingEvent.objects.select_for_update().select_related(
            "module_revision"
        ).filter(tenant=scope.company, pk=target_event_id).first()
        if target is None:
            raise NotFound("Accounting target not found.")
        scope.validate_record(target)
        if (
            not scope.is_company_accountant
            and target.branch_id != application.target_event.branch_id
        ):
            raise PermissionDenied("Branch Accountant cannot reassign a cash application to another Branch.")
        _ensure_target_current(target)
        expected_type = (
            AccountingEvent.EventType.INCOME
            if application.source_event.event_type == AccountingEvent.EventType.RECEIPT
            else AccountingEvent.EventType.EXPENSE
        )
        if target.event_type != expected_type:
            raise ValidationError({"target_event_id": "Target kind does not match the actual cash event."})
        if target.pk == application.target_event_id:
            raise ValidationError({"target_event_id": "Select a different target."})
        if revision.state == CompanyModuleState.State.DISABLED:
            _require_off_target(application.source_event, revision)
            _require_off_target(application.target_event, revision)
            _require_off_target(target, revision)
        else:
            _require_enabled(revision)
        if not reason.strip():
            raise ValidationError({"reason": "A reallocation reason is required."})
        outstanding = target.amount - _application_total(target)
        if application.amount > outstanding:
            raise AccountingConflict(
                "Amount exceeds the new target's current outstanding balance.",
                code="ACCOUNTING_TARGET_BALANCE_EXCEEDED",
            )
        _reverse_application(application, actor=locked_actor, revision=revision, reason=reason.strip())
        replacement = AccountingApplication.objects.create(
            tenant=scope.company,
            source_event=application.source_event,
            target_event=target,
            amount=application.amount,
            actor=locked_actor,
            module_revision=revision,
            reason=reason.strip(),
        )
        return MutationResult(
            201,
            {
                "original_application_id": str(application.pk),
                "reversal_application_id": str(
                    AccountingApplication.objects.get(reversal_of=application).pk
                ),
                "replacement_application_id": str(replacement.pk),
            },
        )

    return _mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        permission_action="accounting.event.correct",
        role_action=AccountingAction.CORRECT,
        branch_id=preview.source_event.branch_id,
        resource=preview.source_event,
        operation=operation,
        allow_off=True,
    )
