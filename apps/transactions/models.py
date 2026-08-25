import uuid
from django.core.validators import RegexValidator
from django.db import models
from accounts.models import Account


class CreditDebitType(models.TextChoices):
    CREDITO = 'CREDITO', 'Crédito (Entrada)'
    DEBITO = 'DEBITO', 'Débito (Saída)'


class TransactionType(models.TextChoices):
    TED = 'TED', 'TED'
    DOC = 'DOC', 'DOC'
    PIX = 'PIX', 'PIX'
    BOLETO = 'BOLETO', 'Boleto Bancário'
    TARIFAS = 'TARIFAS', 'Tarifas'
    ENCARGOS = 'ENCARGOS', 'Encargos'
    DUPLICATA = 'DUPLICATA', 'Cobrança por Duplicata'
    OPERACOES_CREDITO = 'OPERACOES_CREDITO', 'Operações de Crédito'
    OUTROS = 'OUTROS', 'Outros'


class TransactionStatus(models.TextChoices):
    LANCADO = 'LANCADO', 'Lançado'
    PROCESSANDO = 'PROCESSANDO', 'Processando'


class Transaction(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Conta'
    )
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='ID da Transação (Open Finance)'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Valor da Transação'
    )
    currency = models.CharField(max_length=3, default='BRL', verbose_name='Moeda')
    credit_debit_type = models.CharField(
        max_length=10,
        choices=CreditDebitType.choices,
        verbose_name='Tipo de Lançamento (C/D)'
    )
    transaction_status = models.CharField(
        max_length=15,
        choices=TransactionStatus.choices,
        default=TransactionStatus.LANCADO,
        verbose_name='Status da Transação'
    )
    transaction_date = models.DateField(verbose_name='Data da Transação')
    transaction_date_time = models.DateTimeField(verbose_name='Data/Hora Completa da Transação')
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        verbose_name='Tipo de Transação'
    )
    description = models.CharField(max_length=255, verbose_name='Descrição/Histórico')
    
    # Informações da contraparte (opcional)
    payee_cnpj_cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^(\d{11}|\d{14})$',
                message='CPF ou CNPJ deve conter apenas números com 11 ou 14 dígitos.'
            )
        ],
        verbose_name='CPF/CNPJ do Favorecido/Pagador'
    )
    payee_name = models.CharField(
        max_length=140,
        blank=True,
        null=True,
        verbose_name='Nome do Favorecido/Pagador'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-transaction_date_time']
        indexes = [
            models.Index(fields=['account', '-transaction_date_time']),
        ]

    def __str__(self):
        return f"{self.credit_debit_type} - {self.transaction_type} ({self.amount}) - {self.account.number}"
