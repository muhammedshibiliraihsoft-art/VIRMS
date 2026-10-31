from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from apps.tenants.models import Branch, Tenant
from apps.tenants.selectors import visible_branches, visible_companies
from apps.tenants.serializers import BranchSummarySerializer, TenantSummarySerializer


class TenantScopeMixin:
    serializer_class = TenantSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_companies(self.request.user)


class TenantList(TenantScopeMixin, ListAPIView):
    pass


class TenantDetail(TenantScopeMixin, RetrieveAPIView):
    pass


class CompanyBranchScopeMixin:
    serializer_class = BranchSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_branches(self.request.user, self.kwargs["company_id"]).only(
            "id", "tenant_id", "name"
        )


class CompanyBranchList(CompanyBranchScopeMixin, ListAPIView):
    pass


class CompanyBranchDetail(CompanyBranchScopeMixin, RetrieveAPIView):
    queryset = Branch.objects.none()
