from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import LoginAttempt


class Command(BaseCommand):
    help = "Delete one bounded batch of expired login admission buckets"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        size = options["batch_size"]
        if not 1 <= size <= 1000:
            raise CommandError("batch-size must be 1..1000")
        keys = list(
            LoginAttempt.objects.filter(retry_after__lt=timezone.now())
            .order_by("retry_after")
            .values_list("pk", flat=True)[:size]
        )
        count, _ = LoginAttempt.objects.filter(pk__in=keys).delete()
        self.stdout.write(str(count))
