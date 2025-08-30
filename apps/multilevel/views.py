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

            existing_test_result = TestResult.objects.create(
                user_test=existing_user_test,
                section=selected_section,
                status='started',
                start_time=timezone.now(),
                end_time=timezone.now() + timedelta(minutes=selected_section.duration)
            )
            section = selected_section

        serializer = MultilevelSectionSerializer(
            section,
            context={'test_result': existing_test_result.pk, 'request': request}
        )
        test_data = {
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
                required=True
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
        
        if not user_test_id:
            return Response(
                {"error": "user_test_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_test_id = int(user_test_id)
        except ValueError:
            return Response(
                {"error": "user_test_id must be a valid integer"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has access to this test result
        try:
            user_test = UserTest.objects.get(id=user_test_id)
            if user_test.user != request.user:
                return Response(
                    {"error": "You don't have permission to access this test result"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except UserTest.DoesNotExist:
            return Response(
                {"error": "User test not found"}, 
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
        
        # Faqat aktiv imtihonlarni olish
        queryset = Exam.objects.filter(status='active')
        
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

            valid_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'multilevel', 'tys']
            if level.lower() not in valid_levels:
                return Response({"error": f"Noto'g'ri level! Quyidagilardan birini tanlang: {', '.join(valid_levels)}"}, status=status.HTTP_400_BAD_REQUEST)

            exam = Exam.objects.filter(level=level.lower(), status='active').order_by('-id').first()
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
        operation_summary="Test vaqt ma'lumotlarini olish",
        operation_description="Test uchun belgilangan response_time va upload_time ma'lumotlarini qaytaradi",
        manual_parameters=[
            openapi.Parameter(
                'test_id', openapi.IN_QUERY,
                description="Test ID",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'test_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'response_time': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                    'upload_time': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                    'section_type': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            400: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}),
            404: openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)}),
        }
    )
    def get(self, request):
        test_id = request.query_params.get('test_id')
        
        if not test_id:
            return Response({"error": "test_id parametri talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            test = Test.objects.get(id=test_id)
        except Test.DoesNotExist:
            return Response({"error": "Test topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        
        # Faqat writing section uchun vaqt ma'lumotlarini qaytarish
        if test.section.type != 'writing':
            return Response({
                "test_id": test.id,
                "response_time": None,
                "upload_time": None,
                "section_type": test.section.type,
                "message": "Vaqt boshqarish faqat writing section uchun mavjud"
            }, status=status.HTTP_200_OK)
        
        return Response({
            "test_id": test.id,
            "response_time": test.response_time,
            "upload_time": test.upload_time,
            "section_type": test.section.type,
            "message": "Writing test vaqt ma'lumotlari"
        }, status=status.HTTP_200_OK)