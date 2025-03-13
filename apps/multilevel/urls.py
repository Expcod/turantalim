from django.urls import path
from .views import *
urlpatterns = [
    # # Section
    # path('config/listening/', SectionListCreateAPIView.as_view(), name='listening-list-create'),
    # path('config/listening/<int:pk>/', SectionDetailAPIView.as_view(), name='listening-detail'),


    # # Test
    # path('config/test/', TestListCreateAPIView.as_view(), name='test-list-create'),
    # path('config/test/<int:pk>/', TestDetailAPIView.as_view(), name='test-detail'),
    
    # # User Test
    # path('config/user-test/', UserTestListCreateAPIView.as_view(), name='user-test-list-create'),
    # path('config/user-test/<int:pk>/', UserTestDetailAPIView.as_view(), name='user-test-detail'),

    # Main test
    path('test/', TestRequestApiView.as_view(), name='test-request'),

    
    #Check test
    path('check-test/', TestCheckApiView.as_view(), name='check-test'),

    path('user/test-results/', UserTestResultListView.as_view(), name='user-test-results'),

]
