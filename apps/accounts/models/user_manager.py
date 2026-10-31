from django.contrib.auth.models import BaseUserManager

from apps.accounts.login_id import canonical_login_id


class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra_fields):
        if extra_fields.get("email"):
            extra_fields["email"] = self.normalize_email(extra_fields["email"])
        user = self.model(login_id=login_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        login_id = canonical_login_id(username, using=self._db, allow_empty=True)
        return self.get(login_id=login_id)

    def create_superuser(self, login_id, password=None, **extra_fields):
        extra_fields.setdefault("account_kind", "platform")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("must_change_password", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("account_kind") != "platform":
            raise ValueError("Superuser must be a platform account.")

        return self.create_user(login_id, password, **extra_fields)
