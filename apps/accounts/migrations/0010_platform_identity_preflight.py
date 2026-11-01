from django.db import migrations
from django.db.models import Exists, OuterRef, Q


def validate_platform_identities(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        raise RuntimeError("Platform identity preflight requires PostgreSQL")

    alias = connection.alias
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "RoleAssignment")
    Grant = apps.get_model("accounts", "CompanyRoleGrant")

    schema_editor.execute(
        "LOCK TABLE accounts_user, accounts_roleassignment, "
        "accounts_companyrolegrant IN SHARE ROW EXCLUSIVE MODE"
    )

    back_office_history = Role.objects.using(alias).filter(
        user_id=OuterRef("pk"), role="back_office"
    )
    company_role_history = Role.objects.using(alias).filter(
        user_id=OuterRef("pk")
    ).exclude(role="back_office")
    company_grant_history = Grant.objects.using(alias).filter(
        membership__user_id=OuterRef("pk")
    )
    unsafe = (
        User.objects.using(alias)
        .filter(account_kind="platform")
        .annotate(
            _has_back_office=Exists(back_office_history),
            _has_company_role=Exists(company_role_history),
            _has_company_grant=Exists(company_grant_history),
        )
        .filter(
            Q(_has_back_office=False)
            | Q(_has_company_role=True)
            | Q(_has_company_grant=True)
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    count = unsafe.count()
    if count:
        sample = ", ".join(str(user_id) for user_id in unsafe[:10])
        raise RuntimeError(
            f"Platform identity preflight rejected {count} ambiguous account(s). "
            "Run check_account_identity_cutover for UUIDs; preserve rows/history "
            f"for reviewed operator remediation. Sample UUIDs: {sample}"
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_canonical_login_id")]

    operations = [
        migrations.RunPython(
            validate_platform_identities,
            reverse_code=migrations.RunPython.noop,
        )
    ]
