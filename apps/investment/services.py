from decimal import Decimal

from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Sum
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.accounts.audit import record_event
from apps.accounts.policy import require_action
from apps.accounting.models import AccountingEvent, AccountingSourceLink
from apps.accounting.services import record_capital_movement
from apps.common.business_scope import business_scope
from apps.common.domain_mutations import (
    DomainConflict,
    DomainMutationResult,
    execute_domain_mutation,
)
from apps.investment.models import (
    InvestmentIdempotencyRecord,
    Investor,
    InvestorFundCredit,
    InvestorFundCreditCorrection,
    InvestorFundUseAllocation,
    InvestorFundUseAdjustment,
    InvestorInterimConfiguration,
    InvestorPrincipalReturn,
    InvestorPrincipalReturnAllocation,
)
from apps.investment.selectors import with_current_fund_credit_owner
from apps.tenants.models import Branch, CompanyModuleCode, Tenant


def _date_value(value):
    if value is None:
        value = timezone.now()
    if timezone.is_naive(value):
        raise ValidationError({"effective_at": "An aware timestamp is required."})
    if value > timezone.now():
        raise ValidationError(
            {"effective_at": "An actual Fund cash movement cannot be future-dated."}
        )
    return value


def _investor_data(investor):
    return {
        "id": str(investor.pk),
        "company_id": str(investor.tenant_id),
        "name": investor.name,
        "is_active": investor.is_active,
        "created_at": investor.created_at.isoformat(),
        "updated_at": investor.updated_at.isoformat(),
    }


def _credit_data(credit):
    link = AccountingSourceLink.objects.filter(investor_fund_credit=credit).select_related("event").first()
    corrections = list(credit.attribution_corrections.all())
    corrections.sort(key=lambda row: (row.version, str(row.pk)))
    current_investor_id = corrections[-1].to_investor_id if corrections else credit.investor_id
    manual_review_required = getattr(credit, "has_fund_use", None)
    if manual_review_required is None:
        manual_review_required = InvestorFundUseAllocation.objects.filter(
            tenant_id=credit.tenant_id, credit=credit
        ).exists()
    has_principal_return = getattr(credit, "has_principal_return", None)
    if has_principal_return is None:
        has_principal_return = InvestorPrincipalReturnAllocation.objects.filter(
            tenant_id=credit.tenant_id, credit=credit
        ).exists()
    return {
        "id": str(credit.pk),
        "investor_id": str(current_investor_id),
        "original_investor_id": str(credit.investor_id),
        "branch_id": str(credit.branch_id),
        "amount": format(credit.amount, ".2f"),
        "reference": credit.reference,
        "effective_at": credit.effective_at.isoformat(),
        "recorded_at": credit.created_at.isoformat(),
        "accounting_event_id": str(link.event_id) if link else None,
        "correction_version": corrections[-1].version if corrections else 0,
        "manual_review_required": bool(
            corrections and (manual_review_required or has_principal_return)
        ),
        "attribution_corrections": [
            {
                "id": str(row.pk),
                "from_investor_id": str(row.from_investor_id),
                "to_investor_id": str(row.to_investor_id),
                "amount": format(row.amount, ".2f"),
                "effective_at": row.effective_at.isoformat(),
                "recorded_at": row.created_at.isoformat(),
                "reason": row.reason,
            }
            for row in corrections
        ],
    }


def _return_data(principal_return):
    link = AccountingSourceLink.objects.filter(
        investor_principal_return=principal_return
    ).select_related("event").first()
    return {
        "id": str(principal_return.pk),
        "investor_id": str(principal_return.investor_id),
        "branch_id": str(principal_return.branch_id),
        "amount": format(principal_return.amount, ".2f"),
        "reference": principal_return.reference,
        "effective_at": principal_return.effective_at.isoformat(),
        "recorded_at": principal_return.created_at.isoformat(),
        "accounting_event_id": str(link.event_id) if link else None,
        "allocations": [
            {
                "credit_id": str(row.credit_id),
                "amount": format(row.amount, ".2f"),
            }
            for row in principal_return.allocations.select_related("credit").order_by("credit__effective_at", "credit_id")
        ],
    }


def _available_credit(credit):
    returned = InvestorPrincipalReturnAllocation.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    used = InvestorFundUseAllocation.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    adjusted = InvestorFundUseAdjustment.objects.filter(
        tenant_id=credit.tenant_id, credit=credit
    ).aggregate(total=Sum("amount_delta"))["total"] or Decimal("0.00")
    return credit.amount - returned - used - adjusted


def read_scope(*, actor, company_id, action, branch_id=None):
    company = Tenant.objects.filter(pk=company_id, is_active=True).first()
    if company is None:
        raise NotFound("Company not found.")
    branch = None
    if branch_id is not None:
        branch = Branch.objects.filter(pk=branch_id, tenant=company).first()
        if branch is None:
            raise NotFound("Branch not found.")
    current_actor = require_action(actor, action, company=company, branch=branch)
    return company, business_scope(actor=current_actor, company=company), branch


def _filter_branch_records(queryset, *, scope, branch_id, field="branch_id"):
    if branch_id is not None:
        if not scope.is_company_reader and branch_id not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        return queryset.filter(**{field: branch_id})
    if scope.is_company_reader:
        return queryset
    return queryset.filter(**{f"{field}__in": scope.allowed_branch_ids})


def list_investors(*, actor, company_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.profile.read"
    )
    return Investor.objects.filter(tenant=company, is_active=True).order_by("name", "id")


def get_investor(*, actor, company_id, investor_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.profile.read"
    )
    investor = Investor.objects.filter(
        tenant=company, pk=investor_id, is_active=True
    ).first()
    if investor is None:
        raise NotFound("Investor not found.")
    return investor


def create_investor(*, actor, company_id, key, path, name):
    body = {"name": name.strip()}

    def operation(company, _branch, revisions, locked_actor):
        if not body["name"]:
            raise ValidationError({"name": "A name is required."})
        investor = Investor.objects.create(
            tenant=company,
            name=body["name"],
            created_by=locked_actor,
            updated_by=locked_actor,
        )
        record_event(
            action="investor.profile.create",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=investor,
            metadata={"investor_id": str(investor.pk), "new_name": investor.name},
        )
        return DomainMutationResult(201, _investor_data(investor))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.profile.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def update_investor(*, actor, company_id, investor_id, key, path, values):
    body = {"name": values["name"].strip()}

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        old_name = investor.name
        if not body["name"]:
            raise ValidationError({"name": "A name is required."})
        investor.name = body["name"]
        investor.updated_by = locked_actor
        investor.save(update_fields=("name", "updated_by", "updated_at"))
        record_event(
            action="investor.profile.update",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=investor,
            metadata={
                "investor_id": str(investor.pk),
                "old_name": old_name,
                "new_name": investor.name,
            },
        )
        return DomainMutationResult(200, _investor_data(investor))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="PATCH",
        path=path,
        key=key,
        body=body,
        action="investment.profile.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def list_interim_configurations(*, actor, company_id, investor_id):
    company, _, _ = read_scope(
        actor=actor, company_id=company_id, action="investment.interim.read"
    )
    investor = Investor.objects.filter(tenant=company, pk=investor_id, is_active=True).first()
    if investor is None:
        raise NotFound("Investor not found.")
    return investor.interim_configurations.order_by("effective_date", "id")


def create_interim_configuration(
    *, actor, company_id, investor_id, key, path, amount, effective_date
):
    body = {
        "investor_id": str(investor_id),
        "amount": format(Decimal(amount), ".2f"),
        "effective_date": effective_date.isoformat(),
    }

    def operation(company, _branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        config = InvestorInterimConfiguration.objects.create(
            tenant=company,
            investor=investor,
            amount=Decimal(amount),
            effective_date=effective_date,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(
            action="investor.interim.configure",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            resource=config,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(config.amount, ".2f"),
            },
        )
        return DomainMutationResult(
            201,
            {
                "id": str(config.pk),
                "investor_id": str(investor.pk),
                "amount": format(config.amount, ".2f"),
                "effective_date": config.effective_date.isoformat(),
                "recorded_at": config.created_at.isoformat(),
                "actor_id": str(config.actor_id),
            },
        )

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.interim.manage",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
    )


def list_fund_credits(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    queryset = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
        .select_related("investor", "branch")
        .annotate(
            has_fund_use=Exists(
                InvestorFundUseAllocation.objects.filter(
                    tenant_id=company.pk, credit_id=OuterRef("pk")
                )
            ),
            has_principal_return=Exists(
                InvestorPrincipalReturnAllocation.objects.filter(
                    tenant_id=company.pk, credit_id=OuterRef("pk")
                )
            ),
        )
        .prefetch_related(
            Prefetch(
                "attribution_corrections",
                queryset=InvestorFundCreditCorrection.objects.select_related(
                    "from_investor", "to_investor"
                ).order_by("version", "id"),
            )
        )
    )
    if investor_id is not None:
        queryset = queryset.filter(current_investor_id=investor_id)
    queryset = _filter_branch_records(queryset, scope=scope, branch_id=branch_id)
    return queryset.order_by("effective_at", "id")


def correct_fund_credit_investor(
    *, actor, company_id, credit_id, to_investor_id, reason, key, path
):
    reason = (reason or "").strip()
    body = {
        "credit_id": str(credit_id),
        "to_investor_id": str(to_investor_id),
        "reason": reason,
    }
    source_branch_id = InvestorFundCredit.objects.filter(
        tenant_id=company_id, pk=credit_id
    ).values_list("branch_id", flat=True).first()
    if source_branch_id is None:
        raise NotFound("Fund Credit not found.")

    def operation(company, branch, revisions, locked_actor):
        credit = InvestorFundCredit.objects.select_for_update().filter(
            tenant=company, pk=credit_id, branch=branch
        ).first()
        if credit is None:
            raise NotFound("Fund Credit not found.")
        prior = credit.attribution_corrections.order_by("-version", "-id").first()
        from_investor_id = prior.to_investor_id if prior else credit.investor_id
        if str(from_investor_id) == str(to_investor_id):
            raise ValidationError({"to_investor_id": "Choose a different Investor."})
        to_investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=to_investor_id, is_active=True
        ).first()
        if to_investor is None:
            raise NotFound("Investor not found.")
        if not reason:
            raise ValidationError({"reason": "A correction reason is required."})
        correction = InvestorFundCreditCorrection.objects.create(
            tenant=company,
            credit=credit,
            version=(prior.version + 1 if prior else 1),
            from_investor_id=from_investor_id,
            to_investor=to_investor,
            amount=credit.amount,
            effective_at=credit.effective_at,
            reason=reason,
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        record_event(
            action="investment.fund.credit.correct",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=correction,
            reason=reason,
            metadata={
                "credit_id": str(credit.pk),
                "correction_id": str(correction.pk),
                "old_investor_id": str(from_investor_id),
                "new_investor_id": str(to_investor.pk),
                "amount": format(credit.amount, ".2f"),
                "version": correction.version,
            },
        )
        return DomainMutationResult(201, _credit_data(credit))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.credit.correct",
        module_codes=(CompanyModuleCode.INVESTMENT,),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=source_branch_id,
    )


def fund_summary(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    credits = with_current_fund_credit_owner(
        InvestorFundCredit.objects.filter(tenant=company)
    )
    returns = InvestorPrincipalReturn.objects.filter(tenant=company)
    if investor_id is not None:
        investor_exists = Investor.objects.filter(
            tenant=company, pk=investor_id, is_active=True
        ).exists()
        if not investor_exists:
            raise NotFound("Investor not found.")
        credits = credits.filter(current_investor_id=investor_id)
        returns = returns.filter(investor_id=investor_id)
    if branch_id is not None:
        if not scope.is_company_reader and branch_id not in scope.allowed_branch_ids:
            raise NotFound("Branch not found.")
        credits = credits.filter(branch_id=branch_id)
        returns = returns.filter(branch_id=branch_id)
    elif not scope.is_company_reader:
        credits = credits.filter(branch_id__in=scope.allowed_branch_ids)
        returns = returns.filter(branch_id__in=scope.allowed_branch_ids)

    credit_total = credits.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return_total = returns.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    credit_ids = credits.values("id")
    used_total = InvestorFundUseAllocation.objects.filter(
        tenant=company, credit_id__in=credit_ids
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    usage_adjustment_total = InvestorFundUseAdjustment.objects.filter(
        tenant=company, credit_id__in=credit_ids
    ).aggregate(total=Sum("amount_delta"))["total"] or Decimal("0.00")
    allocated_return_total = InvestorPrincipalReturnAllocation.objects.filter(
        tenant=company, credit_id__in=credit_ids
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    result = {
        "company_id": str(company.pk),
        "investor_id": str(investor_id) if investor_id else None,
        "branch_id": str(branch_id) if branch_id else None,
        "credit_total": format(credit_total, ".2f"),
        "principal_return_total": format(return_total, ".2f"),
        "available_amount": format(
            credit_total - allocated_return_total - used_total - usage_adjustment_total,
            ".2f",
        ),
    }
    # The Branch Accountant receives only the sum inside their authorized
    # source-Branch filter; it is never the pooled Company balance.
    return result


def create_fund_credit(
    *, actor, company_id, key, path, investor_id, branch_id, account_id,
    amount, reference, effective_at,
):
    effective_at = _date_value(effective_at)
    body = {
        "investor_id": str(investor_id),
        "branch_id": str(branch_id),
        "account_id": str(account_id),
        "amount": format(Decimal(amount), ".2f"),
        "reference": reference.strip(),
        "effective_at": effective_at.isoformat(),
    }

    def operation(company, branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        credit = InvestorFundCredit.objects.create(
            tenant=company,
            investor=investor,
            branch=branch,
            amount=Decimal(amount),
            effective_at=effective_at,
            reference=body["reference"],
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        event, _movement, event_data = record_capital_movement(
            tenant=company,
            branch=branch,
            account_id=account_id,
            amount=credit.amount,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.CAPITAL_INFLOW,
            source_record=credit,
            description=f"Investor Fund credit: {investor.name}",
            source_reference=credit.reference,
            effective_at=effective_at,
        )
        record_event(
            action="investment.fund.credit",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=credit,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(credit.amount, ".2f"),
                "accounting_event_id": str(event.pk),
                "branch_id": str(branch.pk),
            },
        )
        result = _credit_data(credit)
        result["accounting_event_id"] = event_data["id"]
        return DomainMutationResult(201, result)

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.credit",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )


def list_principal_returns(*, actor, company_id, investor_id=None, branch_id=None):
    company, scope, _ = read_scope(
        actor=actor,
        company_id=company_id,
        action="investment.fund.read",
        branch_id=branch_id,
    )
    queryset = InvestorPrincipalReturn.objects.filter(tenant=company).select_related(
        "investor", "branch"
    )
    if investor_id is not None:
        queryset = queryset.filter(investor_id=investor_id)
    queryset = _filter_branch_records(queryset, scope=scope, branch_id=branch_id)
    return queryset.order_by("effective_at", "id").prefetch_related("allocations")


def create_principal_return(
    *, actor, company_id, key, path, investor_id, branch_id, account_id,
    amount, reference, effective_at,
):
    effective_at = _date_value(effective_at)
    amount = Decimal(amount)
    body = {
        "investor_id": str(investor_id),
        "branch_id": str(branch_id),
        "account_id": str(account_id),
        "amount": format(amount, ".2f"),
        "reference": reference.strip(),
        "effective_at": effective_at.isoformat(),
    }

    def operation(company, branch, revisions, locked_actor):
        investor = Investor.objects.select_for_update().filter(
            tenant=company, pk=investor_id, is_active=True
        ).first()
        if investor is None:
            raise NotFound("Investor not found.")
        credits = list(
            with_current_fund_credit_owner(
                InvestorFundCredit.objects.select_for_update().filter(
                    tenant=company, branch=branch
                )
            )
            .filter(current_investor_id=investor.pk)
            .order_by("effective_at", "id")
        )
        if not credits:
            raise DomainConflict(
                "No returnable Fund credit exists in this source Branch.",
                code="FUND_AVAILABLE_INSUFFICIENT",
            )
        remaining_by_credit = {}
        available_total = Decimal("0.00")
        for credit in credits:
            remaining = _available_credit(credit)
            remaining_by_credit[credit.pk] = remaining
            available_total += remaining
        if amount <= 0 or amount > available_total:
            raise DomainConflict(
                "Return exceeds the Investor's available Fund in this source Branch.",
                code="FUND_AVAILABLE_INSUFFICIENT",
            )
        principal_return = InvestorPrincipalReturn.objects.create(
            tenant=company,
            investor=investor,
            branch=branch,
            amount=amount,
            effective_at=effective_at,
            reference=body["reference"],
            actor=locked_actor,
            module_revision=revisions[CompanyModuleCode.INVESTMENT],
        )
        unallocated = amount
        for credit in credits:
            available = remaining_by_credit[credit.pk]
            if available <= 0:
                continue
            allocation_amount = min(available, unallocated)
            if allocation_amount > 0:
                InvestorPrincipalReturnAllocation.objects.create(
                    tenant=company,
                    principal_return=principal_return,
                    credit=credit,
                    amount=allocation_amount,
                    actor=locked_actor,
                )
                unallocated -= allocation_amount
            if unallocated == 0:
                break
        event, _movement, _event_data = record_capital_movement(
            tenant=company,
            branch=branch,
            account_id=account_id,
            amount=principal_return.amount,
            actor=locked_actor,
            accounting_revision=revisions[CompanyModuleCode.ACCOUNTING],
            event_type=AccountingEvent.EventType.CAPITAL_OUTFLOW,
            source_record=principal_return,
            description=f"Investor principal return: {investor.name}",
            source_reference=principal_return.reference,
            effective_at=effective_at,
        )
        record_event(
            action="investment.fund.principal_return",
            actor=locked_actor,
            subject=locked_actor,
            company=company,
            branch=branch,
            resource=principal_return,
            metadata={
                "investor_id": str(investor.pk),
                "amount": format(amount, ".2f"),
                "accounting_event_id": str(event.pk),
                "branch_id": str(branch.pk),
            },
        )
        return DomainMutationResult(201, _return_data(principal_return))

    return execute_domain_mutation(
        actor=actor,
        company_id=company_id,
        method="POST",
        path=path,
        key=key,
        body=body,
        action="investment.fund.return",
        module_codes=(CompanyModuleCode.INVESTMENT, CompanyModuleCode.ACCOUNTING),
        idempotency_model=InvestmentIdempotencyRecord,
        operation=operation,
        branch_id=branch_id,
    )
