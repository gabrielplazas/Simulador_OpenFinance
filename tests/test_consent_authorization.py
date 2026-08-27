"""
Testes automatizados do fluxo de autorização e consentimento do Open Finance Brasil.

Cenários cobertos:
1. Fluxo de ciclo de vida completo:
   - Criação do consentimento (AWAITING_AUTHORISATION)
   - Bloqueio de acesso a dados protegidos enquanto pendente (403)
   - Autorização do consentimento (AUTHORISED via PATCH)
   - Acesso com sucesso aos dados autorizados (200 OK)
   - Bloqueio por escopo insuficiente (403 INSUFFICIENT_PERMISSIONS)
   - Revogação do consentimento (DELETE)
   - Bloqueio de novo acesso após revogação (403 CONSENT_REVOKED)
2. Casos de borda:
   - Header X-Consent-Id ausente (403 MISSING_CONSENT_HEADER)
   - Header X-Consent-Id com UUID inválido (403 INVALID_CONSENT_ID_FORMAT)
   - Consentimento inexistente ou de outro usuário (403 CONSENT_NOT_FOUND)
   - Consentimento expirado (403 CONSENT_EXPIRED)
"""
import uuid
from datetime import timedelta
from decimal import Decimal

# pyrefly: ignore [missing-import]
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
# pyrefly: ignore [missing-import]
from rest_framework import status
# pyrefly: ignore [missing-import]
from rest_framework.test import APIClient
# pyrefly: ignore [missing-import]
from accounts.models import Account, AccountSubtype, AccountType, Balance
# pyrefly: ignore [missing-import]
from consents.models import Consent, ConsentStatus
# pyrefly: ignore [missing-import]
from transactions.models import CreditDebitType, Transaction, TransactionStatus, TransactionType


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    user = User.objects.create_user(
        username="ana.silva",
        email="ana@email.com",
        password="Senha@123",
    )
    return user


@pytest.fixture
def user_b(db):
    user = User.objects.create_user(
        username="carlos.souza",
        email="carlos@email.com",
        password="Senha@123",
    )
    return user


@pytest.fixture
def account_a(user_a):
    account = Account.objects.create(
        user=user_a,
        brand_name="Banco Itaú S.A.",
        company_cnpj="60701190000104",
        type=AccountType.CONTA_DEPOSITO_A_VISTA,
        subtype=AccountSubtype.INDIVIDUAL,
        number="12345",
        branch_code="0001",
        check_digit="8",
        currency="BRL",
    )
    Balance.objects.create(
        account=account,
        available_amount=Decimal("1500.50"),
        blocked_amount=Decimal("0.00"),
        automatically_invested_amount=Decimal("500.00"),
        currency="BRL",
    )
    Transaction.objects.create(
        account=account,
        amount=Decimal("250.00"),
        currency="BRL",
        credit_debit_type=CreditDebitType.DEBITO,
        transaction_status=TransactionStatus.LANCADO,
        transaction_date=timezone.now().date(),
        transaction_date_time=timezone.now(),
        transaction_type=TransactionType.PIX,
        description="Transferência PIX",
    )
    return account


@pytest.mark.django_db
class TestConsentLifecycleAndAuthorizationFlow:
    """
    Testa o fluxo ponta a ponta: Criação -> Autorização -> Acesso -> Revogação -> Bloqueio.
    """

    def test_full_consent_lifecycle_and_data_access(self, api_client, user_a, account_a):
        # 1. Autentica o usuário A
        api_client.force_authenticate(user=user_a)

        # 2. Criação do consentimento com escopos de Contas e Saldos (sem Transações)
        create_payload = {
            "permissions": ["ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ"],
            "expirationDays": 90,
        }
        create_response = api_client.post(
            "/open-banking/consents/v1/consents/",
            data=create_payload,
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        consent_data = create_response.json()["data"]
        consent_id = consent_data["consentId"]
        assert consent_data["status"] == "AWAITING_AUTHORISATION"

        # 3. Tentar acessar /accounts/ com o consentimento ainda PENDENTE (deve falhar com 403)
        headers = {"HTTP_X_CONSENT_ID": consent_id}
        accounts_response_pending = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            **headers,
        )
        assert accounts_response_pending.status_code == status.HTTP_403_FORBIDDEN
        assert accounts_response_pending.json()["errors"][0]["code"] == "CONSENT_AWAITING_AUTHORISATION"

        # 4. Autorizar o consentimento (PATCH)
        patch_response = api_client.patch(
            f"/open-banking/consents/v1/consents/{consent_id}/",
            data={"status": "AUTHORISED"},
            format="json",
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.json()["data"]["status"] == "AUTHORISED"

        # 5. Acessar /accounts/ com sucesso (200 OK)
        accounts_response_ok = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            **headers,
        )
        assert accounts_response_ok.status_code == status.HTTP_200_OK
        accounts_list = accounts_response_ok.json()["data"]
        assert len(accounts_list) == 1
        assert accounts_list[0]["accountId"] == str(account_a.account_id)
        assert accounts_list[0]["brandName"] == "Banco Itaú S.A."

        # 6. Acessar /accounts/{id}/balances/ com sucesso (200 OK)
        balance_response_ok = api_client.get(
            f"/open-banking/accounts/v1/accounts/{account_a.account_id}/balances/",
            **headers,
        )
        assert balance_response_ok.status_code == status.HTTP_200_OK
        balance_data = balance_response_ok.json()["data"]
        assert balance_data["availableAmount"] == "1500.50"
        assert balance_data["currency"] == "BRL"

        # 7. Tentar acessar /accounts/{id}/transactions/ -> Deve falhar com 403 (INSUFFICIENT_PERMISSIONS)
        # pois o consentimento só possui ACCOUNTS_READ e ACCOUNTS_BALANCES_READ
        transactions_response_forbidden = api_client.get(
            f"/open-banking/accounts/v1/accounts/{account_a.account_id}/transactions/",
            **headers,
        )
        assert transactions_response_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert transactions_response_forbidden.json()["errors"][0]["code"] == "INSUFFICIENT_PERMISSIONS"

        # 8. Revogar o consentimento (DELETE)
        delete_response = api_client.delete(
            f"/open-banking/consents/v1/consents/{consent_id}/",
        )
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # 9. Tentar acessar /accounts/ novamente após revogação -> Deve falhar com 403 (CONSENT_REVOKED)
        accounts_response_revoked = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            **headers,
        )
        assert accounts_response_revoked.status_code == status.HTTP_403_FORBIDDEN
        assert accounts_response_revoked.json()["errors"][0]["code"] == "CONSENT_REVOKED"


@pytest.mark.django_db
class TestConsentPermissionBoundaryCases:
    """
    Testa casos de erro e validações de cabeçalho na classe HasValidConsent.
    """

    def test_missing_x_consent_id_header(self, api_client, user_a, account_a):
        api_client.force_authenticate(user=user_a)
        response = api_client.get("/open-banking/accounts/v1/accounts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["code"] == "MISSING_CONSENT_HEADER"

    def test_invalid_uuid_format_in_header(self, api_client, user_a, account_a):
        api_client.force_authenticate(user=user_a)
        response = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            HTTP_X_CONSENT_ID="nao-e-um-uuid",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["code"] == "INVALID_CONSENT_ID_FORMAT"

    def test_consent_not_found_or_different_user(self, api_client, user_a, user_b, account_a):
        # Consentimento criado para user_b
        consent_user_b = Consent.objects.create(
            user=user_b,
            status=ConsentStatus.AUTHORISED,
            permissions=["ACCOUNTS_READ"],
            expiration_date_time=timezone.now() + timedelta(days=30),
        )

        # Usuário A tenta usar o consentimento do Usuário B
        api_client.force_authenticate(user=user_a)
        response = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            HTTP_X_CONSENT_ID=str(consent_user_b.consent_id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["code"] == "CONSENT_NOT_FOUND"

    def test_expired_consent(self, api_client, user_a, account_a):
        # Consentimento expirado ontem
        expired_consent = Consent.objects.create(
            user=user_a,
            status=ConsentStatus.AUTHORISED,
            permissions=["ACCOUNTS_READ"],
            expiration_date_time=timezone.now() - timedelta(days=1),
        )
        api_client.force_authenticate(user=user_a)
        response = api_client.get(
            "/open-banking/accounts/v1/accounts/",
            HTTP_X_CONSENT_ID=str(expired_consent.consent_id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["errors"][0]["code"] == "CONSENT_EXPIRED"
