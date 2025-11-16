from django.urls import path
from .views import (
    DepositView,
    WithdrawView,
    TransactionListView,
    TransactionDetailView,
)

urlpatterns = [
    path('deposit/', DepositView.as_view(), name='transaction-deposit'),
    path('withdraw/', WithdrawView.as_view(), name='transaction-withdraw'),
    path('', TransactionListView.as_view(), name='transaction-list'),
    path('<int:transaction_id>/', TransactionDetailView.as_view(), name='transaction-detail'),
]

