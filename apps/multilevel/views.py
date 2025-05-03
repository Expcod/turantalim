from datetime import timedelta
from random import choice
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_spectacular.utils import extend_schema
from drf_yasg import openapi
from .models import *
from apps.payment.models import *
from .serializers import *
from .utils import *
from django.utils import timezone
from django.db.models import Avg

class TestRequestApiView(APIView):
    @swagger_auto_schema(
        operation_summary="Test so'rash",
        manual_parameters=[
            openapi.Parameter('language', openapi.IN_QUERY, description="Tilni tanlang (Language ID orqali)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('level', openapi.IN_QUERY, description="Test darajasini tanlang!", type=openapi.TYPE_STRING, enum=['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel']),
            openapi.Parameter('test', openapi.IN_QUERY, description="Test turini tanlang: Listening, Writing, Reading, Speaking", type=openapi.TYPE_STRING, enum=['listening', 'writing', 'reading', 'speaking']),
            openapi.Parameter('exam_id', openapi.IN_QUERY, description="Imtihonni tanlang (Exam ID orqali)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: MultilevelSectionSerializer()},
    )
    def get(self, request):
        language_id = request.GET.get('language')
        level_choice = request.GET.get('level')
        test_type = request.GET.get('test')
        exam_id = request.GET.get('exam_id')

        # Majburiy parametrlarni tekshirish
        if not language_id or not test_type or not level_choice:
            return Response({"error": "Language ID, Test turi va Daraja kiritilishi shart!"}, status=400)

        try:
            language = Language.objects.get(pk=language_id)
        except Language.DoesNotExist:
            return Response({"error": "Til topilmadi!"}, status=404)

        LEVEL_CHOICES = ['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel']
        if level_choice not in LEVEL_CHOICES:
            return Response({"error": f"Noto'g'ri daraja! Daraja quyidagilardan biri bo'lishi kerak: {', '.join(LEVEL_CHOICES)}."}, status=400)
        
        TEST_TYPES = ['listening', 'writing', 'reading', 'speaking']
        if test_type not in TEST_TYPES:
            return Response({"error": f"Noto'g'ri test turi! Test turi quyidagilardan biri bo'lishi kerak: {', '.join(TEST_TYPES)}."}, status=400)

        # Exam tanlash
        if exam_id:
            try:
                exam = Exam.objects.get(pk=exam_id, language=language, level=level_choice)
            except Exam.DoesNotExist:
                return Response({"error": "Tanlangan Exam topilmadi yoki mos emas!"}, status=404)
        else:
            exams = Exam.objects.filter(language=language, level=level_choice)
            if not exams.exists():
                return Response({"error": f"{level_choice} darajasida {language.name} tilida imtihon mavjud emas!"}, status=404)
            return Response({
                "message": "Iltimos, Exam tanlang!",
                "exams": [{"id": exam.id, "title": exam.title} for exam in exams]
            }, status=200)

        # Faol UserTest ni tekshirish yoki yangi yaratish
        existing_user_test = UserTest.objects.filter(
            user=request.user,
            exam=exam,
            status='started'
        ).first()

        if not existing_user_test:
            # Barcha eski faol testlarni yakunlash
            UserTest.objects.filter(user=request.user, status='started').update(status='completed')
            TestResult.objects.filter(user_test__user=request.user, status='started').update(status='completed')
            # Yangi UserTest yaratish
            existing_user_test = UserTest.objects.create(
                user=request.user,
                exam=exam,
                language=language,
                status='started'
            )

        # Faol TestResult ni tekshirish yoki yangi yaratish
        existing_test_result = TestResult.objects.filter(
            user_test=existing_user_test,
            section__type=test_type,
            status='started'
        ).last()

        if existing_test_result:
            section = existing_test_result.section
        else:
            all_sections = Section.objects.filter(exam=exam, type=test_type)
            if not all_sections.exists():
                return Response({"error": f"Ushbu imtihonda {test_type} turidagi testlar mavjud emas!"}, status=404)

            used_section_ids = TestResult.objects.filter(user_test=existing_user_test).values_list('section_id', flat=True).distinct()
            unused_sections = all_sections.exclude(id__in=used_section_ids)

            if unused_sections.exists():
                selected_section = choice(unused_sections)
            else:
                selected_section = choice(all_sections)

            existing_test_result = TestResult.objects.create(
                user_test=existing_user_test,
                section=selected_section,
                status='started',
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=selected_section.duration)
            )
            section = selected_section

        serializer = MultilevelSectionSerializer(
            section,
            context={'test_result': existing_test_result.pk, 'request': request}
        )
        test_data = {
            "test_type": test_type,
            "duration": section.duration,
            "part": serializer.data,
            "test_result_id": existing_test_result.id
        }
        return Response(test_data)

class TestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_error(self, message, status_code):
        return Response({"error": message}, status=status_code)

    @swagger_auto_schema(
        operation_summary="Foydalanuvchi javoblarini tekshirish",
        operation_description="Listening yoki Reading testlari uchun javoblarni tekshiradi.",
        request_body=BulkTestCheckSerializer,
        responses={
            201: TestCheckSerializer(many=True),
            200: TestCheckSerializer(many=True),
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas")
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = BulkTestCheckSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return self.handle_error(serializer.errors, status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        # Birinchi savoldan Exam ni aniqlash
        question = answers_data[0]['question']
        exam = question.test.section.exam

        # TestResult ni aniqlash
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
        except TestResult.DoesNotExist:
            return self.handle_error("TestResult topilmadi yoki faol emas!", status.HTTP_403_FORBIDDEN)

        # Writing yoki Speaking bo'lsa, bu endpoint ishlatilmaydi
        if test_result.section.type in ['writing', 'speaking']:
            return self.handle_error(
                "Writing yoki Speaking testlari uchun /testcheck/writing/ yoki /testcheck/speaking/ endpointlaridan foydalaning!",
                status.HTTP_400_BAD_REQUEST
            )

        # Javoblarni qayta ishlash
        responses = self.process_answers(user, test_result, answers_data)

        # Testni yakunlash
        final_response = self.finalize_test(user, test_result, responses)
        status_code = status.HTTP_201_CREATED if any(r.get('is_new') for r in responses) else status.HTTP_200_OK
        return Response(final_response, status=status_code)

    def process_answers(self, user, test_result, answers_data):
        existing_answers = {ua.question_id: ua for ua in UserAnswer.objects.filter(test_result=test_result)}
        
        new_answers = []
        update_answers = []

        for answer_data in answers_data:
            question = answer_data['question']
            user_option = answer_data.get('user_option')
            user_answer = answer_data.get('user_answer')

            is_correct = False
            if question.has_options:
                correct_option = Option.objects.filter(question=question, is_correct=True).first()
                is_correct = correct_option == user_option if user_option else False
            else:
                is_correct = (
                    question.answer.strip().lower() == user_answer.strip().lower()
                    if user_answer and question.answer else False
                )

            existing_answer = existing_answers.get(question.id)
            if existing_answer:
                existing_answer.user_option = user_option
                existing_answer.user_answer = user_answer
                existing_answer.is_correct = is_correct
                update_answers.append(existing_answer)
            else:
                new_answer = UserAnswer(
                    test_result=test_result,
                    question=question,
                    user_option=user_option,
                    user_answer=user_answer,
                    is_correct=is_correct
                )
                new_answers.append(new_answer)

        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)
        if update_answers:
            UserAnswer.objects.bulk_update(update_answers, ['user_option', 'user_answer', 'is_correct'])

        all_answers = UserAnswer.objects.filter(
            test_result=test_result,
            question__in=[answer_data['question'] for answer_data in answers_data]
        )
        response_serializer = TestCheckSerializer(all_answers, many=True, context={'request': self.request})
        responses = [
            {"data": data, "is_new": answer.question_id not in existing_answers}
            for data, answer in zip(response_serializer.data, all_answers)
        ]

        return responses

    def finalize_test(self, user, test_result, responses):
        response_data = [r["data"] for r in responses]
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()

        if total_questions == answered_questions:
            correct_count = UserAnswer.objects.filter(test_result=test_result, is_correct=True).count()
            score = (correct_count / total_questions * 100) if total_questions > 0 else 0

            UserAnswer.objects.filter(test_result=test_result).update(score=score)

            # Barcha bo'limlar tugaganligini tekshirish
            user_test = test_result.user_test
            all_sections = Section.objects.filter(exam=user_test.exam)
            answered_sections = TestResult.objects.filter(user_test=user_test).distinct()

            required_types = ['listening', 'reading', 'writing', 'speaking']
            answered_types = [tr.section.type for tr in answered_sections]

            if all(section_type in answered_types for section_type in required_types):
                total_score = 0
                section_count = 0

                for section in all_sections:
                    tr = TestResult.objects.filter(user_test=user_test, section=section).last()
                    if tr:
                        section_score = UserAnswer.objects.filter(test_result=tr).aggregate(Avg('score'))['score__avg'] or 0
                        total_score += section_score
                        section_count += 1

                final_score = round(total_score / section_count) if section_count > 0 else 0
                test_result.score = final_score
                test_result.status = 'completed'
                test_result.end_time = timezone.now()
                test_result.save()

                user_test.score = final_score
                user_test.status = 'completed'
                user_test.save()

            return {
                "answers": response_data,
                "test_completed": True,
                "score": round(score)
            }
        return {"answers": response_data}

class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Muayyan test natijasini batafsil olish",
        description="Foydalanuvchining muayyan TestResult ID bo'yicha natijasini qaytaradi: to'g'ri/xato javoblar, foiz va daraja.",
        responses={200: TestResultDetailSerializer(), 404: "Test natijasi topilmadi"}
    )
    def get(self, request, test_result_id):
        user = request.user
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user)
        except TestResult.DoesNotExist:
            return Response({"error": "Test natijasi topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TestResultDetailSerializer(test_result, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class TestResultListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    @extend_schema(
        summary="Foydalanuvchining barcha test natijalari ro'yxatini olish",
        description="Foydalanuvchining barcha test natijalarini qisqacha ko'rsatadi (section, language, status, percentage), pagination bilan.",
        responses={200: TestResultListSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        results = TestResult.objects.filter(user_test__user=user).order_by('-start_time')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(results, request)
        if page is not None:
            serializer = TestResultListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = TestResultListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class OverallTestResultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Foydalanuvchining umumiy test natijasini olish",
        description="Listening, Reading, Writing va Speaking bo'limlari bo'yicha natijalarni va umumiy foiz hamda Multilevel darajasini qaytaradi.",
        responses={200: OverallTestResultSerializer()}
    )
    def get(self, request):
        user = request.user
        serializer = OverallTestResultSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)