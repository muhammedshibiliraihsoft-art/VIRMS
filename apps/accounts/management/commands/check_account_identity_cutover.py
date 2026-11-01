"""Read-only identity cutover preflight before and after account_kind exists."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from apps.accounts.identity_cutover import find_ambiguous_platform_user_ids


class Command(BaseCommand):
    help = (
        "Check legacy superuser/Platform identity evidence without changing "
        "accounts or history"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database", default="default", choices=settings.DATABASES.keys()
        )

    def handle(self, *args, **options):
        connection = connections[options["database"]]
        ambiguous = find_ambiguous_platform_user_ids(connection)

        if ambiguous:
            raise CommandError(
                "Reviewed identity treatment required for User UUIDs: "
                + ", ".join(ambiguous)
            )
        self.stdout.write(
            "Identity cutover preflight passed; no identities or history changed"
        )
