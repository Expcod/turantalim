"""
URL configuration for utils app
"""
from django.urls import path
from .views import TelegramHealthCheckView

urlpatterns = [
    path('telegram/health/', TelegramHealthCheckView.as_view(), name='telegram-health-check'),
]

