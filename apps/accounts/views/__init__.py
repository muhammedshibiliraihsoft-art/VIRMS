import secrets

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.accounts.models import AccountSecurityEvent, RoleAssignment, User
from apps.accounts.serializers import ProvisionSerializer
from apps.tenants.models import TenantMembership


def can_manage(actor, role, tenant_id):
    if not actor.is_active or actor.must_change_password:
        return False
    now = timezone.now()
    membership = TenantMembership.objects.select_for_update().filter(
        user=actor,
        tenant_id=tenant_id,
        tenant__is_active=True,
        effective_from__lte=now,
        effective_until__isnull=True,
    )
    if not membership.exists():
        return False
    if role in {RoleAssignment.Role.OWNER, RoleAssignment.Role.ACCOUNTANT}:
        required_role = RoleAssignment.Role.BACK_OFFICE
    elif role in {RoleAssignment.Role.INVESTOR, RoleAssignment.Role.MEDIA}:
        required_role = RoleAssignment.Role.ACCOUNTANT
    else:
        return False
    return (
        RoleAssignment.objects.select_for_update()
        .filter(
            user=actor,
            role=required_role,
            effective_from__lte=now,
            effective_until__isnull=True,
        )
        .exists()
    )


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def provision_account(request):
    serializer = ProvisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if not can_manage(request.user, data["role"], data["tenant_id"]):
        return Response({"detail": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
    if (
        User.objects.filter(login_id=data["login_id"]).exists()
        or User.objects.filter(email__iexact=data["email"]).exists()
    ):
        return Response(
            {"detail": "Account identifier unavailable"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    temporary_password = secrets.token_urlsafe(24)
    user = User.objects.create_user(
        login_id=data["login_id"],
        password=temporary_password,
        email=data["email"],
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        must_change_password=True,
        created_by=request.user,
    )
    RoleAssignment.objects.create(
        user=user, role=data["role"], assigned_by=request.user
    )
    TenantMembership.objects.create(
        user=user, tenant_id=data["tenant_id"], assigned_by=request.user
    )
    AccountSecurityEvent.objects.create(
        actor=request.user,
        subject=user,
        action="provision",
        tenant_ids=[str(data["tenant_id"])],
    )
    return Response(
        {"id": str(user.pk), "temporary_password": temporary_password},
        status=status.HTTP_201_CREATED,
    )


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reset_account_password(request, user_id):
    target = User.objects.select_for_update().filter(pk=user_id).first()
    if target is None:
        raise Http404
    now = timezone.now()
    target_roles = set(
        target.role_assignments.select_for_update()
        .filter(effective_from__lte=now, effective_until__isnull=True)
        .values_list("role", flat=True)
    )
    target_tenants = set(
        target.tenant_memberships.select_for_update()
        .filter(
            tenant__is_active=True,
            effective_from__lte=now,
            effective_until__isnull=True,
        )
        .values_list("tenant_id", flat=True)
    )
    if not target_roles or not target_tenants:
        raise Http404
    if not all(
        can_manage(request.user, role, tenant_id)
        for role in target_roles
        for tenant_id in target_tenants
    ):
        raise Http404
    temporary_password = secrets.token_urlsafe(24)
    target.set_password(temporary_password)
    target.must_change_password = True
    target.updated_by = request.user
    target.save(
        update_fields=["password", "must_change_password", "updated_by", "updated_at"]
    )
    AccountSecurityEvent.objects.create(
        actor=request.user,
        subject=target,
        action="reset_password",
        tenant_ids=sorted(str(value) for value in target_tenants),
    )
    return Response({"temporary_password": temporary_password})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def set_account_active(request, user_id):
    target = User.objects.select_for_update().filter(pk=user_id).first()
    if target is None:
        raise Http404
    now = timezone.now()
    target_roles = set(
        target.role_assignments.select_for_update()
        .filter(effective_from__lte=now, effective_until__isnull=True)
        .values_list("role", flat=True)
    )
    target_tenants = set(
        target.tenant_memberships.select_for_update()
        .filter(
            tenant__is_active=True,
            effective_from__lte=now,
            effective_until__isnull=True,
        )
        .values_list("tenant_id", flat=True)
    )
    if (
        not target_roles
        or not target_tenants
        or not all(
            can_manage(request.user, role, tenant_id)
            for role in target_roles
            for tenant_id in target_tenants
        )
    ):
        raise Http404
    active = request.data.get("is_active")
    if not isinstance(active, bool):
        return Response({"detail": "is_active must be boolean"}, status=400)
    if target.is_active == active:
        return Response({"is_active": active})
    target.is_active = active
    target.updated_by = request.user
    if not active:
        target.set_unusable_password()
        target.must_change_password = True
    target.save()
    AccountSecurityEvent.objects.create(
        actor=request.user,
        subject=target,
        action="activate" if active else "deactivate",
        tenant_ids=sorted(str(value) for value in target_tenants),
    )
    return Response({"is_active": active})
