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
from django.db import transaction
from datetime import datetime, timedelta
from .models import *
from apps.payment.models import *
from .serializers import *

from apps.main.models import Language

    
############################################################################################################
    #Test uchun API'lar

class TestRequestApiView(APIView):
    @swagger_auto_schema(
        operation_summary="Test so‘rash",
        manual_parameters=[
            openapi.Parameter('language', openapi.IN_QUERY, description="Tilni tanlang (Language ID orqali)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('level', openapi.IN_QUERY, description="Test darajasini tanlang!", type=openapi.TYPE_STRING, enum=['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel']),
            openapi.Parameter('test', openapi.IN_QUERY, description="Test turini tanlang: Listening, Writing, Reading, Speaking", type=openapi.TYPE_STRING, enum=['listening', 'writing', 'reading', 'speaking']),
            openapi.Parameter('exam_id', openapi.IN_QUERY, description="Imtihonni tanlang (Exam ID orqali)", type=openapi.TYPE_INTEGER),  # Yangi parametr
        ],
        responses={200: MultilevelSectionSerializer()},
    )
    def get(self, request):
        language_id = request.GET.get('language')
        level_choice = request.GET.get('level')
        test_type = request.GET.get('test')
        exam_id = request.GET.get('exam_id')  # Yangi parametr

        # Majburiy parametrlarni tekshirish
        if not language_id or not test_type or not level_choice:
            return Response({"error": "Language ID, Test turi va Daraja kiritilishi shart!"}, status=400)

        try:
            language = Language.objects.get(pk=language_id)
        except Language.DoesNotExist:
            return Response({"error": "Til topilmadi!"}, status=404)

        LEVEL_CHOICES = ['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel']
        if level_choice not in LEVEL_CHOICES:
            return Response({"error": f"Noto‘g‘ri daraja! Daraja quyidagilardan biri bo‘lishi kerak: {', '.join(LEVEL_CHOICES)}."}, status=400)
        
        TEST_TYPES = ['listening', 'writing', 'reading', 'speaking']
        if test_type not in TEST_TYPES:
            return Response({"error": f"Noto‘g‘ri test turi! Test turi quyidagilardan biri bo‘lishi kerak: {', '.join(TEST_TYPES)}."}, status=400)

        # Exam tanlash
        if exam_id:
            try:
                exam = Exam.objects.get(pk=exam_id, language=language, level=level_choice)
            except Exam.DoesNotExist:
                return Response({"error": "Tanlangan Exam topilmadi yoki mos emas!"}, status=404)
        else:
            # Agar exam_id kiritilmagan bo‘lsa, mos Examlarni topish
            exams = Exam.objects.filter(language=language, level=level_choice)
            if not exams.exists():
                return Response({"error": f"{level_choice} darajasida {language.name} tilida imtihon mavjud emas!"}, status=404)
            return Response({
                "message": "Iltimos, Exam tanlang!",
                "exams": [{"id": exam.id, "title": exam.title} for exam in exams]
            }, status=200)

        # To‘lov holatini tekshirish
        # if not UserExamPayment.objects.filter(user=request.user, exam=exam, is_paid=True).exists():
        #     return Response({"error": "Bu imtihon uchun to‘lov qilinmagan! Iltimos, avval to‘lov qiling."}, status=403)

        # Foydalanuvchining hozirgi test_type va exam ga mos faol testini qidirish
        existing_test = TestResult.objects.filter(
            user_test__user=request.user,
            user_test__language=language,
            section__exam=exam,  # Exam bo‘yicha filtr
            section__type=test_type,
            status='started'
        ).last()

        if existing_test:
            if existing_test.end_time and existing_test.end_time < timezone.now():
                existing_test.status = 'completed'
                existing_test.save()
                existing_test.user_test.status = 'completed'
                existing_test.user_test.save()
            else:
                # Hozirgi faol testni qaytarish
                serializer = MultilevelSectionSerializer(
                    existing_test.section,
                    context={'test_result': existing_test.pk, 'request': request}
                )
                test_data = {
                    "test_type": test_type,
                    "duration": existing_test.section.duration,
                    "part": serializer.data,
                    "test_result_id": existing_test.id
                }
                return Response(test_data)

        # Sectionlarni Exam va type bo‘yicha filtr qilish
        all_sections = Section.objects.filter(exam=exam, type=test_type)
        if not all_sections.exists():
            return Response({"error": f"Ushbu imtihonda {test_type} turidagi testlar mavjud emas!"}, status=404)

        used_section_ids = TestResult.objects.filter(user_test__user=request.user).values_list('section_id', flat=True).distinct()
        unused_sections = all_sections.exclude(id__in=used_section_ids)

        if unused_sections.exists():
            selected_section = choice(unused_sections)
        else:
            selected_section = choice(all_sections)

        # Yangi test yaratish va boshqa faol testlarni yakunlash
        last_user_test = UserTest.objects.filter(user=request.user, language=language, status='started').last()
        if last_user_test:
            new_test_result = TestResult.objects.create(
                user_test=last_user_test,
                section=selected_section,
                status='started',
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=selected_section.duration)
            )
        else:
            # Barcha boshqa faol UserTest larni yakunlash
            UserTest.objects.filter(user=request.user, status='started').update(status='completed')
            TestResult.objects.filter(user_test__user=request.user, status='started').update(status='completed')
            
            new_user_test = UserTest.objects.create(
                user=request.user,
                language=language,
                status='started'
            )
            new_test_result = TestResult.objects.create(
                user_test=new_user_test,
                section=selected_section,
                status='started',
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=selected_section.duration)
            )

        serializer = MultilevelSectionSerializer(
            selected_section,
            context={'test_result': new_test_result.pk, 'request': request}
        )

        test_data = {
            "test_type": test_type,
            "duration": selected_section.duration,
            "part": serializer.data,
            "test_result_id": new_test_result.id
        }
        
        return Response(test_data)



class TestCheckApiView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TestCheckSerializer
    queryset = UserAnswer.objects.all()

    def create(self, request, *args, **kwargs):
        user = request.user
        test_result_id = request.data.get('test_result_id')

        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question = serializer.validated_data.get('question')
        user_option = serializer.validated_data.get('user_option')
        user_answer = serializer.validated_data.get('user_answer')

        # Agar test_result_id kiritilgan bo‘lsa, uni ishlatamiz
        if test_result_id:
            try:
                current_test_result = TestResult.objects.get(
                    id=test_result_id,
                    user_test__user=user,
                    status='started'
                )
            except TestResult.DoesNotExist:
                return Response({"message": "Bu ID ga mos faol TestResult mavjud emas"}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Agar test_result_id kiritilmagan bo‘lsa, savolning sectioniga mos TestResult ni olish
            current_test_result = TestResult.objects.filter(
                user_test__user=user,
                section=question.test.section,  # Savolning bo‘limiga moslash
                status='started'
            ).last()
            if not current_test_result:
                # Agar mos TestResult topilmasa, yangi yaratish mumkin (ixtiyoriy)
                return Response({"error": "Ushbu bo‘lim uchun faol test topilmadi!"}, status=status.HTTP_400_BAD_REQUEST)

        # Vaqt tugashini tekshirish
        if current_test_result.end_time and current_test_result.end_time < timezone.now():
            current_test_result.status = 'completed'
            current_test_result.save()
            current_test_result.user_test.status = 'completed'
            current_test_result.user_test.save()
            return Response({"message": "Test vaqti tugagan, yangi test so‘rang"}, status=status.HTTP_400_BAD_REQUEST)

        # Savolning sectioni TestResult sectioniga mos kelishini tekshirishni olib tashlaymiz
        # Chunki endi current_test_result har doim savolning sectioniga mos tanlanadi

        existing_answer = UserAnswer.objects.filter(test_result=current_test_result, question=question).first()

        is_correct = False
        if question.has_options:
            correct_option = Option.objects.filter(question=question, is_correct=True).first()
            is_correct = correct_option == user_option if user_option else False
        else:
            is_correct = question.answer.strip().lower() == user_answer.strip().lower() if user_answer and question.answer else False

        if existing_answer:
            existing_answer.user_option = user_option
            existing_answer.user_answer = user_answer
            existing_answer.is_correct = is_correct
            existing_answer.save()
            response_serializer = self.get_serializer(existing_answer, context={'request': request, 'test_result': current_test_result})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            serializer.validated_data['test_result'] = current_test_result
            serializer.validated_data['is_correct'] = is_correct
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            test_result_id = request.data.get('test_result_id')
            if not test_result_id:
                question = Question.objects.get(id=request.data.get('question'))
                test_result = TestResult.objects.filter(
                    user_test__user=request.user,
                    section=question.test.section,
                    status='started'
                ).last()
                test_result_id = test_result.id if test_result else None
            if test_result_id:
                try:
                    current_test_result = TestResult.objects.get(id=test_result_id, user_test__user=request.user, status='started')
                    total_questions = Question.objects.filter(test__section=current_test_result.section).count()
                    answered_questions = UserAnswer.objects.filter(test_result=current_test_result).count()

                    if total_questions == answered_questions:
                        correct_count = UserAnswer.objects.filter(test_result=current_test_result, is_correct=True).count()
                        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                        
                        current_test_result.score = round(score)
                        current_test_result.status = 'completed'
                        current_test_result.end_time = timezone.now()
                        current_test_result.save()

                        current_user_test = current_test_result.user_test
                        current_user_test.score = round(score)
                        current_user_test.status = 'completed'
                        current_user_test.save()

                        response.data['test_completed'] = True
                        response.data['score'] = round(score)
                except TestResult.DoesNotExist:
                    pass

        return super().finalize_response(request, response, *args, **kwargs)
    

# TestResult uchun batafsil natija
class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Muayyan test natijasini batafsil olish",
        description="Foydalanuvchining muayyan TestResult ID bo‘yicha natijasini qaytaradi: to‘g‘ri/xato javoblar, foiz va daraja.",
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

# TestResult ro‘yxati
class TestResultListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    @extend_schema(
        summary="Foydalanuvchining barcha test natijalari ro‘yxatini olish",
        description="Foydalanuvchining barcha test natijalarini qisqacha ko‘rsatadi (section, language, status, percentage), pagination bilan.",
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

# Umumiy TestResult
class OverallTestResultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Foydalanuvchining umumiy test natijasini olish",
        description="Listening va Reading bo‘limlari bo‘yicha natijalarni va umumiy foiz hamda Multilevel darajasini qaytaradi.",
        responses={200: OverallTestResultSerializer()}
    )
    def get(self, request):
        user = request.user
        serializer = OverallTestResultSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)