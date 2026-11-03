from rest_framework import serializers

from apps.tenants.models import CompanyModuleCode, CompanyModuleState


class CompanyModuleStateRowSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=CompanyModuleCode.choices)
    state = serializers.ChoiceField(
        choices=(
            ("unconfigured", "Unconfigured"),
            *CompanyModuleState.State.choices,
        )
    )
    version = serializers.IntegerField(allow_null=True)
    effective_from = serializers.DateTimeField(allow_null=True)


class CompanyModuleStatesSerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
    modules = CompanyModuleStateRowSerializer(many=True)
