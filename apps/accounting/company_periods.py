"""Company-level Accountant confirmation of distributable period amounts."""
import hashlib
import json
from datetime import datetime
from decimal import Decimal

from django.db.models import Case, DecimalField, ExpressionWrapper, F, Sum, Value, When
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounting.finance import calculate_company_period_carryforward
from apps.accounting.models import AccountingEvent, CompanyPeriodConfirmation
from apps.tenants.models import CompanyModuleCode


def period_bounds(period_type, year):
    if period_type == "h1":
        start, end = datetime(year, 1, 1), datetime(year, 7, 1)
    elif period_type == "h2":
        start, end = datetime(year, 7, 1), datetime(year + 1, 1, 1)
    elif period_type == "annual":
        start, end = datetime(year, 1, 1), datetime(year + 1, 1, 1)
    else:
        raise ValidationError({"period_type": "Choose H1, H2 or Annual."})
    from zoneinfo import ZoneInfo
    local_tz = ZoneInfo("Asia/Kolkata")
    return start.replace(tzinfo=local_tz).date(), end.replace(tzinfo=local_tz).date(), start.replace(tzinfo=local_tz), end.replace(tzinfo=local_tz)


def source_result(*, company, starts_at, ends_at):
    qs = AccountingEvent.objects.filter(tenant=company, effective_at__gte=starts_at, effective_at__lt=ends_at).exclude(owner_distribution_payment__isnull=False)
    amount_field = DecimalField(max_digits=38, decimal_places=2)
    net_amount = ExpressionWrapper(F("amount") * F("effect_sign"), output_field=amount_field)
    totals = qs.aggregate(
        income=Sum(Case(When(event_type__in=(AccountingEvent.EventType.INCOME, AccountingEvent.EventType.VEHICLE_COMPANY_SHARE), then=net_amount), default=Value(Decimal("0.00")), output_field=amount_field)),
        expense=Sum(Case(When(event_type=AccountingEvent.EventType.EXPENSE, then=net_amount), default=Value(Decimal("0.00")), output_field=amount_field)),
    )
    income, expense = totals["income"] or Decimal("0.00"), totals["expense"] or Decimal("0.00")
    from apps.investment.finance import exact_money_difference
    result = exact_money_difference(income, expense)
    return income, expense, result, event_source_version(qs)


def event_source_version(qs):
    events = list(qs.exclude(owner_distribution_payment__isnull=False).order_by("id").values_list("id", "event_type", "amount", "effect_sign", "effective_at"))
    digest = hashlib.sha256(json.dumps([
        [str(pk), event_type, format(amount, ".2f"), sign, effective_at.isoformat()]
        for pk, event_type, amount, sign, effective_at in events
    ], separators=(",", ":")).encode()).hexdigest()
    return digest


def event_source_version_from_rows(*, ids, types, amounts, signs, effective_ats):
    rows = zip(ids or [], types or [], amounts or [], signs or [], effective_ats or [])
    payload = [[str(pk), event_type, format(amount, ".2f"), sign, effective_at.isoformat()]
               for pk, event_type, amount, sign, effective_at in rows]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def confirmation_data(row):
    return {
        "id": str(row.pk), "period_type": row.period_type, "period_start": row.period_start.isoformat(),
        "period_end": row.period_end.isoformat(), "version": row.version,
        "previous_id": str(row.previous_id) if row.previous_id else None,
        "carryforward_source_id": str(row.carryforward_source_id) if row.carryforward_source_id else None,
        "source_version": row.source_version, "accounting_result": format(row.accounting_result, ".2f"),
        "prior_loss_carried_forward": format(row.prior_loss_carried_forward, ".2f"),
        "loss_carried_forward": format(row.loss_carried_forward, ".2f"),
        "positive_after_loss": format(row.positive_after_loss, ".2f"),
        "distributable_amount": format(row.distributable_amount, ".2f"),
        "owner_split_configuration_id": str(row.owner_split_configuration_id) if row.owner_split_configuration_id else None,
        "owner_allocation_snapshot": row.owner_allocation_snapshot,
        "liabilities_reviewed": row.liabilities_reviewed, "liability_review_reason": row.liability_review_reason,
        "reason": row.reason, "confirmed_at": row.confirmed_at.isoformat(), "confirmed_by_id": str(row.actor_id),
    }


def current_confirmation_ids(*, company, latest_by_period):
    status, hashes = {}, {}
    from apps.accounting.models import OwnerDistributionConfiguration
    owner_splits = list(OwnerDistributionConfiguration.objects.filter(tenant=company)
                        .order_by("effective_from", "version").values("id", "effective_from"))
    def current(row):
        if row.pk in status:
            return status[row.pk]
        key = (row.period_start, row.period_end)
        prior = [candidate for interval, candidate in latest_by_period.items()
                 if interval != key and candidate.period_end <= row.period_start]
        predecessor = max(prior, key=lambda candidate: candidate.period_end) if prior else None
        if predecessor and not current(predecessor):
            status[row.pk] = False
            return False
        source_key = (row.period_type, row.period_start.year)
        if source_key not in hashes:
            _, _, start_at, end_at = period_bounds(*source_key)
            hashes[source_key] = source_result(company=company, starts_at=start_at, ends_at=end_at)[3]
        applicable_split = next((split for split in reversed(owner_splits)
                                 if split["effective_from"] <= row.period_start), None)
        expected_split_id = applicable_split["id"] if row.distributable_amount > 0 and applicable_split else None
        status[row.pk] = (row.source_version == hashes[source_key]
                          and row.carryforward_source_id == (predecessor.pk if predecessor else None)
                          and row.owner_split_configuration_id == expected_split_id)
        return status[row.pk]
    return {row.pk: current(row) for row in latest_by_period.values()}


def list_confirmations(*, actor, company_id):
    from apps.accounting.policies import AccountingAction, accounting_scope
    scope = accounting_scope(actor, company_id, AccountingAction.REPORT, permission_action="accounting.company_period.read")
    if not (scope.is_company_accountant or scope.is_company_wide_reader):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Company period history is available to Company-wide readers only.")
    company = scope.company
    rows = CompanyPeriodConfirmation.objects.filter(tenant=company).order_by("period_start", "period_end", "version")
    from django.db.models import Sum
    from apps.accounting.models import OwnerDistributionPayment
    payment_rows = OwnerDistributionPayment.objects.filter(tenant=company).values(
        "confirmation__period_start", "confirmation__period_end", "recipient_id",
    ).annotate(total=Sum("amount"))
    paid = {(item["confirmation__period_start"], item["confirmation__period_end"], str(item["recipient_id"])): item["total"] for item in payment_rows}
    def with_payments(row):
        data = confirmation_data(row)
        enriched = []
        for allocation in data["owner_allocation_snapshot"]:
            amount_paid = paid.get((row.period_start, row.period_end, allocation["recipient_id"]), Decimal("0.00"))
            due = Decimal(allocation["amount"]) - amount_paid
            enriched.append({**allocation, "paid_amount": format(amount_paid, ".2f"),
                             "outstanding_amount": format(max(Decimal("0.00"), due), ".2f"),
                             "payment_review_required": amount_paid > Decimal(allocation["amount"])})
        data["owner_allocation_snapshot"] = enriched
        return data
    latest = {}
    history = []
    for row in rows:
        latest[(row.period_start, row.period_end)] = row
        history.append(with_payments(row))
    source_current_by_id = current_confirmation_ids(company=company, latest_by_period=latest)
    def row_status(row):
        return {**with_payments(row),
                "source_current": row.pk in source_current_by_id and source_current_by_id[row.pk],
                "is_latest": latest[(row.period_start, row.period_end)].pk == row.pk}
    return {"confirmations": [row_status(row) for row in latest.values()], "history": [row_status(row) for row in rows]}


def confirm_company_period(*, actor, company_id, period_type, year, expected_source_version,
                            distributable_amount, liabilities_reviewed, liability_review_reason,
                            reason, key, path):
    from apps.accounts.audit import record_event
    from apps.accounts.policy import require_action
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.tenants.models import CompanyModuleState
    from apps.accounting.models import AccountingIdempotencyRecord

    period_start, period_end, starts_at, ends_at = period_bounds(period_type, year)
    amount = Decimal(distributable_amount)
    reason, liability_review_reason = reason.strip(), liability_review_reason.strip()
    if not liabilities_reviewed or len(liability_review_reason) < 3 or len(reason) < 3 or amount < 0:
        raise ValidationError("Review liabilities and enter a nonnegative distributable amount with reasons.")
    body = {"period_type": period_type, "year": year, "expected_source_version": expected_source_version,
            "distributable_amount": format(amount, ".2f"), "liabilities_reviewed": liabilities_reviewed,
            "liability_review_reason": liability_review_reason, "reason": reason}

    def operation(company, _branch, revisions, locked_actor):
        require_action(locked_actor, "accounting.company_period.confirm", company=company)
        from django.db import connection
        start_date, end_date, _, _ = period_bounds(period_type, year)
        overlapping = []
        latest_by_period = {}
        for row in CompanyPeriodConfirmation.objects.select_for_update().filter(tenant=company).order_by("period_start", "period_end", "version"):
            latest_by_period[(row.period_start, row.period_end)] = row
        for existing in latest_by_period.values():
            if existing.period_start < end_date and start_date < existing.period_end and (existing.period_start, existing.period_end) != (start_date, end_date):
                overlapping.append(existing)
        if overlapping:
            raise DomainConflict("This period overlaps a confirmed Company period. Review and supersede the exact period first.", code="COMPANY_PERIOD_OVERLAP")
        income, expense, result, current_source_version = source_result(company=company, starts_at=starts_at, ends_at=ends_at)
        if current_source_version != expected_source_version:
            raise DomainConflict("Accounting sources changed. Reload the Company period review.", code="COMPANY_PERIOD_SOURCE_STALE")
        previous = latest_by_period.get((start_date, end_date))
        prior_status = current_confirmation_ids(company=company, latest_by_period=latest_by_period)
        earlier = [row for row in latest_by_period.values() if row.period_end <= start_date and row.period_start < start_date]
        if any(not prior_status.get(row.pk, False) for row in earlier):
            raise DomainConflict("A prior Company period changed and must be reviewed before this period.", code="COMPANY_PERIOD_PRIOR_REVIEW_REQUIRED")
        carryforward_source = max(earlier, key=lambda row: row.period_end) if earlier else None
        prior_loss = carryforward_source.loss_carried_forward if carryforward_source else Decimal("0.00")
        from apps.accounting.models import OwnerDistributionConfiguration
        owner_split = OwnerDistributionConfiguration.objects.select_for_update().filter(
            tenant=company, effective_from__lte=start_date,
        ).order_by("-effective_from", "-version").first() if amount > 0 else None
        if (previous and previous.source_version == current_source_version
            and previous.carryforward_source_id == (carryforward_source.pk if carryforward_source else None)
            and previous.distributable_amount == amount and previous.owner_split_configuration_id == (owner_split.pk if owner_split else None)
            and previous.liability_review_reason == liability_review_reason
            and previous.reason == reason):
            return DomainMutationResult(200, confirmation_data(previous))
        carry = calculate_company_period_carryforward(period_result=result, prior_loss=prior_loss)
        if amount > carry.positive_after_loss:
            raise DomainConflict("Distributable amount exceeds the positive Company result after carried Loss.", code="COMPANY_DISTRIBUTABLE_EXCEEDS_AVAILABLE")
        owner_allocations = []
        if amount > 0:
            from apps.investment.finance import allocate_owner_distribution
            if owner_split is None:
                raise DomainConflict("An effective Platform-approved Owner split is required before confirming a positive distribution.", code="COMPANY_OWNER_SPLIT_UNAVAILABLE")
            try:
                owner_allocations = allocate_owner_distribution(amount=amount, recipients=owner_split.recipients)
            except ValueError as exc:
                raise DomainConflict("The effective Owner split is invalid; ask Platform Back Office to review it.", code="COMPANY_OWNER_SPLIT_INVALID") from exc
        accounting_revision = revisions[CompanyModuleCode.ACCOUNTING]
        if accounting_revision is None or accounting_revision.state != CompanyModuleState.State.ENABLED:
            raise DomainConflict("Accounting must be ON to confirm a Company period.", code="ACCOUNTING_DISABLED")
        with connection.cursor() as cursor:
            cursor.execute("SELECT clock_timestamp()")
            confirmed_at = cursor.fetchone()[0]
        row = CompanyPeriodConfirmation.objects.create(
            tenant=company, period_type=period_type, period_start=start_date, period_end=end_date,
            version=previous.version + 1 if previous else 1, previous=previous, carryforward_source=carryforward_source,
            source_version=current_source_version,
            accounting_result=result, prior_loss_carried_forward=prior_loss,
            loss_carried_forward=carry.loss_carried_forward, positive_after_loss=carry.positive_after_loss,
            distributable_amount=amount, liabilities_reviewed=True, liability_review_reason=liability_review_reason,
            owner_split_configuration=owner_split,
            owner_allocation_snapshot=[{"recipient_id": item.recipient_id,
                "recipient_label": next((entry.get("recipient_label", "Company Owner") for entry in owner_split.recipients if entry.get("id") == item.recipient_id), "Company Owner"),
                "percentage": format(item.percentage, "f"), "amount": format(item.amount, ".2f")}
                for item in owner_allocations],
            reason=reason, actor=locked_actor, accounting_revision=accounting_revision, confirmed_at=confirmed_at,
        )
        record_event(action="accounting.company_period.confirm", actor=locked_actor, subject=locked_actor,
                     company=company, resource=row, reason=reason,
                     metadata={"period_start": start_date.isoformat(), "period_end": end_date.isoformat(),
                               "version": row.version, "source_version": current_source_version,
                               "accounting_result": format(result, ".2f"), "distributable_amount": format(amount, ".2f"),
                               "loss_carried_forward": format(carry.loss_carried_forward, ".2f")})
        return DomainMutationResult(201, confirmation_data(row))

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
                                   body=body, action="accounting.company_period.confirm",
                                   module_codes=(CompanyModuleCode.ACCOUNTING,),
                                   idempotency_model=AccountingIdempotencyRecord, operation=operation)


def configure_owner_distribution(*, actor, company_id, effective_from, recipients, reason, key=None, path=""):
    """Platform Back Office records protected, effective Owner split terms."""
    from django.core.exceptions import PermissionDenied
    from django.db import transaction
    from django.db.models import Q, Max
    from django.utils import timezone
    from apps.accounts.audit import record_event
    from apps.accounts.models import CompanyRoleGrant, User
    from apps.accounts.platform_identity import is_platform_actor
    from apps.accounting.models import OwnerDistributionConfiguration
    from apps.tenants.models import Tenant
    from apps.investment.finance import allocate_owner_distribution
    if not is_platform_actor(actor):
        raise PermissionDenied("An active Platform Back Office account is required.")
    if not key or len(key) > 128:
        raise ValidationError({"Idempotency-Key": "A key of 1 to 128 characters is required."})
    reason = reason.strip()
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        from rest_framework.exceptions import NotFound
        raise NotFound("Company not found.")
    try:
        checked = allocate_owner_distribution(amount="0.00", recipients=recipients)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    owner_ids = [row.recipient_id for row in checked]
    if not reason or len(reason) < 3:
        raise ValidationError("Recipients must be exactly the Company's current Owners, with a reason.")
    with transaction.atomic():
        company = Tenant.objects.select_for_update().get(pk=company.pk)
        if key:
            from apps.common.domain_mutations import DomainConflict
            from apps.accounting.models import AccountingIdempotencyRecord
            import hashlib, json
            body = {"effective_from": effective_from.isoformat(), "recipients": recipients, "reason": reason}
            digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
            existing = AccountingIdempotencyRecord.objects.filter(tenant=company, actor=actor, key=key).first()
            if existing:
                if existing.method != "POST" or existing.path != path or existing.request_hash != digest:
                    raise DomainConflict("Idempotency-Key was already used for a different request.", code="IDEMPOTENCY_KEY_REUSED")
                return existing.response_body
        from datetime import datetime, time
        from zoneinfo import ZoneInfo
        effective_at = timezone.make_aware(datetime.combine(effective_from, time.min), ZoneInfo("Asia/Kolkata"))
        owners = set(CompanyRoleGrant.objects.filter(
            role="owner", branch__isnull=True, membership__tenant=company,
            membership__user__is_active=True, membership__effective_from__lte=effective_at,
            effective_from__lte=effective_at,
        ).filter(Q(effective_until__isnull=True) | Q(effective_until__gt=effective_at))
          .filter(Q(membership__effective_until__isnull=True) | Q(membership__effective_until__gt=effective_at))
          .values_list("membership__user_id", flat=True))
        owners = {str(owner_id) for owner_id in owners}
        if set(owner_ids) != owners:
            raise ValidationError("Recipients must be exactly the Company's Owners on the effective date.")
        labels = {str(user.pk): (" ".join(part for part in (user.first_name, user.last_name) if part).strip() or user.login_id)
                  for user in User.objects.filter(pk__in=owner_ids)}
        version = (OwnerDistributionConfiguration.objects.filter(tenant=company).aggregate(v=Max("version"))["v"] or 0) + 1
        row = OwnerDistributionConfiguration.objects.create(
            tenant=company, version=version, effective_from=effective_from,
            recipients=[{"id": item.recipient_id, "percentage": format(item.percentage, "f"),
                         "recipient_label": labels[item.recipient_id]} for item in checked],
            actor=actor, reason=reason,
        )
        record_event(action="accounting.owner_split.configure", actor=actor, subject=actor,
                     company=company, resource=row, resource_type="accounting.owner_split", reason=reason,
                     metadata={"version": version, "effective_from": effective_from.isoformat(),
                               "recipient_count": len(row.recipients), "configuration_id": str(row.pk)})
        response = {"id": str(row.pk), "company_id": str(company.pk), "version": row.version,
                "effective_from": row.effective_from.isoformat(), "recipients": row.recipients,
                "actor_id": str(row.actor_id), "reason": row.reason}
        if key:
            from apps.accounting.models import AccountingIdempotencyRecord
            AccountingIdempotencyRecord.objects.create(tenant=company, actor=actor, key=key, method="POST", path=path,
                request_hash=digest, response_status=201, response_body=response)
        return response


def pay_owner_distribution(*, actor, company_id, confirmation_id, recipient_id, branch_id,
                           account_id, amount, effective_at, expected_source_version, reason, key, path):
    """Record a partial Owner distribution as one Accounting PAYMENT cash movement."""
    from apps.accounts.audit import record_event
    from apps.common.domain_mutations import DomainConflict, DomainMutationResult, execute_domain_mutation
    from apps.accounting.models import (AccountingAccount, AccountingEvent, AccountingIdempotencyRecord,
        AccountMovement, CompanyPeriodConfirmation, OwnerDistributionPayment)
    from apps.tenants.models import Branch, CompanyModuleCode, CompanyModuleState
    from django.db.models import Sum
    amount, reason = Decimal(amount), reason.strip()
    if amount <= 0 or effective_at > timezone.now() or len(reason) < 3:
        raise ValidationError("Enter a positive, current Owner payment amount and reason.")
    body = {"confirmation_id": str(confirmation_id), "recipient_id": str(recipient_id),
            "branch_id": str(branch_id), "account_id": str(account_id),
            "amount": format(amount, ".2f"), "effective_at": effective_at.isoformat(),
            "expected_source_version": expected_source_version, "reason": reason}

    def operation(company, branch, revisions, locked_actor):
        confirmation = CompanyPeriodConfirmation.objects.select_for_update().filter(
            tenant=company, pk=confirmation_id,
        ).first()
        if confirmation is None:
            raise NotFound("Company period confirmation not found.")
        if confirmation.source_version != expected_source_version:
            raise DomainConflict("Company period sources changed. Reload before recording an Owner payment.", code="OWNER_DISTRIBUTION_SOURCE_STALE")
        latest = {}
        for candidate in CompanyPeriodConfirmation.objects.select_for_update().filter(tenant=company).order_by("period_start", "period_end", "version"):
            latest[(candidate.period_start, candidate.period_end)] = candidate
        if latest.get((confirmation.period_start, confirmation.period_end), None) != confirmation:
            raise DomainConflict("This Company period has a newer confirmation. Reload the Owner distribution.", code="OWNER_DISTRIBUTION_STALE")
        if not current_confirmation_ids(company=company, latest_by_period=latest).get(confirmation.pk, False):
            raise DomainConflict("Company result or Owner split changed. Reconfirm the period before paying.", code="OWNER_DISTRIBUTION_SOURCE_STALE")
        allocation = next((item for item in confirmation.owner_allocation_snapshot
                           if item.get("recipient_id") == str(recipient_id)), None)
        if allocation is None:
            raise NotFound("Recipient is not part of this confirmed Owner distribution.")
        paid = OwnerDistributionPayment.objects.filter(
            tenant=company, confirmation__period_start=confirmation.period_start,
            confirmation__period_end=confirmation.period_end, recipient_id=recipient_id,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        outstanding = Decimal(allocation["amount"]) - paid
        if amount > outstanding:
            raise DomainConflict("Payment exceeds this Owner's current outstanding allocation.", code="OWNER_PAYMENT_EXCEEDS_OUTSTANDING")
        account = AccountingAccount.objects.select_for_update().filter(tenant=company, pk=account_id, is_active=True).first()
        if account is None:
            raise NotFound("Active Cash/Bank account not found.")
        revision = revisions[CompanyModuleCode.ACCOUNTING]
        if revision is None or revision.state != CompanyModuleState.State.ENABLED:
            raise DomainConflict("Accounting must be ON to record an Owner payment.", code="ACCOUNTING_DISABLED")
        payment = OwnerDistributionPayment(
            tenant=company, confirmation=confirmation, recipient_id=recipient_id,
            branch=branch, account=account, amount=amount, effective_at=effective_at,
            reason=reason, actor=locked_actor, accounting_revision=revision,
            accounting_event_id=None,
        )
        from apps.accounting.services import _event_row
        event = _event_row(tenant=company, branch=branch, event_type=AccountingEvent.EventType.OWNER_DISTRIBUTION_PAYMENT,
            amount=amount, actor=locked_actor, revision=revision, description=reason,
            source_reference=f"OWNER-DISTRIBUTION-{payment.pk}", effective_at=effective_at)
        payment.accounting_event = event
        movement = AccountMovement.objects.create(tenant=company, event=event, account=account, delta=-amount)
        payment.save(force_insert=True)
        record_event(action="accounting.owner_distribution.pay", actor=locked_actor, subject=locked_actor,
            company=company, branch=branch, resource=payment, reason=reason,
            metadata={"payment_id": str(payment.pk), "confirmation_id": str(confirmation.pk),
                      "recipient_id": str(recipient_id), "accounting_event_id": str(event.pk),
                      "amount": format(amount, ".2f"), "branch_id": str(branch.pk), "account_id": str(account.pk),
                      "source_version": expected_source_version})
        remaining = outstanding - amount
        return DomainMutationResult(201, {"id": str(payment.pk), "confirmation_id": str(confirmation.pk),
            "recipient_id": str(recipient_id), "amount": format(amount, ".2f"),
            "paid_amount": format(paid + amount, ".2f"), "outstanding_amount": format(remaining, ".2f"),
            "accounting_event_id": str(event.pk), "movement_id": str(movement.pk)})

    return execute_domain_mutation(actor=actor, company_id=company_id, method="POST", path=path, key=key,
        body=body, action="accounting.payment.create", module_codes=(CompanyModuleCode.ACCOUNTING,),
        idempotency_model=AccountingIdempotencyRecord, operation=operation, branch_id=branch_id)
