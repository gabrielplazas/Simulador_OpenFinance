from django.contrib import admin
from .models import Account, Balance


class BalanceInline(admin.StackedInline):
    model = Balance
    can_delete = False
    verbose_name_plural = 'Saldo da Conta'
    fields = ('available_amount', 'blocked_amount', 'automatically_invested_amount', 'currency', 'update_date_time')
    readonly_fields = ('update_date_time',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'number',
        'check_digit',
        'branch_code',
        'brand_name',
        'user',
        'type',
        'subtype',
        'currency',
        'created_at',
    )
    list_filter = ('type', 'subtype', 'currency', 'brand_name')
    search_fields = (
        'number',
        'branch_code',
        'company_cnpj',
        'brand_name',
        'user__username',
        'user__email',
        'account_id',
    )
    readonly_fields = ('account_id', 'created_at', 'updated_at')
    inlines = [BalanceInline]

    fieldsets = (
        ('Informações do Usuário & Instituição', {
            'fields': ('user', 'account_id', 'brand_name', 'company_cnpj')
        }),
        ('Detalhes da Conta', {
            'fields': ('branch_code', 'number', 'check_digit', 'type', 'subtype', 'currency')
        }),
        ('Datas de Registro', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'currency',
        'available_amount',
        'blocked_amount',
        'automatically_invested_amount',
        'update_date_time',
    )
    list_filter = ('currency',)
    search_fields = ('account__number', 'account__user__username', 'account__user__email')
    readonly_fields = ('update_date_time',)