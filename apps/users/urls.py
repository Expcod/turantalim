from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/change-language/', ChangeLanguageView.as_view(), name='change_language'),
    path('profile/change-name/', ChangeNameView.as_view(), name='change_name'),
    path('profile/change-picture/', ChangePictureView.as_view(), name='change_picture'),
    path('profile/change-gender/', ChangeGenderView.as_view(),),
]