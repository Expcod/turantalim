# multilevel/utils.py ga qo'shish kerak (agar mavjud bo'lmasa)

from django.utils import timezone
from .models import TestResult, UserAnswer, Question
from rest_framework.response import Response
from rest_framework import status

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

def process_test_response(user, test_result, question, processed_answer, prompt, client, logger):
    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )
        result = gpt_response.choices[0].message.content

        score_text = result.split("Baho:")[-1].strip() if "Baho:" in result else "50"
        score = max(0, min(100, int(''.join(filter(str.isdigit, score_text.split()[0])))))
        is_correct = score >= 50
    except Exception as e:
        logger.error(f"ChatGPT xatosi: {str(e)}")
        if "rate_limit" in str(e).lower():
            raise Exception("OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko‘ring")
        raise Exception("Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko‘ring")

    save_user_answer(test_result, question, processed_answer, is_correct)
    final_response = finalize_test_result(test_result, score)
    final_response.update({
        "result": result,
        "score": score,
        "user_answer": processed_answer,
        "question_text": question.text
    })
    return final_response

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

    test_result.user_test.score = round(score)
    test_result.user_test.status = 'completed'
    test_result.user_test.save()

    return {
        "test_completed": True,
        "score": round(score)
    }