"""
Serializers do app transactions.

Mapeamento de campos do modelo em snake_case para o contrato camelCase
do Open Finance Brasil.
"""
from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer de transações/extrato de conta no padrão Open Finance Brasil.
    """
    transactionId = serializers.UUIDField(source='transaction_id', read_only=True)
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        coerce_to_string=True,
    )
    currency = serializers.CharField()
    creditDebitType = serializers.CharField(source='credit_debit_type')
    transactionStatus = serializers.CharField(source='transaction_status')
    transactionDate = serializers.DateField(source='transaction_date')
    transactionDateTime = serializers.DateTimeField(source='transaction_date_time')
    transactionType = serializers.CharField(source='transaction_type')
    description = serializers.CharField()
    payeeCnpjCpf = serializers.CharField(source='payee_cnpj_cpf', allow_null=True)
    payeeName = serializers.CharField(source='payee_name', allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'transactionId',
            'amount',
            'currency',
            'creditDebitType',
            'transactionStatus',
            'transactionDate',
            'transactionDateTime',
            'transactionType',
            'description',
            'payeeCnpjCpf',
            'payeeName',
        ]
