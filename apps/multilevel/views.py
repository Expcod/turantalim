import base64
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
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from pydub import AudioSegment
from openai import OpenAI, OpenAIError
from core.settings import base

import os
import tempfile
from rest_framework.permissions import IsAuthenticated
from openai import OpenAI
from PIL import Image
import speech_recognition as sr
import logging
import magic


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

        # Sectionlarni Exam va type bo'yicha filtr qilish
        all_sections = Section.objects.filter(exam=exam, type=test_type)
        if not all_sections.exists():
            return Response({"error": f"Ushbu imtihonda {test_type} turidagi testlar mavjud emas!"}, status=404)

        # Faol testni tekshirish
        existing_test = TestResult.objects.filter(
            user_test__user=request.user,
            user_test__language=language,
            section__exam=exam,
            section__type=test_type,
            status='started'
        ).last()

        if existing_test and (not existing_test.end_time or existing_test.end_time >= timezone.now()):
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

        # Agar faol test topilmasa yoki vaqti tugagan bo'lsa, yangi test yaratish
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
            UserTest.objects.filter(user=request.user, status='started').update(status='completed')
            TestResult.objects.filter(user_test__user=request.user, status='started').update(status='completed')
            
            new_user_test = UserTest.objects.create(
                user=request.user,
                exam=exam,
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



# OpenAI sozlamalari
OPENAI_API_KEY = base.OPENAI_API_KEY 
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
        serializer = WritingTestCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        question = serializer.validated_data['question']
        writing_image = serializer.validated_data['writing_image']

        # TestResult ni tekshirish
        test_result = get_or_create_test_result(user, test_result_id, question)
        if isinstance(test_result, Response):
            return test_result

        if test_result.section.type != 'writing':
            return Response({"error": "Bu endpoint faqat writing testlari uchun!"}, status=status.HTTP_400_BAD_REQUEST)

        # Rasmni vaqtincha saqlash
        fs = FileSystemStorage()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in writing_image.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # Rasmni base64 formatiga o'tkazish
            with open(temp_file_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{encoded_image}"

            # OpenAI orqali OCR
            try:
                ocr_response = client.chat.completions.create(
                    model="gpt-4o",  # Yangi model
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Bu rasmda yozilgan matnni o'qib bering."},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                    max_tokens=500,
                )
                processed_answer = ocr_response.choices[0].message.content
            except Exception as e:
                logger.error(f"Writing OCR xatosi: {str(e)}")
                return Response({"error": f"Rasmni o'qishda xatolik yuz berdi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # OpenAI bilan tekshirish
            prompt = (
                f"Foydalanuvchi til imtihoni uchun writing javobini yubordi: '{processed_answer}'. "
                f"Savol: '{question.text}'. "
                "Javobni grammatika, so'z boyligi, mazmun va tuzilishi bo'yicha tekshirib, "
                "batafsil izoh bilan 0-100 oralig'ida baho bering. "
                "Agar javob savolga umuman mos kelmasa, 0-20 oralig'ida baho bering va sababini izohda aniq keltiring. "
                "Izoh bir nechta qator bo'lishi mumkin, lekin har bir fikrni qisqa va aniq ifodalang. "
                "Javobingizni quyidagi formatda bering: "
                "Izoh: [batafsil izoh]\n"
                "Baho: [0-100 oralig'ida faqat raqam]"
            )

            # Javobni qayta ishlash
            final_response = process_test_response(user, test_result, question, processed_answer, prompt, client, logger)
            final_response["message"] = "Writing test muvaffaqiyatli tekshirildi"

            response_serializer = TestCheckResponseSerializer(data=final_response)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Writing test tekshirishda xato: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Vaqtincha faylni o'chirish
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

class SpeakingTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking test javobini tekshirish",
        operation_description="Foydalanuvchi yuborgan audioni OpenAI Whisper orqali tekshiradi.",
        request_body=SpeakingTestCheckSerializer,
        responses={
            200: TestCheckResponseSerializer,
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas"),
            500: openapi.Response(description="Server xatosi")
        }
    )
    def post(self, request):
        user = request.user
        serializer = SpeakingTestCheckSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        question = serializer.validated_data['question']
        speaking_audio = serializer.validated_data['speaking_audio']

        # TestResult ni tekshirish
        test_result = get_or_create_test_result(user, test_result_id, question)
        if isinstance(test_result, Response):
            logger.warning(f"get_or_create_test_result failed: {test_result.data}")
            return test_result

        if test_result.section.type != 'speaking':
            return Response({"error": "Bu endpoint faqat speaking testlari uchun!"}, status=status.HTTP_400_BAD_REQUEST)

        # Audio faylni vaqtincha saqlash
        temp_file_path = None
        try:
            # Save the original file with appropriate extension
            file_extension = speaking_audio.name.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                for chunk in speaking_audio.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # OpenAI Whisper orqali transkripsiya qilish
            language = test_result.section.exam.language
            language_code_map = {
                "English": "en",
                "Turkish": "tr",
                "Uzbek": "uz",
            }
            language_code = language_code_map.get(language.name, "tr") if language else "tr"

            try:
                with open(temp_file_path, "rb") as audio_file:
                    # Try with language parameter first
                    try:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language=language_code,
                        )
                    except OpenAIError as e:
                        # If language parameter fails, try without it
                        audio_file.seek(0)  # Reset file pointer
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                        )
                processed_answer = transcription.text
            except OpenAIError as e:
                logger.error(f"Whisper API xatosi: {str(e)}")
                return Response(
                    {"error": f"Whisper API xatosi: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # OpenAI bilan tekshirish uchun prompt
            prompt = (
                f"Foydalanuvchi til imtihoni uchun speaking javobini yubordi: '{processed_answer}'. "
                f"Savol: '{question.text}'. "
                "Javobni talaffuz, grammatika, so'z boyligi, mazmun va ravonligi bo'yicha tekshirib, "
                "batafsil izoh bilan 0-100 oralig'ida baho bering. "
                "Agar javob savolga umuman mos kelmasa, 0-20 oralig'ida baho bering va sababini izohda aniq keltiring. "
                "Izoh bir nechta qator bo'lishi mumkin, lekin har bir fikrni qisqa va aniq ifodalang. "
                "Javobingizni quyidagi formatda bering: "
                "Izoh: [batafsil izoh]\n"
                "Baho: [0-100 oralig'ida faqat raqam]"
            )

            # Javobni qayta ishlash
            final_response = process_test_response(user, test_result, question, processed_answer, prompt, client, logger)
            final_response["message"] = "Speaking test muvaffaqiyatli tekshirildi"

            response_serializer = TestCheckResponseSerializer(data=final_response)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Speaking test tekshirishda xato: {str(e)}")
            return Response({"error": f"Audio o'qishda xatolik yuz berdi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Vaqtincha faylni o'chirishda xato: {str(e)}")

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

        # Writing yoki Speaking bo'lsa, bu endpoint ishlatilmaydi
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
        
        # Yangi va yangilanadigan javoblar uchun ro'yxatlar
        new_answers = []
        update_answers = []

        for answer_data in answers_data:
            question = answer_data['question']
            user_option = answer_data.get('user_option')
            user_answer = answer_data.get('user_answer')

            # To'g'ri javobni aniqlash
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

# TestResult ro'yxati
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

# Umumiy TestResult
class OverallTestResultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Foydalanuvchining umumiy test natijasini olish",
        description="Listening va Reading bo'limlari bo'yicha natijalarni va umumiy foiz hamda Multilevel darajasini qaytaradi.",
        responses={200: OverallTestResultSerializer()}
    )
    def get(self, request):
        user = request.user
        serializer = OverallTestResultSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)