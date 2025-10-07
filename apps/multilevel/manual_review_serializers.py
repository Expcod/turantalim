from rest_framework import serializers
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import (
    TestResult, UserTest, Section, Exam,
    SubmissionMedia, ManualReview, QuestionScore, ReviewLog
)

User = get_user_model()

# Create UserMiniSerializer here since we can't import it
class UserMiniSerializer(serializers.ModelSerializer):
    """Minimalistic User serializer"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class SubmissionMediaSerializer(serializers.ModelSerializer):
    """Serializer for media files (images/audio)"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SubmissionMedia
        fields = ['id', 'section', 'question_number', 'file_url', 'file_type', 'uploaded_at']
        
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None

class QuestionScoreSerializer(serializers.ModelSerializer):
    """Serializer for individual question scores"""
    class Meta:
        model = QuestionScore
        fields = ['id', 'question_number', 'score', 'comment']

class ReviewLogSerializer(serializers.ModelSerializer):
    """Serializer for review logs"""
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewLog
        fields = ['id', 'reviewer_name', 'action', 'question_number', 
                 'old_score', 'new_score', 'comment', 'created_at']
        
    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name()
        return None

class ManualReviewSerializer(serializers.ModelSerializer):
    """Serializer for manual review data"""
    question_scores = QuestionScoreSerializer(many=True, read_only=True)
    logs = ReviewLogSerializer(many=True, read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ManualReview
        fields = ['id', 'section', 'status', 'total_score', 
                 'reviewer_name', 'reviewed_at', 'question_scores', 'logs']
        
    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name()
        return None

class SectionMiniSerializer(serializers.ModelSerializer):
    """Minimalistic Section serializer"""
    class Meta:
        model = Section
        fields = ['id', 'title', 'type']

class ExamMiniSerializer(serializers.ModelSerializer):
    """Minimalistic Exam serializer"""
    class Meta:
        model = Exam
        fields = ['id', 'title', 'level']

class TestResultDetailSerializer(serializers.ModelSerializer):
    """Serializer for test result details"""
    section = SectionMiniSerializer(read_only=True)
    manual_review = ManualReviewSerializer(read_only=True)
    
    class Meta:
        model = TestResult
        fields = ['id', 'section', 'status', 'score', 'start_time', 
                 'end_time', 'manual_review']

class UserTestMiniSerializer(serializers.ModelSerializer):
    """Minimalistic UserTest serializer"""
    user = UserMiniSerializer(read_only=True)
    exam = ExamMiniSerializer(read_only=True)
    
    class Meta:
        model = UserTest
        fields = ['id', 'user', 'exam', 'status', 'score', 'created_at']

class SubmissionListSerializer(serializers.ModelSerializer):
    """Serializer for listing submissions that need manual review"""
    user = UserMiniSerializer(source='user_test.user', read_only=True)
    exam = ExamMiniSerializer(source='user_test.exam', read_only=True)
    sections = serializers.SerializerMethodField()
    writing_status = serializers.SerializerMethodField()
    speaking_status = serializers.SerializerMethodField()
    
    class Meta:
        model = TestResult
        fields = ['id', 'user', 'exam', 'sections', 'writing_status', 
                 'speaking_status', 'created_at']
        
    def get_sections(self, obj):
        # Return a list of section types that need manual review
        sections = []
        
        # Check if there's a writing section that needs review
        if obj.section.type == 'writing':
            sections.append('writing')
            
        # Check if there's a speaking section that needs review
        if obj.section.type == 'speaking':
            sections.append('speaking')
            
        return sections
    
    def get_writing_status(self, obj):
        if obj.section.type == 'writing':
            try:
                review = obj.manual_review
                return review.status
            except ManualReview.DoesNotExist:
                return 'pending'
        return None
    
    def get_speaking_status(self, obj):
        if obj.section.type == 'speaking':
            try:
                review = obj.manual_review
                return review.status
            except ManualReview.DoesNotExist:
                return 'pending'
        return None

class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a full submission with all sections"""
    user_test = UserTestMiniSerializer(read_only=True)
    listening_result = serializers.SerializerMethodField()
    reading_result = serializers.SerializerMethodField()
    writing_result = serializers.SerializerMethodField()
    speaking_result = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    
    class Meta:
        model = TestResult
        fields = ['id', 'user_test', 'listening_result', 'reading_result',
                 'writing_result', 'speaking_result', 'media']
    
    def get_listening_result(self, obj):
        # Get listening result for the same user_test
        listening_result = TestResult.objects.filter(
            user_test=obj.user_test,
            section__type='listening'
        ).first()
        
        if listening_result:
            return TestResultDetailSerializer(listening_result).data
        return None
    
    def get_reading_result(self, obj):
        # Get reading result for the same user_test
        reading_result = TestResult.objects.filter(
            user_test=obj.user_test,
            section__type='reading'
        ).first()
        
        if reading_result:
            return TestResultDetailSerializer(reading_result).data
        return None
    
    def get_writing_result(self, obj):
        # Get writing result for the same user_test
        writing_result = TestResult.objects.filter(
            user_test=obj.user_test,
            section__type='writing'
        ).first()
        
        if writing_result:
            return TestResultDetailSerializer(writing_result).data
        return None
    
    def get_speaking_result(self, obj):
        # Get speaking result for the same user_test
        speaking_result = TestResult.objects.filter(
            user_test=obj.user_test,
            section__type='speaking'
        ).first()
        
        if speaking_result:
            return TestResultDetailSerializer(speaking_result).data
        return None
    
    def get_media(self, obj):
        # Get all media for this test result's user_test
        # Group them by section and question_number
        media = {}
        
        # Get test results for writing and speaking
        test_results = TestResult.objects.filter(
            user_test=obj.user_test,
            section__type__in=['writing', 'speaking']
        )
        
        # Get all media for these test results
        for tr in test_results:
            submission_media = SubmissionMedia.objects.filter(test_result=tr)
            
            for sm in submission_media:
                if sm.section not in media:
                    media[sm.section] = {}
                
                if sm.question_number not in media[sm.section]:
                    media[sm.section][sm.question_number] = []
                
                # Use the serializer to get the full data
                serializer = SubmissionMediaSerializer(
                    sm, 
                    context={'request': self.context.get('request')}
                )
                media[sm.section][sm.question_number].append(serializer.data)
        
        return media

class WriteManualReviewSerializer(serializers.Serializer):
    """Serializer for updating manual review scores"""
    question_scores = serializers.DictField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        required=True
    )
    total_score = serializers.FloatField(required=True)
    notified = serializers.BooleanField(default=True)
    
    def validate_question_scores(self, value):
        # Validate that all question scores are numbers between 0-100
        for question_num, data in value.items():
            if 'score' not in data:
                raise serializers.ValidationError(f"Question {question_num} missing score")
            
            try:
                score = float(data['score'])
                if score < 0 or score > 100:
                    raise serializers.ValidationError(
                        f"Question {question_num} score must be between 0-100"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Question {question_num} score must be a number"
                )
        
        return value
    
    def validate_total_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Total score must be between 0-100")
        return value