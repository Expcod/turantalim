# multilevel/utils.py
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
            return Response({"error": "Ushbu bo‘lim uchun faol test topilmadi!"}, status=status.HTTP_400_BAD_REQUEST)

    if test_result.end_time and test_result.end_time < timezone.now():
        test_result.status = 'completed'
        test_result.save()
        test_result.user_test.status = 'completed'
        test_result.user_test.save()
        return Response({"error": "Test vaqti tugagan, yangi test so‘rang"}, status=status.HTTP_400_BAD_REQUEST)

    return test_result

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