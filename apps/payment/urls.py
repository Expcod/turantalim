from django.urls import path
from .views import *

urlpatterns = [
    path('exampayment/', ExamPaymentAPIView.as_view(), name='create-payment'),
    path("update/", PaymeCallBackAPIView.as_view()),
    path("balance/topup/", BalanceTopUpAPIView.as_view(), name='balance-topup'),
    path("balance/", BalanceAPIView.as_view(), name='balance'),
    path("balance/transactions/", BalanceTransactionListAPIView.as_view(), name='balance-transactions'),
]