from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.models import CompanyModuleCode, CompanyModuleState
from apps.tenants.selectors import visible_companies
from apps.tenants.serializers.module_state import CompanyModuleStatesSerializer


class CompanyModuleStatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        if request.query_params:
            raise ValidationError("Query parameters are not supported.")

        company = visible_companies(request.user).filter(pk=company_id).only("pk").first()
        if company is None:
            raise Http404

        latest_revisions = (
            CompanyModuleState.objects.filter(tenant_id=company.pk)
            .order_by("module_code", "-version")
            .distinct("module_code")
            .values("module_code", "state", "version", "effective_from")
        )
        latest_by_code = {
            revision["module_code"]: revision for revision in latest_revisions
        }
        modules = []
        for code in CompanyModuleCode.values:
            revision = latest_by_code.get(code)
            modules.append(
                {
                    "code": code,
                    "state": revision["state"] if revision else "unconfigured",
                    "version": revision["version"] if revision else None,
                    "effective_from": revision["effective_from"] if revision else None,
                }
            )

        serializer = CompanyModuleStatesSerializer(
            instance={"company_id": company.pk, "modules": modules}
        )
        response = Response(serializer.data)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Pragma"] = "no-cache"
        response["Vary"] = "Cookie"
        return response
