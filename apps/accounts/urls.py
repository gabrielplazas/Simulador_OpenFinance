from django.urls import path

from transactions.views import TransactionListView
from .views import AccountBalanceView, AccountDetailView, AccountListView

app_name = 'accounts'

urlpatterns = [
    path('', AccountListView.as_view(), name='account-list'),
    path('<uuid:account_id>/', AccountDetailView.as_view(), name='account-detail'),
    path('<uuid:account_id>/balances/', AccountBalanceView.as_view(), name='account-balances'),
    path('<uuid:account_id>/transactions/', TransactionListView.as_view(), name='account-transactions'),
]
