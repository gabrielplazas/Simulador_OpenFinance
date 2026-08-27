from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.core.login_view import LoginView, LogoutView

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

    # Autenticação via API
    path('api/login/', LoginView.as_view(), name='api-login'),
    path('api/logout/', LogoutView.as_view(), name='api-logout'),

    # Documentação OpenAPI 3.0 (Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
