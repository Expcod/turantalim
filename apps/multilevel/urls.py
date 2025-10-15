from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .writing_views import WritingTestCheckApiView
from .speaking_views import SpeakingTestCheckApiView
from .listening_check_views import ListeningTestCheckApiView
from .reading_check_views import ReadingTestCheckApiView
from .exam_results_views import MultilevelTysExamResultView, MultilevelTysExamListResultView
from .manual_review_views import ManualReviewViewSet

# Register ViewSets
router = DefaultRouter()
router.register(r'admin/submissions', ManualReviewViewSet, basename='admin-submissions')

urlpatterns = [
    # API Router for ViewSets
    path('api/', include(router.urls)),

    # Exams list
    path('exams/', ExamListView.as_view(), name='exam-list'),

    # Main test
    path('test/', TestRequestApiView.as_view(), name='test-request'),
    path('test/preview/', TestPreviewApiView.as_view(), name='test-preview'),
    
    # Check test
    path('testcheck/listening/', ListeningTestCheckApiView.as_view(), name='listening-test-check'),
    path('testcheck/reading/', ReadingTestCheckApiView.as_view(), name='reading-test-check'),
    path('testcheck/writing/', WritingTestCheckApiView.as_view(), name='writing-test-check'),
    path('testcheck/speaking/', SpeakingTestCheckApiView.as_view(), name='speaking-test-check'),

    # Test result
    path('test-result/<int:test_result_id>/', TestResultDetailView.as_view(), name='test-result-detail'),
    path('test-results/', TestResultListView.as_view(), name='test-result-list'),
    path('test-result/overall/', OverallTestResultView.as_view(), name='test-result-overall'),
    path('test-result/calculate/', OverallTestResultView.as_view(), name='calculate-overall-result'),

    # Multilevel va TYS imtihon natijalari
    path('exam-results/multilevel-tys/', MultilevelTysExamResultView.as_view(), name='multilevel-tys-exam-result'),
    path('exam-results/multilevel-tys/list/', MultilevelTysExamListResultView.as_view(), name='multilevel-tys-exam-list'),

    # Test time info
    path('test/time-info/', TestTimeInfoView.as_view(), name='test-time-info'),
    
    # Test SMS notification
    path('test/sms-notification/', TestSMSNotificationView.as_view(), name='test-sms-notification'),
]