"""
Views do app accounts — API REST protegida por consentimento seguindo o padrão Open Finance Brasil.

Estrutura de endpoints:
  GET /open-banking/accounts/v1/accounts                        → lista contas do usuário
  GET /open-banking/accounts/v1/accounts/{accountId}            → detalha conta
  GET /open-banking/accounts/v1/accounts/{accountId}/balances   → consulta saldo da conta
"""
import math
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes

from core.serializers import OpenFinanceErrorResponseSerializer
from consents.permissions import HasValidConsent
from .models import Account
from .serializers import (
    AccountSerializer,
    BalanceSerializer,
    AccountResponseEnvelopeSerializer,
    AccountListEnvelopeSerializer,
    BalanceResponseEnvelopeSerializer,
)

PAGE_SIZE = 25

# Parâmetro global de cabeçalho Open Finance
CONSENT_HEADER_PARAM = OpenApiParameter(
    name="X-Consent-Id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.HEADER,
    required=True,
    description="UUID do consentimento ativo, autorizado e válido para o usuário autenticado."
)


def _data_envelope(serializer_data):
    """Envolve um item único no envelope { 'data': {...} }."""
    return {"data": serializer_data}


def _paginated_response(request, queryset, serializer_class):
    """Paginação manual seguindo o padrão do Open Finance Brasil."""
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
    serialized = serializer_class(items, many=True).data

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


class AccountListView(APIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_READ"

    @extend_schema(
        summary="Listar contas bancárias",
        description="Retorna a lista paginada das contas bancárias do usuário autenticado vinculadas ao consentimento informado. Exige escopo `ACCOUNTS_READ`.",
        parameters=[
            CONSENT_HEADER_PARAM,
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Número da página", default=1),
            OpenApiParameter("page-size", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Quantidade de registros por página", default=PAGE_SIZE),
        ],
        responses={
            200: AccountListEnvelopeSerializer,
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenFinanceErrorResponseSerializer,
        },
        tags=["Open Finance - Contas"]
    )
    def get(self, request):
        queryset = Account.objects.filter(user=request.user).order_by("-created_at")
        return _paginated_response(request, queryset, AccountSerializer)


class AccountDetailView(APIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_READ"

    @extend_schema(
        summary="Detalhes de uma conta bancária",
        description="Consulta informações cadastrais de uma conta específica pertencente ao usuário. Exige escopo `ACCOUNTS_READ`.",
        parameters=[
            CONSENT_HEADER_PARAM,
            OpenApiParameter("account_id", OpenApiTypes.UUID, OpenApiParameter.PATH, description="UUID da conta bancária"),
        ],
        responses={
            200: AccountResponseEnvelopeSerializer,
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenFinanceErrorResponseSerializer,
            404: OpenApiResponse(description="Conta não encontrada"),
        },
        tags=["Open Finance - Contas"]
    )
    def get(self, request, account_id):
        account = get_object_or_404(Account, account_id=account_id, user=request.user)
        return Response(_data_envelope(AccountSerializer(account).data))


class AccountBalanceView(APIView):
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_BALANCES_READ"

    @extend_schema(
        summary="Consultar saldos da conta",
        description="Consulta os saldos contábil disponível, bloqueado e aplicado de uma conta específica. Exige escopo `ACCOUNTS_BALANCES_READ`.",
        parameters=[
            CONSENT_HEADER_PARAM,
            OpenApiParameter("account_id", OpenApiTypes.UUID, OpenApiParameter.PATH, description="UUID da conta bancária"),
        ],
        responses={
            200: BalanceResponseEnvelopeSerializer,
            401: OpenApiResponse(description="Não autenticado"),
            403: OpenFinanceErrorResponseSerializer,
            404: OpenFinanceErrorResponseSerializer,
        },
        tags=["Open Finance - Contas"]
    )
    def get(self, request, account_id):
        account = get_object_or_404(Account, account_id=account_id, user=request.user)
        balance = getattr(account, 'balance', None)
        if not balance:
            return Response(
                {"errors": [{"code": "BALANCE_NOT_FOUND", "title": "Saldo não encontrado", "detail": "A conta informada não possui registro de saldo ativo."}]},
                status=404,
            )
        return Response(_data_envelope(BalanceSerializer(balance).data))

