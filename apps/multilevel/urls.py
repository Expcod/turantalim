from django.urls import path
from .views import *
urlpatterns = [

    # Main test
    path('test/', TestRequestApiView.as_view(), name='test-request'),

    path('testrequest/writing/', WritingTestRequestAPIView.as_view(), name='writing-test'),
    path('testrequest/speaking/', SpeakingTestRequestAPIView.as_view(), name='speaking-test'),

    
    #Check test
    path('check-test/', TestCheckApiView.as_view(), name='check-test'),

    # Test result
    path('test-result/<int:test_result_id>/', TestResultDetailView.as_view(), name='test-result-detail'),
    path('test-results/', TestResultListView.as_view(), name='test-result-list'),
    path('test-result/overall/', OverallTestResultView.as_view(), name='test-result-overall'),

]
