import hashlib
import json
from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.accounts.locks import locked_users
from apps.accounts.models import User
from apps.accounts.policy import require_action
from apps.tenants.models import CompanyModuleState, Tenant


class DomainConflict(APIException):
    status_code = 409
    default_code = "domain_conflict"

    def __init__(self, detail, *, code="domain_conflict"):
        super().__init__({"detail": detail, "code": code}, code=code)


@dataclass(frozen=True)
class DomainMutationResult:
    status: int
    body: dict


def _revision_map(company_id, module_codes):
    result = {}
    for module_code in module_codes:
        revision = (
            CompanyModuleState.objects.filter(
                tenant_id=company_id, module_code=module_code
            )
            .order_by("-version", "-id")
            .first()
        )
        result[module_code] = revision
    return result


def _version(revision):
    return revision.version if revision else 0


def execute_domain_mutation(
    *,
    actor,
    company_id,
    method,
    path,
    key,
    body,
    action,
    module_codes,
    idempotency_model,
    operation,
    branch_id=None,
):
    """Serialize a Phase 5 domain write with company module-state revisions."""
    if not key or len(key) > 128:
        raise ValidationError({"Idempotency-Key": "A key of 1 to 128 characters is required."})
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    module_codes = tuple(sorted(set(module_codes)))

    try:
        with locked_users(actor.pk) as users:
            locked_actor = users[actor.pk]
            if (
                actor.auth_epoch != locked_actor.auth_epoch
                or actor.password != locked_actor.password
            ):
                raise PermissionDenied("Authentication changed.")
            observed = _revision_map(company_id, module_codes)
            company = Tenant.objects.select_for_update().filter(pk=company_id).first()
            if company is None or not company.is_active:
                raise NotFound("Company not found.")
            current = _revision_map(company.pk, module_codes)
            if any(_version(observed[code]) != _version(current[code]) for code in module_codes):
                raise DomainConflict(
                    "Company module state changed while this request was being prepared. Reload and retry.",
                    code="MODULE_STATE_CHANGED",
                )

            from apps.tenants.models import Branch

            branch = None
            if branch_id is not None:
                branch = Branch.objects.filter(pk=branch_id, tenant=company).first()
                if branch is None:
                    raise NotFound("Branch not found.")
            require_action(
                locked_actor,
                action,
                company=company,
                branch=branch,
            )

            existing = idempotency_model.objects.filter(
                tenant=company, actor=locked_actor, key=key
            ).first()
            if existing is not None:
                if (
                    existing.method != method
                    or existing.path != path
                    or existing.request_hash != digest
                ):
                    raise DomainConflict(
                        "Idempotency-Key was already used for a different request.",
                        code="IDEMPOTENCY_KEY_REUSED",
                    )
                return DomainMutationResult(
                    existing.response_status, existing.response_body
                )

            for module_code in module_codes:
                revision = current[module_code]
                if (
                    revision is None
                    or revision.state != CompanyModuleState.State.ENABLED
                ):
                    raise PermissionDenied(f"{module_code} module is not enabled.")
            if any(
                _version(current[code]) != _version(_revision_map(company.pk, module_codes)[code])
                for code in module_codes
            ):
                raise DomainConflict(
                    "Company module state changed during validation. Reload and retry.",
                    code="MODULE_STATE_CHANGED",
                )

            result = operation(company, branch, current, locked_actor)
            idempotency_model.objects.create(
                tenant=company,
                actor=locked_actor,
                key=key,
                method=method,
                path=path,
                request_hash=digest,
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
        if constraint == "fund_credit_reference_uq":
            raise DomainConflict(
                "This reference already exists for the selected Cash/Bank account.",
                code="FUND_CREDIT_REFERENCE_DUPLICATE",
            ) from exc
        if constraint == "invest_idem_scope_key_uq" or constraint == "vehicle_idem_scope_key_uq":
            existing = idempotency_model.objects.filter(
                tenant_id=company_id, actor_id=actor.pk, key=key
            ).first()
            if existing and existing.method == method and existing.path == path and existing.request_hash == digest:
                return DomainMutationResult(existing.response_status, existing.response_body)
            raise DomainConflict(
                "Idempotency-Key was already used for a different request.",
                code="IDEMPOTENCY_KEY_REUSED",
            ) from exc
        raise
