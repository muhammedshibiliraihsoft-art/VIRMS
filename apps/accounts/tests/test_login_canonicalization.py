import json

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User


class LoginIDCanonicalizationTests(TestCase):
    def create_user(self, login_id, *, suffix):
        return User.objects.create_user(
            login_id=login_id,
            email=f"{suffix}@example.invalid",
            password="A-Long-Private-Test-Passphrase-123!",
            must_change_password=False,
        )

    def test_manager_uses_trimmed_unicode_lowercase_and_rejects_empty_ids(self):
        cases = (
            ("\tAcme\t", "acme"),
            ("\u2003North\u2003", "north"),
            ("ΟΣ", "ος"),
            ("İ", "i\u0307"),
        )
        for index, (provided, canonical) in enumerate(cases):
            with self.subTest(provided=provided):
                user = self.create_user(provided, suffix=f"unicode-{index}")
                self.assertEqual(user.login_id, canonical)
                user.refresh_from_db()
                self.assertEqual(user.login_id, canonical)

        with self.assertRaises(ValidationError):
            self.create_user("\t\u2003\n", suffix="blank")

    def test_database_write_path_canonicalizes_and_unique_index_blocks_collisions(self):
        user = self.create_user("first", suffix="first")
        User.objects.filter(pk=user.pk).update(login_id="\tAcme\t")
        user.refresh_from_db()
        self.assertEqual(user.login_id, "acme")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_user(" \u2003ACME\u2003 ", suffix="duplicate")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.filter(pk=user.pk).update(login_id=" \u2003 ")
        user.refresh_from_db()
        self.assertEqual(user.login_id, "acme")

    def test_login_and_throttle_share_the_canonical_identifier(self):
        user = self.create_user("North", suffix="north")
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("auth-csrf"))
        response = client.post(
            reverse("auth-login"),
            data=json.dumps(
                {
                    "login_id": "\u2003NORTH\t",
                    "password": "A-Long-Private-Test-Passphrase-123!",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get(reverse("auth-me")).status_code, 200)
        self.assertEqual(user.login_id, "north")

    def test_postgres_function_matches_every_python_lower_mapping_and_strip_character(
        self,
    ):
        self.assertEqual(connection.vendor, "postgresql")
        mapping_source = "".join(
            chr(codepoint)
            for codepoint in range(0x110000)
            if not 0xD800 <= codepoint <= 0xDFFF
            and chr(codepoint).lower() != chr(codepoint)
        )
        expected_lower = mapping_source.lower()
        whitespace = "".join(
            chr(codepoint) for codepoint in range(0x110000) if chr(codepoint).isspace()
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT virms_canonical_login_id(%s), virms_canonical_login_id(%s)",
                [mapping_source, whitespace + "North" + whitespace],
            )
            actual_lower, actual_stripped = cursor.fetchone()
        self.assertEqual(actual_lower, expected_lower)
        self.assertEqual(actual_stripped, "north")
