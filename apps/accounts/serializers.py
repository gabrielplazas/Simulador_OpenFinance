"""
Serializers do app accounts.

Mapeamento de campos do modelo em snake_case para o contrato camelCase
do Open Finance Brasil.
"""
from rest_framework import serializers

from .models import Account, Balance


class BalanceSerializer(serializers.ModelSerializer):
    """
    Serializer de saldo de conta bancária no padrão Open Finance Brasil.
    """
    availableAmount = serializers.DecimalField(
        source='available_amount',
        max_digits=15,
        decimal_places=2,
        coerce_to_string=True,
    )
    blockedAmount = serializers.DecimalField(
        source='blocked_amount',
        max_digits=15,
        decimal_places=2,
        coerce_to_string=True,
    )
    automaticallyInvestedAmount = serializers.DecimalField(
        source='automatically_invested_amount',
        max_digits=15,
        decimal_places=2,
        coerce_to_string=True,
    )
    currency = serializers.CharField()
    updateDateTime = serializers.DateTimeField(source='update_date_time')

    class Meta:
        model = Balance
        fields = [
            'availableAmount',
            'blockedAmount',
            'automaticallyInvestedAmount',
            'currency',
            'updateDateTime',
        ]


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer de dados de identificação da conta no padrão Open Finance Brasil.
    """
    accountId = serializers.UUIDField(source='account_id', read_only=True)
    brandName = serializers.CharField(source='brand_name')
    companyCnpj = serializers.CharField(source='company_cnpj')
    type = serializers.CharField()
    subtype = serializers.CharField()
    number = serializers.CharField()
    branchCode = serializers.CharField(source='branch_code')
    checkDigit = serializers.CharField(source='check_digit')
    currency = serializers.CharField()

    class Meta:
        model = Account
        fields = [
            'accountId',
            'brandName',
            'companyCnpj',
            'type',
            'subtype',
            'number',
            'branchCode',
            'checkDigit',
            'currency',
        ]
