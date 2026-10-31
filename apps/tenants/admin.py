from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef

from apps.accounts.models import CompanyRoleGrant, User

from .admin_scope import is_platform_admin_actor, managed_companies
from .commands import (
    add_membership,
    assign_branch,
    create_branch,
    create_company,
    end_membership,
    end_scope_row,
    grant_role,
    rename_branch,
    set_company,
)
from .models import Branch, BranchAssignment, Tenant, TenantMembership
from .selectors import current_interval


def _end_selected(request, queryset, operation, label):
    rows = list(queryset.order_by("pk"))
    try:
        with transaction.atomic():
            for row in rows:
                operation(actor=request.user, row=row)
    except (PermissionDenied, ValidationError, Tenant.DoesNotExist):
        messages.error(request, "The selected records could not be processed.")
        return None
    messages.success(request, f"{len(rows)} {label} ended.")
    return None


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    ordering = ("name", "id")

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(pk__in=managed_companies(request.user).values("pk"))
        )

    def has_view_permission(self, request, obj=None):
        if not is_platform_admin_actor(request.user):
            return False
        if obj is None:
            return True
        return managed_companies(request.user).filter(pk=obj.pk).exists()

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = {"id", "created_at", "updated_at"}
        if obj is None:
            fields.add("is_active")
        else:
            fields.add("slug")
        return tuple(
            field.name for field in self.model._meta.fields if field.name in fields
        )

    def save_model(self, request, obj, form, change):
        if not is_platform_admin_actor(request.user):
            raise PermissionDenied
        if not change:
            created = create_company(
                actor=request.user,
                name=form.cleaned_data["name"],
                slug=form.cleaned_data["slug"],
            )
            obj.pk = created.pk
            return

        original = Tenant.objects.get(pk=obj.pk)
        name_changed = original.name != form.cleaned_data["name"]
        active_changed = original.is_active != form.cleaned_data["is_active"]
        if name_changed and active_changed:
            raise PermissionDenied("Apply one Company lifecycle action at a time")
        if name_changed:
            saved = set_company(actor=request.user, company=original, name=obj.name)
            obj.name = saved.name
        elif active_changed:
            saved = set_company(
                actor=request.user, company=original, is_active=obj.is_active
            )
            obj.is_active = saved.is_active


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant")
    list_select_related = ("tenant",)
    search_fields = ("name", "tenant__name")
    autocomplete_fields = ("tenant",)
    fields = ("tenant", "name", "id", "created_at", "updated_at")

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(tenant__in=managed_companies(request.user))
        )

    def has_view_permission(self, request, obj=None):
        if not is_platform_admin_actor(request.user):
            return False
        return (
            obj is None
            or managed_companies(request.user).filter(pk=obj.tenant_id).exists()
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = {"id", "created_at", "updated_at"}
        if obj is not None:
            fields.add("tenant")
        return tuple(
            field.name for field in self.model._meta.fields if field.name in fields
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tenant":
            kwargs["queryset"] = managed_companies(request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not is_platform_admin_actor(request.user):
            raise PermissionDenied
        if not change:
            created = create_branch(
                actor=request.user, company=obj.tenant, name=form.cleaned_data["name"]
            )
            obj.pk = created.pk
            return
        original = Branch.objects.get(
            pk=obj.pk, tenant__in=managed_companies(request.user)
        )
        if original.name != form.cleaned_data["name"]:
            saved = rename_branch(
                actor=request.user, branch=original, name=form.cleaned_data["name"]
            )
            obj.name = saved.name


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "effective_from", "effective_until")
    list_select_related = ("user", "tenant")
    search_fields = ("user__login_id", "tenant__name")
    autocomplete_fields = ("user", "tenant")
    fields = (
        "user",
        "tenant",
        "id",
        "effective_from",
        "effective_until",
        "assigned_by",
    )
    actions = ("end_selected_memberships",)
    ordering = ("tenant__name", "user__login_id", "id")

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(tenant__in=managed_companies(request.user))
        )

    def has_view_permission(self, request, obj=None):
        if not is_platform_admin_actor(request.user):
            return False
        return (
            obj is None
            or managed_companies(request.user).filter(pk=obj.tenant_id).exists()
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return tuple(field.name for field in self.model._meta.fields)
        return ("id", "effective_from", "effective_until", "assigned_by")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        companies = managed_companies(request.user)
        if db_field.name == "tenant":
            kwargs["queryset"] = companies
        elif db_field.name == "user":
            company_ids = companies.values("pk")
            outside_membership = TenantMembership.objects.filter(
                user_id=OuterRef("pk")
            ).exclude(tenant_id__in=company_ids)
            company_users = (
                User.objects.filter(
                    account_kind=User.AccountKind.COMPANY, is_active=True
                )
                .annotate(_outside_company=Exists(outside_membership))
                .filter(_outside_company=False)
            )
            platform_users = User.objects.filter(
                account_kind=User.AccountKind.PLATFORM, is_active=True
            )
            kwargs["queryset"] = (company_users | platform_users).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionDenied("Membership changes require lifecycle commands")
        row = add_membership(actor=request.user, company=obj.tenant, user=obj.user)
        obj.pk = row.pk

    @admin.action(description="End selected memberships", permissions=("change",))
    def end_selected_memberships(self, request, queryset):
        rows = list(queryset.order_by("pk"))
        try:
            with transaction.atomic():
                for row in rows:
                    end_membership(actor=request.user, membership=row)
        except (PermissionDenied, ValidationError):
            messages.error(request, "The selected memberships could not be ended.")
            return None
        messages.success(request, f"{len(rows)} memberships ended.")


@admin.register(CompanyRoleGrant)
class CompanyRoleGrantAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "company",
        "role",
        "branch",
        "effective_from",
        "effective_until",
    )
    list_select_related = ("membership__user", "membership__tenant", "branch")
    search_fields = ("membership__user__login_id", "membership__tenant__name")
    autocomplete_fields = ("membership", "branch")
    fields = (
        "membership",
        "role",
        "branch",
        "id",
        "effective_from",
        "effective_until",
        "assigned_by",
    )
    actions = ("end_selected_grants",)

    @admin.display(ordering="membership__user__login_id")
    def account(self, obj):
        return obj.membership.user

    @admin.display(ordering="membership__tenant__name")
    def company(self, obj):
        return obj.membership.tenant

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(membership__tenant__in=managed_companies(request.user))
        )

    def has_view_permission(self, request, obj=None):
        if not is_platform_admin_actor(request.user):
            return False
        return (
            obj is None
            or managed_companies(request.user)
            .filter(pk=obj.membership.tenant_id)
            .exists()
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return tuple(field.name for field in self.model._meta.fields)
        return ("id", "effective_from", "effective_until", "assigned_by")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        companies = managed_companies(request.user)
        if db_field.name == "membership":
            kwargs["queryset"] = TenantMembership.objects.filter(
                tenant__in=companies, user__is_active=True
            ).filter(current_interval())
        elif db_field.name == "branch":
            kwargs["queryset"] = Branch.objects.filter(tenant__in=companies)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionDenied("Role changes require scope commands")
        row = grant_role(
            actor=request.user,
            membership=obj.membership,
            role=obj.role,
            branch=obj.branch,
        )
        obj.pk = row.pk

    @admin.action(
        description="End selected Company role grants", permissions=("change",)
    )
    def end_selected_grants(self, request, queryset):
        return _end_selected(request, queryset, end_scope_row, "Company role grants")


@admin.register(BranchAssignment)
class BranchAssignmentAdmin(admin.ModelAdmin):
    list_display = ("account", "company", "branch", "effective_from", "effective_until")
    list_select_related = ("membership__user", "membership__tenant", "branch")
    search_fields = (
        "membership__user__login_id",
        "membership__tenant__name",
        "branch__name",
    )
    autocomplete_fields = ("membership", "branch")
    fields = (
        "membership",
        "branch",
        "id",
        "effective_from",
        "effective_until",
        "assigned_by",
    )
    actions = ("end_selected_assignments",)

    @admin.display(ordering="membership__user__login_id")
    def account(self, obj):
        return obj.membership.user

    @admin.display(ordering="membership__tenant__name")
    def company(self, obj):
        return obj.membership.tenant

    def has_module_permission(self, request):
        return (
            is_platform_admin_actor(request.user)
            and managed_companies(request.user).exists()
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(membership__tenant__in=managed_companies(request.user))
        )

    def has_view_permission(self, request, obj=None):
        if not is_platform_admin_actor(request.user):
            return False
        return (
            obj is None
            or managed_companies(request.user)
            .filter(pk=obj.membership.tenant_id)
            .exists()
        )

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return tuple(field.name for field in self.model._meta.fields)
        return ("id", "effective_from", "effective_until", "assigned_by")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        companies = managed_companies(request.user)
        if db_field.name == "membership":
            kwargs["queryset"] = TenantMembership.objects.filter(
                tenant__in=companies, user__is_active=True
            ).filter(current_interval())
        elif db_field.name == "branch":
            kwargs["queryset"] = Branch.objects.filter(tenant__in=companies)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionDenied("Branch assignment changes require scope commands")
        row = assign_branch(
            actor=request.user, membership=obj.membership, branch=obj.branch
        )
        obj.pk = row.pk

    @admin.action(
        description="End selected Branch assignments", permissions=("change",)
    )
    def end_selected_assignments(self, request, queryset):
        return _end_selected(request, queryset, end_scope_row, "Branch assignments")
