from django.urls import path
from .views import *
from .writing_views import WritingTestCheckApiView
from .speaking_views import SpeakingTestCheckApiView
urlpatterns = [

    # Main test
    path('test/', TestRequestApiView.as_view(), name='test-request'),
    
    #Check test
    path('check-test/', TestCheckApiView.as_view(), name='check-test'),
    path('testcheck/writing/', WritingTestCheckApiView.as_view(), name='writing-test-check'),
    path('testcheck/speaking/', SpeakingTestCheckApiView.as_view(), name='speaking-test-check'),

    # Test result
    path('test-result/<int:test_result_id>/', TestResultDetailView.as_view(), name='test-result-detail'),
    path('test-results/', TestResultListView.as_view(), name='test-result-list'),
    path('test-result/overall/', OverallTestResultView.as_view(), name='test-result-overall'),

]
