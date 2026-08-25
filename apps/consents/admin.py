from django.contrib import admin
from .models import Consent


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = (
        'consent_id',
        'user',
        'status',
        'get_is_valid',
        'creation_date_time',
        'expiration_date_time',
    )
    list_filter = ('status', 'creation_date_time')
    search_fields = ('consent_id', 'user__username', 'user__email')
    readonly_fields = ('consent_id', 'creation_date_time', 'status_update_date_time')
    date_hierarchy = 'creation_date_time'

    fieldsets = (
        ('Identificação & Status', {
            'fields': ('user', 'consent_id', 'status')
        }),
        ('Escopos do Open Finance', {
            'fields': ('permissions',)
        }),
        ('Prazos & Validade', {
            'fields': ('creation_date_time', 'expiration_date_time', 'status_update_date_time')
        }),
    )

    @admin.display(description='Válido?', boolean=True)
    def get_is_valid(self, obj):
        return obj.is_valid