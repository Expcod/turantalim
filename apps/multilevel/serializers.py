from rest_framework import serializers
from .models import Exam, Section, Test, Question, Option, UserTest, TestResult, UserAnswer, TestImage, QuestionImage
from apps.main.serializers import LanguageSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.users.models import *
import tempfile
import os
import logging
from django.db.models import Avg
from .multilevel_score import get_test_score, get_level_from_score, get_tys_listening_score, get_tys_reading_score

logger = logging.getLogger(__name__)

# Asosiy model serializer'lari
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title', 'level', 'language']

# Imtihonlar ro'yxati uchun alohida serializer
class ExamListSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source='language.name', read_only=True)
    
    class Meta:
        model = Exam
        fields = ['id', 'title', 'description', 'level', 'language', 'price', 'order_id']

class TestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestImage
        fields = ['id', 'image', 'order']

class TestSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    images = TestImageSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = '__all__'

    def get_options(self, obj):
        return obj.get_options()

class QuestionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionImage
        fields = ['id', 'image', 'order']

class QuestionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = '__all__'

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'

class UserTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTest
        fields = '__all__'

# TestResult yaratish uchun serializer
class TestResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = '__all__'

    def create(self, validated_data):
        user_test = validated_data['user_test']
        user = user_test.user
        user_test_result, created = TestResult.objects.get_or_create(
            user_test=user_test,
            defaults={'status': 'started'}
        )
        if not created and user_test_result.status == 'completed':
            user_test_result.delete()
            user_test_result = TestResult.objects.create(user_test=user_test, status='started')
        return user_test_result

# Multilevel serializer'lari
class MultilevelOptionSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = ["id", "text", "is_selected"]

    def get_is_selected(self, obj):
        test_result = self.context.get('test_result')
        if not test_result:
            return False
        question = self.context.get('question') or obj.question
        if question:
            return UserAnswer.objects.filter(
                test_result=test_result,
                question=question,
                user_option=obj
            ).exists()
        return False

class MultilevelQuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    user_answer = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "picture",
            "images",
            "has_options",
            "user_answer",
            "options",
            "preparation_time",
            "response_time",
        ]

    def get_options(self, obj):
        return MultilevelOptionSerializer(
            obj.option_set.all(),
            many=True,
            context=self.context
        ).data

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url) if request else obj.picture.url
        return None

    def get_images(self, obj):
        request = self.context.get("request")
        images = obj.get_all_images()
        image_data = []
        for img in images:
            image_data.append({
                'id': img.id,
                'image': request.build_absolute_uri(img.image.url) if request else img.image.url,
                'order': img.order
            })
        return image_data

    def get_user_answer(self, obj):
        test_result = self.context.get('test_result')
        if not test_result:
            return None
        user_answer = UserAnswer.objects.filter(
            test_result=test_result,
            question=obj
        ).values_list('user_answer', flat=True).first()
        return user_answer if not obj.has_options else None

class MultilevelTestSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    order_id = serializers.IntegerField(source='order', read_only=True)
    response_time = serializers.SerializerMethodField()
    upload_time = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = ["id", "order_id", "title", "description", "picture", "images", "audio", "options", "sample", "text_title", "text", "constraints", "questions", "response_time", "upload_time"]

    def get_questions(self, obj):
        return MultilevelQuestionSerializer(
            obj.question_set.all().order_by('id'),
            many=True,
            context=self.context
        ).data

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url) if request else obj.picture.url
        return None

    def get_images(self, obj):
        request = self.context.get("request")
        images = obj.get_all_images()
        image_data = []
        for img in images:
            image_data.append({
                'id': img.id,
                'image': request.build_absolute_uri(img.image.url) if request else img.image.url,
                'order': img.order
            })
        return image_data

    def get_audio(self, obj):
        request = self.context.get("request")
        if obj.audio:
            return request.build_absolute_uri(obj.audio.url) if request else obj.audio.url
        return None

    def get_options(self, obj):
        return obj.get_options()

    def get_response_time(self, obj):
        # Writing test uchun response_time maydoni
        if hasattr(obj, 'response_time') and obj.response_time:
            return obj.response_time
        return None

    def get_upload_time(self, obj):
        # Writing test uchun upload_time maydoni
        if hasattr(obj, 'upload_time') and obj.upload_time:
            return obj.upload_time
        return None

class MultilevelSectionSerializer(serializers.ModelSerializer):
    tests = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    exam = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "exam", "type", "language", "title", "description", "tests", "level"]

    def get_tests(self, obj):
        return MultilevelTestSerializer(
            obj.test_set.all().order_by('order'),
            many=True,
            context=self.context
        ).data

    def get_language(self, obj):
        if obj.exam and obj.exam.language:
            return LanguageSerializer(obj.exam.language, context=self.context).data
        return None

    def get_level(self, obj):
        return obj.exam.level if obj.exam else None

    def get_exam(self, obj):
        return ExamSerializer(obj.exam, context=self.context).data if obj.exam else None

# TestCheckSerializer (Listening va Reading uchun)
class TestCheckSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    user_option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all(), required=False, allow_null=True)
    user_answer = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    test_result_id = serializers.SerializerMethodField()

    class Meta:
        model = UserAnswer
        fields = ['question', 'user_option', 'user_answer', 'is_correct', 'test_result', 'test_result_id']
        read_only_fields = ['is_correct', 'test_result']

    def get_test_result_id(self, obj):
        return obj.test_result.id if obj.test_result else None

    def validate(self, data):
        question = data.get('question')
        user_option = data.get('user_option')
        user_answer = data.get('user_answer')

        if question.has_options and not user_option:
            raise serializers.ValidationError("Optionli savol uchun variant tanlash kerak.")
        if not question.has_options and not user_answer:
            raise serializers.ValidationError("Optionsiz savol uchun javob kiritish kerak.")
        return data

class BulkTestCheckSerializer(serializers.Serializer):
    test_result_id = serializers.IntegerField(required=False, allow_null=True)
    answers = TestCheckSerializer(many=True)

    def validate(self, data):
        question_ids = [answer['question'].id for answer in data['answers']]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Bir xil savol ID si bir nechta kiritilgan.")
        return data

# Writing va Speaking javoblarini formatlash uchun serializer
class TestCheckResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    result = serializers.CharField()
    score = serializers.IntegerField()
    test_completed = serializers.BooleanField()
    user_answer = serializers.CharField(required=False, allow_null=True)
    question_text = serializers.CharField(required=False, allow_null=True)

class SpeakingTestResponseSerializer(serializers.Serializer):
    answers = serializers.ListField(child=TestCheckResponseSerializer())
    test_completed = serializers.BooleanField()
    score = serializers.IntegerField(required=False, allow_null=True)

# TestResult serializer'lari
class TestResultDetailSerializer(serializers.ModelSerializer):
    section = serializers.CharField(source="section.title")
    language = serializers.CharField(source="user_test.exam.language.name", default="Unknown")
    total_questions = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    incorrect_answers = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = [
            'id', 'section', 'language', 'status', 'start_time', 'end_time',
            'total_questions', 'correct_answers', 'incorrect_answers', 'percentage', 'level'
        ]

    def get_total_questions(self, obj):
        return Question.objects.filter(test__section=obj.section).count()

    def get_correct_answers(self, obj):
        return UserAnswer.objects.filter(test_result=obj, is_correct=True).count()

    def get_incorrect_answers(self, obj):
        total = self.get_total_questions(obj)
        correct = self.get_correct_answers(obj)
        return total - correct

    def get_percentage(self, obj):
        total = self.get_total_questions(obj)
        correct = self.get_correct_answers(obj)
        
        # Use multilevel or TYS scoring for listening and reading tests
        section_type = obj.section.type.lower()
        if section_type in ['listening', 'reading']:
            try:
                # Get exam level for proper scoring
                exam_level = obj.user_test.exam.level
                if exam_level.lower() == 'tys':
                    if section_type == 'listening':
                        return get_tys_listening_score(correct, total)
                    elif section_type == 'reading':
                        return get_tys_reading_score(correct, total)
                else:
                    return get_test_score(section_type, correct)
            except ValueError:
                return 0
        else:
            # For writing and speaking, return stored section score (0-75 or 0-25)
            return getattr(obj, 'score', 0) or 0

    def get_level(self, obj):
        section_type = obj.section.type.lower()
        exam_level = obj.user_test.exam.level
        
        if section_type in ['listening', 'reading']:
            correct = self.get_correct_answers(obj)
            total = self.get_total_questions(obj)
            
            if exam_level.lower() == 'tys':
                if section_type == 'listening':
                    score = get_tys_listening_score(correct, total)
                elif section_type == 'reading':
                    score = get_tys_reading_score(correct, total)
            else:
                score = get_test_score(section_type, correct)
        else:
            score = getattr(obj, 'score', 0) or 0

        return get_level_from_score(score, exam_level)

class TestResultListSerializer(serializers.ModelSerializer):
    section = serializers.CharField(source="section.title")
    language = serializers.CharField(source="user_test.exam.language.name", default="Unknown")
    level = serializers.CharField(source="user_test.exam.level", help_text="Exam level (multilevel, a1, a2, b1, b2, c1)")
    percentage = serializers.SerializerMethodField(help_text="All sections: multilevel score (0-75).")

    class Meta:
        model = TestResult
        fields = ['id', 'section', 'level', 'language', 'status', 'start_time', 'end_time', 'percentage']

    def get_percentage(self, obj):
        # Listening/Reading: compute score from correct answers using tables
        section_type = obj.section.type.lower()
        if section_type in ['listening', 'reading']:
            total = Question.objects.filter(test__section=obj.section).count()
            correct = UserAnswer.objects.filter(test_result=obj, is_correct=True).count()
            if total <= 0:
                return 0
            try:
                # Get exam level for proper scoring
                exam_level = obj.user_test.exam.level
                if exam_level.lower() == 'tys':
                    if section_type == 'listening':
                        return get_tys_listening_score(correct, total)
                    elif section_type == 'reading':
                        return get_tys_reading_score(correct, total)
                else:
                    return get_test_score(section_type, correct)
            except ValueError:
                return 0
        # Writing/Speaking: use stored section score (sum of parts, max 75 or 25)
        return getattr(obj, 'score', 0) or 0

class OverallTestResultSerializer(serializers.Serializer):
    listening = serializers.SerializerMethodField()
    reading = serializers.SerializerMethodField()
    writing = serializers.SerializerMethodField()
    speaking = serializers.SerializerMethodField()
    overall_percentage = serializers.SerializerMethodField()
    overall_level = serializers.SerializerMethodField()

    def get_listening(self, obj):
        test_result = TestResult.objects.filter(user_test__user=obj, section__type='listening').last()
        if test_result:
            return TestResultDetailSerializer(test_result, context=self.context).data
        return None

    def get_reading(self, obj):
        test_result = TestResult.objects.filter(user_test__user=obj, section__type='reading').last()
        if test_result:
            return TestResultDetailSerializer(test_result, context=self.context).data
        return None

    def get_writing(self, obj):
        test_result = TestResult.objects.filter(user_test__user=obj, section__type='writing').last()
        if test_result:
            return TestResultDetailSerializer(test_result, context=self.context).data
        return None

    def get_speaking(self, obj):
        test_result = TestResult.objects.filter(user_test__user=obj, section__type='speaking').last()
        if test_result:
            return TestResultDetailSerializer(test_result, context=self.context).data
        return None

    def get_overall_percentage(self, obj):
        section_types = ['listening', 'reading', 'writing', 'speaking']
        percentages = []
        
        for section_type in section_types:
            test_result = TestResult.objects.filter(user_test__user=obj, section__type=section_type).last()
            if test_result:
                percentage = TestResultDetailSerializer(test_result, context=self.context).get_percentage(test_result)
                percentages.append(percentage)

        return round(sum(percentages) / len(percentages), 2) if percentages else 0

    def get_overall_level(self, obj):
        # Get individual section results to calculate overall level properly
        section_types = ['listening', 'reading', 'writing', 'speaking']
        scores = []
        
        for section_type in section_types:
            test_result = TestResult.objects.filter(user_test__user=obj, section__type=section_type).last()
            if test_result:
                if section_type in ['listening', 'reading']:
                    # For listening and reading, use score-based level
                    correct = UserAnswer.objects.filter(test_result=test_result, is_correct=True).count()
                    try:
                        score = get_test_score(section_type, correct)
                        level_score = get_level_from_score(score)
                        # Convert level to numeric for averaging
                        level_numeric = self._level_to_numeric(level_score)
                        scores.append(level_numeric)
                    except ValueError:
                        # Fallback to percentage-based calculation
                        percentage = TestResultDetailSerializer(test_result, context=self.context).get_percentage(test_result)
                        level_numeric = self._percentage_to_level_numeric(percentage)
                        scores.append(level_numeric)
                else:
                    # For writing and speaking, use percentage-based level
                    percentage = TestResultDetailSerializer(test_result, context=self.context).get_percentage(test_result)
                    level_numeric = self._percentage_to_level_numeric(percentage)
                    scores.append(level_numeric)
        
        if not scores:
            return "Below A1"
        
        # Calculate average level
        avg_level_numeric = sum(scores) / len(scores)
        return self._numeric_to_level(avg_level_numeric)
    
    def _level_to_numeric(self, level):
        """Convert CEFR level to numeric value for averaging"""
        level_map = {
            "C1": 5,
            "B2": 4,
            "B1": 3,
            "A2": 2,
            "A1": 1,
            "Below A1": 0
        }
        return level_map.get(level, 0)
    
    def _percentage_to_level_numeric(self, percentage):
        """Convert percentage to numeric level for averaging"""
        if percentage >= 85:
            return 5  # C1
        elif percentage >= 70:
            return 4  # B2
        elif percentage >= 55:
            return 3  # B1
        elif percentage >= 40:
            return 2  # A2
        elif percentage >= 20:
            return 1  # A1
        else:
            return 0  # Below A1
    
    def _numeric_to_level(self, numeric_level):
        """Convert numeric level back to CEFR level"""
        if numeric_level >= 4.5:
            return "C1"
        elif numeric_level >= 3.5:
            return "B2"
        elif numeric_level >= 2.5:
            return "B1"
        elif numeric_level >= 1.5:
            return "A2"
        elif numeric_level >= 0.5:
            return "A1"
        else:
            return "Below A1"