from django.urls import path
from .views import RegisterAPIView, CustomTokenObtainPairView, ProfileUpdateAPIView, ProfileDetailView 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('update-profile/', ProfileUpdateAPIView.as_view(), name='update_profile'),
    path('detail/', ProfileDetailView.as_view(), name='profile_detail'),
]