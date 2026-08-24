# pyrefly: ignore [missing-import]
from rest_framework.decorators import api_view, permission_classes
# pyrefly: ignore [missing-import]
from rest_framework.permissions import AllowAny
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint simples para verificar a integridade da aplicação.
    Retorna 200 OK com status da aplicação.
    """
    return Response({"status": "ok"}, status=status.HTTP_200_OK)
