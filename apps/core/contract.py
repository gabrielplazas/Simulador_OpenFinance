from datetime import timezone
from uuid import UUID, uuid4

from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


def utc(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ContractView(APIView):
    """Require and echo a correlation ID on the versioned demonstration APIs."""
    def initial(self, request, *args, **kwargs):
        value = request.headers.get("x-fapi-interaction-id", "")
        try:
            parsed = UUID(value)
            if str(parsed) != value.lower():
                raise ValueError
        except ValueError:
            self.interaction_id = str(uuid4())
            raise serializers.ValidationError("Informe um UUID em x-fapi-interaction-id.")
        self.interaction_id = value
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["x-fapi-interaction-id"] = self.interaction_id
        return response


interaction = OpenApiParameter("x-fapi-interaction-id", str, OpenApiParameter.HEADER,
                               required=True, default="9b88d760-8661-4aef-9004-78bde76f5ba8",
                               description="UUID de correlação. Gere um por requisição.")
consent_header = OpenApiParameter("X-Consent-Id", str, OpenApiParameter.HEADER,
                                  required=True, description="URN devolvida na criação do consentimento.")


def single(request, data, status=200):
    return Response({"data": data, "links": {"self": request.build_absolute_uri()},
                     "meta": {"totalRecords": 1, "totalPages": 1}}, status=status)
