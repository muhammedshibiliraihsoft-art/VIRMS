"""Interactive reauthentication for actor-attributed offline commands."""

import getpass
import sys

from django.contrib.auth.hashers import check_password
from django.core.management.base import CommandError


def prompt_platform_password():
    """Read a password without echoing it or accepting it from command arguments."""
    if not sys.stdin.isatty():
        raise CommandError(
            "Interactive Platform operator authentication requires a TTY"
        )
    try:
        return getpass.getpass("Platform operator password: ")
    except (EOFError, KeyboardInterrupt) as error:
        raise CommandError("Platform operator authentication was cancelled") from error


def require_platform_password(password, actor):
    """Verify against the freshly locked actor hash without upgrading that hash."""
    if (
        not isinstance(password, str)
        or not password
        or not check_password(password, actor.password)
    ):
        raise CommandError("Platform Back Office authentication failed")
