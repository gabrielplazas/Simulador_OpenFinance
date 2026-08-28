from rest_framework import serializers


class OpenFinanceErrorDetailSerializer(serializers.Serializer):
    """Estrutura de detalhe de erro do Open Finance Brasil."""
    code = serializers.CharField(help_text="Código padronizado do erro regulatório (ex: CONSENT_EXPIRED, INSUFFICIENT_PERMISSIONS)")
    title = serializers.CharField(help_text="Título legível do erro")
    detail = serializers.CharField(help_text="Explicação detalhada da causa do erro")


class OpenFinanceErrorResponseSerializer(serializers.Serializer):
    """Envelope padrão de erro do Open Finance Brasil."""
    errors = OpenFinanceErrorDetailSerializer(many=True)


class PaginationLinksSerializer(serializers.Serializer):
    """Estrutura padrão de links de navegação da paginação."""
    self = serializers.CharField(help_text="URL da página atual")
    first = serializers.CharField(help_text="URL da primeira página")
    prev = serializers.CharField(allow_null=True, required=False, help_text="URL da página anterior")
    next = serializers.CharField(allow_null=True, required=False, help_text="URL da próxima página")
    last = serializers.CharField(help_text="URL da última página")


class PaginationMetaSerializer(serializers.Serializer):
    """Metadados da paginação regulatória."""
    totalRecords = serializers.IntegerField(help_text="Total de registros encontrados")
    totalPages = serializers.IntegerField(help_text="Total de páginas disponíveis")


class HealthCheckResponseSerializer(serializers.Serializer):
    """Resposta de verificação de saúde da aplicação."""
    status = serializers.CharField(default="ok", help_text="Status de saúde da aplicação")

