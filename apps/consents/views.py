"""
Views do app consents — API REST seguindo o padrão Open Finance Brasil.

Estrutura de endpoints:
  POST   /open-banking/consents/v1/consents               → criar consentimento
  GET    /open-banking/consents/v1/consents               → listar consentimentos do usuário
  GET    /open-banking/consents/v1/consents/{consentId}   → detalhar consentimento
  PATCH  /open-banking/consents/v1/consents/{consentId}   → autorizar ou rejeitar
  DELETE /open-banking/consents/v1/consents/{consentId}   → revogar

Decisão de design:
  Usamos duas APIViews (ConsentListCreateView + ConsentDetailView) em vez de ViewSet
  porque a URI do Open Finance é fixa e não se beneficia do roteamento automático do
  DefaultRouter. As duas views espelham exatamente os dois padrões de URL com
  responsabilidades claras.

Envelope de resposta:
  { "data": {...} }                        — resposta de item único
  { "data": [...], "links": {...}, "meta": {...} }  — resposta paginada

Formato de erro (422):
  { "errors": [{ "code": "...", "title": "...", "detail": "..." }] }
"""
import math

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .models import Consent, ConsentStatus
from .serializers import ConsentCreateSerializer, ConsentSerializer

# ---------------------------------------------------------------------------
# Constantes de transição de status permitidas via PATCH
# ---------------------------------------------------------------------------

ALLOWED_PATCH_TRANSITIONS = {
    ConsentStatus.AWAITING_AUTHORISATION: {
        ConsentStatus.AUTHORISED,
        ConsentStatus.REJECTED,
    }
}

# Tamanho de página padrão para a listagem
PAGE_SIZE = 25


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _data_envelope(serializer_data):
    """Envolve um item único no envelope { 'data': {...} }."""
    return {"data": serializer_data}


def _error_response(code: str, title: str, detail: str, http_status: int):
    """Retorna o envelope de erro padronizado do Open Finance Brasil."""
    return Response(
        {"errors": [{"code": code, "title": title, "detail": detail}]},
        status=http_status,
    )


def _paginated_response(request, queryset):
    """
    Paginação manual seguindo o contrato Open Finance:
    {
      "data": [...],
      "links": { "self": "...", "first": "...", "prev": "...", "next": "...", "last": "..." },
      "meta": { "totalRecords": N, "totalPages": N }
    }
    """
    # Parâmetros de paginação
    try:
        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(max(1, int(request.query_params.get("page-size", PAGE_SIZE))), 1000)
    except (ValueError, TypeError):
        page = 1
        page_size = PAGE_SIZE

    total_records = queryset.count()
    total_pages = max(1, math.ceil(total_records / page_size))
    page = min(page, total_pages)

    offset = (page - 1) * page_size
    items = queryset[offset: offset + page_size]
    serialized = ConsentSerializer(items, many=True).data

    # Monta URLs de navegação
    base_url = request.build_absolute_uri(request.path)

    def page_url(p):
        return f"{base_url}?page={p}&page-size={page_size}"

    links = {
        "self": page_url(page),
        "first": page_url(1),
        "prev": page_url(page - 1) if page > 1 else None,
        "next": page_url(page + 1) if page < total_pages else None,
        "last": page_url(total_pages),
    }

    return Response({
        "data": serialized,
        "links": links,
        "meta": {
            "totalRecords": total_records,
            "totalPages": total_pages,
        },
    })


# ---------------------------------------------------------------------------
# View 1: Lista + Criação
# ---------------------------------------------------------------------------

class ConsentListCreateView(APIView):
    serializer_class = ConsentSerializer
    """
    GET  /open-banking/consents/v1/consents  → lista paginada dos consentimentos do usuário
    POST /open-banking/consents/v1/consents  → cria novo consentimento
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Consent.objects
            .filter(user=request.user)
            .order_by("-creation_date_time")
        )
        return _paginated_response(request, queryset)

    def post(self, request):
        serializer = ConsentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": [
                    {"code": "VALIDATION_ERROR", "title": "Dados inválidos", "detail": str(e)}
                    for field_errors in serializer.errors.values()
                    for e in field_errors
                ]},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        consent = serializer.save(user=request.user)
        return Response(
            _data_envelope(ConsentSerializer(consent).data),
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# View 2: Detalhe + Atualização de status + Revogação
# ---------------------------------------------------------------------------

class ConsentDetailView(APIView):
    serializer_class = ConsentSerializer
    """
    GET    /open-banking/consents/v1/consents/{consentId}  → detalha consentimento
    PATCH  /open-banking/consents/v1/consents/{consentId}  → autoriza ou rejeita
    DELETE /open-banking/consents/v1/consents/{consentId}  → revoga
    """
    permission_classes = [IsAuthenticated]

    def _get_consent_or_404(self, request, consent_id):
        """
        Busca o consentimento pelo consent_id (UUID), filtrando pelo usuário autenticado.
        Retorna 404 em ambos os casos (não encontrado ou de outro usuário) para não
        revelar a existência do recurso a terceiros — princípio de segurança do Open Finance.
        """
        return get_object_or_404(Consent, consent_id=consent_id, user=request.user)

    def get(self, request, consent_id):
        consent = self._get_consent_or_404(request, consent_id)
        return Response(_data_envelope(ConsentSerializer(consent).data))

    def patch(self, request, consent_id):
        consent = self._get_consent_or_404(request, consent_id)

        new_status = request.data.get("status")

        # Valida presença do campo
        if not new_status:
            return _error_response(
                code="INVALID_PAYLOAD",
                title="Campo obrigatório ausente",
                detail="O campo 'status' é obrigatório.",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Normaliza para maiúsculas e valida se é um status conhecido
        new_status = new_status.upper()
        valid_statuses = {s.value for s in ConsentStatus}
        if new_status not in valid_statuses:
            return _error_response(
                code="INVALID_STATUS",
                title="Status inválido",
                detail=f"'{new_status}' não é um status válido. Valores aceitos: {sorted(valid_statuses)}",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Valida se a transição é permitida a partir do status atual
        current_status = consent.status
        allowed_targets = ALLOWED_PATCH_TRANSITIONS.get(current_status, set())

        if new_status not in allowed_targets:
            return _error_response(
                code="INVALID_STATUS_TRANSITION",
                title="Transição de status não permitida",
                detail=(
                    f"Não é possível alterar o status de '{current_status}' para '{new_status}'. "
                    f"Transições permitidas a partir de '{current_status}': "
                    f"{sorted(s.value for s in allowed_targets) if allowed_targets else 'nenhuma'}."
                ),
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        consent.status = new_status
        consent.save(update_fields=["status", "status_update_date_time"])
        return Response(_data_envelope(ConsentSerializer(consent).data))

    def delete(self, request, consent_id):
        consent = self._get_consent_or_404(request, consent_id)

        # Só consentimentos AUTHORISED podem ser revogados
        if consent.status != ConsentStatus.AUTHORISED:
            return _error_response(
                code="CONSENT_NOT_AUTHORISED",
                title="Consentimento não pode ser revogado",
                detail=(
                    f"Apenas consentimentos com status 'AUTHORISED' podem ser revogados. "
                    f"Status atual: '{consent.status}'."
                ),
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        consent.status = ConsentStatus.REVOKED
        consent.save(update_fields=["status", "status_update_date_time"])
        return Response(status=status.HTTP_204_NO_CONTENT)
