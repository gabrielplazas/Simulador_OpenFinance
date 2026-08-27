"""
Views do app transactions — API REST protegida por consentimento seguindo o padrão Open Finance Brasil.

Estrutura de endpoints:
  GET /open-banking/accounts/v1/accounts/{accountId}/transactions → extrato da conta
"""
import math
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from accounts.models import Account
from consents.permissions import HasValidConsent
from .models import Transaction
from .serializers import TransactionSerializer

PAGE_SIZE = 25


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


class TransactionListView(APIView):
    serializer_class = TransactionSerializer
    """
    GET /open-banking/accounts/v1/accounts/{accountId}/transactions
    Consulta o extrato de transações de uma conta bancária vinculada ao consentimento.
    """
    permission_classes = [IsAuthenticated, HasValidConsent]
    required_scope = "ACCOUNTS_TRANSACTIONS_READ"

    def get(self, request, account_id):
        account = get_object_or_404(Account, account_id=account_id, user=request.user)
        queryset = Transaction.objects.filter(account=account).order_by("-transaction_date_time")

        # Filtros de data opcionais conforme padrão Open Finance (fromDate, toDate)
        from_date_param = request.query_params.get("fromDate")
        to_date_param = request.query_params.get("toDate")

        if from_date_param:
            dt_from = parse_date(from_date_param)
            if dt_from:
                queryset = queryset.filter(transaction_date__gte=dt_from)

        if to_date_param:
            dt_to = parse_date(to_date_param)
            if dt_to:
                queryset = queryset.filter(transaction_date__lte=dt_to)

        return _paginated_response(request, queryset, TransactionSerializer)
