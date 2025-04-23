from celery import shared_task
from django.conf import settings
from django.utils import timezone
import os
import logging
from openai import OpenAI
import speech_recognition as sr
from .models import TestResult, UserAnswer, Question
from core.settings import base
# OpenAI sozlamalari

OPENAI_API_KEY = base.OPENAI_API_KEY 
client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

# Writing testni asinxron tekshirish
@shared_task
def process_writing_test(test_result_id, question_id, image_path):
    """
    Writing test javobini OpenAI orqali asinxron tekshiradi.
    Args:
        test_result_id (int): TestResult ID
        question_id (int): Question ID
        image_path (str): Saqlangan rasmning yo‘li
    Returns:
        dict: Tekshiruv natijalari (message, result, score, user_answer, question_text)
    """
    try:
        # TestResult va Question ni olish
        test_result = TestResult.objects.get(id=test_result_id, status='started')
        question = Question.objects.get(id=question_id)

        # Section turini tekshirish
        if test_result.section.type != 'writing':
            logger.error(f"TestResult {test_result_id} writing testiga mos emas")
            return {"error": "Bu test writing testiga mos emas"}

        # Rasmni matnga aylantirish (OCR)
        image_url = f"{settings.MEDIA_URL}writing_images/{os.path.basename(image_path)}"
        ocr_response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Bu rasmda yozilgan matnni o'qib bering."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
        )
        processed_answer = ocr_response.choices[0].message.content

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi til imtihoni uchun writing javobini yubordi: '{processed_answer}'. "
            f"Savol: '{question.text}'. "
            "Javobni grammatika, so'z boyligi, mazmun va tuzilishi bo'yicha tekshirib, "
            "batafsil izoh bilan 0-100 oralig'ida baho bering. "
            "Javobingizni quyidagi formatda bering: "
            "Izoh: [batafsil izoh]\n"
            "Baho: [0-100 oralig'ida son]"
        )

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        result = gpt_response.choices[0].message.content

        # Bahoni ajratib olish
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

            test_result.user_test.score = round(score)
            test_result.user_test.status = 'completed'
            test_result.user_test.save()

        return {
            "message": "Writing test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score,
            "test_completed": test_completed,
            "user_answer": processed_answer,
            "question_text": question.text
        }

    except TestResult.DoesNotExist:
        logger.error(f"TestResult {test_result_id} topilmadi")
        return {"error": "Test natijasi topilmadi"}
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} topilmadi")
        return {"error": "Savol topilmadi"}
    except Exception as e:
        logger.error(f"Writing test tekshirishda xato: {str(e)}")
        if "rate_limit" in str(e).lower():
            return {"error": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko‘ring"}
        return {"error": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring"}

# Speaking testni asinxron tekshirish
@shared_task
def process_speaking_test(test_result_id, question_id, audio_path):
    """
    Speaking test javobini asinxron tekshiradi.
    Args:
        test_result_id (int): TestResult ID
        question_id (int): Question ID
        audio_path (str): Saqlangan audioning yo‘li
    Returns:
        dict: Tekshiruv natijalari (message, result, score, user_answer, question_text)
    """
    try:
        # TestResult va Question ni olish
        test_result = TestResult.objects.get(id=test_result_id, status='started')
        question = Question.objects.get(id=question_id)

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

        # ChatGPT bilan tekshirish
        prompt = (
            f"Foydalanuvchi til imtihoni uchun speaking javobini yubordi: '{processed_answer}'. "
            f"Savol: '{question.text}'. "
            "Javobni talaffuz, grammatika, so'z boyligi, mazmun va ravonligi bo'yicha tekshirib, "
            "batafsil izoh bilan 0-100 oralig'ida baho bering. "
            "Javobingizni quyidagi formatda bering: "
            "Izoh: [batafsil izoh]\n"
            "Baho: [0-100 oralig'ida son]"
        )

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        result = gpt_response.choices[0].message.content

        # Bahoni ajratib olish
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

            test_result.user_test.score = round(score)
            test_result.user_test.status = 'completed'
            test_result.user_test.save()

        return {
            "message": "Speaking test muvaffaqiyatli tekshirildi",
            "result": result,
            "score": score,
            "test_completed": test_completed,
            "user_answer": processed_answer,
            "question_text": question.text
        }

    except TestResult.DoesNotExist:
        logger.error(f"TestResult {test_result_id} topilmadi")
        return {"error": "Test natijasi topilmadi"}
    except Question.DoesNotExist:
        logger.error(f"Question {question_id} topilmadi")
        return {"error": "Savol topilmadi"}
    except Exception as e:
        logger.error(f"Speaking test tekshirishda xato: {str(e)}")
        if "rate_limit" in str(e).lower():
            return {"error": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko‘ring"}
        return {"error": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring"}

# Vaqtinchalik fayllarni tozalash vazifasi
@shared_task
def cleanup_temp_file_task(file_path):
    """
    Vaqtinchalik faylni o‘chiradi.
    Args:
        file_path (str): O‘chiriladigan faylning yo‘li
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Fayl o‘chirildi: {file_path}")
        else:
            logger.warning(f"Fayl topilmadi: {file_path}")
    except Exception as e:
        logger.error(f"Fayl o‘chirishda xato: {str(e)}")