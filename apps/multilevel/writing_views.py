import base64
import tempfile
import logging
import os
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from openai import OpenAI
from .utils import process_test_response
from .serializers import SpeakingTestResponseSerializer
from .writing_serializers import BulkWritingTestCheckSerializer
from .models import Question, TestResult, UserAnswer, Section
from core.settings import base
from django.utils import timezone
from django.db.models import Avg

logger = logging.getLogger(__name__)

class WritingTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Bulk writing test javoblarini tekshirish",
        request_body=BulkWritingTestCheckSerializer,
        responses={200: SpeakingTestResponseSerializer}
    )
    def post(self, request):
        # Custom parse for bulk form-data
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            answers = []
            i = 0
            while True:
                q_key = f'answers[{i}][question]'
                f_key = f'answers[{i}][writing_image]'
                if q_key in request.data and f_key in request.FILES:
                    try:
                        question_id = int(request.data[q_key])  # Convert to int
                        writing_image = request.FILES[f_key]
                        answers.append({
                            'question': question_id,  # Pass question ID as integer
                            'writing_image': writing_image
                        })
                        i += 1
                    except (ValueError, KeyError) as e:
                        logger.error(f"Invalid question ID or conversion error for index {i}: {str(e)}")
                        break
                else:
                    break
            data = {
                'test_result_id': request.data.get('test_result_id'),
                'answers': answers
            }
        else:
            data = request.data

        logger.debug(f"Parsed data: {data}")  # Debug log
        serializer = BulkWritingTestCheckSerializer(data=data)
        if not serializer.is_valid():
            logger.error(f"Serializer validation error: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        user = request.user
        # TestResult ni tekshirish
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
        except TestResult.DoesNotExist:
            return Response({"error": "TestResult topilmadi yoki faol emas!"}, status=status.HTTP_403_FORBIDDEN)

        client = OpenAI(api_key=base.OPENAI_API_KEY)
        responses = []
        new_answers = []
        existing_answers = {ua.question_id: ua for ua in UserAnswer.objects.filter(test_result=test_result)}

        for answer in answers_data:
            question = answer['question']  # This is now a Question object (resolved by serializer)
            writing_image = answer['writing_image']
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in writing_image.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                with open(temp_file_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{encoded_image}"

                # OpenAI orqali OCR
                try:
                    ocr_response = client.chat.completions.create(
                        model="gpt-4o",
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
                    processed_answer = ocr_response.choices[0].message.content if ocr_response.choices else None
                except Exception as e:
                    logger.error(f"Writing OCR xatosi: {str(e)}")
                    processed_answer = None

                if processed_answer is None:
                    logger.error(f"No text extracted from image for question {question.id}")
                    responses.append({
                        "message": "Rasmda matn aniqlanmadi yoki OCR xatolik yuz berdi.",
                        "result": "OCR xatolik",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text
                    })
                    continue

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

                final_response = process_test_response(user, test_result, question, processed_answer, prompt, client, logger)
                if final_response is None:
                    logger.error(f"Failed to process response for question {question.id}")
                    responses.append({
                        "message": "Javobni baholashda xatolik yuz berdi.",
                        "result": "Tekshirilmadi",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text
                    })
                else:
                    final_response["message"] = f"Savol {question.id} uchun writing test muvaffaqiyatli tekshirildi"
                    final_response["user_answer"] = processed_answer
                    final_response["question_text"] = question.text
                    responses.append(final_response)

                    # UserAnswer ni saqlash yoki yangilash
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

            except Exception as e:
                logger.error(f"Writing test tekshirishda xato: {str(e)}")
                responses.append({
                    "message": f"Writing test tekshirishda xato: {str(e)}",
                    "result": "Tekshirilmadi",
                    "score": 0,
                    "test_completed": False,
                    "user_answer": "",
                    "question_text": question.text
                })
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)

        # Testni yakunlash
        total_score = sum(r['score'] for r in responses if r['score'] is not None) / len(responses) if responses else 0
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

        return Response({
            "answers": responses,
            "test_completed": True,
            "score": round(total_score)
        }, status=status.HTTP_200_OK)