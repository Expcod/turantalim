import logging
import os
import tempfile
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from openai import OpenAI, OpenAIError
from .models import TestResult, UserAnswer, Section, Question
from .utils import process_test_response
from .serializers import SpeakingTestResponseSerializer
from .speaking_serializers import BulkSpeakingTestCheckSerializer
from .multilevel_score import get_speaking_prompt, validate_test_level, count_words, process_speaking_response
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
            
            # Get all question IDs and audio files with their indices
            question_data = {}
            audio_data = {}
            
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
            
            # Parse audio files
            for key, value in request.FILES.items():
                if key.startswith('answers[') and key.endswith('][speaking_audio]'):
                    try:
                        # Extract index: answers[0][speaking_audio] -> 0
                        start_idx = key.find('[') + 1
                        end_idx = key.find('][speaking_audio]')
                        if start_idx > 0 and end_idx > start_idx:
                            index_str = key[start_idx:end_idx]
                            index = int(index_str)
                            audio_data[index] = value
                    except (ValueError, IndexError):
                        continue
            
            # Combine question IDs and audio files
            all_indices = set(question_data.keys()) | set(audio_data.keys())
            
            for index in sorted(all_indices):
                question_id = question_data.get(index)
                audio_file = audio_data.get(index)
                
                if question_id is not None:
                    answer_item = {
                        'question': question_id,
                        'speaking_audio': audio_file
                    }
                    answers.append(answer_item)
            
            data = {
                'test_result_id': request.data.get('test_result_id'),
                'answers': answers
            }
        else:
            data = request.data

        serializer = BulkSpeakingTestCheckSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        # TestResult ni tekshirish
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=request.user, status='started')
            # Test tekshirilgan bo'lsa, uni completed ga o'tkazish
            test_result.status = 'completed'
            test_result.save()
        except TestResult.DoesNotExist:
            return Response({"error": "TestResult topilmadi yoki faol emas!"}, status=status.HTTP_403_FORBIDDEN)

        # Javoblarni qayta ishlash
        client = OpenAI(api_key=base.OPENAI_API_KEY)
        responses = self.process_answers(request.user, test_result, answers_data, client)

        # Testni yakunlash (faqat barcha savollar baholanganidan keyin)
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()
        
        # Calculate total score from responses
        total_score = sum(r['score'] for r in responses if r['score'] is not None)
        
        # For speaking tests, save the score if we have valid responses, even if not all questions are answered
        # This handles cases where some questions might be skipped or failed to process
        if total_score > 0 and len(responses) > 0:
            # Speaking max score for multilevel is 75
            test_result.score = min(round(total_score), 75)
            test_result.status = 'completed'
            test_result.end_time = timezone.now()
            test_result.save()

        final_response = {
            "answers": responses,
            "test_completed": test_result.status == 'completed',
            "score": total_score  # Always return the calculated total score
        }

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
            speaking_audio = answer_data.get('speaking_audio')

            # Agar audio yuborilmagan bo'lsa, bu savolni o'tkazib yuborish
            if speaking_audio is None:
                responses.append({
                    "message": f"Savol {question.id} uchun audio yuborilmagan",
                    "result": "Audio yuborilmagan",
                    "score": 0,
                    "test_completed": False,
                    "user_answer": "",
                    "question_text": question.text
                })
                continue

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
                                timeout=60  # 60 second timeout
                            )
                        except (OpenAIError, Exception) as e:
                            # Try without language parameter
                            audio_file.seek(0)
                            try:
                                transcription = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    timeout=60
                                )
                            except (OpenAIError, Exception) as e2:
                                # If both attempts fail, return error
                                responses.append({
                                    "message": f"Whisper API xatosi: {str(e2)}",
                                    "result": "Transkripsiya qilinmadi",
                                    "score": 0,
                                    "test_completed": False,
                                    "user_answer": "",
                                    "question_text": question.text
                                })
                                continue
                    processed_answer = transcription.text
                except Exception as e:
                    responses.append({
                        "message": f"Audio fayl o'qishda xatolik: {str(e)}",
                        "result": "Transkripsiya qilinmadi",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text
                    })
                    continue

                # Get exam level for scoring validation
                exam_level = test_result.user_test.exam.level
                
                # Check if multilevel scoring should be used
                if validate_test_level(exam_level):
                    # Use multilevel speaking scoring system
                    prompt = get_speaking_prompt(question.text, question.test.constraints or "", processed_answer)
                else:
                    # Fallback to original scoring for other levels
                    constraints = question.test.constraints or ""
                    rubric = (
                        "Baholash mezonlari: \n"
                        "1) Savolga moslik (relevance) 0-35\n"
                        "2) Talaffuz va ravonlik 0-25\n"
                        "3) Grammatik to'g'rilik 0-20\n"
                        "4) Leksik boylik 0-20\n"
                    )
                    prompt = (
                        "Siz professional speaking baholovchisiz. \n"
                        f"Savol: {question.text}\n"
                        f"Cheklovlar/shartlar (agar bo'lsa): {constraints}\n"
                        f"Foydalanuvchi javobi (transkripsiya): {processed_answer}\n\n"
                        f"{rubric}"
                        "Umumiy yakuniy bahoni 0-100 oralig'ida bering. Faqat JSON qaytaring: "
                        "{\"score\": <0-100>, \"comment\": \"qisqa va aniq tahlil, talaffuz va mazmun bo'yicha fikrlar\"}"
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
                final_response["message"] = f"Savol {question.id} uchun speaking test muvaffaqiyatli tekshirildi"
                
                # Process enhanced response for multilevel tests
                if validate_test_level(exam_level):
                    word_count = count_words(processed_answer)
                    final_response["word_count"] = word_count
                    final_response["max_score"] = 75  # Speaking max score for multilevel
                    
                    # Convert score from 0-100 to 0-75 for multilevel speaking tests
                    original_score = final_response.get("score", 0)
                    final_response["score"] = round((original_score / 100) * 75)
                    
                    # Process the enhanced response format but only keep score and comment
                    try:
                        # Try to parse the result as JSON to get detailed criteria
                        import json
                        result_text = final_response.get("result", "")
                        if result_text and result_text.strip().startswith('{'):
                            try:
                                parsed_response = json.loads(result_text)
                                processed_response = process_speaking_response(parsed_response)
                                if processed_response['is_valid']:
                                    # Only keep score and detailed comment, exclude criteria details
                                    final_response["score"] = processed_response['score']
                                    final_response["result"] = processed_response['detailed_comment']
                            except json.JSONDecodeError:
                                # If JSON parsing fails, keep original response
                                pass
                    except Exception:
                        # If processing fails, keep original response
                        pass

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
                    except Exception:
                        # Ignore file deletion errors
                        pass

        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)

        return responses