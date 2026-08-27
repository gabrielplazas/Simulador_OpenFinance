"""
Permission classes para o ecossistema Open Finance Brasil.

Este módulo implementa a classe de permissão `HasValidConsent`, responsável por
vincular o acesso aos dados protegidos (contas, saldos, transações) a um consentimento
ativo, válido e com escopo apropriado.
"""
import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from consents.models import Consent, ConsentStatus


class OpenFinancePermissionDenied(APIException):
    """
    Exceção customizada de permissão negada (HTTP 403) formatada rigorosamente
    de acordo com o envelope de erros padronizado do Open Finance Brasil.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "FORBIDDEN"

    def __init__(self, code: str, title: str, detail: str):
        self.detail = {
            "errors": [
                {
                    "code": code,
                    "title": title,
                    "detail": detail,
                }
            ]
        }


class HasValidConsent(BasePermission):
    """
    Permission Class do DRF que garante que a requisição está autorizada por um Consentimento Open Finance.

    Regras de Validação:
    1. Header HTTP 'X-Consent-Id' (ou 'HTTP_X_CONSENT_ID') deve estar presente e ser um UUID válido.
    2. O Consentimento deve existir no banco de dados e pertencer ao usuário autenticado (`request.user`).
    3. O Consentimento deve ser válido (`consent.is_valid == True` -> status AUTHORISED e não expirado).
    4. O Consentimento deve conter o(s) escopo(s) exigido(s) pela view (`view.required_scope` ou `view.required_scopes`).

    Caso qualquer verificação falhe, levanta `OpenFinancePermissionDenied` com HTTP 403 e código específico.
    Se aprovado, injeta o objeto `consent` em `request.consent` para uso posterior na view.
    """

    def has_permission(self, request, view):
        # 1. Usuário precisa estar autenticado
        if not request.user or not request.user.is_authenticated:
            # Deixa o DRF tratar a autenticação básica / 401 via IsAuthenticated
            return False

        # 2. Obter o identificador do consentimento via Header HTTP
        raw_consent_id = request.headers.get("X-Consent-Id") or request.META.get("HTTP_X_CONSENT_ID")

        if not raw_consent_id:
            raise OpenFinancePermissionDenied(
                code="MISSING_CONSENT_HEADER",
                title="Cabeçalho obrigatório ausente",
                detail="O cabeçalho 'X-Consent-Id' é obrigatório para acessar este recurso.",
            )

        # Validação do formato UUID
        try:
            consent_uuid = uuid.UUID(str(raw_consent_id).strip())
        except (ValueError, TypeError):
            raise OpenFinancePermissionDenied(
                code="INVALID_CONSENT_ID_FORMAT",
                title="ID de consentimento com formato inválido",
                detail=f"'{raw_consent_id}' não é um UUID válido.",
            )

        # 3. Buscar consentimento pertencente ao usuário autenticado
        try:
            consent = Consent.objects.get(consent_id=consent_uuid, user=request.user)
        except Consent.DoesNotExist:
            raise OpenFinancePermissionDenied(
                code="CONSENT_NOT_FOUND",
                title="Consentimento não encontrado",
                detail="Consentimento informado não foi encontrado ou não pertence ao usuário autenticado.",
            )

        # 4. Verificar validade do consentimento (is_valid: status AUTHORISED + dentro do prazo)
        if not consent.is_valid:
            if consent.status == ConsentStatus.REVOKED:
                raise OpenFinancePermissionDenied(
                    code="CONSENT_REVOKED",
                    title="Consentimento revogado",
                    detail="O consentimento informado foi revogado pelo usuário.",
                )
            elif consent.status == ConsentStatus.REJECTED:
                raise OpenFinancePermissionDenied(
                    code="CONSENT_REJECTED",
                    title="Consentimento rejeitado",
                    detail="O consentimento informado foi rejeitado ou cancelado.",
                )
            elif consent.status == ConsentStatus.AWAITING_AUTHORISATION:
                raise OpenFinancePermissionDenied(
                    code="CONSENT_AWAITING_AUTHORISATION",
                    title="Consentimento aguardando autorização",
                    detail="O consentimento informado ainda não foi autorizado pelo usuário.",
                )
            elif consent.expiration_date_time <= timezone.now():
                raise OpenFinancePermissionDenied(
                    code="CONSENT_EXPIRED",
                    title="Consentimento expirado",
                    detail="A data de validade do consentimento expirou.",
                )
            else:
                raise OpenFinancePermissionDenied(
                    code="CONSENT_INVALID",
                    title="Consentimento inválido",
                    detail=f"O consentimento está com status '{consent.status}' e não pode ser utilizado.",
                )

        # 5. Verificar escopos necessários para a View
        # Suporta tanto `required_scope` (string única) quanto `required_scopes` (lista/conjunto de strings)
        required_scope = getattr(view, "required_scope", None)
        required_scopes = getattr(view, "required_scopes", None)

        scopes_to_check = set()
        if required_scope:
            scopes_to_check.add(required_scope)
        if required_scopes:
            scopes_to_check.update(required_scopes)

        consent_permissions = set(consent.permissions or [])

        # Se a view exige escopos e o consentimento não possui todos eles:
        if scopes_to_check and not scopes_to_check.issubset(consent_permissions):
            missing_scopes = sorted(list(scopes_to_check - consent_permissions))
            raise OpenFinancePermissionDenied(
                code="INSUFFICIENT_PERMISSIONS",
                title="Permissão insuficiente no consentimento",
                detail=(
                    f"O consentimento informado não possui o(s) escopo(s) necessário(s): {missing_scopes}. "
                    f"Escopos autorizados no consentimento: {sorted(list(consent_permissions))}."
                ),
            )

        # Injeta o consentimento no request para conveniência e auditoria
        request.consent = consent
        return True
