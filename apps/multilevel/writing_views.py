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
        # Custom parse for bulk form-data with multiple images per question
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            answers = []
            
            # Get all question IDs and image files with their indices and orders
            question_data = {}
            image_data = {}
            
            # Parse question IDs from answers[0][question] format
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
                            logger.info(f"Question ID found: index={index}, question_id={value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse question key '{key}': {e}")
                        continue
            
            # Parse image files from answers[0][writing_images][1][image] format
            for key, value in request.FILES.items():
                if key.startswith('answers[') and '][writing_images][' in key and key.endswith('][image]'):
                    try:
                        # Extract index and order: answers[0][writing_images][1][image] -> index=0, order=1
                        # More robust parsing method
                        if '][writing_images][' in key:
                            # Split by writing_images to get the parts
                            parts = key.split('][writing_images][')
                            if len(parts) == 2:
                                # First part: answers[0 -> extract index
                                index_part = parts[0]
                                if index_part.startswith('answers['):
                                    index_str = index_part[8:]  # Remove 'answers['
                                    index = int(index_str)
                                    
                                    # Second part: 1][image -> extract order
                                    order_part = parts[1]
                                    if order_part.endswith('][image]'):
                                        order_str = order_part[:-8]  # Remove '][image]'
                                        order = int(order_str)
                                        
                                        if index not in image_data:
                                            image_data[index] = {}
                                        image_data[index][order] = value
                                        logger.info(f"Image found: index={index}, order={order}, filename={value.name}")
                                    else:
                                        logger.warning(f"Invalid order format in key '{key}': {order_part}")
                                else:
                                    logger.warning(f"Invalid index format in key '{key}': {index_part}")
                            else:
                                logger.warning(f"Unexpected parts count in key '{key}': {parts}")
                        else:
                            logger.warning(f"Key '{key}' doesn't contain expected format")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse image key '{key}': {e}")
                        continue
            
            # Debug logging
            logger.info(f"Parsed question_data: {question_data}")
            logger.info(f"Parsed image_data: {image_data}")
            
            # Combine question IDs and image files
            all_indices = set(question_data.keys()) | set(image_data.keys())
            logger.info(f"All indices: {all_indices}")
            
            for index in sorted(all_indices):
                question_id = question_data.get(index)
                images_dict = image_data.get(index, {})
                
                logger.info(f"Processing index {index}: question_id={question_id}, images={images_dict}")
                
                if question_id is not None and images_dict:
                    # Sort images by order
                    sorted_images = []
                    for order in sorted(images_dict.keys()):
                        sorted_images.append({
                            'image': images_dict[order],
                            'order': order
                        })
                    
                    answer_item = {
                        'question': question_id,
                        'writing_images': sorted_images
                    }
                    answers.append(answer_item)
                    logger.info(f"Added answer item: {answer_item}")
                else:
                    logger.warning(f"Skipping index {index}: question_id={question_id}, images={images_dict}")
            
            data = {
                'test_result_id': request.data.get('test_result_id'),
                'answers': answers
            }
            
            logger.info(f"Final parsed data: {data}")
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
            
            # Vaqt chegarasi tekshirish
            from .utils import check_test_time_limit
            if check_test_time_limit(test_result):
                return Response({"error": "Test vaqti tugagan, javob qabul qilinmadi"}, status=status.HTTP_400_BAD_REQUEST)
                
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
            writing_images = answer['writing_images']  # List of images with order
            temp_file_paths = []
            
            try:
                # Barcha rasmlarni OCR qilish va birlashtirish
                all_texts = []
                
                for image_data in writing_images:
                    image_file = image_data['image']
                    order = image_data['order']
                    temp_file_path = None
                    
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                            for chunk in image_file.chunks():
                                temp_file.write(chunk)
                            temp_file_path = temp_file.name
                            temp_file_paths.append(temp_file_path)

                        with open(temp_file_path, "rb") as image_file_obj:
                            encoded_image = base64.b64encode(image_file_obj.read()).decode('utf-8')
                        image_url = f"data:image/jpeg;base64,{encoded_image}"

                        # OpenAI orqali OCR
                        try:
                            ocr_response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": f"Bu rasmda yozilgan matnni o'qib bering. Bu {order}-rasm."},
                                            {"type": "image_url", "image_url": {"url": image_url}},
                                        ],
                                    }
                                ],
                                max_tokens=500,
                            )
                            processed_text = ocr_response.choices[0].message.content if ocr_response.choices else None
                            
                            if processed_text:
                                all_texts.append(f"[Rasm {order}]: {processed_text}")
                            else:
                                all_texts.append(f"[Rasm {order}]: Matn aniqlanmadi")
                                
                        except Exception as e:
                            logger.error(f"OCR xatolik rasm {order} uchun: {str(e)}")
                            all_texts.append(f"[Rasm {order}]: OCR xatolik")
                            
                    except Exception as e:
                        logger.error(f"Rasm {order} qayta ishlashda xatolik: {str(e)}")
                        all_texts.append(f"[Rasm {order}]: Fayl xatolik")

                # Barcha matnlarni birlashtirish
                if all_texts:
                    processed_answer = "\n\n".join(all_texts)
                else:
                    processed_answer = None

                if processed_answer is None or not processed_answer.strip():
                    responses.append({
                        "message": "Barcha rasmlarda matn aniqlanmadi yoki OCR xatolik yuz berdi.",
                        "result": "OCR xatolik",
                        "score": 0,
                        "test_completed": False,
                        "user_answer": "",
                        "question_text": question.text,
                        "images_count": len(writing_images)
                    })
                    continue

                # Get exam level for scoring validation
                exam_level = test_result.user_test.exam.level
                
                # Determine question part based on test constraints or question order
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
                            "min_required": score_details['min_required'],
                            "images_count": len(writing_images)
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
                        f"Foydalanuvchi javobi ({len(writing_images)} ta rasmdan OCR'dan): {processed_answer}\n\n"
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
                        "question_text": question.text,
                        "images_count": len(writing_images)
                    })
                else:
                    final_response["message"] = f"Savol {question.id} uchun writing test ({len(writing_images)} ta rasm) muvaffaqiyatli tekshirildi"
                    final_response["user_answer"] = processed_answer
                    final_response["question_text"] = question.text
                    final_response["images_count"] = len(writing_images)
                    
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
                    "question_text": question.text,
                    "images_count": len(writing_images) if 'writing_images' in locals() else 0
                })
            finally:
                # Barcha vaqtinchalik fayllarni o'chirish
                for temp_file_path in temp_file_paths:
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception as e:
                            logger.error(f"Vaqtinchalik fayl o'chirishda xato: {str(e)}")

        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)

        # Calculate total score from responses
        total_score = sum(r['score'] for r in responses if r['score'] is not None)
        
        # Save the writing section score
        if total_score > 0 and len(responses) > 0:
            # Cap to 75 as writing total is 25 + 50 = 75
            test_result.score = min(round(total_score), 75)
            test_result.status = 'completed'
            test_result.end_time = timezone.now()
            test_result.save()

        # Check if this is a multilevel or tys exam
        user_test = test_result.user_test
        is_multilevel_exam = user_test.exam.level in ['multilevel', 'tys']
        
        # For multilevel/tys exams, only show section completion, not overall results
        if is_multilevel_exam:
            # Multilevel/TYS: barcha section'lar tugatilganda UserTest ni yakunlash
            all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
            total_sections = Section.objects.filter(exam=user_test.exam).count()
            completed_sections = all_test_results.count()
            
            if completed_sections >= total_sections:
                # Barcha section'lar tugatilgan, UserTest ni yakunlash
                total_score = sum(tr.score for tr in all_test_results)
                user_test.score = round(total_score / total_sections)  # O'rtacha score
                user_test.status = 'completed'
                user_test.save()
            else:
                # Hali section'lar tugatilmagan
                user_test.status = 'started'
                user_test.save()
            
            return Response({
                "answers": responses,
                "section_completed": True,
                "section_score": test_result.score,
                "message": "Writing section tugatildi. Barcha sectionlar tugagandan keyin umumiy natija ko'rsatiladi."
            }, status=status.HTTP_200_OK)
        else:
            # For other exam types, show immediate results
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