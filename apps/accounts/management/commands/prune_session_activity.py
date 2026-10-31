import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import SessionActivity


class Command(BaseCommand):
    help = "Delete one bounded batch of expired session-activity leases"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        size = options["batch_size"]
        if not 1 <= size <= 1000:
            raise CommandError("batch-size must be 1..1000")
        keys = list(
            SessionActivity.objects.filter(
                issued_at__lt=int(time.time()) - settings.VIRMS_SESSION_ABSOLUTE_SECONDS
            )
            .order_by("issued_at")
            .values_list("pk", flat=True)[:size]
        )
        count, _ = SessionActivity.objects.filter(pk__in=keys).delete()
        self.stdout.write(str(count))
