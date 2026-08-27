from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Utilitários internos
    path('', include('core.urls')),

    # Open Finance Brasil — estrutura de URI padrão
    # /open-banking/<api>/<versão>/<recurso>
    path('open-banking/consents/v1/consents/', include('consents.urls')),
    path('open-banking/accounts/v1/accounts/', include('accounts.urls')),

    # Rotas internas / aliases
    path('accounts/', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
]
