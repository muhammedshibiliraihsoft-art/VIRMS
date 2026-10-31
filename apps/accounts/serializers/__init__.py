from rest_framework import serializers

from apps.accounts.models import RoleAssignment


class ProvisionSerializer(serializers.Serializer):
    login_id = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=RoleAssignment.Role.choices)
    tenant_id = serializers.UUIDField()
