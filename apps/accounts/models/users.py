from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import TimestampedUUIDModel

from .user_manager import UserManager


class User(TimestampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    login_id = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="provisioned_users",
    )
    updated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="updated_users",
    )

    objects = UserManager()
    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.login_id or str(self.pk)


class RoleAssignment(TimestampedUUIDModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ACCOUNTANT = "accountant", "Accountant"
        INVESTOR = "investor", "Investor"
        MEDIA = "media", "Media User"
        BACK_OFFICE = "back_office", "Back Office Admin"

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="role_assignments"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    effective_from = models.DateTimeField(default=timezone.now)
    effective_until = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="assigned_roles"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(effective_until__isnull=True)
                | models.Q(effective_until__gt=models.F("effective_from")),
                name="role_valid_interval",
            ),
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(effective_until__isnull=True),
                name="one_open_role_assignment",
            ),
        ]


class LoginAttempt(TimestampedUUIDModel):
    """Hashed Login ID for rate limiting; never stores credentials."""

    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    retry_after = models.DateTimeField(null=True, blank=True)


class AccountSecurityEvent(TimestampedUUIDModel):
    """Successful sensitive account action without credentials or session data."""

    actor = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="account_actions_performed"
    )
    subject = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="account_actions_received"
    )
    action = models.CharField(max_length=40)
    tenant_ids = models.JSONField(default=list)
    outcome = models.CharField(max_length=20, default="success")
