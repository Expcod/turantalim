from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import (
    TestResult, UserTest, ManualReview, 
    QuestionScore, ReviewLog, SubmissionMedia
)
from .manual_review_serializers import (
    SubmissionListSerializer,
    SubmissionDetailSerializer,
    WriteManualReviewSerializer
)

class ManualReviewViewSet(viewsets.ViewSet):
    """
    API viewset for manual review of writing and speaking sections
    """
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        """
        List all submissions that need manual review
        GET /api/admin/submissions/
        
        Filters:
        - status: pending, reviewing, checked
        - section: writing, speaking
        - exam_level: tys, multilevel
        - search: user's first/last name or username
        """
        # Get all test results for writing and speaking sections
        queryset = TestResult.objects.filter(
            section__type__in=['writing', 'speaking'],
            status='completed'
        ).select_related(
            'user_test__user',
            'user_test__exam',
            'section'
        ).order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        section_filter = request.query_params.get('section')
        exam_level = request.query_params.get('exam_level')
        search = request.query_params.get('search')
        
        if status_filter:
            # Filter by review status
            if status_filter == 'pending':
                # Items without manual_review or with pending status
                queryset = queryset.filter(
                    Q(manual_review__isnull=True) | Q(manual_review__status='pending')
                )
            elif status_filter == 'reviewing':
                queryset = queryset.filter(manual_review__status='reviewing')
            elif status_filter == 'checked':
                queryset = queryset.filter(manual_review__status='checked')
        
        if section_filter:
            # Filter by section type
            queryset = queryset.filter(section__type=section_filter)
        
        if exam_level:
            # Filter by exam level
            queryset = queryset.filter(user_test__exam__level=exam_level)
        
        if search:
            # Search by user's name or username
            queryset = queryset.filter(
                Q(user_test__user__first_name__icontains=search) |
                Q(user_test__user__last_name__icontains=search) |
                Q(user_test__user__username__icontains=search)
            )
        
        serializer = SubmissionListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Get details for a specific submission
        GET /api/admin/submissions/{submission_id}/
        """
        test_result = get_object_or_404(
            TestResult.objects.select_related(
                'user_test__user', 'user_test__exam', 'section'
            ),
            pk=pk
        )
        
        serializer = SubmissionDetailSerializer(
            test_result, 
            context={'request': request}
        )
        
        # Mark as reviewing if it was pending
        if hasattr(test_result, 'manual_review'):
            if test_result.manual_review.status == 'pending':
                test_result.manual_review.status = 'reviewing'
                test_result.manual_review.save()
        else:
            # Create manual review record if it doesn't exist yet
            ManualReview.objects.create(
                test_result=test_result,
                section=test_result.section.type,
                status='reviewing',
                reviewer=request.user
            )
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='writing')
    def update_writing(self, request, pk=None):
        """
        Update writing scores for a submission
        PATCH /api/admin/submissions/{submission_id}/writing/
        """
        test_result = get_object_or_404(
            TestResult.objects.select_related(
                'user_test__user', 'user_test__exam', 'section'
            ),
            pk=pk,
            section__type='writing'
        )
        
        serializer = WriteManualReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create manual review
        manual_review, created = ManualReview.objects.get_or_create(
            test_result=test_result,
            section='writing',
            defaults={
                'status': 'reviewing',
                'reviewer': request.user
            }
        )
        
        # Update manual review
        old_score = manual_review.total_score
        manual_review.total_score = serializer.validated_data['total_score']
        manual_review.status = 'checked'
        manual_review.reviewer = request.user
        manual_review.reviewed_at = timezone.now()
        manual_review.save()
        
        # Create review log for total score change
        ReviewLog.objects.create(
            manual_review=manual_review,
            reviewer=request.user,
            action='update_total_score',
            old_score=old_score,
            new_score=manual_review.total_score,
            comment=f"Writing score updated by {request.user.get_full_name()}"
        )
        
        # Create or update question scores and add to review log
        for question_num, data in serializer.validated_data['question_scores'].items():
            score = float(data['score'])
            comment = data.get('comment', '')
            
            # Get or create question score
            question_score, created = QuestionScore.objects.get_or_create(
                manual_review=manual_review,
                question_number=int(question_num),
                defaults={
                    'score': score,
                    'comment': comment
                }
            )
            
            if not created:
                # Log old score before updating
                old_q_score = question_score.score
                question_score.score = score
                question_score.comment = comment
                question_score.save()
                
                # Create review log for question score change
                ReviewLog.objects.create(
                    manual_review=manual_review,
                    reviewer=request.user,
                    action='update_question_score',
                    question_number=int(question_num),
                    old_score=old_q_score,
                    new_score=score,
                    comment=f"Writing Q{question_num} score updated by {request.user.get_full_name()}"
                )
            else:
                # Create review log for new question score
                ReviewLog.objects.create(
                    manual_review=manual_review,
                    reviewer=request.user,
                    action='create_question_score',
                    question_number=int(question_num),
                    new_score=score,
                    comment=f"Writing Q{question_num} score created by {request.user.get_full_name()}"
                )
        
        # Handle notifications to the user if requested
        if serializer.validated_data.get('notified', True):
            # This would typically call a notification service
            # For now, we'll just log it
            ReviewLog.objects.create(
                manual_review=manual_review,
                reviewer=request.user,
                action='notify_user',
                comment=f"User notified about writing score by {request.user.get_full_name()}"
            )
            
            # TODO: Implement actual notification here - Telegram/Email/etc.
            # Example: send_notification_to_user(test_result.user_test.user, 'writing', manual_review.total_score)
        
        return Response({'status': 'success', 'message': 'Writing scores updated successfully'})
    
    @action(detail=True, methods=['patch'], url_path='speaking')
    def update_speaking(self, request, pk=None):
        """
        Update speaking scores for a submission
        PATCH /api/admin/submissions/{submission_id}/speaking/
        """
        test_result = get_object_or_404(
            TestResult.objects.select_related(
                'user_test__user', 'user_test__exam', 'section'
            ),
            pk=pk,
            section__type='speaking'
        )
        
        serializer = WriteManualReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create manual review
        manual_review, created = ManualReview.objects.get_or_create(
            test_result=test_result,
            section='speaking',
            defaults={
                'status': 'reviewing',
                'reviewer': request.user
            }
        )
        
        # Update manual review
        old_score = manual_review.total_score
        manual_review.total_score = serializer.validated_data['total_score']
        manual_review.status = 'checked'
        manual_review.reviewer = request.user
        manual_review.reviewed_at = timezone.now()
        manual_review.save()
        
        # Create review log for total score change
        ReviewLog.objects.create(
            manual_review=manual_review,
            reviewer=request.user,
            action='update_total_score',
            old_score=old_score,
            new_score=manual_review.total_score,
            comment=f"Speaking score updated by {request.user.get_full_name()}"
        )
        
        # Create or update question scores and add to review log
        for question_num, data in serializer.validated_data['question_scores'].items():
            score = float(data['score'])
            comment = data.get('comment', '')
            
            # Get or create question score
            question_score, created = QuestionScore.objects.get_or_create(
                manual_review=manual_review,
                question_number=int(question_num),
                defaults={
                    'score': score,
                    'comment': comment
                }
            )
            
            if not created:
                # Log old score before updating
                old_q_score = question_score.score
                question_score.score = score
                question_score.comment = comment
                question_score.save()
                
                # Create review log for question score change
                ReviewLog.objects.create(
                    manual_review=manual_review,
                    reviewer=request.user,
                    action='update_question_score',
                    question_number=int(question_num),
                    old_score=old_q_score,
                    new_score=score,
                    comment=f"Speaking Q{question_num} score updated by {request.user.get_full_name()}"
                )
            else:
                # Create review log for new question score
                ReviewLog.objects.create(
                    manual_review=manual_review,
                    reviewer=request.user,
                    action='create_question_score',
                    question_number=int(question_num),
                    new_score=score,
                    comment=f"Speaking Q{question_num} score created by {request.user.get_full_name()}"
                )
        
        # Handle notifications to the user if requested
        if serializer.validated_data.get('notified', True):
            # This would typically call a notification service
            # For now, we'll just log it
            ReviewLog.objects.create(
                manual_review=manual_review,
                reviewer=request.user,
                action='notify_user',
                comment=f"User notified about speaking score by {request.user.get_full_name()}"
            )
            
            # TODO: Implement actual notification here - Telegram/Email/etc.
            # Example: send_notification_to_user(test_result.user_test.user, 'speaking', manual_review.total_score)
        
        return Response({'status': 'success', 'message': 'Speaking scores updated successfully'})
    
    @action(detail=True, methods=['get'], url_path='media')
    def get_media(self, request, pk=None):
        """
        Get all media for a specific submission
        GET /api/admin/submissions/{submission_id}/media/
        """
        test_result = get_object_or_404(
            TestResult.objects.select_related(
                'user_test__user', 'user_test__exam', 'section'
            ),
            pk=pk
        )
        
        # Get all media for this test result's user_test
        media = {}
        
        # Get test results for writing and speaking
        test_results = TestResult.objects.filter(
            user_test=test_result.user_test,
            section__type__in=['writing', 'speaking']
        )
        
        # Get all media for these test results
        for tr in test_results:
            submission_media = SubmissionMedia.objects.filter(test_result=tr)
            
            if submission_media.exists():
                section_type = tr.section.type
                if section_type not in media:
                    media[section_type] = {}
                
                for sm in submission_media:
                    if sm.question_number not in media[section_type]:
                        media[section_type][sm.question_number] = []
                    
                    file_url = request.build_absolute_uri(sm.file.url) if sm.file else None
                    
                    media[section_type][sm.question_number].append({
                        'id': sm.id,
                        'file_url': file_url,
                        'file_type': sm.file_type,
                        'uploaded_at': sm.uploaded_at
                    })
        
        return Response(media)