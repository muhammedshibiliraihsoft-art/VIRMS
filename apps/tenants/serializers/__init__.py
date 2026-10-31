from rest_framework import serializers

from apps.tenants.models import Branch, Tenant


class TenantSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("id", "name", "slug", "is_active")


class BranchSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "tenant_id", "name")
