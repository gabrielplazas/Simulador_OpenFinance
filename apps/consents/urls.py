from django.urls import path

from .views import ConsentDetailView, ConsentListCreateView

app_name = 'consents'

# Prefixo do Open Finance Brasil: /open-banking/consents/v1/consents
# O prefixo raiz é registrado no config/urls.py
urlpatterns = [
    path('', ConsentListCreateView.as_view(), name='consent-list-create'),
    path('<uuid:consent_id>/', ConsentDetailView.as_view(), name='consent-detail'),
]
