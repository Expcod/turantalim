from django.urls import path
from .views import *
urlpatterns = [

# Payme Payment Integration
    path('payments/initiate/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),

    # Click Payment Integration
    path('click/initiate/', InitiateClickPaymentView.as_view(), name='initiate-click-payment'),
    path('click/webhook/', ClickWebhookView.as_view(), name='click-webhook'),
]