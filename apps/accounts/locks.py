"""Stable parent locks shared by scope and credential mutations."""

from contextlib import contextmanager

from django.db import transaction

from .models import User


@contextmanager
def locked_users(*user_ids):
    with transaction.atomic():
        users = {
            u.pk: u
            for u in User.objects.select_for_update()
            .filter(pk__in=set(user_ids))
            .order_by("id")
        }
        if len(users) != len(set(user_ids)):
            raise User.DoesNotExist
        yield users
