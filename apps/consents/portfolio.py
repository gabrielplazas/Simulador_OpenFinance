from datetime import timedelta
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from core.contract import ContractView, interaction, single, utc
from core.serializers import PaginationLinksSerializer, PaginationMetaSerializer
from .models import Consent, ConsentStatus, ConsentExtension


class Document(serializers.Serializer):
    identification = serializers.RegexField(r"^[0-9]{11}$")
    rel = serializers.ChoiceField(["CPF"])


class LoggedUser(serializers.Serializer):
    document = Document()


class Term(serializers.Serializer):
    loggedUser = LoggedUser()
    expirationDateTime = serializers.DateTimeField(required=False)

    def validate_expirationDateTime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Informe uma data futura.")
        return value


class CreateData(Term):
    permissions = serializers.ListField(child=serializers.ChoiceField([
        "RESOURCES_READ", "ACCOUNTS_READ", "ACCOUNTS_BALANCES_READ",
        "ACCOUNTS_TRANSACTIONS_READ", "ACCOUNTS_OVERDRAFT_LIMITS_READ",
    ]))

    def validate_permissions(self, values):
        permissions = set(values)
        base = {"ACCOUNTS_READ", "RESOURCES_READ"}
        if len(permissions) != len(values) or not base < permissions:
            raise serializers.ValidationError("Inclua ACCOUNTS_READ, RESOURCES_READ e uma permissão de saldo, extrato ou limite, sem duplicatas.")
        return values


class CreateRequest(serializers.Serializer):
    data = CreateData()


class ExtendRequest(serializers.Serializer):
    data = Term()


class Decision(serializers.Serializer):
    status = serializers.ChoiceField(["AUTHORISED", "REJECTED"])
    accountIds = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=False)


class ConsentData(serializers.Serializer):
    consentId = serializers.CharField()
    status = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())
    creationDateTime = serializers.DateTimeField()
    statusUpdateDateTime = serializers.DateTimeField()
    expirationDateTime = serializers.DateTimeField(required=False)
    rejection = serializers.DictField(required=False)


class ConsentResponse(serializers.Serializer):
    data = ConsentData()
    links = PaginationLinksSerializer()
    meta = PaginationMetaSerializer()


def representation(consent):
    data = {
        "consentId": f"urn:portfolio:{consent.consent_id}", "status": consent.status,
        "creationDateTime": utc(consent.creation_date_time),
        "statusUpdateDateTime": utc(consent.status_update_date_time),
        "permissions": consent.permissions,
    }
    if consent.expiration_date_time:
        data["expirationDateTime"] = utc(consent.expiration_date_time)
    if consent.rejection_reason:
        data["rejection"] = {"rejectedBy": "USER" if consent.rejection_reason.startswith("CUSTOMER") else "ASPSP",
                             "reason": {"code": consent.rejection_reason}}
    return data


def locked_consent(user, consentId):
    prefix = "urn:portfolio:"
    try:
        if not consentId.startswith(prefix):
            raise ValueError
        key = UUID(consentId[len(prefix):])
    except ValueError:
        raise NotFound()
    consent = get_object_or_404(Consent.objects.select_for_update().exclude(logged_user={}),
                                consent_id=key, user=user)
    consent.refresh_expiry()
    return consent


def invalid(message):
    return Response({"errors": [{"code": "INVALID_REQUEST", "title": "Solicitação inválida",
                                 "detail": str(message)}]}, status=422)


example_user = {"document": {"identification": "00000000000", "rel": "CPF"}}


class CreateConsent(ContractView):
    @extend_schema(request=CreateRequest, responses={201: ConsentResponse}, parameters=[interaction],
                   examples=[OpenApiExample("Compartilhar contas", request_only=True, value={"data": {
                       "loggedUser": example_user, "permissions": ["RESOURCES_READ", "ACCOUNTS_READ",
                       "ACCOUNTS_BALANCES_READ", "ACCOUNTS_TRANSACTIONS_READ"]}})])
    def post(self, request):
        payload = CreateRequest(data=request.data)
        if not payload.is_valid():
            return invalid(payload.errors)
        data = payload.validated_data["data"]
        consent = Consent.objects.create(user=request.user, logged_user=data["loggedUser"],
                                        permissions=data["permissions"], expiration_date_time=data.get("expirationDateTime"))
        return single(request, representation(consent), 201)


class ConsentResource(ContractView):
    @extend_schema(responses=ConsentResponse, parameters=[interaction])
    @transaction.atomic
    def get(self, request, consentId: str):
        return single(request, representation(locked_consent(request.user, consentId)))

    @extend_schema(responses={204: None}, parameters=[interaction])
    @transaction.atomic
    def delete(self, request, consentId: str):
        consent = locked_consent(request.user, consentId)
        if consent.status != ConsentStatus.REJECTED:
            reason = "CUSTOMER_MANUALLY_REVOKED" if consent.status == ConsentStatus.AUTHORISED else "CUSTOMER_MANUALLY_REJECTED"
            consent.reject(reason)
        return Response(status=204)


class DemoDecision(APIView):
    @extend_schema(request=Decision, responses=ConsentResponse, summary="Confirmar a seleção de contas do titular")
    @transaction.atomic
    def post(self, request, consentId: str):
        consent = locked_consent(request.user, consentId)
        decision = Decision(data=request.data)
        if not decision.is_valid():
            return invalid(decision.errors)
        if consent.status != ConsentStatus.AWAITING_AUTHORISATION:
            return invalid("A decisão exige um consentimento pendente.")
        if decision.validated_data["status"] == ConsentStatus.REJECTED:
            consent.reject("CUSTOMER_MANUALLY_REJECTED")
        else:
            ids = set(decision.validated_data.get("accountIds", []))
            accounts = list(request.user.accounts.filter(account_id__in=ids))
            if not ids or len(accounts) != len(ids):
                return invalid("Selecione pelo menos uma conta do titular em /demo/accounts.")
            consent.accounts.set(accounts)
            consent.status = ConsentStatus.AUTHORISED
            consent.save(update_fields=["status", "status_update_date_time"])
        return single(request, representation(consent))


class ExtendConsent(ContractView):
    @extend_schema(request=ExtendRequest, responses={201: ConsentResponse}, parameters=[interaction])
    @transaction.atomic
    def post(self, request, consentId: str):
        consent = locked_consent(request.user, consentId)
        payload = ExtendRequest(data=request.data)
        if not payload.is_valid():
            return invalid(payload.errors)
        data = payload.validated_data["data"]
        if not consent.is_valid or data["loggedUser"] != consent.logged_user:
            return invalid("A renovação exige consentimento ativo e o mesmo titular.")
        consent.expiration_date_time = data.get("expirationDateTime")
        consent.save(update_fields=["expiration_date_time"])
        ConsentExtension.objects.create(consent=consent, expiration_date_time=consent.expiration_date_time)
        return single(request, representation(consent), 201)


class ExtensionData(serializers.Serializer):
    loggedUser = LoggedUser()
    requestDateTime = serializers.DateTimeField()
    expirationDateTime = serializers.DateTimeField(required=False)


class Extensions(ContractView):
    @extend_schema(responses=inline_serializer(name="ExtensionsResponse", fields={
        "data": ExtensionData(many=True), "links": PaginationLinksSerializer(), "meta": PaginationMetaSerializer()
    }), parameters=[interaction])
    @transaction.atomic
    def get(self, request, consentId: str):
        consent = locked_consent(request.user, consentId)
        rows = []
        for entry in consent.extensions.order_by("-pk"):
            row = {"requestDateTime": utc(entry.created_at), "loggedUser": consent.logged_user}
            if entry.expiration_date_time:
                row["expirationDateTime"] = utc(entry.expiration_date_time)
            rows.append(row)
        return Response({"data": rows, "links": {"self": request.build_absolute_uri()},
                         "meta": {"totalRecords": len(rows), "totalPages": 1}})
