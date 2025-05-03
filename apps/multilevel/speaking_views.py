import logging
import os
import tempfile
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from openai import OpenAI, OpenAIError
from .models import TestResult, UserAnswer, Section
from .utils import process_test_response
from .serializers import SpeakingTestResponseSerializer
from .speaking_serializers import BulkSpeakingTestCheckSerializer
from core.settings import base
from django.utils import timezone
from django.db.models import Avg

logger = logging.getLogger(__name__)

class SpeakingTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Speaking test javoblarini tekshirish",
        operation_description="Foydalanuvchi yuborgan bir nechta audiolarni OpenAI Whisper orqali tekshiradi.",
        request_body=BulkSpeakingTestCheckSerializer,
        responses={
            200: SpeakingTestResponseSerializer,
            400: "Validation xatosi",
            403: "TestResult topilmadi yoki faol emas",
            500: "Server xatosi"
        }
    )
    def post(self, request):
        # Custom parse for bulk form-data
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            answers = []
            i = 0
            while True:
                q_key = f'answers[{i}][question]'
                f_key = f'answers[{i}][speaking_audio]'
                if q_key in request.data and f_key in request.FILES:
                    answers.append({
                        'question': request.data[q_key],
                        'speaking_audio': request.FILES[f_key]
                    })
                    i += 1
                else:
                    break
            data = {
                'test_result_id': request.data.get('test_result_id'),
                'answers': answers
            }
        else:
            data = request.data

        logger.debug(f"Received request data: {data}")
        serializer = BulkSpeakingTestCheckSerializer(data=data)
        if not serializer.is_valid():
            logger.error(f"Serializer validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        # TestResult ni tekshirish
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=request.user, status='started')
        except TestResult.DoesNotExist:
            return Response({"error": "TestResult topilmadi yoki faol emas!"}, status=status.HTTP_403_FORBIDDEN)

        # Javoblarni qayta ishlash
        client = OpenAI(api_key=base.OPENAI_API_KEY)
        responses = self.process_answers(request.user, test_result, answers_data, client)

        # Testni yakunlash
        total_score = sum(r['score'] for r in responses if r['score'] is not None) / len(responses) if responses else 0
        final_response = {
            "answers": responses,
            "test_completed": True,
            "score": round(total_score)
        }
        test_result.score = round(total_score)
        test_result.status = 'completed'
        test_result.end_time = timezone.now()
        test_result.save()

        user_test = test_result.user_test
        all_test_results = TestResult.objects.filter(user_test=user_test, status='completed').values('section__type').annotate(avg_score=Avg('score'))
        if all_test_results:
            total_score = sum(item['avg_score'] for item in all_test_results) / len(all_test_results)
            user_test.score = round(total_score)
            user_test.status = 'completed' if len(all_test_results) == len(Section.objects.filter(exam=user_test.exam)) else 'started'
            user_test.save()

        return Response(final_response, status=status.HTTP_200_OK)

    def process_answers(self, user, test_result, answers_data, client):
        existing_answers = {ua.question_id: ua for ua in UserAnswer.objects.filter(test_result=test_result)}
        new_answers = []
        responses = []

        language = test_result.user_test.exam.language
        language_code_map = {
            "English": "en",
            "Turkish": "tr",
            "Uzbek": "uz",
        }
        language_code = language_code_map.get(language.name, "tr") if language else "tr"

        for answer_data in answers_data:
            question = answer_data['question']
            speaking_audio = answer_data['speaking_audio']

            temp_file_path = None
            try:
                file_extension = speaking_audio.name.split('.')[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                    for chunk in speaking_audio.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                try:
                    with open(temp_file_path, "rb") as audio_file:
                        try:
                            transcription = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                language=language_code,
                            )
                        except OpenAIError as e:
                            audio_file.seek(0)
                            transcription = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                            )
                    processed_answer = transcription.text
                except OpenAIError as e:
                    logger.error(f"Whisper API xatosi: {str(e)}")
                    responses.append({
                        "message": f"Whisper API xatosi: {str(e)}",
                        "result": "Transkripsiya qilinmadi",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text
                    })
                    continue

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

                final_response = process_test_response(user, test_result, question, processed_answer, prompt, client, logger)
                final_response["message"] = f"Savol {question.id} uchun speaking test muvaffaqiyatli tekshirildi"

                existing_answer = existing_answers.get(question.id)
                if existing_answer:
                    existing_answer.user_answer = processed_answer
                    existing_answer.save()
                else:
                    new_answer = UserAnswer(
                        test_result=test_result,
                        question=question,
                        user_answer=processed_answer
                    )
                    new_answers.append(new_answer)

                responses.append(final_response)

            except Exception as e:
                logger.error(f"Speaking test tekshirishda xato: {str(e)}")
                responses.append({
                    "message": f"Audio o'qishda xatolik yuz berdi: {str(e)}",
                    "result": "Tekshirilmadi",
                    "score": 0,
                    "test_completed": False,
                    "user_answer": "",
                    "question_text": question.text
                })
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Vaqtincha faylni o'chirishda xato: {str(e)}")

        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)

        return responses