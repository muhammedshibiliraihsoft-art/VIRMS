from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.login_id import canonical_login_id
from apps.common.models import TimestampedUUIDModel

from .user_manager import UserManager


class User(TimestampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    class AccountKind(models.TextChoices):
        COMPANY = "company", "Company"
        PLATFORM = "platform", "Platform"

    account_kind = models.CharField(
        max_length=8, choices=AccountKind.choices, default=AccountKind.COMPANY
    )
    auth_epoch = models.PositiveBigIntegerField(default=1)
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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(login_id=""), name="account_login_id_nonempty"
            )
        ]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self._state.adding or update_fields is None or "login_id" in update_fields:
            self.login_id = canonical_login_id(self.login_id, using=kwargs.get("using"))
        return super().save(*args, **kwargs)

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

    class Meta:
        indexes = [models.Index(fields=["retry_after"], name="login_retry_after_idx")]


class AccountSecurityEvent(TimestampedUUIDModel):
    """Append-oriented security evidence; never credentials or request bodies."""

    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="account_actions_performed",
    )
    subject = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="account_actions_received",
    )
    action = models.CharField(max_length=40)
    tenant_ids = models.JSONField(default=list)
    outcome = models.CharField(max_length=20, default="success")

    actor_kind = models.CharField(max_length=16, default="user")
    company_id = models.UUIDField(null=True, blank=True)
    branch_id = models.UUIDField(null=True, blank=True)
    resource_type = models.CharField(max_length=40, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    request_id = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict)
    bootstrap_operation_id = models.UUIDField(null=True, blank=True, unique=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["company_id", "occurred_at", "id"],
                name="audit_company_time_idx",
            ),
            models.Index(
                fields=["subject", "occurred_at", "id"], name="audit_subject_time_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from django.core.exceptions import ValidationError

            raise ValidationError("Audit events cannot be changed")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        raise ValidationError("Audit events cannot be deleted")


class SessionActivity(models.Model):
    """Ephemeral server-side lease keyed by session-key hash, not an audit event."""

    key_hash = models.CharField(max_length=64, primary_key=True)
    issued_at = models.PositiveBigIntegerField(db_index=True)
    last_activity = models.PositiveBigIntegerField()
