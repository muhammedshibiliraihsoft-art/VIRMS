"""Canonical Login ID handling delegated to PostgreSQL's Unicode 15.0 mapping."""

from django.core.exceptions import ValidationError
from django.db import DEFAULT_DB_ALIAS, connections

MAX_LOGIN_ID_LENGTH = 150


def canonical_login_id(value, *, using=None, allow_empty=False):
    if not isinstance(value, str) or "\x00" in value:
        raise ValidationError("A valid Login ID is required.")
    database = connections[using or DEFAULT_DB_ALIAS]
    if database.vendor != "postgresql":
        raise RuntimeError("Login ID canonicalization requires PostgreSQL")
    try:
        with database.cursor() as cursor:
            cursor.execute("SELECT virms_canonical_login_id(%s)", [value])
            canonical = cursor.fetchone()[0]
    except UnicodeError as error:
        raise ValidationError("A valid Login ID is required.") from error
    if not canonical:
        if allow_empty:
            return ""
        raise ValidationError("A Login ID cannot be blank.")
    if len(canonical) > MAX_LOGIN_ID_LENGTH:
        raise ValidationError(
            f"Login ID must be at most {MAX_LOGIN_ID_LENGTH} characters after normalization."
        )
    return canonical
