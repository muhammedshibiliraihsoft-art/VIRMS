from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm

from .login_admission import admit_login, clear_identifier_budget


class VIRMSAdminAuthenticationForm(AdminAuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get("username")
        if username:
            admitted, _ = admit_login(self.request, username)
            if not admitted:
                raise forms.ValidationError(
                    "Please try again later.", code="invalid_login"
                )
        result = super().clean()
        if username and self.get_user():
            clear_identifier_budget(username)
        return result
