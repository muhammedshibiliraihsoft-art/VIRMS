from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import AccountSecurityEvent, RoleAssignment, User


class VIRMSUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("login_id", "email")


class VIRMSUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = VIRMSUserCreationForm
    form = VIRMSUserChangeForm
    list_display = (
        "login_id",
        "email",
        "is_active",
        "is_staff",
        "must_change_password",
    )
    search_fields = ("login_id", "email")
    ordering = ("login_id",)
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("login_id", "email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name")}),
        ("Account", {"fields": ("is_active", "must_change_password")}),
        (
            "Django administration",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "History",
            {"fields": ("id", "created_at", "updated_at", "date_joined", "last_login")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "login_id",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        if change and not obj.is_active:
            was_active = User.objects.filter(pk=obj.pk, is_active=True).exists()
            if was_active:
                obj.set_unusable_password()
                obj.must_change_password = True
        super().save_model(request, obj, form, change)

    def user_change_password(self, request, id, form_url=""):
        response = super().user_change_password(request, id, form_url)
        if request.method == "POST" and response.status_code == 302:
            subject = User.objects.get(pk=id)
            subject.must_change_password = True
            subject.updated_by = request.user
            subject.save(
                update_fields=["must_change_password", "updated_by", "updated_at"]
            )
            AccountSecurityEvent.objects.create(
                actor=request.user,
                subject=subject,
                action="reset_password",
                tenant_ids=[
                    str(value)
                    for value in subject.tenant_memberships.values_list(
                        "tenant_id", flat=True
                    )
                ],
            )
        return response


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "effective_from", "effective_until", "assigned_by")
    readonly_fields = ("id", "created_at", "updated_at", "assigned_by")

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj:
            fields.extend(("user", "role", "effective_from"))
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
