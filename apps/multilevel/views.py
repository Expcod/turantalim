from datetime import timedelta
from random import choice
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular import openapi as spectacular_openapi
from drf_yasg import openapi
from .models import *
from apps.payment.models import *
from .serializers import *
from .utils import *
from django.utils import timezone
from django.db.models import Avg
from .multilevel_score import calculate_overall_test_result

class TestRequestApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Test so'rash",
        manual_parameters=[
            openapi.Parameter('language', openapi.IN_QUERY, description="Tilni tanlang (Language ID orqali)", type=openapi.TYPE_INTEGER),
            openapi.Parameter('level', openapi.IN_QUERY, description="Test darajasini tanlang!", type=openapi.TYPE_STRING, enum=['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel','tys']),
            openapi.Parameter('test', openapi.IN_QUERY, description="Test turini tanlang: Listening, Writing, Reading, Speaking", type=openapi.TYPE_STRING, enum=['listening', 'writing', 'reading', 'speaking']),
            openapi.Parameter('exam_id', openapi.IN_QUERY, description="Imtihonni tanlang (Exam ID orqali)", type=openapi.TYPE_INTEGER),
        ],
        responses={200: MultilevelSectionSerializer()},
    )
    def get(self, request):
        language_id = request.GET.get('language')
        level_choice = request.GET.get('level')
        test_type = request.GET.get('test')
        exam_id = request.GET.get('exam_id')

        # Majburiy parametrlarni tekshirish
        if not language_id or not test_type or not level_choice:
            return Response({"error": "Language ID, Test turi va Daraja kiritilishi shart!"}, status=400)

        try:
            language = Language.objects.get(pk=language_id)
        except Language.DoesNotExist:
            return Response({"error": "Til topilmadi!"}, status=404)

        LEVEL_CHOICES = ['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel','tys']
        if level_choice not in LEVEL_CHOICES:
            return Response({"error": f"Noto'g'ri daraja! Daraja quyidagilardan biri bo'lishi kerak: {', '.join(LEVEL_CHOICES)}."}, status=400)
        
        TEST_TYPES = ['listening', 'writing', 'reading', 'speaking']
        if test_type not in TEST_TYPES:
            return Response({"error": f"Noto'g'ri test turi! Test turi quyidagilardan biri bo'lishi kerak: {', '.join(TEST_TYPES)}."}, status=400)

        # Exam tanlash
        if exam_id:
            try:
                exam = Exam.objects.get(pk=exam_id, language=language, level=level_choice.lower())
            except Exam.DoesNotExist:
                return Response({"error": "Tanlangan Exam topilmadi yoki mos emas!"}, status=404)
        else:
            exams = Exam.objects.filter(language=language, level=level_choice.lower())
            if not exams.exists():
                return Response({"error": f"{level_choice} darajasida {language.name} tilida imtihon mavjud emas!"}, status=404)
            return Response({
                "message": "Iltimos, Exam tanlang!",
                "exams": [{"id": exam.id, "title": exam.title} for exam in exams]
            }, status=200)

        # Faol UserTest ni tekshirish yoki yangi yaratish
        existing_user_test = UserTest.objects.filter(
            user=request.user,
            exam=exam,
            status='started'
        ).first()

        if not existing_user_test:
            # Multilevel imtihonlar uchun maxsus logika
            if exam.level == 'multilevel':
                # Multilevel imtihon boshlanmagan bo'lsa, yangi yaratish
                # Barcha eski faol testlarni yakunlash
                UserTest.objects.filter(user=request.user, status='started').update(status='completed')
                TestResult.objects.filter(user_test__user=request.user, status='started').update(status='completed')
                # Yangi UserTest yaratish
                existing_user_test = UserTest.objects.create(
                    user=request.user,
                    exam=exam,
                    language=language,
                    status='started'
                )
            else:
                # Boshqa level'lar uchun: har bir section uchun alohida UserTest
                # Barcha eski faol testlarni yakunlash
                UserTest.objects.filter(user=request.user, status='started').update(status='completed')
                TestResult.objects.filter(user_test__user=request.user, status='started').update(status='completed')
                # Yangi UserTest yaratish
                existing_user_test = UserTest.objects.create(
                    user=request.user,
                    exam=exam,
                    language=language,
                    status='started'
                )

        # Faol TestResult ni tekshirish yoki yangi yaratish
        existing_test_result = TestResult.objects.filter(
            user_test=existing_user_test,
            section__type=test_type,
            status='started'
        ).last()

        if existing_test_result:
            section = existing_test_result.section
        else:
            all_sections = Section.objects.filter(exam=exam, type=test_type)
            if not all_sections.exists():
                return Response({"error": f"Ushbu imtihonda {test_type} turidagi testlar mavjud emas!"}, status=404)

            # Multilevel imtihonlar uchun maxsus logika
            if exam.level == 'multilevel':
                # Multilevel: barcha section'larni ketma-ket o'tish kerak
                used_section_ids = TestResult.objects.filter(user_test=existing_user_test).values_list('section_id', flat=True).distinct()
                unused_sections = all_sections.exclude(id__in=used_section_ids)
                
                if unused_sections.exists():
                    # Keyingi section'ni tanlash
                    selected_section = unused_sections.first()
                else:
                    # Barcha section'lar tugatilgan, qayta boshlash
                    # Faqat completed testlar bo'lsa, yangi test yaratish
                    completed_test_results = TestResult.objects.filter(
                        user_test=existing_user_test,
                        section__type=test_type,
                        status='completed'
                    )
                    if completed_test_results.exists():
                        # Yangi section tanlash (random)
                        selected_section = choice(all_sections)
                    else:
                        # Hech qanday test yo'q, birinchi section'ni tanlash
                        selected_section = all_sections.first()
            else:
                # Boshqa level'lar: har bir section uchun alohida
                used_section_ids = TestResult.objects.filter(user_test=existing_user_test).values_list('section_id', flat=True).distinct()
                unused_sections = all_sections.exclude(id__in=used_section_ids)

                if unused_sections.exists():
                    selected_section = choice(unused_sections)
                else:
                    selected_section = choice(all_sections)

            # Writing test uchun maxsus vaqt boshqarish
            if test_type == 'writing':
                # Writing test uchun vaqt chegarasi yo'q yoki uzoqroq bo'lishi mumkin
                # chunki foydalanuvchi rasmlar yuklaydi va javob yozadi
                duration = selected_section.duration if selected_section.duration else 120  # 2 soat default
                end_time = timezone.now() + timedelta(minutes=duration)
            else:
                # Boshqa testlar uchun oddiy vaqt boshqarish
                end_time = timezone.now() + timedelta(minutes=selected_section.duration)

            existing_test_result = TestResult.objects.create(
                user_test=existing_user_test,
                section=selected_section,
                status='started',
                start_time=timezone.now(),
                end_time=end_time
            )
            section = selected_section
            
            # Vaqt chegarasi task'ini rejalashtirish (writing test uchun maxsus)
            from .utils import schedule_test_time_limit
            if test_type == 'writing':
                # Writing test uchun vaqt chegarasi task'ini rejalashtirmaslik mumkin
                # chunki foydalanuvchi o'zi tugatadi
                pass
            else:
                schedule_test_time_limit(existing_test_result)

        # Writing test uchun ham boshqa bo'limlar kabi bir xil response formatini qaytaramiz
        if test_type == 'writing':
            serializer = MultilevelSectionSerializer(
                section,
                context={'test_result': existing_test_result.pk, 'request': request}
            )
            test_data = {
                "user_test_id": existing_user_test.id,
                "test_type": test_type,
                "duration": section.duration,
                "part": serializer.data,
                "test_result_id": existing_test_result.id
            }
            return Response(test_data, status=200)

        serializer = MultilevelSectionSerializer(
            section,
            context={'test_result': existing_test_result.pk, 'request': request}
        )
        test_data = {
            "user_test_id": existing_user_test.id,
            "test_type": test_type,
            "duration": section.duration,
            "part": serializer.data,
            "test_result_id": existing_test_result.id
        }
        return Response(test_data)

class TestResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Muayyan test natijasini batafsil olish",
        description="Foydalanuvchining muayyan TestResult ID bo'yicha natijasini qaytaradi: to'g'ri/xato javoblar, foiz va daraja.",
        responses={200: TestResultDetailSerializer(), 404: "Test natijasi topilmadi"}
    )
    def get(self, request, test_result_id):
        user = request.user
        try:
            test_result = TestResult.objects.get(id=test_result_id, user_test__user=user)
        except TestResult.DoesNotExist:
            return Response({"error": "Test natijasi topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TestResultDetailSerializer(test_result, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class TestResultListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    @extend_schema(
        summary="Foydalanuvchining barcha test natijalari ro'yxatini olish",
        description="Barcha bo'limlar uchun ball (0-75) ko'rsatiladi: Listening/Reading jadval bo'yicha, Writing/Speaking bo'lim ballari yig'indisi. Pagination bilan.",
        responses={200: TestResultListSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        results = TestResult.objects.filter(user_test__user=user).order_by('-start_time')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(results, request)
        if page is not None:
            serializer = TestResultListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = TestResultListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class OverallTestResultView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get overall test result with level calculation",
        manual_parameters=[
            openapi.Parameter(
                'user_test_id',
                openapi.IN_QUERY,
                description="UserTest ID to get results for",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'test_result_id',
                openapi.IN_QUERY,
                description="TestResult ID to get results for",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Overall test result",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_test_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'exam_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'exam_level': openapi.Schema(type=openapi.TYPE_STRING),
                        'section_scores': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'listening': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'reading': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'writing': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'speaking': openapi.Schema(type=openapi.TYPE_INTEGER),
                            }
                        ),
                        'total_score': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'max_possible_score': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'average_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'level': openapi.Schema(type=openapi.TYPE_STRING),
                        'completed_sections': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_sections': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_complete': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="Not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request):
        """
        Get overall test result with level calculation.
        
        Returns:
            JSON response with section scores, total score, average score, and CEFR level
        """
        user_test_id = request.query_params.get('user_test_id')
        test_result_id = request.query_params.get('test_result_id')
        
        # Check if either user_test_id or test_result_id is provided
        if not user_test_id and not test_result_id:
            return Response(
                {"error": "user_test_id yoki test_result_id parametri majburiy"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If test_result_id is provided, get user_test_id from it
        if test_result_id and not user_test_id:
            try:
                test_result_id = int(test_result_id)
                test_result = TestResult.objects.get(id=test_result_id, user_test__user=request.user)
                user_test_id = test_result.user_test.id
            except (ValueError, TestResult.DoesNotExist):
                return Response(
                    {"error": "test_result_id noto'g'ri yoki mavjud emas"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try:
            user_test_id = int(user_test_id)
        except ValueError:
            return Response(
                {"error": "user_test_id to'g'ri son bo'lishi kerak"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has access to this test result
        try:
            user_test = UserTest.objects.get(id=user_test_id, user=request.user)
        except UserTest.DoesNotExist:
            return Response(
                {"error": "User test topilmadi yoki ruxsatingiz yo'q"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate overall result
        result = calculate_overall_test_result(user_test_id)
        
        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(result, status=status.HTTP_200_OK)

class ExamListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Imtihonlar ro'yxatini olish",
        operation_description="Level bo'yicha filtrlangan, faqat aktiv (status='aktiv') imtihonlar ro'yxatini qaytaradi.",
        manual_parameters=[
            openapi.Parameter(
                'level', 
                openapi.IN_QUERY, 
                description="Imtihon darajasini tanlang", 
                type=openapi.TYPE_STRING, 
                enum=['a1', 'a2', 'b1', 'b2', 'c1', 'multilevel', 'tys'],
                required=False
            ),
        ],
        responses={200: ExamListSerializer(many=True)}
    )
    @extend_schema(
        summary="Imtihonlar ro'yxatini olish",
        description="Level bo'yicha filtrlangan, faqat aktiv (status='aktiv') imtihonlar ro'yxatini qaytaradi.",
        parameters=[
            OpenApiParameter(
                name='level', 
                location=OpenApiParameter.QUERY, 
                description="Imtihon darajasini tanlang", 
                type=str,
                enum=['a1', 'a2', 'b1', 'b2', 'c1', 'multilevel', 'tys'],
                required=False
            ),
        ],
        responses={200: ExamListSerializer(many=True)}
    )
    def get(self, request):
        level = request.GET.get('level')
        
        # Faqat aktiv imtihonlarni olish va order_id bo'yicha tartiblash
        queryset = Exam.objects.filter(status='active').order_by('level', 'order_id')
        
        # Level bo'yicha filtrlash
        if level:
            # Level choices tekshiruvi
            valid_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'multilevel', 'tys']
            if level.lower() not in valid_levels:
                return Response({
                    "error": f"Noto'g'ri level! Quyidagilardan birini tanlang: {', '.join(valid_levels)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = queryset.filter(level=level.lower())
        
        # Agar hech qanday imtihon topilmasa
        if not queryset.exists():
            message = f"'{level}' darajasida" if level else "Hozircha hech qanday"
            return Response({
                "message": f"{message} aktiv imtihonlar mavjud emas.",
                "exams": []
            }, status=status.HTTP_200_OK)
        
        serializer = ExamListSerializer(queryset, many=True)
        return Response({
            "message": "Imtihonlar muvaffaqiyatli topildi.",
            "count": queryset.count(),
            "exams": serializer.data
        }, status=status.HTTP_200_OK)

class TestPreviewApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Test preview",
        operation_description="Faqat test strukturasi va mavjud section turlarini qaytaradi. Hech qanday TestResult/UserTest yaratmaydi.",
        manual_parameters=[
            openapi.Parameter(
                'level', openapi.IN_QUERY,
                description="Daraja (masalan: A1, A2, B1, B2, C1, multilevel, tys)",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel', 'tys']
            ),
            openapi.Parameter(
                'exam_id', openapi.IN_QUERY,
                description="Agar ma'lum exam uchun preview kerak bo'lsa, exam ID ni yuboring",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'test_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'sections': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                }
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}),
        }
    )
    def get(self, request):
        level = request.query_params.get('level')
        exam_id = request.query_params.get('exam_id')

        exam = None

        if exam_id:
            try:
                exam = Exam.objects.get(id=exam_id, status='active')
            except Exam.DoesNotExist:
                return Response({"error": "Exam topilmadi yoki aktiv emas"}, status=status.HTTP_404_NOT_FOUND)
        else:
            if not level:
                return Response({"error": "level yoki exam_id parametrlaridan biri talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

            valid_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'multilevel', 'tys']
            if level not in valid_levels:
                return Response({"error": f"Noto'g'ri level! Quyidagilardan birini tanlang: {', '.join(valid_levels)}"}, status=status.HTTP_400_BAD_REQUEST)

            exam = Exam.objects.filter(level=level, status='active').order_by('-id').first()
            if not exam:
                return Response({"error": f"'{level}' darajasida aktiv imtihon topilmadi"}, status=status.HTTP_404_NOT_FOUND)

        sections = list(Section.objects.filter(exam=exam).values_list('type', flat=True).distinct())
        
        # Agar exam level = multilevel yoki tys bo'lsa, sectionlar ketma ketligini belgilash
        if exam.level in ['multilevel', 'tys']:
            # Standart ketma ketlik: listening -> reading -> writing -> speaking
            standard_order = ['listening', 'reading', 'writing', 'speaking']
            # Faqat mavjud sectionlarni standart ketma ketlikda qaytarish
            ordered_sections = [section for section in standard_order if section in sections]
            sections = ordered_sections

        return Response({
            "test_id": exam.id,
            "sections": sections,
        }, status=status.HTTP_200_OK)

class TestTimeInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Test vaqti ma'lumotlarini olish",
        operation_description="Foydalanuvchining faol testining qolgan vaqtini va boshqa ma'lumotlarini qaytaradi.",
        manual_parameters=[
            openapi.Parameter('test_result_id', openapi.IN_QUERY, description="TestResult ID", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response(
                description="Test vaqti ma'lumotlari",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'test_result_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'section_title': openapi.Schema(type=openapi.TYPE_STRING),
                        'section_type': openapi.Schema(type=openapi.TYPE_STRING),
                        'start_time': openapi.Schema(type=openapi.TYPE_STRING),
                        'end_time': openapi.Schema(type=openapi.TYPE_STRING),
                        'duration_minutes': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'remaining_minutes': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'remaining_seconds': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_expired': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "Test topilmadi",
            400: "Xatolik"
        }
    )
    def get(self, request):
        test_result_id = request.query_params.get('test_result_id')
        
        if not test_result_id:
            return Response({"error": "test_result_id parametri majburiy"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Avval started statusdagi testni qidiramiz
            test_result = TestResult.objects.get(
                id=test_result_id, 
                user_test__user=request.user,
                status='started'
            )
        except TestResult.DoesNotExist:
            try:
                # Agar started topilmasa, completed statusdagi testni qidiramiz
                # Bu vaqt tugaganda avtomatik completed bo'lgan testlar uchun
                test_result = TestResult.objects.get(
                    id=test_result_id, 
                    user_test__user=request.user,
                    status='completed'
                )
            except TestResult.DoesNotExist:
                return Response({"error": "Test topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        
        # Vaqt chegarasi tekshirish
        from .utils import check_test_time_limit
        is_expired = check_test_time_limit(test_result)
        
        if is_expired:
            return Response({
                "test_result_id": test_result.id,
                "section_title": test_result.section.title,
                "section_type": test_result.section.type,
                "start_time": test_result.start_time.isoformat(),
                "end_time": test_result.end_time.isoformat() if test_result.end_time else None,
                "duration_minutes": test_result.section.duration,
                "remaining_minutes": 0,
                "remaining_seconds": 0,
                "is_expired": True,
                "status": "expired"
            }, status=status.HTTP_200_OK)
        
        # Qolgan vaqtni hisoblash
        now = timezone.now()
        if test_result.end_time:
            time_remaining = test_result.end_time - now
            remaining_minutes = max(0, int(time_remaining.total_seconds() // 60))
            remaining_seconds = max(0, int(time_remaining.total_seconds() % 60))
        else:
            remaining_minutes = test_result.section.duration
            remaining_seconds = 0
        
        return Response({
            "test_result_id": test_result.id,
            "section_title": test_result.section.title,
            "section_type": test_result.section.type,
            "start_time": test_result.start_time.isoformat(),
            "end_time": test_result.end_time.isoformat() if test_result.end_time else None,
            "duration_minutes": test_result.section.duration,
            "remaining_minutes": remaining_minutes,
            "remaining_seconds": remaining_seconds,
            "is_expired": False,
            "status": test_result.status
        }, status=status.HTTP_200_OK)


class TestSMSNotificationView(APIView):
    """
    Test SMS notification endpoint for development/testing purposes
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Test SMS notification",
        operation_description="Test the SMS notification functionality",
        manual_parameters=[
            openapi.Parameter(
                'phone_number',
                in_=openapi.IN_QUERY,
                description="Phone number to send test SMS to",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(description="SMS sent successfully"),
            400: openapi.Response(description="Bad request"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request):
        """
        Test SMS notification functionality
        """
        phone_number = request.query_params.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'phone_number parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .utils import test_sms_notification
            success = test_sms_notification(phone_number)
            
            if success:
                return Response({
                    'success': True,
                    'message': f'Test SMS sent successfully to {phone_number}',
                    'phone_number': phone_number
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to send SMS',
                    'phone_number': phone_number
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error sending test SMS: {str(e)}',
                'phone_number': phone_number
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)