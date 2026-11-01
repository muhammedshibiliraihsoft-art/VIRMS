"""Read-only checks guarding the released one-Company identity migration."""

LEGACY_ONE_COMPANY_MIGRATION = "0007_one_company_account"
TABLE_CREATING_MIGRATIONS = {
    "accounts_roleassignment": ("accounts", "0001_initial"),
    "accounts_companyrolegrant": ("accounts", "0004_platform_scope"),
    "tenants_tenantmembership": ("tenants", "0001_initial"),
}


def find_ambiguous_platform_user_ids(connection):
    """Return candidate Platform UUIDs with missing or conflicting evidence."""
    tables = set(connection.introspection.table_names())
    if "accounts_user" not in tables:
        return []

    with connection.cursor() as cursor:
        applied = set()
        if "django_migrations" in tables:
            cursor.execute("SELECT app, name FROM django_migrations")
            applied = set(cursor.fetchall())

    missing_after_creation = {
        table
        for table, creating_migration in TABLE_CREATING_MIGRATIONS.items()
        if table not in tables and creating_migration in applied
    }
    if missing_after_creation:
        raise RuntimeError(
            "Cannot preflight legacy account identities; applied migrations "
            "should have created missing tables: "
            + ", ".join(sorted(missing_after_creation))
        )
    if (
        "accounts_companyrolegrant" in tables
        and "tenants_tenantmembership" not in tables
    ):
        raise RuntimeError(
            "Cannot preflight legacy account identities; Company role grants "
            "exist without tenant memberships"
        )

    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, "accounts_user"
            )
        }
        if "account_kind" in columns:
            predicate = "u.account_kind = %s"
            params = ["platform"]
        elif "is_superuser" in columns:
            predicate = "u.is_superuser IS TRUE"
            params = []
        else:
            raise RuntimeError(
                "Cannot preflight legacy account identities; accounts_user has "
                "neither account_kind nor is_superuser"
            )

        history_checks = []
        back_office_check = "FALSE"
        if "accounts_roleassignment" in tables:
            history_checks.append(
                "EXISTS (SELECT 1 FROM accounts_roleassignment r "
                "WHERE r.user_id=u.id AND r.role<>'back_office')"
            )
            back_office_check = (
                "EXISTS (SELECT 1 FROM accounts_roleassignment r "
                "WHERE r.user_id=u.id AND r.role='back_office')"
            )
        if "accounts_companyrolegrant" in tables:
            history_checks.append(
                "EXISTS (SELECT 1 FROM accounts_companyrolegrant g "
                "JOIN tenants_tenantmembership m ON m.id=g.membership_id "
                "WHERE m.user_id=u.id)"
            )
        history_checks.append(f"NOT ({back_office_check})")

        cursor.execute(
            """SELECT u.id FROM accounts_user u WHERE """
            + predicate
            + " AND ("
            + " OR ".join(history_checks)
            + ") ORDER BY u.id",
            params,
        )
        return [str(row[0]) for row in cursor.fetchall()]
