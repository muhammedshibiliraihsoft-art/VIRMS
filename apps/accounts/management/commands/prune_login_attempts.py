from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Delete one bounded batch of expired login admission buckets"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        size = options["batch_size"]
        if not 1 <= size <= 1000:
            raise CommandError("batch-size must be 1..1000")
        from apps.accounts.login_admission import prune_expired_attempts

        count = prune_expired_attempts(size)
        self.stdout.write(str(count))
