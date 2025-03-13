from django.urls import path
from .views import LanguageListCreateAPIView, LanguageDetailAPIView

urlpatterns = [
    path('languages/', LanguageListCreateAPIView.as_view(), name='language-list-create'),
    path('languages/<int:pk>/', LanguageDetailAPIView.as_view(), name='language-detail'),
]
