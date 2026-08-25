"""
Comando de seed para popular o banco com dados de teste realistas.
Uso: docker compose exec web python manage.py seed_data
     docker compose exec web python manage.py seed_data --clear
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Account, AccountSubtype, AccountType, Balance
from consents.models import Consent, ConsentStatus
from transactions.models import (
    CreditDebitType,
    Transaction,
    TransactionStatus,
    TransactionType,
)


# ---------------------------------------------------------------------------
# Dados fictícios realistas
# ---------------------------------------------------------------------------

INSTITUICOES = [
    {"brand": "Banco Itaú S.A.", "cnpj": "60701190000104"},
    {"brand": "Banco Bradesco S.A.", "cnpj": "60746948000112"},
    {"brand": "Banco do Brasil S.A.", "cnpj": "00000000000191"},
    {"brand": "Nubank Pagamentos S.A.", "cnpj": "18236120000158"},
    {"brand": "Caixa Econômica Federal", "cnpj": "00360305000104"},
]

USUARIOS_SEED = [
    {"username": "ana.silva", "email": "ana.silva@email.com", "first_name": "Ana", "last_name": "Silva"},
    {"username": "carlos.souza", "email": "carlos.souza@email.com", "first_name": "Carlos", "last_name": "Souza"},
    {"username": "mariana.lima", "email": "mariana.lima@email.com", "first_name": "Mariana", "last_name": "Lima"},
    {"username": "pedro.costa", "email": "pedro.costa@email.com", "first_name": "Pedro", "last_name": "Costa"},
]

DESCRICOES_CREDITO = [
    "Salário referente ao mês",
    "Transferência recebida via PIX",
    "Pagamento de freelance",
    "Restituição de imposto de renda",
    "Depósito em conta",
    "Reembolso de despesas",
    "Recebimento de aluguel",
]

DESCRICOES_DEBITO = [
    "Pagamento de boleto",
    "Transferência via PIX",
    "Débito automático conta de luz",
    "Débito automático internet",
    "Compra no débito",
    "Tarifa de manutenção de conta",
    "Pagamento de cartão de crédito",
    "Saque em caixa eletrônico",
]

PERMISSOES_DISPONIVEIS = [
    "ACCOUNTS_READ",
    "ACCOUNTS_BALANCES_READ",
    "ACCOUNTS_TRANSACTIONS_READ",
    "ACCOUNTS_OVERDRAFT_LIMITS_READ",
    "CUSTOMERS_PERSONAL_IDENTIFICATIONS_READ",
]


class Command(BaseCommand):
    help = "Popula o banco de dados com dados de teste realistas para desenvolvimento."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove todos os dados de seed antes de criar novos.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("🗑️  Removendo dados de seed anteriores..."))
            self._clear_data()

        self.stdout.write(self.style.MIGRATE_HEADING("🌱 Iniciando seed de dados..."))

        usuarios = self._criar_usuarios()
        contas = self._criar_contas(usuarios)
        self._criar_consentimentos(usuarios)
        self._criar_transacoes(contas)

        self.stdout.write(self.style.SUCCESS("\n✅ Seed concluído com sucesso!"))
        self.stdout.write(
            f"   👤 {len(usuarios)} usuários | "
            f"🏦 {len(contas)} contas | "
            f"📋 Consentimentos e Transações criados.\n"
        )
        self.stdout.write(
            self.style.WARNING(
                "   Senha padrão de todos os usuários seed: Senha@123\n"
            )
        )

    # -----------------------------------------------------------------------
    # Helpers internos
    # -----------------------------------------------------------------------

    def _clear_data(self):
        Transaction.objects.all().delete()
        Consent.objects.all().delete()
        Balance.objects.all().delete()
        Account.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("   Dados removidos.")

    def _criar_usuarios(self):
        usuarios = []
        for dados in USUARIOS_SEED:
            user, created = User.objects.get_or_create(
                username=dados["username"],
                defaults={
                    "email": dados["email"],
                    "first_name": dados["first_name"],
                    "last_name": dados["last_name"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("Senha@123")
                user.save()
                self.stdout.write(f"   ✓ Usuário criado: {user.username}")
            else:
                self.stdout.write(f"   ~ Usuário já existe: {user.username}")
            usuarios.append(user)
        return usuarios

    def _criar_contas(self, usuarios):
        contas = []
        tipos = list(AccountType)
        subtipos = list(AccountSubtype)

        for i, user in enumerate(usuarios):
            # Cada usuário recebe 1 ou 2 contas
            n_contas = random.randint(1, 2)
            for j in range(n_contas):
                instituicao = INSTITUICOES[(i + j) % len(INSTITUICOES)]

                numero = str(random.randint(10000, 99999))
                agencia = str(random.randint(1000, 9999))
                digito = str(random.randint(0, 9))

                conta, created = Account.objects.get_or_create(
                    user=user,
                    number=numero,
                    branch_code=agencia,
                    defaults={
                        "brand_name": instituicao["brand"],
                        "company_cnpj": instituicao["cnpj"],
                        "type": random.choice(tipos),
                        "subtype": random.choice(subtipos),
                        "check_digit": digito,
                        "currency": "BRL",
                    },
                )

                if created:
                    # Cria o saldo associado
                    disponivel = Decimal(str(round(random.uniform(100, 50000), 2)))
                    bloqueado = Decimal(str(round(random.uniform(0, 500), 2)))
                    aplicado = Decimal(str(round(random.uniform(0, 5000), 2)))

                    Balance.objects.create(
                        account=conta,
                        available_amount=disponivel,
                        blocked_amount=bloqueado,
                        automatically_invested_amount=aplicado,
                        currency="BRL",
                    )
                    self.stdout.write(
                        f"   ✓ Conta criada: {conta.branch_code}/{conta.number} "
                        f"({conta.brand_name}) → {user.username}"
                    )

                contas.append(conta)

        return contas

    def _criar_consentimentos(self, usuarios):
        agora = timezone.now()
        status_choices = list(ConsentStatus)

        for user in usuarios:
            # 1 a 3 consentimentos por usuário
            for _ in range(random.randint(1, 3)):
                n_permissoes = random.randint(2, len(PERMISSOES_DISPONIVEIS))
                permissoes = random.sample(PERMISSOES_DISPONIVEIS, n_permissoes)
                status = random.choice(status_choices)

                # Expiração: entre 30 e 365 dias a partir de agora
                expiracao = agora + timedelta(days=random.randint(30, 365))

                Consent.objects.create(
                    user=user,
                    status=status,
                    permissions=permissoes,
                    expiration_date_time=expiracao,
                )

        total = Consent.objects.count()
        self.stdout.write(f"   ✓ {total} consentimentos criados")

    def _criar_transacoes(self, contas):
        tipos_tx = list(TransactionType)
        agora = timezone.now()

        for conta in contas:
            # 10 a 25 transações por conta
            n_tx = random.randint(10, 25)
            for _ in range(n_tx):
                credit_debit = random.choice(list(CreditDebitType))
                tipo_tx = random.choice(tipos_tx)
                dias_atras = random.randint(0, 90)
                dt = agora - timedelta(days=dias_atras, hours=random.randint(0, 23))

                descricoes = (
                    DESCRICOES_CREDITO if credit_debit == CreditDebitType.CREDITO
                    else DESCRICOES_DEBITO
                )
                descricao = random.choice(descricoes)
                valor = Decimal(str(round(random.uniform(5, 8000), 2)))

                # CPF/CNPJ da contraparte (opcional, ~70% das transações)
                cpf_cnpj = None
                nome_contraparte = None
                if random.random() < 0.7:
                    if random.random() < 0.5:
                        cpf_cnpj = str(random.randint(10000000000, 99999999999))  # CPF 11 dígitos
                        nome_contraparte = random.choice(
                            ["João Ferreira", "Maria Oliveira", "Lucas Pereira", "Fernanda Santos"]
                        )
                    else:
                        inst = random.choice(INSTITUICOES)
                        cpf_cnpj = inst["cnpj"]
                        nome_contraparte = inst["brand"]

                Transaction.objects.create(
                    account=conta,
                    amount=valor,
                    currency="BRL",
                    credit_debit_type=credit_debit,
                    transaction_status=random.choice(list(TransactionStatus)),
                    transaction_date=dt.date(),
                    transaction_date_time=dt,
                    transaction_type=tipo_tx,
                    description=descricao,
                    payee_cnpj_cpf=cpf_cnpj,
                    payee_name=nome_contraparte,
                )

        total = Transaction.objects.count()
        self.stdout.write(f"   ✓ {total} transações criadas")
