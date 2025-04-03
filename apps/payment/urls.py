from django.urls import path
from .views import *

urlpatterns = [
    path('create/', ExamPaymentAPIView.as_view(), name='create-payment'),
    path("update/", PaymeCallBackAPIView.as_view()),
]