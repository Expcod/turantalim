from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.db.models import Avg
from .models import *
from .serializers import *
from .multilevel_score import get_score_details, validate_test_level


class ListeningTestCheckApiView(APIView):
    permission_classes = [IsAuthenticated]

    def handle_error(self, message, status_code):
        return Response({"error": message}, status=status_code)

    @swagger_auto_schema(
        operation_summary="Listening testini tekshirish",
        operation_description="Listening testi uchun foydalanuvchi javoblarini tekshiradi.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'test_result_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Test natijasi ID si', nullable=True),
                'answers': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'question': openapi.Schema(type=openapi.TYPE_INTEGER, description='Savol ID si'),
                            'user_option': openapi.Schema(type=openapi.TYPE_INTEGER, description='Tanlangan variant ID si', nullable=True),
                            'user_answer': openapi.Schema(type=openapi.TYPE_STRING, description='Foydalanuvchi javobi', nullable=True),
                        },
                        required=['question']
                    )
                )
            }
        ),
        responses={
            201: TestCheckSerializer(many=True),
            200: TestCheckSerializer(many=True),
            400: openapi.Response(description="Validation xatosi"),
            403: openapi.Response(description="TestResult topilmadi yoki faol emas")
        }
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data if isinstance(request.data, dict) else {'answers': request.data}
        serializer = BulkTestCheckSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            return self.handle_error(serializer.errors, status.HTTP_400_BAD_REQUEST)

        test_result_id = serializer.validated_data.get('test_result_id')
        answers_data = serializer.validated_data['answers']

        # Birinchi savoldan Exam ni aniqlash
        question = answers_data[0]['question']
        section = question.test.section
        
        # Faqat Listening testini tekshirish
        if section.type != 'listening':
            return self.handle_error("Bu endpoint faqat Listening testi uchun!", status.HTTP_400_BAD_REQUEST)

        # TestResult ni aniqlash va vaqtni tekshirish
        current_test_result = self.get_active_test_result(user, test_result_id, question)
        if isinstance(current_test_result, Response):
            return current_test_result

        # Javoblarni qayta ishlash
        responses = self.process_answers(user, current_test_result, answers_data)

        # Testni yakunlash
        final_response = self.finalize_test(user, current_test_result, responses)
        status_code = status.HTTP_201_CREATED if any(r.get('is_new') for r in responses) else status.HTTP_200_OK
        return Response(final_response, status=status_code)

    def get_active_test_result(self, user, test_result_id, question):
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
                    return self.handle_error("Bu ID ga mos TestResult mavjud emas", status.HTTP_403_FORBIDDEN)
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
                    return self.handle_error("Ushbu bo'lim uchun test topilmadi!", status.HTTP_400_BAD_REQUEST)

        # Test vaqti tugagan bo'lsa, uni completed ga o'tkazish
        from .utils import check_test_time_limit
        if check_test_time_limit(test_result):
            # Vaqt tugaganda completed bo'lgan test uchun maxsus xabar
            if test_result.status == 'completed':
                return test_result
            return self.handle_error("Test vaqti tugagan, javob qabul qilinmadi", status.HTTP_400_BAD_REQUEST)
        
        # Test tekshirilgan bo'lsa (vaqt tugamasdan), uni completed ga o'tkazish
        # Bu yerda test_result ni completed ga o'tkazamiz, lekin hali end_time ni o'zgartirmaymiz
        # chunki finalize_test metodida end_time ni o'zgartiramiz
        if test_result.status == 'started':
            test_result.status = 'completed'
            test_result.save()

        return test_result

    def process_answers(self, user, test_result, answers_data):
        # Mavjud javoblarni olish
        existing_answers = {ua.question_id: ua for ua in UserAnswer.objects.filter(test_result=test_result)}
        
        # Yangi va yangilanadigan javoblar uchun ro'yxatlar
        new_answers = []
        update_answers = []

        for answer_data in answers_data:
            question = answer_data['question']
            user_option = answer_data.get('user_option')
            user_answer = answer_data.get('user_answer')

            # To'g'ri javobni aniqlash
            is_correct = False
            if question.has_options:
                correct_option = Option.objects.filter(question=question, is_correct=True).first()
                is_correct = correct_option == user_option if user_option else False
            else:
                is_correct = (
                    question.answer.strip().lower() == user_answer.strip().lower()
                    if user_answer and question.answer else False
                )

            # Mavjud javobni yangilash yoki yangi javob yaratish
            existing_answer = existing_answers.get(question.id)
            if existing_answer:
                existing_answer.user_option = user_option
                existing_answer.user_answer = user_answer
                existing_answer.is_correct = is_correct
                update_answers.append(existing_answer)
            else:
                new_answer = UserAnswer(
                    test_result=test_result,
                    question=question,
                    user_option=user_option,
                    user_answer=user_answer,
                    is_correct=is_correct
                )
                new_answers.append(new_answer)

        # Bulk operatsiyalar
        if new_answers:
            UserAnswer.objects.bulk_create(new_answers)
        if update_answers:
            UserAnswer.objects.bulk_update(update_answers, ['user_option', 'user_answer', 'is_correct'])

        # Javoblar uchun serializer tayyorlash
        all_answers = UserAnswer.objects.filter(
            test_result=test_result,
            question__in=[answer_data['question'] for answer_data in answers_data]
        )
        response_serializer = TestCheckSerializer(all_answers, many=True, context={'request': self.request})
        responses = [
            {"data": data, "is_new": answer.question_id not in existing_answers}
            for data, answer in zip(response_serializer.data, all_answers)
        ]

        return responses

    def finalize_test(self, user, test_result, responses):
        response_data = [r["data"] for r in responses]
        total_questions = Question.objects.filter(test__section=test_result.section).count()
        answered_questions = UserAnswer.objects.filter(test_result=test_result).count()

        # Test allaqachon completed bo'lsa, faqat score ni hisoblash
        if test_result.status == 'completed':
            correct_count = UserAnswer.objects.filter(test_result=test_result, is_correct=True).count()
            
            # Get exam level for scoring validation
            exam_level = test_result.user_test.exam.level
            
            # Use multilevel or TYS scoring system for supported levels
            if validate_test_level(exam_level):
                score_details = get_score_details('listening', correct_count, total_questions, exam_level)
                score = score_details['score']
                level = score_details['level']
            else:
                # Fallback to percentage-based scoring for other levels
                score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                level = "N/A"

            test_result.score = score
            test_result.end_time = timezone.now()  # End time ni o'zgartirish
            test_result.save()

            # Multilevel va TYS imtihonlar uchun maxsus logika
            user_test = test_result.user_test
            is_multilevel_exam = user_test.exam.level in ['multilevel', 'tys']
            
            if is_multilevel_exam:
                # Multilevel/TYS: barcha section'lar tugatilganda UserTest ni yakunlash
                all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
                total_sections = Section.objects.filter(exam=user_test.exam).count()
                completed_sections = all_test_results.count()
                
                if completed_sections >= total_sections:
                    # Barcha section'lar tugatilgan, UserTest ni yakunlash
                    total_score = sum(tr.score for tr in all_test_results)
                    
                    # Calculate final score based on exam type
                    if exam_level.lower() == 'tys':
                        # TYS: total score is the sum of all sections (max 100)
                        user_test.score = round(total_score, 2)
                    else:
                        # Multilevel: average score of all sections (max 75)
                        user_test.score = round(total_score / total_sections, 2)
                    
                    user_test.status = 'completed'
                    user_test.save()
                else:
                    # Hali section'lar tugatilmagan
                    user_test.status = 'started'
                    user_test.save()
                
                # Multilevel/TYS uchun faqat section completion ko'rsatish
                return {
                    "answers": response_data,
                    "section_completed": True,
                    "section_score": score,
                    "message": "Listening section tugatildi. Barcha sectionlar tugagandan keyin umumiy natija ko'rsatiladi."
                }
            else:
                # Boshqa level'lar: har bir section uchun alohida
                user_test.score = score
                user_test.status = 'completed'  # Har bir section tugatilganda UserTest ham tugaydi
                user_test.save()

                return {
                    "answers": response_data,
                    "test_completed": True,
                    "score": score,
                    "correct_answers": correct_count,
                    "total_questions": total_questions,
                    "level": level
                }

        # Agar test hali completed emas bo'lsa, eski logika
        if total_questions == answered_questions:
            correct_count = UserAnswer.objects.filter(test_result=test_result, is_correct=True).count()
            
            # Get exam level for scoring validation
            exam_level = test_result.user_test.exam.level
            
            # Use multilevel or TYS scoring system for supported levels
            if validate_test_level(exam_level):
                score_details = get_score_details('listening', correct_count, total_questions, exam_level)
                score = score_details['score']
                level = score_details['level']
            else:
                # Fallback to percentage-based scoring for other levels
                score = (correct_count / total_questions * 100) if total_questions > 0 else 0
                level = "N/A"

            test_result.score = score
            test_result.status = 'completed'
            test_result.end_time = timezone.now()
            test_result.save()

            # Multilevel va TYS imtihonlar uchun maxsus logika
            user_test = test_result.user_test
            is_multilevel_exam = user_test.exam.level in ['multilevel', 'tys']
            
            if is_multilevel_exam:
                # Multilevel/TYS: barcha section'lar tugatilganda UserTest ni yakunlash
                all_test_results = TestResult.objects.filter(user_test=user_test, status='completed')
                total_sections = Section.objects.filter(exam=user_test.exam).count()
                completed_sections = all_test_results.count()
                
                if completed_sections >= total_sections:
                    # Barcha section'lar tugatilgan, UserTest ni yakunlash
                    total_score = sum(tr.score for tr in all_test_results)
                    
                    # Calculate final score based on exam type
                    if exam_level.lower() == 'tys':
                        # TYS: total score is the sum of all sections (max 100)
                        user_test.score = round(total_score, 2)
                    else:
                        # Multilevel: average score of all sections (max 75)
                        user_test.score = round(total_score / total_sections, 2)
                    
                    user_test.status = 'completed'
                    user_test.save()
                else:
                    # Hali section'lar tugatilmagan
                    user_test.status = 'started'
                    user_test.save()
                
                # Multilevel/TYS uchun faqat section completion ko'rsatish
                return {
                    "answers": response_data,
                    "section_completed": True,
                    "section_score": score,
                    "message": "Listening section tugatildi. Barcha sectionlar tugagandan keyin umumiy natija ko'rsatiladi."
                }
            else:
                # Boshqa level'lar: har bir section uchun alohida
                user_test.score = score
                user_test.status = 'completed'  # Har bir section tugatilganda UserTest ham tugaydi
                user_test.save()

                return {
                    "answers": response_data,
                    "test_completed": True,
                    "score": score,
                    "correct_answers": correct_count,
                    "total_questions": total_questions,
                    "level": level
                }
        return {"answers": response_data}
