from django import forms
from django.contrib import admin
from django.contrib import admin as django_admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from apps.tenants.admin_scope import is_platform_admin_actor, managed_companies
from apps.tenants.models import Branch, Tenant

from .admin_login import VIRMSAdminAuthenticationForm
from .lifecycle import reset_account, revoke_account_sessions, set_account_status
from .models import CompanyRoleGrant, User
from .provisioning import provision_company_account

django_admin.site.login_form = VIRMSAdminAuthenticationForm


class AdminProvisionAccountForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Tenant.objects.none())
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.none(), required=False, empty_label="Company-wide"
    )
    # Platform Back Office provisions privileged Company accounts here.
    # Investor and Media provisioning remains Accountant-scoped.
    role = forms.ChoiceField(
        choices=tuple(
            choice
            for choice in CompanyRoleGrant.Role.choices
            if choice[0]
            in {CompanyRoleGrant.Role.OWNER, CompanyRoleGrant.Role.ACCOUNTANT}
        )
    )
    login_id = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=254)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        companies = managed_companies(actor)
        self.fields["company"].queryset = companies
        selected_company = self.data.get("company") if self.is_bound else None
        branches = Branch.objects.filter(tenant__in=companies)
        if selected_company:
            branches = branches.filter(tenant_id=selected_company)
        self.fields["branch"].queryset = branches

    def clean(self):
        cleaned = super().clean()
        company = cleaned.get("company")
        branch = cleaned.get("branch")
        if (
            company is not None
            and branch is not None
            and branch.tenant_id != company.pk
        ):
            self.add_error("branch", "Choose a Branch in the selected Company.")
        return cleaned


def _no_store(response):
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["Pragma"] = "no-cache"
    response["Vary"] = "Cookie"
    return response


def _account_admin_template(request, template, context, status=200):
    return _no_store(
        TemplateResponse(
            request,
            template,
            {**admin.site.each_context(request), **context},
            status=status,
        )
    )


def _run_selected_accounts(request, queryset, operation, success_message):
    rows = list(queryset.order_by("pk"))
    try:
        with transaction.atomic():
            for row in rows:
                operation(actor=request.user, user_id=row.pk)
    except (PermissionDenied, ValidationError, User.DoesNotExist):
        messages.error(request, "The selected accounts could not be processed.")
        return None
    messages.success(request, success_message.format(count=len(rows)))
    return None


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("login_id", "email", "is_active", "must_change_password")
    list_filter = ("is_active", "must_change_password")
    search_fields = ("login_id", "email")
    ordering = ("login_id", "id")
    actions = (
        "deactivate_selected_accounts",
        "reactivate_selected_accounts",
        "revoke_selected_sessions",
    )

    fieldsets = (
        (None, {"fields": ("login_id", "email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name")}),
        (
            "Account",
            {
                "fields": (
                    "is_active",
                    "must_change_password",
                    "account_kind",
                    "auth_epoch",
                )
            },
        ),
        (
            "Django administration",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "History",
            {"fields": ("id", "created_at", "updated_at", "date_joined", "last_login")},
        ),
    )

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not is_platform_admin_actor(request.user):
            return queryset.filter(pk=request.user.pk)
        return queryset.filter(
            Q(tenant_memberships__tenant__in=managed_companies(request.user))
            | Q(pk=request.user.pk)
        ).distinct()

    def has_view_permission(self, request, obj=None):
        actor = request.user
        if not actor.is_active or not actor.is_staff:
            return False
        if obj is None:
            return True
        if obj.pk == actor.pk:
            return True
        return (
            is_platform_admin_actor(actor)
            and self.get_queryset(request).filter(pk=obj.pk).exists()
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields) + (
            "groups",
            "user_permissions",
        )

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            return HttpResponseForbidden("Not authorized")
        form = AdminProvisionAccountForm(
            request.POST if request.method == "POST" else None,
            actor=request.user,
        )
        if request.method == "POST" and form.is_valid():
            data = form.cleaned_data
            try:
                user, temporary_password = provision_company_account(
                    actor=request.user,
                    company_id=data["company"].pk,
                    branch_id=data["branch"].pk if data["branch"] else None,
                    role=data["role"],
                    login_id=data["login_id"],
                    email=data["email"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
            except PermissionDenied:
                return HttpResponseForbidden("Not authorized")
            except (IntegrityError, ValidationError):
                form.add_error(
                    None, "The account could not be created with this request."
                )
            else:
                return _account_admin_template(
                    request,
                    "admin/accounts/temporary_password.html",
                    {"user": user, "temporary_password": temporary_password},
                )
        return _account_admin_template(
            request,
            "admin/accounts/provision_user.html",
            {"form": form, "opts": self.model._meta},
            status=400 if request.method == "POST" else 200,
        )

    def user_change_password(self, request, id, form_url=""):
        subject = self.get_object(request, id)
        if subject is None or not self.has_change_permission(request, subject):
            raise PermissionDenied
        if subject.pk == request.user.pk:
            if request.method != "GET":
                return HttpResponseForbidden("Use the self-service password form")
            return redirect(reverse("admin:password_change"))
        if not is_platform_admin_actor(request.user):
            raise PermissionDenied
        if request.method == "GET":
            return _account_admin_template(
                request,
                "admin/accounts/reset_user_confirm.html",
                {"user": subject},
            )
        if request.method != "POST" or request.POST.get("confirm") != "yes":
            return HttpResponseForbidden("Confirm the approved reset action")
        try:
            temporary_password = reset_account(actor=request.user, user_id=subject.pk)
        except (PermissionDenied, User.DoesNotExist):
            raise PermissionDenied
        return _account_admin_template(
            request,
            "admin/accounts/temporary_password.html",
            {"user": subject, "temporary_password": temporary_password},
        )

    def save_model(self, request, obj, form, change):
        # Profile, identity, password, privilege and status changes have no raw
        # Admin save path; approved command adapters handle consequential actions.
        raise PermissionDenied("Use an approved account command")

    @admin.action(
        description="Deactivate selected Company accounts", permissions=("change",)
    )
    def deactivate_selected_accounts(self, request, queryset):
        return _run_selected_accounts(
            request,
            queryset,
            lambda **kwargs: set_account_status(**kwargs, active=False),
            "{count} accounts deactivated.",
        )

    @admin.action(
        description="Reactivate selected Company accounts", permissions=("change",)
    )
    def reactivate_selected_accounts(self, request, queryset):
        return _run_selected_accounts(
            request,
            queryset,
            lambda **kwargs: set_account_status(**kwargs, active=True),
            "{count} accounts reactivated. A fresh password reset is required before sign-in.",
        )

    @admin.action(
        description="Revoke selected account sessions", permissions=("change",)
    )
    def revoke_selected_sessions(self, request, queryset):
        return _run_selected_accounts(
            request,
            queryset,
            revoke_account_sessions,
            "Sessions revoked for {count} accounts.",
        )
