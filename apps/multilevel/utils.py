# apps/multilevel/utils.py
import logging
from django.utils import timezone
from openai import OpenAI, OpenAIError, RateLimitError
from .models import Section, TestResult, UserAnswer, UserTest, Question
from rest_framework.response import Response
from rest_framework import status
import re  # re modulini import qilish
import json
from .tasks import schedule_test_completion

logger = logging.getLogger(__name__)

def check_test_time_limit(test_result):
    """
    Test vaqti tugaganligini tekshiradi va kerak bo'lsa avtomatik yakunlaydi.
    Args:
        test_result: TestResult obyekti
    Returns:
        bool: True agar vaqt tugagan bo'lsa, False aks holda
    """
    if test_result.end_time and test_result.end_time < timezone.now():
        # Vaqt tugagan, testni avtomatik yakunlash
        test_result.status = 'completed'
        test_result.save()
        
        # UserTest ni ham tekshirish
        user_test = test_result.user_test
        active_tests = TestResult.objects.filter(user_test=user_test, status='started')
        
        if not active_tests.exists():
            user_test.status = 'completed'
            user_test.save()
        
        logger.info(f"Test {test_result.id} vaqt chegarasi tugagani uchun avtomatik yakunlandi")
        return True
    
    return False

def schedule_test_time_limit(test_result):
    """
    Test uchun vaqt chegarasi task'ini rejalashtiradi.
    Args:
        test_result: TestResult obyekti
    """
    if test_result.section.duration:
        try:
            # Vaqt chegarasi task'ini rejalashtirish
            from .tasks import schedule_test_completion
            schedule_test_completion.delay(test_result.id, test_result.section.duration)
            logger.info(f"Test {test_result.id} uchun {test_result.section.duration} daqiqa vaqt chegarasi rejalashtirildi")
        except Exception as e:
            # Celery yoki Redis muammosi bo'lsa, xatolikni log qilish lekin davom etish
            logger.warning(f"Test {test_result.id} uchun vaqt chegarasi rejalashtirilmadi: {str(e)}")
            # Muammo bo'lsa ham test davom etishi kerak
            pass

def get_or_create_test_result(user, test_result_id, question):
    """TestResult ni olish yoki yaratish"""
    if test_result_id:
        try:
            # Avval started statusdagi testni qidiramiz
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='started')
        except TestResult.DoesNotExist:
            try:
                # Agar started topilmasa, completed statusdagi testni qidiramiz
                # Bu vaqt tugaganda avtomatik completed bo'lgan testlar uchun
                test_result = TestResult.objects.get(id=test_result_id, user_test__user=user, status='completed')
                # Vaqt tugaganda completed bo'lgan test uchun maxsus xabar
                return test_result
            except TestResult.DoesNotExist:
                return Response({"error": "Bu ID ga mos TestResult mavjud emas"}, status=status.HTTP_403_FORBIDDEN)
    else:
        # test_result_id yo'q bo'lsa, avval started, keyin completed testlarni qidiramiz
        test_result = TestResult.objects.filter(
            user_test__user=user,
            section=question.test.section,
            status='started'
        ).last()
        
        if not test_result:
            # Started topilmasa, completed testni qidiramiz
            test_result = TestResult.objects.filter(
                user_test__user=user,
                section=question.test.section,
                status='completed'
            ).last()
            
            if not test_result:
                return Response({"error": "Ushbu bo'lim uchun test topilmadi!"}, status=status.HTTP_400_BAD_REQUEST)

    # Vaqt chegarasi tekshirish
    if check_test_time_limit(test_result):
        # Vaqt tugaganda completed bo'lgan test uchun maxsus xabar
        if test_result.status == 'completed':
            return test_result
        return Response({"error": "Test vaqti tugagan, yangi test so'rang"}, status=status.HTTP_400_BAD_REQUEST)

    return test_result

def process_test_response(
    user,
    test_result,
    question,
    processed_answer,
    prompt,
    client,
    logger=None,
    expect_json: bool = True,
    finalize: bool = False,
):
    """
    Writing yoki Speaking test uchun OpenAI orqali baholash funksiyasi.

    - expect_json: modeldan qat'iy JSON qaytishini kutish (muvaffaqiyatsiz bo'lsa, fallback ishlaydi)
    - finalize: True bo'lsa, test_result va user_test ni shu yerning o'zida yakunlaydi
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Vaqt chegarasi tekshirish
    if check_test_time_limit(test_result):
        return {
            "score": 0,
            "result": "Test vaqti tugagan, javob qabul qilinmadi",
            "test_completed": True,
            "user_answer": processed_answer or "",
            "question_text": question.text,
        }

    # Handle case where processed_answer is None
    if processed_answer is None:
        logger.error(f"No processed answer for question {question.id}")
        return {
            "score": 0,
            "result": "Javob matni aniqlanmadi yoki OCR xatolik yuz berdi.",
            "test_completed": False,
            "user_answer": "",
            "question_text": question.text,
        }

    try:
        # JSON formatni qat'iy so'rashga urinamiz
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Siz professional til imtihoni baholovchisiz. Qoidaga ko'ra faqat so'ralgan formatda javob bering."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
            response_format={"type": "json_object"} if expect_json else None,
            timeout=60  # 60 second timeout
        )

        reply_text = response.choices[0].message.content.strip()

        score = 0
        comment = ""
        parsed = None

        # Avval JSON sifatida parse qilishga harakat qilamiz
        if expect_json:
            try:
                parsed = json.loads(reply_text)
            except json.JSONDecodeError:
                parsed = None

        if parsed is not None and isinstance(parsed, dict):
            score_val = parsed.get("score")
            try:
                score = int(score_val)
            except Exception:
                score = 0
            score = max(0, min(100, score))
            comment = parsed.get("comment") or parsed.get("feedback") or ""
        else:
            # Fallback: matndan "Baho:" va "Izoh:" ni ajratamiz
            lines = reply_text.split("\n")
            comment_lines = []
            score_line = None
            for line in lines:
                if line.strip().lower().startswith("baho:"):
                    score_line = line
                    break
                if line.strip():
                    comment_lines.append(line.replace("Izoh: ", "").strip())
            if score_line:
                score_match = re.search(r"\d+", score_line)
                if score_match:
                    score = int(score_match.group())
            score = max(0, min(100, score))
            comment = " ".join(comment_lines)

        # finalize True bo'lsa, shu yerning o'zida yakunlaymiz
        if finalize and test_result is not None:
            test_result.score = round(score)
            test_result.status = 'completed'
            test_result.end_time = timezone.now()
            test_result.save()

            user_test = test_result.user_test
            all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
            if all_test_results.exists():
                total_score = sum(tr.score for tr in all_test_results) / all_test_results.count()
                user_test.score = round(total_score)
                user_test.status = 'completed' if all_test_results.count() == Section.objects.filter(exam=user_test.exam).count() else 'started'
                user_test.save()

        return {
            "score": score,
            "result": reply_text if reply_text else comment,
            "test_completed": finalize,
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
            "result": "OpenAI API limiti oshib ketdi, iltimos keyinroq urinib ko'ring",
            "test_completed": False,
            "user_answer": processed_answer,
            "question_text": question.text,
        }
    except Exception as e:
        logger.error(f"OpenAI javobini qayta ishlashda xato: {str(e)}")
        return {
            "score": 0,
            "result": "Tizimda xatolik yuz berdi, iltimos keyinroq urinib ko'ring",
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
    
    # Multilevel imtihonlar uchun maxsus logika
    if user_test.exam.level == 'multilevel':
        # Multilevel: barcha section'lar tugatilganda UserTest ni yakunlash
        total_sections = Section.objects.filter(exam=user_test.exam).count()
        completed_sections = all_test_results.count()
        
        if completed_sections >= total_sections:
            # Barcha section'lar tugatilgan, UserTest ni yakunlash
            total_score = sum(tr.score for tr in all_test_results)
            user_test.score = round(total_score / total_sections)  # O'rtacha score
            user_test.status = 'completed'
            user_test.save()
            return {
                "test_completed": True,
                "score": round(score),
                "exam_completed": True,
                "completed_sections": completed_sections,
                "total_sections": total_sections
            }
        else:
            # Hali section'lar tugatilmagan
            user_test.status = 'started'
            user_test.save()
            return {
                "test_completed": True,
                "score": round(score),
                "exam_completed": False,
                "completed_sections": completed_sections,
                "total_sections": total_sections
            }
    else:
        # Boshqa level'lar: har bir section uchun alohida
        total_score = sum(tr.score for tr in all_test_results)
        user_test.score = round(total_score)
        user_test.status = 'completed'  # Har bir section tugatilganda UserTest ham tugaydi
        user_test.save()
        return {
            "test_completed": True,
            "score": round(score),
            "exam_completed": True
        }