"""Django Admin self-service adapter for the private password lifecycle."""

from django.contrib import admin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .passwords import change_private_password


class VIRMSAdminPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy("admin:password_change_done")

    def get_context_data(self, **kwargs):
        return {
            **admin.site.each_context(self.request),
            **super().get_context_data(**kwargs),
        }

    def form_valid(self, form):
        try:
            change_private_password(
                self.request,
                current_password=form.cleaned_data["old_password"],
                new_password=form.cleaned_data["new_password1"],
                confirmation=form.cleaned_data["new_password2"],
            )
        except PermissionDenied:
            return HttpResponseForbidden("Authentication changed; sign in again")
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        # PasswordChangeView.form_valid would save the form a second time.
        return FormView.form_valid(self, form)
