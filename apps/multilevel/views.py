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

from core.settings import base

import os
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
from PIL import Image
import speech_recognition as sr
import logging

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
        # if not ExamPayment.objects.filter(user=request.user, exam=exam, status='completed').exists():
        #         return Response({"error": "Bu imtihon uchun to‘lov qilinmagan! Iltimos, avval to‘lov qiling."}, status=403)
        
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

image_url = "https://a6d9-188-113-246-221.ngrok-free.app/media/writing/example.png"

# OpenAI sozlamalari
OPENAI_API_KEY = base.OPENAI_API_KEY  # OpenAI API kalitingizni qo‘ying
client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

class WritingTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Writing test javobini tekshirish",
        operation_description="Foydalanuvchi yuborgan rasmni OpenAI orqali tekshiradi.",
        request_body=WritingTestCheckSerializer,
        responses={
            200: TestCheckResponseSerializer,
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas")
        }
    )
    def post(self, request):
        user = request.user

        # So‘rovni validatsiya qilish
        serializer = WritingTestCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data['test_result_id']
        question = serializer.validated_data['question']
        writing_image = serializer.validated_data['writing_image']

        # TestResult ni olish yoki yaratish
        test_result = get_or_create_test_result(user, test_result_id, question)
        if isinstance(test_result, Response):
            return test_result

        # Section turini tekshirish
        if test_result.section.type != 'writing':
            return Response({"error": "Bu endpoint faqat writing testlari uchun!"}, status=status.HTTP_400_BAD_REQUEST)

        # Rasmni saqlash
        image_path = os.path.join(settings.MEDIA_ROOT, f"writing_images/{writing_image.name}")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, 'wb') as f:
            for chunk in writing_image.chunks():
                f.write(chunk)

        # Rasmni matnga aylantirish (OCR)
        try:
            with Image.open(image_path) as img:
                ocr_response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Bu rasmda yozilgan matnni o‘qib bering."},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                )
                processed_answer = ocr_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Writing OCR xatosi: {str(e)}")
            return Response({"error": "Rasmni o‘qishda xatolik yuz berdi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi Turk tili multilevel imtihoni uchun writing javobini yubordi: '{processed_answer}'. "
            "Javobni turk tili grammatikasi va multilevel qoidalariga ko‘ra tekshirib, "
            "batafsil izoh bilan 0-100 oralig‘ida baho bering."
        )
        try:
            gpt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            result = gpt_response.choices[0].message.content
            score = int(result.split("Baho:")[-1].strip()) if "Baho:" in result else 50
            is_correct = score >= 50
        except Exception as e:
            logger.error(f"ChatGPT xatosi (writing): {str(e)}")
            return Response({"error": "Javobni tekshirishda xatolik yuz berdi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Foydalanuvchi javobini saqlash
        save_user_answer(test_result, question, processed_answer, is_correct)

        # Test natijasini yakunlash
        final_response = finalize_test_result(test_result, score)
        final_response.update({
            "message": "Writing test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score
        })

        # Javobni serializer orqali formatlash
        response_serializer = TestCheckResponseSerializer(final_response)
        return Response(response_serializer.data)

class SpeakingTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking test javobini tekshirish",
        operation_description="Foydalanuvchi yuborgan audioni OpenAI orqali tekshiradi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'test_result_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Test natijasi ID si (ixtiyoriy)',
                    nullable=True
                ),
                'question': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Savol ID si (majburiy)'
                ),
                'speaking_audio': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='Speaking javobi uchun audio fayl (WAV yoki MP3, majburiy)'
                ),
            },
            required=['question', 'speaking_audio'],
            description="So‘rov `multipart/form-data` formatida bo‘lishi kerak."
        ),
        responses={
            200: TestCheckResponseSerializer,
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas")
        },
        consumes=['multipart/form-data']  # So‘rov formati
    )
    def post(self, request):
        user = request.user

        # So‘rovda fayl borligini tekshirish
        if 'speaking_audio' not in request.FILES:
            return Response(
                {"speaking_audio": ["Speaking javobi uchun audio fayl yuklanishi kerak!"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # So‘rovni validatsiya qilish
        serializer = SpeakingTestCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data['test_result_id']
        question = serializer.validated_data['question']
        speaking_audio = serializer.validated_data['speaking_audio']

        # TestResult ni olish yoki yaratish
        test_result = get_or_create_test_result(user, test_result_id, question)
        if isinstance(test_result, Response):
            return test_result

        # Section turini tekshirish
        if test_result.section.type != 'speaking':
            return Response({"error": "Bu endpoint faqat speaking testlari uchun!"}, status=status.HTTP_400_BAD_REQUEST)

        # Audio faylni saqlash
        audio_path = os.path.join(settings.MEDIA_ROOT, f"speaking_audios/{speaking_audio.name}")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, 'wb') as f:
            for chunk in speaking_audio.chunks():
                f.write(chunk)

        # Audio faylni matnga aylantirish (Speech-to-Text)
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
                processed_answer = recognizer.recognize_google(audio, language="tr-TR")
        except Exception as e:
            logger.error(f"Speaking STT xatosi: {str(e)}")
            return Response({"error": "Audio o‘qishda xatolik yuz berdi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi Turk tili multilevel imtihoni uchun speaking javobini yubordi: '{processed_answer}'. "
            "Javobni turk tili grammatikasi va multilevel qoidalariga ko‘ra tekshirib, "
            "batafsil izoh bilan 0-100 oralig‘ida baho bering."
        )
        try:
            gpt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            result = gpt_response.choices[0].message.content
            score = int(result.split("Baho:")[-1].strip()) if "Baho:" in result else 50
            is_correct = score >= 50
        except Exception as e:
            logger.error(f"ChatGPT xatosi (speaking): {str(e)}")
            return Response({"error": "Javobni tekshirishda xatolik yuz berdi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Foydalanuvchi javobini saqlash
        save_user_answer(test_result, question, processed_answer, is_correct)

        # Test natijasini yakunlash
        final_response = finalize_test_result(test_result, score)
        final_response.update({
            "message": "Speaking test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score,
            "user_answer": processed_answer,
            "question_text": question.text
        })

        # Javobni serializer orqali formatlash
        response_serializer = TestCheckResponseSerializer(final_response)
        return Response(response_serializer.data)
    
#######################
    
# multilevel/views.py (davomi)
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

        # TestResult ni aniqlash va vaqtni tekshirish
        current_test_result = get_or_create_test_result(user, test_result_id, question)
        if isinstance(current_test_result, Response):
            return current_test_result

        # Writing yoki Speaking bo‘lsa, bu endpoint ishlatilmaydi
        if current_test_result.section.type in ['writing', 'speaking']:
            return self.handle_error(
                "Writing yoki Speaking testlari uchun /testcheck/writing/ yoki /testcheck/speaking/ endpointlaridan foydalaning!",
                status.HTTP_400_BAD_REQUEST
            )

        # Javoblarni qayta ishlash
        responses = self.process_answers(user, current_test_result, answers_data)

        # Testni yakunlash
        final_response = self.finalize_test_result(user, current_test_result, responses)
        status_code = status.HTTP_201_CREATED if any(r.get('is_new') for r in responses) else status.HTTP_200_OK
        return Response(final_response, status=status_code)

    def process_answers(self, user, test_result, answers_data):
        # Mavjud javoblarni olish
        existing_answers = {ua.question_id: ua for ua in UserAnswer.objects.filter(test_result=test_result)}
        
        # Yangi va yangilanadigan javoblar uchun ro‘yxatlar
        new_answers = []
        update_answers = []

        for answer_data in answers_data:
            question = answer_data['question']
            user_option = answer_data.get('user_option')
            user_answer = answer_data.get('user_answer')

            # To‘g‘ri javobni aniqlash
            is_correct = False
            if question.has_options:
                correct_option = Option.objects.filter(question=question, is_correct=True).first()
                is_correct = correct_option == user_option if user_option else False
            else:
                is_correct = (
                    question.answer.strip().lower() == user_answer.strip().lower()
                    if user_answer and question.answer else False
                )

            # Mavjud javobni yangilash yoki yangi javob yaratish
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

        # Bulk operatsiyalar
        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)
        if update_answers:
            UserAnswer.objects.bulk_update(update_answers, ['user_option', 'user_answer', 'is_correct'])

        # Javoblar uchun serializer tayyorlash
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

    def finalize_test_result(self, user, test_result, responses):
        response_data = [r["data"] for r in responses]
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()

        if total_questions == answered_questions:
            correct_count = UserAnswer.objects.filter(test_result=test_result, is_correct=True).count()
            score = (correct_count / total_questions * 100) if total_questions > 0 else 0

            test_result.score = round(score)
            test_result.status = 'completed'
            test_result.end_time = timezone.now()
            test_result.save()

            test_result.user_test.score = round(score)
            test_result.user_test.status = 'completed'
            test_result.user_test.save()

            return {
                "answers": response_data,
                "test_completed": True,
                "score": round(score)
            }
        return {"answers": response_data}

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