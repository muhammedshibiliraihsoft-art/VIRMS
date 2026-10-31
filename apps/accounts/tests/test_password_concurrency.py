import threading

from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, transaction
from django.test import RequestFactory, TransactionTestCase

from apps.accounts.models import User
from apps.accounts.passwords import change_private_password


class PasswordConcurrencyTests(TransactionTestCase):
    def test_reset_wins_before_stale_change(self):
        old = "old synthetic long private passphrase"
        user = User.objects.create_user(
            login_id="race", email="race@example.invalid", password=old
        )
        self.client.force_login(user)
        request = RequestFactory().post("/")
        request.user = user
        request.session = self.client.session
        started, result = threading.Event(), []

        def change():
            close_old_connections()
            started.set()
            try:
                change_private_password(
                    request,
                    current_password=old,
                    new_password="new synthetic long private passphrase",
                    confirmation="new synthetic long private passphrase",
                )
                result.append("unsafe success")
            except PermissionDenied:
                result.append("denied")
            except Exception as error:
                result.append(type(error).__name__)
            finally:
                close_old_connections()

        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            thread = threading.Thread(target=change)
            thread.start()
            self.assertTrue(started.wait(5))
            current.set_password("reset synthetic long temporary credential")
            current.save(update_fields=["password"])
        thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result, ["denied"])
        current.refresh_from_db()
        self.assertTrue(
            current.check_password("reset synthetic long temporary credential")
        )
