import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User


class AccountType(models.TextChoices):
    CONTA_DEPOSITO_A_VISTA = 'CONTA_DEPOSITO_A_VISTA', 'Conta de Depósito à Vista (Corrente)'
    CONTA_POUPANCA = 'CONTA_POUPANCA', 'Conta Poupança'
    CONTA_PAGAMENTO_PRE_PAGA = 'CONTA_PAGAMENTO_PRE_PAGA', 'Conta de Pagamento Pré-Paga'


class AccountSubtype(models.TextChoices):
    INDIVIDUAL = 'INDIVIDUAL', 'Individual'
    CONJUNTA_SIMPLES = 'CONJUNTA_SIMPLES', 'Conjunta Simples'
    CONJUNTA_SOLIDARIA = 'CONJUNTA_SOLIDARIA', 'Conjunta Solidária'


class Account(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts',
        verbose_name='Usuário'
    )
    account_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='ID da Conta (Open Finance)'
    )
    brand_name = models.CharField(max_length=80, verbose_name='Nome da Marca')
    company_cnpj = models.CharField(
        max_length=14,
        validators=[
            RegexValidator(
                regex=r'^\d{14}$',
                message='CNPJ deve conter apenas números, com 14 dígitos.'
            )
        ],
        verbose_name='CNPJ da Instituição'
    )
    type = models.CharField(
        max_length=30,
        choices=AccountType.choices,
        verbose_name='Tipo de Conta'
    )
    subtype = models.CharField(
        max_length=30,
        choices=AccountSubtype.choices,
        verbose_name='Subtipo de Conta'
    )
    number = models.CharField(max_length=20, verbose_name='Número da Conta')
    branch_code = models.CharField(max_length=4, verbose_name='Código da Agência')
    check_digit = models.CharField(max_length=2, verbose_name='Dígito Verificador')
    currency = models.CharField(max_length=3, default='BRL', verbose_name='Moeda')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand_name} - {self.branch_code}/{self.number}-{self.check_digit} ({self.user.username})"


class Balance(models.Model):
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='balance',
        verbose_name='Conta'
    )
    available_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Saldo Disponível'
    )
    blocked_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Saldo Bloqueado'
    )
    automatically_invested_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Saldo Aplicado Automaticamente'
    )
    currency = models.CharField(max_length=3, default='BRL', verbose_name='Moeda')
    update_date_time = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')

    class Meta:
        verbose_name = 'Saldo'
        verbose_name_plural = 'Saldos'

    def __str__(self):
        return f"Saldo de {self.account.number}: {self.currency} {self.available_amount}"
