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

from consents.permissions import HasValidConsent
from .models import Account
from .serializers import AccountSerializer, BalanceSerializer

PAGE_SIZE = 25


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
    """
    GET /open-banking/accounts/v1/accounts
    Lista as contas bancárias do usuário autenticado vinculadas ao consentimento.
    """
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_READ"

    def get(self, request):
        queryset = Account.objects.filter(user=request.user).order_by("-created_at")
        return _paginated_response(request, queryset, AccountSerializer)


class AccountDetailView(APIView):
    """
    GET /open-banking/accounts/v1/accounts/{accountId}
    Detalhes de uma conta bancária específica.
    """
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_READ"

    def get(self, request, account_id):
        account = get_object_or_404(Account, account_id=account_id, user=request.user)
        return Response(_data_envelope(AccountSerializer(account).data))


class AccountBalanceView(APIView):
    """
    GET /open-banking/accounts/v1/accounts/{accountId}/balances
    Consulta de saldos (disponível, bloqueado, aplicado) de uma conta específica.
    """
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_BALANCES_READ"

    def get(self, request, account_id):
        account = get_object_or_404(Account, account_id=account_id, user=request.user)
        balance = getattr(account, 'balance', None)
        if not balance:
            return Response(
                {"errors": [{"code": "BALANCE_NOT_FOUND", "title": "Saldo não encontrado", "detail": "A conta informada não possui registro de saldo ativo."}]},
                status=404,
            )
        return Response(_data_envelope(BalanceSerializer(balance).data))
