from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db import transaction
from django.http import Http404
from django.views.decorators.cache import never_cache

from apps.accounts.lifecycle import (
    reset_account,
    revoke_account_sessions,
    set_account_status,
)
from apps.accounts.models import User
from apps.accounts.provisioning import provision_company_account
from apps.accounts.serializers import ProvisionSerializer


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def provision_account(request):
    serializer = ProvisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.db import IntegrityError

    try:
        user, temporary_password = provision_company_account(
            actor=request.user,
            company_id=data["tenant_id"],
            branch_id=data.get("branch_id"),
            role=data["role"],
            login_id=data["login_id"],
            email=data["email"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
    except PermissionDenied:
        return Response({"detail": "Not authorized"}, status=403)
    except (ValidationError, IntegrityError):
        return Response({"detail": "Account identifier unavailable"}, status=400)
    return Response(
        {"id": str(user.pk), "temporary_password": temporary_password},
        status=status.HTTP_201_CREATED,
    )


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reset_account_password(request, user_id):
    from django.core.exceptions import PermissionDenied

    try:
        temporary_password = reset_account(actor=request.user, user_id=user_id)
    except (User.DoesNotExist, PermissionDenied):
        raise Http404
    return Response({"temporary_password": temporary_password})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
@never_cache
def set_account_active(request, user_id):
    active = request.data.get("is_active")
    if not isinstance(active, bool):
        return Response({"detail": "is_active must be boolean"}, status=400)
    from django.core.exceptions import PermissionDenied

    try:
        set_account_status(actor=request.user, user_id=user_id, active=active)
    except (User.DoesNotExist, PermissionDenied):
        raise Http404
    return Response({"is_active": active})


@never_cache
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_account_sessions_view(request, user_id):
    from django.core.exceptions import PermissionDenied

    try:
        epoch = revoke_account_sessions(actor=request.user, user_id=user_id)
    except (User.DoesNotExist, PermissionDenied):
        raise Http404
    return Response({"revoked": True, "auth_epoch": epoch})
