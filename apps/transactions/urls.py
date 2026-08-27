from django.urls import path

from .views import TransactionListView

app_name = 'transactions'

urlpatterns = [
    path('<uuid:account_id>/transactions/', TransactionListView.as_view(), name='transaction-list'),
]
