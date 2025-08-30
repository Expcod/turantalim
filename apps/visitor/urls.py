from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VisitorViewSet

router = DefaultRouter()
router.register(r'visitors', VisitorViewSet, basename='visitor')

app_name = 'visitor'

urlpatterns = [
    path('api/', include(router.urls)),
]
