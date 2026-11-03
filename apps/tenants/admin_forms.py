from django import forms

from .admin_scope import managed_companies
from .models import CompanyModuleCode, CompanyModuleState, Tenant


class CompanyModuleStateLookupForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Tenant.objects.none())
    module_code = forms.ChoiceField(choices=CompanyModuleCode.choices)

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = managed_companies(actor).filter(
            is_active=True
        )


class CompanyModuleStateChangeForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Tenant.objects.none(), widget=forms.HiddenInput
    )
    module_code = forms.ChoiceField(
        choices=CompanyModuleCode.choices, widget=forms.HiddenInput
    )
    state = forms.ChoiceField(
        choices=(("", "Choose a state"), *CompanyModuleState.State.choices),
        required=True,
    )
    expected_version = forms.IntegerField(
        min_value=0, widget=forms.HiddenInput
    )
    reason = forms.CharField(
        max_length=500,
        strip=True,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = managed_companies(actor).filter(
            is_active=True
        )
