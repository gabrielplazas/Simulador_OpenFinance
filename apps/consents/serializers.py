"""
Serializers do app consents.

Convenção de nomenclatura:
- Campos da API (saída/entrada) seguem camelCase conforme o padrão Open Finance Brasil.
- Campos do model estão em snake_case.
- A conversão é feita explicitamente via `source=` em cada campo, sem dependência de
  bibliotecas externas (djangorestframework-camel-case), mantendo o contrato visível e
  auditável diretamente no serializer.
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Consent, ConsentStatus

# ---------------------------------------------------------------------------
# Escopos válidos do Open Finance Brasil (subconjunto implementado)
# ---------------------------------------------------------------------------

VALID_PERMISSIONS = {
    "ACCOUNTS_READ",
    "ACCOUNTS_BALANCES_READ",
    "ACCOUNTS_TRANSACTIONS_READ",
    "ACCOUNTS_OVERDRAFT_LIMITS_READ",
    "CUSTOMERS_PERSONAL_IDENTIFICATIONS_READ",
    "CUSTOMERS_PERSONAL_ADITTIONAL_INFO_READ",
    "CUSTOMERS_BUSINESS_IDENTIFICATIONS_READ",
    "CUSTOMERS_BUSINESS_ADITTIONAL_INFO_READ",
}

DEFAULT_EXPIRATION_DAYS = 90


# ---------------------------------------------------------------------------
# Serializer de leitura — resposta de consulta (GET)
# ---------------------------------------------------------------------------

class ConsentSerializer(serializers.ModelSerializer):
    """
    Serializer somente-leitura para respostas de consulta de consentimento.
    Todos os campos são expostos em camelCase, conforme contrato Open Finance Brasil.

    Exemplo de resposta:
    {
        "consentId": "urn:banco:consent:abc123",
        "status": "AWAITING_AUTHORISATION",
        "permissions": ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"],
        "creationDateTime": "2024-01-15T10:30:00Z",
        "expirationDateTime": "2024-04-15T10:30:00Z",
        "statusUpdateDateTime": "2024-01-15T10:30:00Z"
    }
    """
    # Campos camelCase mapeados para os campos snake_case do model
    consentId = serializers.UUIDField(source='consent_id', read_only=True)
    status = serializers.CharField(read_only=True)
    permissions = serializers.JSONField(read_only=True)
    creationDateTime = serializers.DateTimeField(
        source='creation_date_time',
        read_only=True,
    )
    expirationDateTime = serializers.DateTimeField(
        source='expiration_date_time',
        read_only=True,
    )
    statusUpdateDateTime = serializers.DateTimeField(
        source='status_update_date_time',
        read_only=True,
    )

    class Meta:
        model = Consent
        fields = [
            'consentId',
            'status',
            'permissions',
            'creationDateTime',
            'expirationDateTime',
            'statusUpdateDateTime',
        ]


# ---------------------------------------------------------------------------
# Serializer de criação — entrada de dados (POST)
# ---------------------------------------------------------------------------

class ConsentCreateSerializer(serializers.Serializer):
    """
    Serializer de criação de consentimento.

    Aceita:
    - permissions (obrigatório): lista não vazia de escopos válidos.
    - expirationDays (opcional): número de dias de validade. Default: 90 dias.

    O campo `user` é preenchido automaticamente via `save(user=request.user)` na view —
    nunca deve ser recebido pelo payload.

    Exemplo de payload:
    {
        "permissions": ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"],
        "expirationDays": 180
    }
    """
    permissions = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        help_text=(
            f"Lista de escopos de acesso solicitados. "
            f"Valores válidos: {', '.join(sorted(VALID_PERMISSIONS))}"
        ),
    )
    expirationDays = serializers.IntegerField(
        required=False,
        default=DEFAULT_EXPIRATION_DAYS,
        min_value=1,
        max_value=365,
        help_text=f"Validade do consentimento em dias (padrão: {DEFAULT_EXPIRATION_DAYS}).",
    )

    def validate_permissions(self, value):
        """
        Garante que todos os escopos informados pertencem ao conjunto de
        permissões válidas definidas pela constante VALID_PERMISSIONS.
        """
        invalid = set(value) - VALID_PERMISSIONS
        if invalid:
            raise serializers.ValidationError(
                f"Permissões inválidas: {sorted(invalid)}. "
                f"Valores aceitos: {sorted(VALID_PERMISSIONS)}"
            )
        # Remove duplicatas preservando ordem
        seen = set()
        return [p for p in value if not (p in seen or seen.add(p))]

    def create(self, validated_data):
        """
        Cria o consentimento calculando expiration_date_time automaticamente.
        O `user` deve ser passado via `save(user=request.user)` na view.
        """
        expiration_days = validated_data.pop('expirationDays', DEFAULT_EXPIRATION_DAYS)
        user = validated_data.pop('user')

        consent = Consent.objects.create(
            user=user,
            permissions=validated_data['permissions'],
            expiration_date_time=timezone.now() + timedelta(days=expiration_days),
            status=ConsentStatus.AWAITING_AUTHORISATION,
        )
        return consent


# ---------------------------------------------------------------------------
# Serializer de atualização de status (PATCH)
# ---------------------------------------------------------------------------

class ConsentStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer de alteração de status do consentimento.
    """
    status = serializers.ChoiceField(
        choices=[
            (ConsentStatus.AUTHORISED, 'Autorizar consentimento'),
            (ConsentStatus.REJECTED, 'Rejeitar consentimento'),
        ],
        help_text="Novo status a ser aplicado (AUTHORISED ou REJECTED)."
    )


# ---------------------------------------------------------------------------
# Envelopes de Resposta Open Finance (Documentação OpenAPI / Swagger)
# ---------------------------------------------------------------------------

class ConsentResponseEnvelopeSerializer(serializers.Serializer):
    """Envelope de resposta para item único de consentimento."""
    data = ConsentSerializer()


class ConsentListEnvelopeSerializer(serializers.Serializer):
    """Envelope de resposta para lista paginada de consentimentos."""
    from core.serializers import PaginationLinksSerializer, PaginationMetaSerializer
    data = ConsentSerializer(many=True)
    links = PaginationLinksSerializer()
    meta = PaginationMetaSerializer()

