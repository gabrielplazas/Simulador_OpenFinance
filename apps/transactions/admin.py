from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'account',
        'credit_debit_type',
        'transaction_type',
        'get_amount_formatted',
        'transaction_status',
        'transaction_date_time',
    )
    list_filter = (
        'credit_debit_type',
        'transaction_type',
        'transaction_status',
        'currency',
        'transaction_date',
    )
    search_fields = (
        'transaction_id',
        'description',
        'payee_name',
        'payee_cnpj_cpf',
        'account__number',
        'account__user__username',
    )
    readonly_fields = ('transaction_id', 'created_at')
    date_hierarchy = 'transaction_date_time'

    fieldsets = (
        ('Identificação & Conta', {
            'fields': ('account', 'transaction_id')
        }),
        ('Valores & Status', {
            'fields': ('amount', 'currency', 'credit_debit_type', 'transaction_status')
        }),
        ('Detalhes da Operação', {
            'fields': ('transaction_type', 'description', 'transaction_date', 'transaction_date_time')
        }),
        ('Dados da Contraparte (Favorecido/Pagador)', {
            'fields': ('payee_name', 'payee_cnpj_cpf')
        }),
        ('Registro', {
            'fields': ('created_at',)
        }),
    )

    @admin.display(description='Valor Monetário')
    def get_amount_formatted(self, obj):
        return f"{obj.currency} {obj.amount:,.2f}"
