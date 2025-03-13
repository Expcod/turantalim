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

class UserTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = '__all__'

    def create(self, validated_data):
        user_test = validated_data['user_test']  # `user` va `test` emas, `user_test` olinadi

        # `user_test` orqali `user` va `test`ni olish
        user = user_test.user
        test = user_test.test

        # UserTestResult obyektini yaratamiz yoki mavjudini olamiz
        user_test_result, created = TestResult.objects.get_or_create(
            user_test=user_test,
            defaults={'status': False}  # `status='in_progress'` emas, `False` bo‘lishi kerak
        )

        if not created and user_test_result.status:  # Agar `status=True` bo‘lsa, yangisini yaratamiz
            user_test_result.delete()
            user_test_result = TestResult.objects.create(user_test=user_test, status=False)

        return user_test_result




class MultilevelOptionSerializer(serializers.ModelSerializer):
    is_selected = serializers.SerializerMethodField()
    class Meta:
        model = Option
        fields = ["id", "text", "is_selected"]

    def get_is_selected(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        test_result = self.context.get('test_result')
        print(user, test_result)
        if not user or not test_result:
            return False

        question = self.context.get('question')
        if question:
            return UserAnswer.objects.filter(
                test_result=test_result,
                question=question,
                user_option=obj
            ).exists()
        return False


class MultilevelQuestionSerializer(serializers.ModelSerializer):
    options = MultilevelOptionSerializer(many=True, source='option_set')
    user_answer = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "picture", "has_options", "user_answer", "options"]

    def get_user_answer(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        test_result = self.context.get('test_result')

        if not user or not test_result:
            return None  # Default if no context

        # Fetch user_answer from UserAnswer for this question
        user_answer = UserAnswer.objects.filter(
            test_result=test_result,
            question=obj
        ).values_list('user_answer', flat=True).first()

        # Return user_answer if it exists and question has no options
        return user_answer if not obj.has_options else None


class MultilevelTestSerializer(serializers.ModelSerializer):
    questions = MultilevelQuestionSerializer(many=True, source='question_set')
    class Meta:
        model = Test
        fields = ["id", "title", "description", "picture", "audio", "options", "sample", "text_title","text","constraints", "questions"]


class MultilevelSectionSerializer(serializers.ModelSerializer):
    tests = MultilevelTestSerializer(many=True, source='test_set')
    language = LanguageSerializer()
    class Meta:
        model = Section
        fields = ["id", "type", "language", "title", "description", "tests"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        # Get the current active test_result for the user
        test_result = TestResult.objects.filter(
            user_test__user=user
        ).exclude(status="ended", user_test__status='ended').last()
        context['test_result'] = test_result
        return context


class TestCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ["id", "test_result", "question", "user_option", "user_answer", "is_correct"]
        read_only_fields = ["id", "test_result", "is_correct"]
    
    def create(self, validated_data):
        user_answer_instance = UserAnswer.objects.create(**validated_data)
        return user_answer_instance
    
# user test natijasini ko'rish uchun
    
class UserTestResultSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user_test.user.get_full_name")  # Foydalanuvchi ismi
    test_title = serializers.CharField(source="user_test.test.title")  # Test nomi
    language = serializers.CharField(source="language.name", default="Unknown")  # Til
    section = serializers.CharField(source="section.name", default="Unknown")  # Bo‘lim
    status = serializers.BooleanField()  # Test statusi (Bajargan yoki yo‘q)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # Sanani formatlash

    class Meta:
        model = TestResult
        fields = ['id', 'user', 'test_title', 'language', 'section', 'status', 'created_at']
