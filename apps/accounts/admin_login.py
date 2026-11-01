from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm

from .login_admission import login_attempt


class VIRMSAdminAuthenticationForm(AdminAuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._credentials_authenticated = False

    def confirm_login_allowed(self, user):
        # Django calls this after credentials authenticate but before applying
        # the Admin-only staff check. A non-staff denial is not a bad password.
        self._credentials_authenticated = True
        return super().confirm_login_allowed(user)

    def clean(self):
        username = self.cleaned_data.get("username")
        if not username:
            return super().clean()
        with login_attempt(self.request, username) as outcome:
            if not outcome.allowed:
                raise forms.ValidationError(
                    "Please try again later.", code="invalid_login"
                )
            try:
                result = super().clean()
            except forms.ValidationError as error:
                outcome.authenticated = self._credentials_authenticated
                failure = error
            else:
                outcome.authenticated = (
                    self._credentials_authenticated or self.get_user() is not None
                )
                failure = None
        if failure is not None:
            raise failure
        return result
