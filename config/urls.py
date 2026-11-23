from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from accounts import portfolio as accounts
from consents import portfolio as consents
from core.login_view import LoginView, LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Utilitários internos
    path('', include('core.urls')),

    # Open Finance Brasil — estrutura de URI padrão
    # /open-banking/<api>/<versão>/<recurso>
    path('open-banking/consents/v1/consents/', include('consents.urls')),
    path('open-banking/accounts/v1/accounts/', include('accounts.urls')),

    path('demo/accounts', accounts.DemoAccounts.as_view()),
    path('demo/consents/<str:consentId>/decision', consents.DemoDecision.as_view()),
    path('open-banking/consents/v3/consents', consents.CreateConsent.as_view()),
    path('open-banking/consents/v3/consents/<str:consentId>', consents.ConsentResource.as_view()),
    path('open-banking/consents/v3/consents/<str:consentId>/extends', consents.ExtendConsent.as_view()),
    path('open-banking/consents/v3/consents/<str:consentId>/extensions', consents.Extensions.as_view()),
    path('open-banking/accounts/v2/accounts', accounts.Accounts.as_view()),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>', accounts.Detail.as_view()),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>/balances', accounts.Balances.as_view()),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>/transactions', accounts.Transactions.as_view()),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>/transactions-current', accounts.Transactions.as_view(current=True)),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>/overdraft-limits', accounts.Overdraft.as_view()),
    path('open-banking/accounts/v2/accounts/<uuid:accountId>/reserved-balances', accounts.Reserves.as_view()),

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
