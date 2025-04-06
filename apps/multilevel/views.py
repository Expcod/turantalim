from random import choice
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_yasg import openapi
from django.db import transaction
from datetime import datetime, timedelta
from .models import *
from apps.payment.models import *
from .serializers import *

from apps.main.models import Language

import os
from rest_framework import views, response
from rest_framework.permissions import IsAuthenticated
from core.settings import base
from .models import Test, Exam
from .serializers import MultilevelTestSerializer
from openai import OpenAI
import requests
from PIL import Image
import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = "your_openai_api_key_here"  # OpenAI API kalitingizni qo‘ying
client = OpenAI(api_key=OPENAI_API_KEY)

class WritingTestRequestAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Writing test so‘rovini qabul qilish va tekshirish"""
        exam_id = request.data.get('exam')
        section_type = 'writing'

        # Exam va Section tekshiruvi
        try:
            exam = Exam.objects.get(id=exam_id)
            section = Section.objects.get(exam=exam, type=section_type)
        except Exam.DoesNotExist:
            return response.Response({"error": "Imtihon topilmadi"}, status=404)
        except Section.DoesNotExist:
            return response.Response({"error": "Writing bo‘limi topilmadi"}, status=404)

        # UserTest yaratish yoki olish
        user_test, created = UserTest.objects.get_or_create(
            user=request.user,
            exam=exam,
            defaults={'status': 'started',}  # To‘lov oldindan tasdiqlangan deb faraz qilamiz
        )

        # TestResult yaratish
        test_result, created = TestResult.objects.get_or_create(
            user_test=user_test,
            section=section,
            defaults={'status': 'started'}
        )

        # Rasmni qabul qilish
        writing_image = request.FILES.get('writing_image')
        if not writing_image:
            return response.Response({"error": "Rasm yuklanmadi"}, status=400)

        # Rasmni matnga aylantirish (OCR)
        image_path = os.path.join(base.MEDIA_ROOT, f"writing_images/{writing_image.name}")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, 'wb') as f:
            for chunk in writing_image.chunks():
                f.write(chunk)

        try:
            with Image.open(image_path) as img:
                ocr_response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Bu rasmda yozilgan matnni o‘qib bering."},
                                {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                            ],
                        }
                    ],
                )
                text = ocr_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Writing OCR xatosi: {str(e)}")
            return response.Response({"error": "Rasmni o‘qishda xatolik"}, status=500)

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi Turk tili multilevel imtihoni uchun writing javobini yubordi: '{text}'. "
            "Javobni turk tili grammatikasi va multilevel qoidalariga ko‘ra tekshirib, "
            "batafsil izoh bilan 0-100 oralig‘ida baho bering."
        )
        try:
            gpt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            result = gpt_response.choices[0].message.content
            # Natijadan score ajratib olish (masalan, "Baho: 85" formatida kelsa)
            score = int(result.split("Baho:")[-1].strip()) if "Baho:" in result else 50
        except Exception as e:
            logger.error(f"ChatGPT xatosi (writing): {str(e)}")
            return response.Response({"error": "Javobni tekshirishda xatolik"}, status=500)

        # UserAnswer saqlash
        question = Question.objects.filter(test__section=section).first()  # Writing uchun savol mavjud deb faraz qilamiz
        if not question:
            question = Question.objects.create(test=section.test_set.first(), text="Writing javobi")
        
        UserAnswer.objects.create(
            test_result=test_result,
            question=question,
            user_answer=text,
            is_correct=score >= 50  # 50 dan yuqori bo‘lsa to‘g‘ri deb hisoblaymiz
        )

        # TestResult yangilash
        test_result.status = 'completed'
        test_result.score = score
        test_result.end_time = timezone.now()
        test_result.save()

        return response.Response({
            "message": "Writing test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score
        })

class SpeakingTestRequestAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Speaking test so‘rovini qabul qilish va tekshirish"""
        exam_id = request.data.get('exam')
        section_type = 'speaking'

        # Exam va Section tekshiruvi
        try:
            exam = Exam.objects.get(id=exam_id)
            section = Section.objects.get(exam=exam, type=section_type)
        except Exam.DoesNotExist:
            return response.Response({"error": "Imtihon topilmadi"}, status=404)
        except Section.DoesNotExist:
            return response.Response({"error": "Speaking bo‘limi topilmadi"}, status=404)

        # UserTest yaratish yoki olish
        user_test, created = UserTest.objects.get_or_create(
            user=request.user,
            exam=exam,
            defaults={'status': 'started',}
        )

        # TestResult yaratish
        test_result, created = TestResult.objects.get_or_create(
            user_test=user_test,
            section=section,
            defaults={'status': 'started'}
        )

        # Audio faylni qabul qilish
        speaking_audio = request.FILES.get('speaking_audio')
        if not speaking_audio:
            return response.Response({"error": "Audio yuklanmadi"}, status=400)

        # Audio faylni saqlash
        audio_path = os.path.join(base.MEDIA_ROOT, f"speaking_audios/{speaking_audio.name}")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        with open(audio_path, 'wb') as f:
            for chunk in speaking_audio.chunks():
                f.write(chunk)

        # Audio faylni matnga aylantirish (Speech-to-Text)
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language="tr-TR")  # Turk tili uchun
        except Exception as e:
            logger.error(f"Speaking STT xatosi: {str(e)}")
            return response.Response({"error": "Audio o‘qishda xatolik"}, status=500)

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi Turk tili multilevel imtihoni uchun speaking javobini yubordi: '{text}'. "
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
        except Exception as e:
            logger.error(f"ChatGPT xatosi (speaking): {str(e)}")
            return response.Response({"error": "Javobni tekshirishda xatolik"}, status=500)

        # UserAnswer saqlash
        question = Question.objects.filter(test__section=section).first()  # Speaking uchun savol mavjud deb faraz qilamiz
        if not question:
            question = Question.objects.create(test=section.test_set.first(), text="Speaking javobi")
        
        UserAnswer.objects.create(
            test_result=test_result,
            question=question,
            user_answer=text,
            is_correct=score >= 50
        )

        # TestResult yangilash
        test_result.status = 'completed'
        test_result.score = score
        test_result.end_time = timezone.now()
        test_result.save()

        return response.Response({
            "message": "Speaking test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score
        })
    
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



class TestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_error(self, message, status_code):
        return Response({"error": message}, status=status_code)

    @swagger_auto_schema(
        operation_summary="Foydalanuvchi javoblarini tekshirish",
        operation_description="Bitta yoki bir nechta savol uchun javoblarni tekshiradi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'test_result_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Test natijasi ID si', nullable=True),
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question': openapi.Schema(type=openapi.TYPE_INTEGER, description='Savol ID si'),
                            'user_option': openapi.Schema(type=openapi.TYPE_INTEGER, description='Tanlangan variant ID si', nullable=True),
                            'user_answer': openapi.Schema(type=openapi.TYPE_STRING, description='Foydalanuvchi javobi', nullable=True),
                        },
                        required=['question']
                    )
                )
            }
        ),
        responses={
            201: TestCheckSerializer(many=True),
            200: TestCheckSerializer(many=True),
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas")
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data if isinstance(request.data, dict) else {'answers': request.data}
        serializer = BulkTestCheckSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            return self.handle_error(serializer.errors, status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        # Birinchi savoldan Exam ni aniqlash
        question = answers_data[0]['question']
        exam = question.test.section.exam

        # TestResult ni aniqlash va vaqtni tekshirish
        current_test_result = self.get_active_test_result(user, test_result_id, question)
        if isinstance(current_test_result, Response):
            return current_test_result

        # Javoblarni qayta ishlash
        responses = self.process_answers(user, current_test_result, answers_data)

        # Testni yakunlash
        final_response = self.finalize_test_result(user, current_test_result, responses)
        status_code = status.HTTP_201_CREATED if any(r.get('is_new') for r in responses) else status.HTTP_200_OK
        return Response(final_response, status=status_code)

    def get_active_test_result(self, user, test_result_id, question):
        if test_result_id:
            try:
                test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
            except TestResult.DoesNotExist:
                return self.handle_error("Bu ID ga mos faol TestResult mavjud emas", status.HTTP_403_FORBIDDEN)
        else:
            test_result = TestResult.objects.filter(
                user_test__user=user,
                section=question.test.section,
                status='started'
            ).last()
            if not test_result:
                return self.handle_error("Ushbu bo‘lim uchun faol test topilmadi!", status.HTTP_400_BAD_REQUEST)

        if test_result.end_time and test_result.end_time < timezone.now():
            test_result.status = 'completed'
            test_result.save()
            test_result.user_test.status = 'completed'
            test_result.user_test.save()
            return self.handle_error("Test vaqti tugagan, yangi test so‘rang", status.HTTP_400_BAD_REQUEST)

        return test_result

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