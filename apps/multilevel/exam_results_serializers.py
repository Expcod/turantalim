from rest_framework import serializers
from .models import UserTest, TestResult, Section
from .multilevel_score import get_level_from_score


class SectionResultSerializer(serializers.Serializer):
    """Har bir section natijasi uchun serializer"""
    section_name = serializers.CharField()
    score = serializers.IntegerField()
    max_score = serializers.IntegerField()
    status = serializers.CharField()
    completed_at = serializers.DateTimeField(allow_null=True)


class ExamInfoSerializer(serializers.Serializer):
    """Imtihon ma'lumotlari uchun serializer"""
    exam_id = serializers.IntegerField()
    exam_name = serializers.CharField()
    exam_level = serializers.CharField()
    language = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)


class OverallResultSerializer(serializers.Serializer):
    """Umumiy natija uchun serializer"""
    total_score = serializers.IntegerField()
    max_possible_score = serializers.IntegerField()
    average_score = serializers.FloatField()
    level = serializers.CharField()
    level_description = serializers.CharField()
    completed_sections = serializers.IntegerField()
    total_sections = serializers.IntegerField()
    is_complete = serializers.BooleanField()


class LevelRangesSerializer(serializers.Serializer):
    """Daraja oralig'lari uchun serializer"""
    B1 = serializers.CharField()
    B2 = serializers.CharField()
    C1 = serializers.CharField()


class MultilevelTysExamResultSerializer(serializers.Serializer):
    """Multilevel va TYS imtihon natijasi uchun asosiy serializer"""
    success = serializers.BooleanField()
    exam_info = ExamInfoSerializer()
    section_results = serializers.DictField(
        child=SectionResultSerializer()
    )
    overall_result = OverallResultSerializer()
    level_ranges = LevelRangesSerializer()


class ExamListItemSerializer(serializers.Serializer):
    """Imtihon ro'yxati elementi uchun serializer"""
    user_test_id = serializers.IntegerField()
    exam_name = serializers.CharField()
    exam_level = serializers.CharField()
    language = serializers.CharField()
    status = serializers.CharField()
    total_score = serializers.IntegerField()
    average_score = serializers.FloatField()
    level = serializers.CharField()
    completed_sections = serializers.IntegerField()
    total_sections = serializers.IntegerField()
    is_complete = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)


class MultilevelTysExamListSerializer(serializers.Serializer):
    """Multilevel va TYS imtihonlar ro'yxati uchun serializer"""
    success = serializers.BooleanField()
    total_exams = serializers.IntegerField()
    exams = ExamListItemSerializer(many=True)


class ErrorResponseSerializer(serializers.Serializer):
    """Xato response uchun serializer"""
    success = serializers.BooleanField()
    error = serializers.CharField()


# Model-based serializers for more complex operations
class TestResultDetailSerializer(serializers.ModelSerializer):
    """TestResult model uchun batafsil serializer"""
    section_name = serializers.CharField(source='section.title')
    section_type = serializers.CharField(source='section.type')
    exam_name = serializers.CharField(source='user_test.exam.title')
    exam_level = serializers.CharField(source='user_test.exam.level')
    language = serializers.CharField(source='user_test.exam.language.name', default='Unknown')
    
    class Meta:
        model = TestResult
        fields = [
            'id', 'section_name', 'section_type', 'exam_name', 'exam_level', 
            'language', 'status', 'score', 'start_time', 'end_time', 'created_at'
        ]


class UserTestSummarySerializer(serializers.ModelSerializer):
    """UserTest model uchun qisqacha serializer"""
    exam_name = serializers.CharField(source='exam.title')
    exam_level = serializers.CharField(source='exam.level')
    language = serializers.CharField(source='exam.language.name', default='Unknown')
    total_score = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    completed_sections = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()
    
    class Meta:
        model = UserTest
        fields = [
            'id', 'exam_name', 'exam_level', 'language', 'status', 
            'total_score', 'average_score', 'level', 'completed_sections', 
            'is_complete', 'created_at'
        ]
    
    def get_total_score(self, obj):
        """Umumiy ballni hisoblash"""
        test_results = TestResult.objects.filter(
            user_test=obj,
            status='completed'
        )
        return sum(result.score for result in test_results)
    
    def get_average_score(self, obj):
        """O'rtacha ballni hisoblash"""
        total_score = self.get_total_score(obj)
        completed_sections = TestResult.objects.filter(
            user_test=obj,
            status='completed'
        ).count()
        return round(total_score / 4, 2) if completed_sections == 4 else 0
    
    def get_level(self, obj):
        """Darajani aniqlash"""
        average_score = self.get_average_score(obj)
        return get_level_from_score(average_score)
    
    def get_completed_sections(self, obj):
        """Tugatilgan sectionlar soni"""
        return TestResult.objects.filter(
            user_test=obj,
            status='completed'
        ).count()
    
    def get_is_complete(self, obj):
        """Imtihon tugatilganmi"""
        return self.get_completed_sections(obj) == 4
