from celery import shared_task
from django.conf import settings
from django.utils import timezone
import os
import logging
from openai import OpenAI
import speech_recognition as sr
from .models import TestResult, UserAnswer, Question, Section
from .multilevel_score import (
    get_writing_score_details, get_writing_prompt, get_speaking_prompt, 
    validate_test_level, count_words, process_speaking_response
)
from core.settings import base
# OpenAI sozlamalari

OPENAI_API_KEY = base.OPENAI_API_KEY 
client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

# Writing testni asinxron tekshirish (ko'p rasmli)
@shared_task
def process_writing_test(test_result_id, question_id, image_paths_data):
    """
    Writing test javobini OpenAI orqali asinxron tekshiradi (ko'p rasmli).
    Args:
        test_result_id (int): TestResult ID
        question_id (int): Question ID
        image_paths_data (list): Rasmlar ma'lumotlari [{'path': 'path/to/image', 'order': 1}, ...]
    Returns:
        dict: Tekshiruv natijalari (message, result, score, user_answer, question_text)
    """
    try:
        # TestResult va Question ni olish
        test_result = TestResult.objects.get(id=test_result_id, status='started')
        question = Question.objects.get(id=question_id)

        # Test tekshirilgan bo'lsa, uni completed ga o'tkazish
        test_result.status = 'completed'
        test_result.save()

        # Section turini tekshirish
        if test_result.section.type != 'writing':
            logger.error(f"TestResult {test_result_id} writing testiga mos emas")
            return {"error": "Bu test writing testiga mos emas"}

        # Barcha rasmlarni OCR qilish va birlashtirish
        all_texts = []
        
        for image_data in image_paths_data:
            image_path = image_data['path']
            order = image_data['order']
            
            try:
                # Rasmni matnga aylantirish (OCR)
                image_url = f"{settings.MEDIA_URL}writing_images/{os.path.basename(image_path)}"
                ocr_response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Bu rasmda yozilgan matnni o'qib bering. Bu {order}-rasm."},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                )
                processed_text = ocr_response.choices[0].message.content
                
                if processed_text:
                    all_texts.append(f"[Rasm {order}]: {processed_text}")
                else:
                    all_texts.append(f"[Rasm {order}]: Matn aniqlanmadi")
                    
            except Exception as e:
                logger.error(f"OCR xatolik rasm {order} uchun: {str(e)}")
                all_texts.append(f"[Rasm {order}]: OCR xatolik")

        # Barcha matnlarni birlashtirish
        if all_texts:
            processed_answer = "\n\n".join(all_texts)
        else:
            processed_answer = "Barcha rasmlarda matn aniqlanmadi"

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
                return {
                    "message": score_details['reason'],
                    "result": "Matn juda qisqa",
                    "score": 0,
                    "test_completed": False,
                    "user_answer": processed_answer,
                    "question_text": question.text,
                    "word_count": score_details['word_count'],
                    "min_required": score_details['min_required']
                }
            
            # Generate comprehensive prompt for multilevel scoring
            prompt = get_writing_prompt(question.text, question.test.constraints or "", processed_answer, question_part)
        else:
            # Fallback to original scoring for other levels
            prompt = (
            f"Foydalanuvchi til imtihoni uchun writing javobini yubordi ({len(image_paths_data)} ta rasmdan): '{processed_answer}'. "
            f"Savol: '{question.text}'. "
            "Javobni grammatika, so'z boyligi, mazmun va tuzilishi bo'yicha tekshirib, "
            "batafsil izoh bilan 0-100 oralig'ida baho bering. "
            "Javobingizni quyidagi formatda bering: "
            "Izoh: [batafsil izoh]\n"
            "Baho: [0-100 oralig'ida son]"
        )

        # ChatGPT bilan tekshirish
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
        )
        result = gpt_response.choices[0].message.content

        # Process response based on scoring system
        if validate_test_level(exam_level):
            # Try to parse JSON response for multilevel scoring
            try:
                import json
                if result.strip().startswith('{'):
                    parsed_response = json.loads(result)
                    score = parsed_response.get('score', 0)
                    is_correct = score >= (25 if question_part == 1 else 50) * 0.6  # 60% threshold
                else:
                    # Fallback to simple score extraction
                    score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "0"
                    score = max(0, min(75, int(''.join(filter(str.isdigit, score_text.split()[0])))))
                    is_correct = score >= (25 if question_part == 1 else 50) * 0.6
            except (json.JSONDecodeError, ValueError):
                # Fallback to simple score extraction
                score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "0"
                score = max(0, min(75, int(''.join(filter(str.isdigit, score_text.split()[0])))))
                is_correct = score >= (25 if question_part == 1 else 50) * 0.6
        else:
            # Original scoring for non-multilevel tests
            score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "50"
            score = max(0, min(100, int(''.join(filter(str.isdigit, score_text.split()[0])))))
            is_correct = score >= 50

        # Foydalanuvchi javobini saqlash
        UserAnswer.objects.create(
            test_result=test_result,
            question=question,
            user_answer=processed_answer,
            is_correct=is_correct
        )

        # Test natijasini yakunlash
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()
        test_completed = total_questions == answered_questions

        if test_completed:
            test_result.status = 'completed'
            test_result.score = round(score)
            test_result.end_time = timezone.now()
            test_result.save()

            # Multilevel imtihonlar uchun maxsus logika
            user_test = test_result.user_test
            if user_test.exam.level == 'multilevel':
                # Multilevel: barcha section'lar tugatilganda UserTest ni yakunlash
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
            else:
                # Boshqa level'lar: har bir section uchun alohida
                user_test.score = round(score)
                user_test.status = 'completed'  # Har bir section tugatilganda UserTest ham tugaydi
                user_test.save()

        # Prepare response
        response_data = {
            "message": f"Writing test ({len(image_paths_data)} ta rasm) muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score,
            "test_completed": test_completed,
            "user_answer": processed_answer,
            "question_text": question.text,
            "images_count": len(image_paths_data)
        }

        # Add additional info for multilevel tests
        if validate_test_level(exam_level):
            word_count = count_words(processed_answer)
            response_data.update({
                "word_count": word_count,
                "question_part": question_part,
                "max_score": score_details['max_score'],
                "min_required": score_details['min_required'],
                "target_words": score_details['target_words']
            })

        return response_data

    except TestResult.DoesNotExist:
        logger.error(f"TestResult {test_result_id} topilmadi")
        return {"error": "Test natijasi topilmadi"}
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} topilmadi")
        return {"error": "Savol topilmadi"}
    except Exception as e:
        logger.error(f"Writing test tekshirishda xato: {str(e)}")
        if "rate_limit" in str(e).lower():
            return {"error": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko'ring"}
        return {"error": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko'ring"}

# Speaking testni asinxron tekshirish
@shared_task
def process_speaking_test(test_result_id, question_id, audio_path):
    """
    Speaking test javobini asinxron tekshiradi.
    Args:
        test_result_id (int): TestResult ID
        question_id (int): Question ID
        audio_path (str): Saqlangan audioning yo'li
    Returns:
        dict: Tekshiruv natijalari (message, result, score, user_answer, question_text)
    """
    try:
        # TestResult va Question ni olish
        test_result = TestResult.objects.get(id=test_result_id, status='started')
        question = Question.objects.get(id=question_id)

        # Test tekshirilgan bo'lsa, uni completed ga o'tkazish
        test_result.status = 'completed'
        test_result.save()

        # Section turini tekshirish
        if test_result.section.type != 'speaking':
            logger.error(f"TestResult {test_result_id} speaking testiga mos emas")
            return {"error": "Bu test speaking testiga mos emas"}

        # Audio faylni matnga aylantirish (Speech-to-Text)
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            language_code = test_result.section.exam.language.code if test_result.section.exam.language else "tr-TR"
            processed_answer = recognizer.recognize_google(audio, language=language_code)

        # Get exam level for scoring validation
        exam_level = test_result.user_test.exam.level
        
        # Check if multilevel scoring should be used
        if validate_test_level(exam_level):
            # Use multilevel speaking scoring system
            prompt = get_speaking_prompt(question.text, question.test.constraints or "", processed_answer)
        else:
            # Fallback to original scoring for other levels
            prompt = (
                f"Foydalanuvchi til imtihoni uchun speaking javobini yubordi: '{processed_answer}'. "
                f"Savol: '{question.text}'. "
                "Javobni talaffuz, grammatika, so'z boyligi, mazmun va ravonligi bo'yicha tekshirib, "
                "batafsil izoh bilan 0-100 oralig'ida baho bering. "
                "Javobingizni quyidagi formatda bering: "
                "Izoh: [batafsil izoh]\n"
                "Baho: [0-100 oralig'ida son]"
            )

        # ChatGPT bilan tekshirish
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500,
        )
        result = gpt_response.choices[0].message.content

        # Process response based on scoring system
        if validate_test_level(exam_level):
            # Try to parse JSON response for multilevel scoring
            try:
                import json
                if result.strip().startswith('{'):
                    parsed_response = json.loads(result)
                    processed_response = process_speaking_response(parsed_response)
                    if processed_response['is_valid']:
                        score = processed_response['score']
                        is_correct = score >= 45  # 60% threshold for 75 max score
                        result = processed_response['detailed_comment']
                    else:
                        # Fallback to simple score extraction
                        score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "0"
                        score = max(0, min(75, int(''.join(filter(str.isdigit, score_text.split()[0])))))
                        is_correct = score >= 45
                else:
                    # Fallback to simple score extraction
                    score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "0"
                    score = max(0, min(75, int(''.join(filter(str.isdigit, score_text.split()[0])))))
                    is_correct = score >= 45
            except (json.JSONDecodeError, ValueError):
                # Fallback to simple score extraction
                score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "0"
                score = max(0, min(75, int(''.join(filter(str.isdigit, score_text.split()[0])))))
                is_correct = score >= 45
        else:
            # Original scoring for non-multilevel tests
            score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "50"
            score = max(0, min(100, int(''.join(filter(str.isdigit, score_text.split()[0])))))
            is_correct = score >= 50

        # Foydalanuvchi javobini saqlash
        UserAnswer.objects.create(
            test_result=test_result,
            question=question,
            user_answer=processed_answer,
            is_correct=is_correct
        )

        # Test natijasini yakunlash
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()
        test_completed = total_questions == answered_questions

        if test_completed:
            test_result.status = 'completed'
            test_result.score = round(score)
            test_result.end_time = timezone.now()
            test_result.save()

            # Multilevel imtihonlar uchun maxsus logika
            user_test = test_result.user_test
            if user_test.exam.level == 'multilevel':
                # Multilevel: barcha section'lar tugatilganda UserTest ni yakunlash
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
            else:
                # Boshqa level'lar: har bir section uchun alohida
                user_test.score = round(score)
                user_test.status = 'completed'  # Har bir section tugatilganda UserTest ham tugaydi
                user_test.save()

        # Prepare response
        response_data = {
            "message": "Speaking test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score,
            "test_completed": test_completed,
            "user_answer": processed_answer,
            "question_text": question.text
        }

        # Add additional info for multilevel tests
        if validate_test_level(exam_level):
            word_count = count_words(processed_answer)
            response_data.update({
                "word_count": word_count,
                "max_score": 75,  # Speaking max score for multilevel
            })

        return response_data

    except TestResult.DoesNotExist:
        logger.error(f"TestResult {test_result_id} topilmadi")
        return {"error": "Test natijasi topilmadi"}
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} topilmadi")
        return {"error": "Savol topilmadi"}
    except Exception as e:
        logger.error(f"Speaking test tekshirishda xato: {str(e)}")
        if "rate_limit" in str(e).lower():
            return {"error": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko'ring"}
        return {"error": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko'ring"}

# Vaqtinchalik fayllarni tozalash vazifasi
@shared_task
def cleanup_temp_file_task(file_path):
    """
    Vaqtinchalik faylni o'chiradi.
    Args:
        file_path (str): O'chiriladigan faylning yo'li
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Fayl o'chirildi: {file_path}")
        else:
            logger.warning(f"Fayl topilmadi: {file_path}")
    except Exception as e:
        logger.error(f"Fayl o'chirishda xato: {str(e)}")

# Vaqt chegarasi tugaganda testni avtomatik yakunlash
@shared_task
def auto_complete_test(test_result_id):
    """
    Vaqt chegarasi tugaganda testni avtomatik yakunlaydi.
    Args:
        test_result_id (int): TestResult ID
    Returns:
        dict: Yakunlash natijasi
    """
    try:
        test_result = TestResult.objects.get(id=test_result_id, status='started')
        
        # Testni completed ga o'tkazish
        test_result.status = 'completed'
        test_result.end_time = timezone.now()
        test_result.save()
        
        # UserTest ni ham tekshirish
        user_test = test_result.user_test
        active_tests = TestResult.objects.filter(user_test=user_test, status='started')
        
        if not active_tests.exists():
            user_test.status = 'completed'
            user_test.save()
        
        logger.info(f"Test {test_result_id} vaqt chegarasi tugagani uchun avtomatik yakunlandi")
        
        return {
            "success": True,
            "message": f"Test {test_result_id} avtomatik yakunlandi",
            "test_result_id": test_result_id
        }
        
    except TestResult.DoesNotExist:
        logger.warning(f"TestResult {test_result_id} topilmadi")
        return {
            "success": False,
            "message": f"TestResult {test_result_id} topilmadi"
        }
    except Exception as e:
        logger.error(f"Test {test_result_id} yakunlashda xatolik: {str(e)}")
        return {
            "success": False,
            "message": f"Xatolik: {str(e)}"
        }

# Muntazam tekshirish - vaqt chegarasi tugagan testlarni topish
@shared_task
def check_expired_tests():
    """
    Vaqt chegarasi tugagan testlarni muntazam tekshirib, ularni avtomatik yakunlaydi.
    Bu task celery beat orqali muntazam ishga tushiriladi.
    """
    try:
        # Vaqt chegarasi tugagan, lekin hali started holatda bo'lgan testlarni topish
        expired_tests = TestResult.objects.filter(
            status='started',
            end_time__lt=timezone.now()
        )
        
        completed_count = 0
        for test_result in expired_tests:
            try:
                # Testni completed ga o'tkazish
                test_result.status = 'completed'
                test_result.save()
                
                # UserTest ni ham tekshirish
                user_test = test_result.user_test
                active_tests = TestResult.objects.filter(user_test=user_test, status='started')
                
                if not active_tests.exists():
                    user_test.status = 'completed'
                    user_test.save()
                
                completed_count += 1
                logger.info(f"Test {test_result.id} vaqt chegarasi tugagani uchun avtomatik yakunlandi")
                
            except Exception as e:
                logger.error(f"Test {test_result.id} yakunlashda xatolik: {str(e)}")
        
        if completed_count > 0:
            logger.info(f"{completed_count} ta test vaqt chegarasi tugagani uchun avtomatik yakunlandi")
        
        return {
            "success": True,
            "completed_count": completed_count,
            "message": f"{completed_count} ta test avtomatik yakunlandi"
        }
        
    except Exception as e:
        logger.error(f"Vaqt chegarasi tekshirishda xatolik: {str(e)}")
        return {
            "success": False,
            "message": f"Xatolik: {str(e)}"
        }

# Vaqt chegarasi tekshirish va task rejalashtirish
@shared_task
def schedule_test_completion(test_result_id, duration_minutes):
    """
    Test uchun vaqt chegarasi task'ini rejalashtiradi.
    Args:
        test_result_id (int): TestResult ID
        duration_minutes (int): Test vaqti (daqiqa)
    """
    from celery import current_app
    
    # Vaqt chegarasi tugaganda auto_complete_test ni ishga tushirish
    eta = timezone.now() + timezone.timedelta(minutes=duration_minutes)
    
    current_app.send_task(
        'apps.multilevel.tasks.auto_complete_test',
        args=[test_result_id],
        eta=eta
    )
    
    logger.info(f"Test {test_result_id} uchun vaqt chegarasi rejalashtirildi: {eta}")

# Stale manual reviews ni avtomatik pending ga qaytarish
@shared_task
def reset_stale_manual_reviews():
    """
    12 soatdan eski 'reviewing' statusdagi manual review larni 
    'pending' statusga qaytaradi.
    Bu task celery beat orqali har 30 daqiqada ishga tushiriladi.
    """
    from django.core.management import call_command
    from io import StringIO
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Management command ni ishga tushirish
        output = StringIO()
        call_command('reset_stale_reviews', stdout=output)
        result = output.getvalue()
        
        logger.info(f"Stale reviews reset task completed: {result}")
        
        return {
            "success": True,
            "message": "Stale reviews reset task completed",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Stale reviews reset task failed: {str(e)}")
        return {
            "success": False,
            "message": f"Task failed: {str(e)}"
        }