"""
Speaking Test Check API - Manual Review Version
Fayllarni saqlaydi va manual review uchun admin-dashboard ga yuboradi
"""
import logging
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from django.db import transaction

from .models import Question, TestResult, Section, SubmissionMedia, ManualReview
from .speaking_serializers import BulkSpeakingTestCheckSerializer
from .serializers import SpeakingTestResponseSerializer

logger = logging.getLogger(__name__)


class SpeakingTestCheckApiView(APIView):
    """
    Speaking test submission - saves files and creates manual review record
    NO automatic grading - all results go to admin dashboard
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking test javoblarini yuklash (Manual Review)",
        operation_description="Speaking javoblarni audio sifatida yuklaydi va admin-dashboard ga tekshirish uchun yuboradi.",
        request_body=BulkSpeakingTestCheckSerializer,
        responses={
            201: "TestResult yaratildi va manual review uchun yuborildi",
            400: "Validation xatosi",
            403: "Ruxsat yo'q",
            500: "Server xatosi"
        }
    )
    def post(self, request):
        user = request.user
        
        logger.info(f"[SPEAKING] User {user.id} submitting speaking test")
        logger.info(f"[SPEAKING] Content-Type: {request.content_type}")
        logger.info(f"[SPEAKING] Data keys: {list(request.data.keys())}")
        logger.info(f"[SPEAKING] Files keys: {list(request.FILES.keys())}")
        
        # Parse multipart form data
        if not request.content_type or not request.content_type.startswith('multipart/form-data'):
            return Response(
                {'error': 'Content-Type multipart/form-data bo\'lishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse answers and audio files from form-data
        try:
            parsed_data = self._parse_form_data(request)
            logger.info(f"[SPEAKING] Parsed data: {parsed_data}")
        except Exception as e:
            logger.error(f"[SPEAKING] Parse error: {str(e)}")
            return Response(
                {'error': f'Ma\'lumotlar noto\'g\'ri formatda yuborilgan: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        test_result_id = parsed_data.get('test_result_id')
        answers = parsed_data.get('answers', [])
        
        if not answers:
            return Response(
                {'error': 'Kamida bitta javob yuborilishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create TestResult
        try:
            test_result = self._get_or_create_test_result(user, test_result_id, answers)
            logger.info(f"[SPEAKING] TestResult: {test_result.id}")
        except Exception as e:
            logger.error(f"[SPEAKING] TestResult error: {str(e)}")
            return Response(
                {'error': f'TestResult yaratishda xatolik: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save submission files and create manual review
        try:
            with transaction.atomic():
                # Save audio files to SubmissionMedia
                for answer in answers:
                    question = answer['question']
                    audio_file = answer['audio']
                    
                    SubmissionMedia.objects.create(
                        test_result=test_result,
                        section='speaking',
                        question_number=question.id,
                        file=audio_file,
                        file_type='audio'
                    )
                    logger.info(f"[SPEAKING] Saved audio for question {question.id}")
                
                # Create or get ManualReview record
                manual_review, created = ManualReview.objects.get_or_create(
                    test_result=test_result,
                    section='speaking',
                    defaults={
                        'status': 'pending',
                        'reviewer': None
                    }
                )
                
                if created:
                    logger.info(f"[SPEAKING] Created ManualReview: {manual_review.id}")
                else:
                    logger.info(f"[SPEAKING] ManualReview already exists: {manual_review.id}")
                
                # Mark test result as completed
                test_result.status = 'completed'
                test_result.end_time = timezone.now()
                test_result.save()
                
                logger.info(f"[SPEAKING] TestResult {test_result.id} marked as completed")
        
        except Exception as e:
            logger.error(f"[SPEAKING] Save error: {str(e)}")
            return Response(
                {'error': f'Fayllarni saqlashda xatolik: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'test_result_id': test_result.id,
            'status': 'pending',
            'message': 'Speaking test muvaffaqiyatli yuklandi. Admin tomonidan tekshiriladi.',
            'manual_review_id': manual_review.id,
            'audios_count': len(answers)
        }, status=status.HTTP_201_CREATED)
    
    def _parse_form_data(self, request):
        """Parse multipart form-data into structured format"""
        test_result_id = request.data.get('test_result_id')
        
        # Parse questions and audio files
        question_data = {}
        audio_data = {}
        
        # Get question IDs
        for key, value in request.data.items():
            if key.startswith('answers[') and '][question]' in key:
                try:
                    # Extract index: answers[0][question] -> 0
                    index = int(key.split('[')[1].split(']')[0])
                    question_data[index] = int(value)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse question key {key}: {e}")
        
        # Get audio files
        for key, value in request.FILES.items():
            if key.startswith('answers[') and '][speaking_audio]' in key:
                try:
                    # Extract index: answers[0][speaking_audio] -> 0
                    index = int(key.split('[')[1].split(']')[0])
                    audio_data[index] = value
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse audio key {key}: {e}")
        
        # Combine into answers list
        answers = []
        all_indices = set(question_data.keys()) | set(audio_data.keys())
        
        for index in sorted(all_indices):
            question_id = question_data.get(index)
            audio_file = audio_data.get(index)
            
            if question_id and audio_file:
                try:
                    question = Question.objects.get(id=question_id)
                    answers.append({
                        'question': question,
                        'audio': audio_file
                    })
                except Question.DoesNotExist:
                    logger.error(f"Question {question_id} not found")
        
        return {
            'test_result_id': int(test_result_id) if test_result_id else None,
            'answers': answers
        }
    
    def _get_or_create_test_result(self, user, test_result_id, answers):
        """Get existing or create new TestResult"""
        if test_result_id:
            # Use existing TestResult
            test_result = TestResult.objects.get(
                id=test_result_id,
                user_test__user=user,
                status='started'
            )
            return test_result
        
        # Create new TestResult
        first_question = answers[0]['question']
        section = first_question.test.section
        
        # Validate section type
        if section.type != 'speaking':
            raise ValueError(f"Bu endpoint faqat speaking testi uchun! (Berilgan: {section.type})")
        
        # Get or create UserTest
        from .models import UserTest
        user_test = UserTest.objects.filter(
            user=user,
            exam=section.exam,
            status__in=['created', 'started']
        ).first()
        
        if not user_test:
            user_test = UserTest.objects.create(
                user=user,
                exam=section.exam,
                language=section.exam.language,
                status='started'
            )
        
        # Create TestResult
        test_result = TestResult.objects.create(
            user_test=user_test,
            section=section,
            status='started',
            start_time=timezone.now()
        )
        
        return test_result
