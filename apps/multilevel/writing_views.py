"""
Writing Test Check API - Manual Review Version
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
from .writing_serializers import BulkWritingTestCheckSerializer
from .serializers import SpeakingTestResponseSerializer
from .telegram_notifications import telegram_notifier

logger = logging.getLogger(__name__)


class WritingTestCheckApiView(APIView):
    """
    Writing test submission - saves files and creates manual review record
    NO automatic grading - all results go to admin dashboard
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Writing test javoblarini yuklash (Manual Review)",
        operation_description="Writing javoblarni rasm sifatida yuklaydi va admin-dashboard ga tekshirish uchun yuboradi.",
        request_body=BulkWritingTestCheckSerializer,
        responses={
            201: "TestResult yaratildi va manual review uchun yuborildi",
            400: "Validation xatosi",
            403: "Ruxsat yo'q",
            500: "Server xatosi"
        }
    )
    def post(self, request):
        user = request.user
        
        logger.info(f"[WRITING] User {user.id} submitting writing test")
        logger.info(f"[WRITING] Content-Type: {request.content_type}")
        logger.info(f"[WRITING] Data keys: {list(request.data.keys())}")
        logger.info(f"[WRITING] Files keys: {list(request.FILES.keys())}")
        
        # Parse multipart form data
        if not request.content_type or not request.content_type.startswith('multipart/form-data'):
            return Response(
                {'error': 'Content-Type multipart/form-data bo\'lishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse answers and images from form-data
        try:
            parsed_data = self._parse_form_data(request)
            logger.info(f"[WRITING] Parsed data: {parsed_data}")
        except Exception as e:
            logger.error(f"[WRITING] Parse error: {str(e)}")
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
            logger.info(f"[WRITING] TestResult: {test_result.id}")
        except Exception as e:
            logger.error(f"[WRITING] TestResult error: {str(e)}")
            return Response(
                {'error': f'TestResult yaratishda xatolik: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save submission files and create manual review
        try:
            with transaction.atomic():
                # Save images to SubmissionMedia
                for answer in answers:
                    question = answer['question']
                    images = answer['images']
                    
                    for image in images:
                        SubmissionMedia.objects.create(
                            test_result=test_result,
                            section='writing',
                            question_number=question.id,
                            file=image['file'],
                            file_type='image'
                        )
                        logger.info(f"[WRITING] Saved image for question {question.id}")
                
                # Create or get ManualReview record
                manual_review, created = ManualReview.objects.get_or_create(
                    test_result=test_result,
                    section='writing',
                    defaults={
                        'status': 'pending',
                        'reviewer': None
                    }
                )
                
                if created:
                    logger.info(f"[WRITING] Created ManualReview: {manual_review.id}")
                else:
                    logger.info(f"[WRITING] ManualReview already exists: {manual_review.id}")
                
                # Mark test result as completed
                test_result.status = 'completed'
                test_result.end_time = timezone.now()
                test_result.save()
                
                logger.info(f"[WRITING] TestResult {test_result.id} marked as completed")
                
                # Send Telegram notification to teachers and save message_id
                try:
                    message_id = telegram_notifier.notify_new_submission(test_result, section='writing')
                    if message_id:
                        manual_review.telegram_message_id = message_id
                        manual_review.save(update_fields=['telegram_message_id'])
                        logger.info(f"[WRITING] Saved telegram_message_id: {message_id}")
                except Exception as e:
                    logger.error(f"[WRITING] Failed to send Telegram notification: {e}")
        
        except Exception as e:
            logger.error(f"[WRITING] Save error: {str(e)}")
            return Response(
                {'error': f'Fayllarni saqlashda xatolik: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'test_result_id': test_result.id,
            'status': 'pending',
            'message': 'Writing test muvaffaqiyatli yuklandi. Admin tomonidan tekshiriladi.',
            'manual_review_id': manual_review.id,
            'images_count': len([img for ans in answers for img in ans['images']])
        }, status=status.HTTP_201_CREATED)
    
    def _parse_form_data(self, request):
        """Parse multipart form-data into structured format
        
        Supports TWO formats:
        1. New format (answers[0][question], answers[0][writing_images][1][image])
        2. Legacy format (task1_image1, task2_image1) - frontend currently uses this
        """
        test_result_id = request.data.get('test_result_id') or request.data.get('user_test_id')
        
        # Parse questions and images
        question_data = {}
        image_data = {}
        
        # Get question IDs (new format)
        for key, value in request.data.items():
            if key.startswith('answers[') and '][question]' in key:
                try:
                    # Extract index: answers[0][question] -> 0
                    index = int(key.split('[')[1].split(']')[0])
                    question_data[index] = int(value)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse question key {key}: {e}")
        
        # Get image files (new format)
        for key, value in request.FILES.items():
            if key.startswith('answers[') and '][writing_images][' in key:
                try:
                    # Extract index and order: answers[0][writing_images][1][image]
                    parts = key.split('][writing_images][')
                    index = int(parts[0].split('[')[1])
                    order = int(parts[1].split(']')[0])
                    
                    if index not in image_data:
                        image_data[index] = {}
                    image_data[index][order] = value
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse image key {key}: {e}")
        
        # LEGACY FORMAT SUPPORT: task1_image1, task2_image1, etc.
        # This is what the frontend currently sends
        legacy_images = {}
        for key, value in request.FILES.items():
            if key.startswith('task') and '_image' in key:
                try:
                    # Extract task number: task1_image1 -> task=1, order=1
                    task_num = int(key.split('task')[1].split('_')[0])
                    image_num = int(key.split('_image')[1])
                    
                    if task_num not in legacy_images:
                        legacy_images[task_num] = {}
                    legacy_images[task_num][image_num] = value
                    logger.info(f"[WRITING] Legacy format detected: {key} -> task={task_num}, order={image_num}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse legacy image key {key}: {e}")
        
        # If legacy format detected, use it
        if legacy_images and not image_data:
            logger.info(f"[WRITING] Using LEGACY format, found {len(legacy_images)} tasks")
            
            # Get section from exam_id
            exam_id = request.data.get('exam_id')
            section_type = request.data.get('section_type', 'writing')
            
            if not exam_id:
                raise ValueError("exam_id maydoni kiritilishi shart!")
            
            # Get section
            from .models import Exam
            exam = Exam.objects.get(id=int(exam_id))
            section = Section.objects.get(exam=exam, type=section_type)
            
            # Get all questions for this section
            questions = list(Question.objects.filter(
                test__section=section
            ).order_by('test__order', 'id'))
            
            logger.info(f"[WRITING] Found {len(questions)} questions for section")
            
            # Map tasks to questions
            answers = []
            for task_num in sorted(legacy_images.keys()):
                if task_num - 1 < len(questions):
                    question = questions[task_num - 1]
                    images = legacy_images[task_num]
                    
                    answer_images = [
                        {'order': order, 'file': img_file}
                        for order, img_file in sorted(images.items())
                    ]
                    
                    answers.append({
                        'question': question,
                        'images': answer_images
                    })
                    logger.info(f"[WRITING] Task {task_num} -> Question {question.id}, {len(answer_images)} images")
            
            return {
                'test_result_id': int(test_result_id) if test_result_id else None,
                'answers': answers
            }
        
        # NEW FORMAT: Combine into answers list
        answers = []
        all_indices = set(question_data.keys()) | set(image_data.keys())
        
        for index in sorted(all_indices):
            question_id = question_data.get(index)
            images = image_data.get(index, {})
            
            if question_id and images:
                try:
                    question = Question.objects.get(id=question_id)
                    answer_images = [
                        {'order': order, 'file': img_file}
                        for order, img_file in sorted(images.items())
                    ]
                    
                    answers.append({
                        'question': question,
                        'images': answer_images
                    })
                except Question.DoesNotExist:
                    logger.error(f"Question {question_id} not found")
        
        return {
            'test_result_id': int(test_result_id) if test_result_id else None,
            'answers': answers
        }
    
    def _get_or_create_test_result(self, user, test_result_id, answers):
        """Get existing or create new TestResult
        
        Args:
            user: Current user
            test_result_id: Can be UserTest ID (from user_test_id) or TestResult ID
            answers: List of answers with questions
        """
        from .models import UserTest
        
        # Get section from first question
        first_question = answers[0]['question']
        section = first_question.test.section
        
        # Validate section type
        if section.type != 'writing':
            raise ValueError(f"Bu endpoint faqat writing testi uchun! (Berilgan: {section.type})")
        
        if test_result_id:
            # Check if it's a UserTest ID (legacy format from frontend)
            try:
                user_test = UserTest.objects.get(
                    id=test_result_id,
                    user=user
                )
                logger.info(f"[WRITING] Found UserTest {user_test.id}, checking for existing TestResult")
                
                # Check if TestResult already exists for this UserTest and section
                test_result = TestResult.objects.filter(
                    user_test=user_test,
                    section=section
                ).first()
                
                if test_result:
                    logger.info(f"[WRITING] Using existing TestResult {test_result.id}")
                    return test_result
                else:
                    # Create new TestResult for this UserTest
                    logger.info(f"[WRITING] Creating new TestResult for UserTest {user_test.id}")
                    test_result = TestResult.objects.create(
                        user_test=user_test,
                        section=section,
                        status='started',
                        start_time=timezone.now()
                    )
                    return test_result
                    
            except UserTest.DoesNotExist:
                # Maybe it's a TestResult ID, try that
                try:
                    test_result = TestResult.objects.get(
                        id=test_result_id,
                        user_test__user=user,
                        section=section
                    )
                    logger.info(f"[WRITING] Using existing TestResult {test_result.id}")
                    return test_result
                except TestResult.DoesNotExist:
                    raise ValueError(f"UserTest yoki TestResult ID {test_result_id} topilmadi!")
        
        # Create new UserTest and TestResult
        logger.info(f"[WRITING] Creating new UserTest and TestResult")
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
            logger.info(f"[WRITING] Created new UserTest {user_test.id}")
        
        # Create TestResult
        test_result = TestResult.objects.create(
            user_test=user_test,
            section=section,
            status='started',
            start_time=timezone.now()
        )
        logger.info(f"[WRITING] Created new TestResult {test_result.id}")
        
        return test_result