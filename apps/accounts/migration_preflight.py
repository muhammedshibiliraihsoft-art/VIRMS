"""Block unsafe legacy identity rewrites before migration 0007 runs."""

from django.core.management.base import CommandError
from django.db import connections
from django.db.models.signals import pre_migrate
from django.dispatch import receiver

from .identity_cutover import (
    LEGACY_ONE_COMPANY_MIGRATION,
    find_ambiguous_platform_user_ids,
)


@receiver(pre_migrate, dispatch_uid="accounts.legacy_identity_preflight")
def preflight_legacy_identity_migration(sender, *, plan, using, **kwargs):
    if getattr(sender, "label", None) != "accounts":
        return
    if not any(
        migration.app_label == "accounts"
        and migration.name == LEGACY_ONE_COMPANY_MIGRATION
        for migration, backwards in plan
        if not backwards
    ):
        return

    connection = connections[using]
    ambiguous = find_ambiguous_platform_user_ids(connection)
    if ambiguous:
        raise CommandError(
            "One-Company identity migration preflight failed. Reviewed "
            "identity treatment is required for User UUIDs: " + ", ".join(ambiguous)
        )
