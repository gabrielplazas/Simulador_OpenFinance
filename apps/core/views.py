from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import HealthCheckResponseSerializer


@extend_schema(
    summary="Verificação de Saúde (Healthcheck)",
    description="Endpoint simples para verificar a disponibilidade e integridade da aplicação.",
    responses={200: HealthCheckResponseSerializer},
    tags=["Utilitários"]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint simples para verificar a integridade da aplicação.
    Retorna 200 OK com status da aplicação.
    """
    return Response({"status": "ok"}, status=status.HTTP_200_OK)

