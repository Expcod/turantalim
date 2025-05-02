# apps/multilevel/utils.py
import logging
from django.utils import timezone
from openai import OpenAI, OpenAIError, RateLimitError
from .models import Section, TestResult, UserAnswer, UserTest, Question
from rest_framework.response import Response
from rest_framework import status
import re  # re modulini import qilish

logger = logging.getLogger(__name__)

def get_or_create_test_result(user, test_result_id, question):
    """TestResult ni olish yoki yaratish"""
    if test_result_id:
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
        except TestResult.DoesNotExist:
            return Response({"error": "Bu ID ga mos faol TestResult mavjud emas"}, status=status.HTTP_403_FORBIDDEN)
    else:
        test_result = TestResult.objects.filter(
            user_test__user=user,
            section=question.test.section,
            status='started'
        ).last()
        if not test_result:
            return Response({"error": "Ushbu bo'lim uchun faol test topilmadi!"}, status=status.HTTP_400_BAD_REQUEST)

    if test_result.end_time and test_result.end_time < timezone.now():
        test_result.status = 'completed'
        test_result.save()
        user_test = test_result.user_test
        user_test.status = 'completed' if not TestResult.objects.filter(user_test=user_test, status='started').exists() else 'started'
        user_test.save()
        return Response({"error": "Test vaqti tugagan, yangi test so'rang"}, status=status.HTTP_400_BAD_REQUEST)

    return test_result

def process_test_response(user, test_result, question, processed_answer, prompt, client, logger=None):
    """
    Writing yoki Speaking test uchun OpenAI orqali baholash funksiyasi
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Siz professional IELTS baholovchisiz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        reply_text = response.choices[0].message.content.strip()

        # Izoh va bahoni ajratish
        lines = reply_text.split("\n")
        
        # Izoh qismini yig‘ish
        comment_lines = []
        score_line = None
        for line in lines:
            if line.startswith("Baho:"):
                score_line = line
                break
            if line.strip():  # Bo‘sh qatorlarni o‘tkazib yuboramiz
                comment_lines.append(line.replace("Izoh: ", "").strip())
        
        if not score_line:
            logger.warning(f"Bahoni ajratib bo‘lmadi: {reply_text}, qatorlar: {lines}")
            score = 0
        else:
            # Bahodan faqat raqamni olish
            score_match = re.search(r'\d+', score_line)
            if score_match:
                score = int(score_match.group())
                score = max(0, min(100, score))
            else:
                logger.warning(f"Bahoni ajratib bo‘lmadi: {reply_text}")
                score = 0

        comment = " ".join(comment_lines)  # Izohlarni birlashtirish

        # TestResult ni yangilash
        test_result.score = round(score)
        test_result.status = 'completed'
        test_result.end_time = timezone.now()
        test_result.save()

        # UserTest uchun umumiy score ni yangilash
        user_test = test_result.user_test
        all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
        if all_test_results.exists():
            total_score = sum(tr.score for tr in all_test_results) / all_test_results.count()
            user_test.score = round(total_score)
            user_test.status = 'completed' if all_test_results.count() == Section.objects.filter(exam=user_test.exam).count() else 'started'
            user_test.save()

        return {
            "score": score,
            "result": reply_text,
            "test_completed": True,
            "user_answer": processed_answer,
            "question_text": question.text,
        }

    except OpenAIError as e:
        if "404" in str(e) or "not found" in str(e).lower():
            logger.error(f"OpenAI model topilmadi: {str(e)}")
            return {
                "score": 0,
                "result": f"OpenAI model topilmadi: {str(e)}",
                "test_completed": False,
                "user_answer": processed_answer,
                "question_text": question.text,
            }
        logger.error(f"OpenAI xatolik: {str(e)}")
        return {
            "score": 0,
            "result": str(e),
            "test_completed": False,
            "user_answer": processed_answer,
            "question_text": question.text,
        }
    except RateLimitError as e:
        logger.error(f"OpenAI API limiti oshib ketdi: {str(e)}")
        return {
            "score": 0,
            "result": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko‘ring",
            "test_completed": False,
            "user_answer": processed_answer,
            "question_text": question.text,
        }
    except Exception as e:
        logger.error(f"OpenAI javobini qayta ishlashda xato: {str(e)}")
        return {
            "score": 0,
            "result": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring",
            "test_completed": False,
            "user_answer": processed_answer,
            "question_text": question.text,
        }

def save_user_answer(test_result, question, user_answer, is_correct):
    """Foydalanuvchi javobini saqlash"""
    UserAnswer.objects.create(
        test_result=test_result,
        question=question,
        user_answer=user_answer,
        is_correct=is_correct
    )

def finalize_test_result(test_result, score):
    """Test natijasini yakunlash"""
    test_result.status = 'completed'
    test_result.score = round(score)
    test_result.end_time = timezone.now()
    test_result.save()

    # UserTest uchun umumiy score ni yangilash
    user_test = test_result.user_test
    all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
    if all_test_results.exists():
        total_score = sum(tr.score for tr in all_test_results) / all_test_results.count()
        user_test.score = round(total_score)
        user_test.status = 'completed' if all_test_results.count() == Section.objects.filter(exam=user_test.exam).count() else 'started'
        user_test.save()

    return {
        "test_completed": True,
        "score": round(score)
    }