from datetime import timedelta
from datetime import timezone as tz

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_field, inline_serializer, OpenApiParameter
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from consents.permissions import HasValidConsent
from core.contract import ContractView, consent_header, interaction, single, utc
from core.serializers import PaginationLinksSerializer, PaginationMetaSerializer
from transactions.models import TransactionStatus
from transactions.views import _paginated_response
from .serializers import AccountSerializer


class Money(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()


class MoneyField(serializers.Field):
    def __init__(self, attribute):
        self.attribute = attribute
        super().__init__(source="*", read_only=True)

    def to_representation(self, obj):
        return Money({"amount": getattr(obj, self.attribute), "currency": obj.currency}).data


extend_schema_field(Money)(MoneyField)


class Identification(AccountSerializer):
    compeCode = serializers.CharField(source="compe_code")
    number = serializers.SerializerMethodField()

    def get_number(self, obj) -> str:
        return obj.number.zfill(8)


class Amounts(serializers.Serializer):
    availableAmount = MoneyField("available_amount")
    blockedAmount = MoneyField("blocked_amount")
    automaticallyInvestedAmount = MoneyField("automatically_invested_amount")
    updateDateTime = serializers.SerializerMethodField()

    def get_updateDateTime(self, obj) -> str:
        return utc(obj.update_date_time)


class Entry(serializers.Serializer):
    transactionId = serializers.UUIDField(source="transaction_id")
    transactionAmount = MoneyField("amount")
    creditDebitType = serializers.CharField(source="credit_debit_type")
    completedAuthorisedPaymentType = serializers.SerializerMethodField()
    transactionName = serializers.CharField(source="description")
    transactionDateTime = serializers.SerializerMethodField()
    type = serializers.CharField(source="transaction_type")

    def get_completedAuthorisedPaymentType(self, obj) -> str:
        if obj.transaction_status == TransactionStatus.LANCADO:
            return "TRANSACAO_EFETIVADA"
        return "TRANSACAO_PROCESSANDO"

    def get_transactionDateTime(self, obj) -> str:
        return obj.transaction_date_time.astimezone(tz.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if data["type"] == "OUTROS":
            data["typeAdditionalInfo"] = obj.description[:144]
        if obj.payee_cnpj_cpf:
            data["partieCnpjCpf"] = obj.payee_cnpj_cpf
            data["partiePersonType"] = "PESSOA_NATURAL" if len(obj.payee_cnpj_cpf) == 11 else "PESSOA_JURIDICA"
        return data


def envelope(name, data):
    return inline_serializer(name=name, fields={"data": data, "links": PaginationLinksSerializer(),
                                                "meta": PaginationMetaSerializer()})


class AccountSummary(Identification):
    class Meta(AccountSerializer.Meta):
        fields = [*AccountSerializer.Meta.fields, "compeCode"]


class AccountInfo(Identification):
    class Meta(AccountSerializer.Meta):
        fields = ["compeCode", "branchCode", "number", "checkDigit", "type", "subtype", "currency"]


accounts_response = envelope("SelectedAccounts", AccountSummary(many=True))
headers = [interaction, consent_header]
paging = [OpenApiParameter("page", int), OpenApiParameter("page-size", int)]


class DemoAccounts(APIView):
    @extend_schema(summary="Escolher contas do titular para a autorização", responses=accounts_response, parameters=paging)
    def get(self, request):
        return _paginated_response(request, request.user.accounts.order_by("pk"), AccountSummary)


class AccountResource(ContractView):
    permission_classes = [HasValidConsent]
    required_scope = "ACCOUNTS_READ"

    def account(self, request, accountId):
        return get_object_or_404(request.consent.accounts.filter(user=request.user), account_id=accountId)


class Accounts(AccountResource):
    @extend_schema(responses=accounts_response, parameters=headers + paging)
    def get(self, request):
        return _paginated_response(request, request.consent.accounts.filter(user=request.user).order_by("pk"), AccountSummary)


class Detail(AccountResource):
    @extend_schema(responses=envelope("IdentificationResponse", AccountInfo()), parameters=headers)
    def get(self, request, accountId):
        return single(request, AccountInfo(self.account(request, accountId)).data)


class Balances(AccountResource):
    required_scope = "ACCOUNTS_BALANCES_READ"

    @extend_schema(responses=envelope("AmountsResponse", Amounts()), parameters=headers)
    def get(self, request, accountId):
        balance = getattr(self.account(request, accountId), "balance", None)
        if balance is None:
            raise NotFound("Saldo não encontrado.")
        return single(request, Amounts(balance).data)


class DateRange(serializers.Serializer):
    fromBookingDate = serializers.DateField(required=False)
    toBookingDate = serializers.DateField(required=False)
    creditDebitIndicator = serializers.ChoiceField(["CREDITO", "DEBITO"], required=False)

    def validate(self, attrs):
        start, end = attrs.get("fromBookingDate"), attrs.get("toBookingDate")
        if (start is None) != (end is None) or (start and start > end):
            raise serializers.ValidationError("Informe as duas datas em ordem cronológica.")
        return attrs


class Transactions(AccountResource):
    required_scope = "ACCOUNTS_TRANSACTIONS_READ"
    current = False

    @extend_schema(responses=envelope("Statement", Entry(many=True)), parameters=headers + paging + [DateRange])
    def get(self, request, accountId):
        account = self.account(request, accountId)
        query = DateRange(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        today = timezone.localdate()
        start = params.get("fromBookingDate", today)
        end = params.get("toBookingDate", today)
        def year_offset(year):
            try:
                return today.replace(year=year)
            except ValueError:  # 29 February
                return today.replace(year=year, day=28)
        earliest = today - timedelta(days=6) if self.current else year_offset(today.year - 1)
        if start < earliest or end > year_offset(today.year + 1):
            raise serializers.ValidationError("Período fora da janela permitida.")
        entries = account.transactions.filter(transaction_date_time__date__range=(start, end))
        if "creditDebitIndicator" in params:
            entries = entries.filter(credit_debit_type=params["creditDebitIndicator"])
        return _paginated_response(request, entries.order_by("-transaction_date_time", "-pk"), Entry)


class Overdraft(AccountResource):
    required_scope = "ACCOUNTS_OVERDRAFT_LIMITS_READ"

    @extend_schema(responses=envelope("OverdraftResponse", serializers.DictField()), parameters=headers)
    def get(self, request, accountId):
        self.account(request, accountId)
        return single(request, {})


class Reserves(AccountResource):
    required_scope = "ACCOUNTS_BALANCES_READ"

    @extend_schema(responses={404: dict}, parameters=headers, description="A instituição fictícia não oferta reservas de saldo.")
    def get(self, request, accountId):
        self.account(request, accountId)
        raise NotFound("Produto de reserva não ofertado.")
