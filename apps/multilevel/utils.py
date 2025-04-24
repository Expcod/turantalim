# apps/multilevel/utils.py
import logging
from django.utils import timezone
from openai import OpenAI
from .models import TestResult, UserAnswer, UserTest, Question
from rest_framework.response import Response
from rest_framework import status

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
        test_result.user_test.status = 'completed'
        test_result.user_test.save()
        return Response({"error": "Test vaqti tugagan, yangi test so'rang"}, status=status.HTTP_400_BAD_REQUEST)

    return test_result

# apps/multilevel/utils.py
def process_test_response(user, test_result, question, processed_answer, prompt, client, logger=None):
    """OpenAI’dan javob olish va TestResult ni yangilash"""
    if logger is None:
        logger = logging.getLogger(__name__)  # Standart logger

    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        result = gpt_response.choices[0].message.content

        # Izoh va bahoni ajratish
        lines = result.split("\n")
        comment = lines[0].replace("Izoh: ", "").strip()
        score_line = lines[1].replace("Baho: ", "").strip()
        score = max(0, min(100, int(score_line)))
        is_correct = score >= 50

        # Foydalanuvchi javobini saqlash
        save_user_answer(test_result, question, processed_answer, is_correct)

        # Test natijasini yakunlash
        final_response = finalize_test_result(test_result, score)
        final_response.update({
            "comment": comment,
            "score": score,
            "user_answer": processed_answer,
            "question_text": question.text
        })
        return final_response

    except OpenAI.NotFoundError as e:
        logger.error(f"OpenAI model topilmadi: {str(e)}")
        raise Exception(f"OpenAI model topilmadi: {str(e)}")
    except OpenAI.RateLimitError as e:
        logger.error(f"OpenAI API limiti oshib ketdi: {str(e)}")
        raise Exception("OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko‘ring")
    except Exception as e:
        logger.error(f"OpenAI javobini qayta ishlashda xato: {str(e)}")
        raise Exception("Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring")

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

    # UserTest uchun umumiy score ni yangilash (barcha TestResult larni hisobga olib)
    user_test = test_result.user_test
    all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
    if all_test_results.exists():
        total_score = sum(tr.score for tr in all_test_results) / all_test_results.count()
        user_test.score = round(total_score)
        user_test.status = 'completed' if all_test_results.count() == user_test.exam.sections.count() else 'started'
        user_test.save()

    return {
        "test_completed": True,
        "score": round(score)
    }