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
from .multilevel_score import get_writing_score_details, get_writing_prompt, validate_test_level, count_words
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
            
            # Get all question IDs and image files with their indices
            question_data = {}
            image_data = {}
            
            # Parse question IDs
            for key, value in request.data.items():
                if key.startswith('answers[') and key.endswith('][question]'):
                    try:
                        # Extract index: answers[0][question] -> 0
                        start_idx = key.find('[') + 1
                        end_idx = key.find('][question]')
                        if start_idx > 0 and end_idx > start_idx:
                            index_str = key[start_idx:end_idx]
                            index = int(index_str)
                            question_data[index] = int(value)
                    except (ValueError, IndexError):
                        continue
            
            # Parse image files
            for key, value in request.FILES.items():
                if key.startswith('answers[') and key.endswith('][writing_image]'):
                    try:
                        # Extract index: answers[0][writing_image] -> 0
                        start_idx = key.find('[') + 1
                        end_idx = key.find('][writing_image]')
                        if start_idx > 0 and end_idx > start_idx:
                            index_str = key[start_idx:end_idx]
                            index = int(index_str)
                            image_data[index] = value
                    except (ValueError, IndexError):
                        continue
            
            # Combine question IDs and image files
            all_indices = set(question_data.keys()) | set(image_data.keys())
            
            for index in sorted(all_indices):
                question_id = question_data.get(index)
                image_file = image_data.get(index)
                
                if question_id is not None and image_file is not None:
                    answer_item = {
                        'question': question_id,
                        'writing_image': image_file
                    }
                    answers.append(answer_item)
            
            data = {
                'test_result_id': request.data.get('test_result_id'),
                'answers': answers
            }
        else:
            data = request.data

        serializer = BulkWritingTestCheckSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        user = request.user
        # TestResult ni tekshirish
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
            # Test tekshirilgan bo'lsa, uni completed ga o'tkazish
            test_result.status = 'completed'
            test_result.save()
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
                except Exception:
                    processed_answer = None

                if processed_answer is None:
                    responses.append({
                        "message": "Rasmda matn aniqlanmadi yoki OCR xatolik yuz berdi.",
                        "result": "OCR xatolik",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text
                    })
                    continue

                # Get exam level for scoring validation
                exam_level = test_result.user_test.exam.level
                
                # Determine question part based on test constraints or question order
                # This can be enhanced based on your specific question structure
                question_part = 1  # Default to part 1, can be determined by question metadata
                
                # Check if multilevel scoring should be used
                if validate_test_level(exam_level):
                    # Use multilevel writing scoring system
                    score_details = get_writing_score_details(processed_answer, question_part)
                    
                    # If text is too short, return 0 score immediately
                    if score_details['score'] == 0:
                        responses.append({
                            "message": score_details['reason'],
                            "result": "Matn juda qisqa",
                            "score": 0,
                            "test_completed": False,
                            "user_answer": processed_answer,
                            "question_text": question.text,
                            "word_count": score_details['word_count'],
                            "min_required": score_details['min_required']
                        })
                        continue
                    
                    # Generate comprehensive prompt for multilevel scoring
                    prompt = get_writing_prompt(question.text, question.test.constraints or "", processed_answer, question_part)
                else:
                    # Fallback to original scoring for other levels
                    constraints = question.test.constraints or ""
                    rubric = (
                        "Baholash mezonlari: \n"
                        "1) Savolga moslik (relevance) 0-40\n"
                        "2) Grammatik to'g'rilik 0-20\n"
                        "3) Leksik boylik 0-20\n"
                        "4) Tuzilish va kohesiya 0-20\n"
                    )
                    prompt = (
                        "Siz professional writing baholovchisiz. \n"
                        f"Savol: {question.text}\n"
                        f"Cheklovlar/shartlar (agar bo'lsa): {constraints}\n"
                        f"Foydalanuvchi javobi (OCR'dan): {processed_answer}\n\n"
                        f"{rubric}"
                        "Umumiy yakuniy bahoni 0-100 oralig'ida bering. Faqat JSON qaytaring: "
                        "{\"score\": <0-100>, \"comment\": \"qisqa va aniq tahlil, asosiy kamchiliklar va kuchli tomonlar\"}"
                    )

                final_response = process_test_response(
                    user,
                    test_result,
                    question,
                    processed_answer,
                    prompt,
                    client,
                    logger,
                    expect_json=True,
                    finalize=False,
                )
                if final_response is None:
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
                    
                    # Add word count information for multilevel tests
                    if validate_test_level(exam_level):
                        word_count = count_words(processed_answer)
                        final_response["word_count"] = word_count
                        final_response["question_part"] = question_part
                        if question_part == 1:
                            final_response["min_required"] = 70
                            final_response["target_words"] = 150
                        else:
                            final_response["min_required"] = 110
                            final_response["target_words"] = 250
                        
                        # Convert score from 0-100 to 0-75 for multilevel writing tests
                        original_score = final_response.get("score", 0)
                        final_response["score"] = round((original_score / 100) * 75)
                    
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

        # Testni yakunlash (faqat ushbu bo'limdagi barcha savollar baholanganidan so'ng)
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()
        
        # Calculate total score from responses
        total_score = sum(r['score'] for r in responses if r['score'] is not None)
        
        # For writing tests, save the score if we have valid responses, even if not all questions are answered
        # This handles cases where some questions might be skipped or failed to process
        if total_score > 0 and len(responses) > 0:
            # Cap to 75 as writing total is 25 + 50 = 75
            test_result.score = min(round(total_score), 75)
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
            "test_completed": test_result.status == 'completed',
            "score": total_score  # Always return the calculated total score
        }, status=status.HTTP_200_OK)