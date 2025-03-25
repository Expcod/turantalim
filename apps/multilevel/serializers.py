from rest_framework import serializers
from .models import *
from apps.main.serializers import LanguageSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.users.models import *

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = '__all__'

    def get_options(self, obj):
        return obj.get_options()

class QuestionSerializer(serializers.ModelSerializer):
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

# TestResult yaratish uchun serializer (eski nom saqlanadi)
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

    options = serializers.SerializerMethodField()
    user_answer = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "picture", "has_options", "user_answer", "options"]

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
    def get_questions(self, obj):
        return MultilevelQuestionSerializer(
            obj.question_set.all(),
            many=True,
            context=self.context
        ).data

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url) if request else obj.picture.url
        return None

    def get_audio(self, obj):
        request = self.context.get("request")
        if obj.audio:
            return request.build_absolute_uri(obj.audio.url) if request else obj.audio.url
        return None

    questions = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    def get_options(self, obj):
        return obj.get_options()

    class Meta:
        model = Test
        fields = ["id", "title", "description", "picture", "audio", "options", "sample", "text_title", "text", "constraints", "questions"]

class MultilevelSectionSerializer(serializers.ModelSerializer):
    def get_tests(self, obj):
        return MultilevelTestSerializer(
            obj.test_set.all(),
            many=True,
            context=self.context
        ).data

    tests = serializers.SerializerMethodField()
    language = LanguageSerializer()

    class Meta:
        model = Section
        fields = ["id", "type", "language", "title", "description", "tests", "level"]

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

# TestResult uchun yangi serializerlar
class TestResultDetailSerializer(serializers.ModelSerializer):
    section = serializers.CharField(source="section.title")
    language = serializers.CharField(source="language.name", default="Unknown")
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
        return round((correct / total * 100), 2) if total > 0 else 0

    def get_level(self, obj):
        percentage = self.get_percentage(obj)
        if percentage >= 85:
            return "C1"
        elif percentage >= 70:
            return "B2"
        elif percentage >= 55:
            return "B1"
        elif percentage >= 40:
            return "A2"
        elif percentage >= 20:
            return "A1"
        else:
            return "Below A1"

class TestResultListSerializer(serializers.ModelSerializer):
    section = serializers.CharField(source="section.title")
    language = serializers.CharField(source="language.name", default="Unknown")
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = ['id', 'section', 'language', 'status', 'start_time', 'end_time', 'percentage']

    def get_percentage(self, obj):
        total = Question.objects.filter(test__section=obj.section).count()
        correct = UserAnswer.objects.filter(test_result=obj, is_correct=True).count()
        return round((correct / total * 100), 2) if total > 0 else 0

class OverallTestResultSerializer(serializers.Serializer):
    listening = serializers.SerializerMethodField()
    reading = serializers.SerializerMethodField()
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

    def get_overall_percentage(self, obj):
        test_results = TestResult.objects.filter(user_test__user=obj, status='completed')
        if not test_results.exists():
            return 0
        total_percentage = sum(
            TestResultDetailSerializer(tr, context=self.context).get_percentage(tr)
            for tr in test_results
        )
        return round(total_percentage / test_results.count(), 2)

    def get_overall_level(self, obj):
        percentage = self.get_overall_percentage(obj)
        if percentage >= 85:
            return "C1"
        elif percentage >= 70:
            return "B2"
        elif percentage >= 55:
            return "B1"
        elif percentage >= 40:
            return "A2"
        elif percentage >= 20:
            return "A1"
        else:
            return "Below A1"
