from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserTest, TestResult, Section
from .multilevel_score import get_level_from_score
from .exam_results_serializers import (
    MultilevelTysExamResultSerializer,
    MultilevelTysExamListSerializer,
    ErrorResponseSerializer
)


class MultilevelTysExamResultView(APIView):
    """
    Multilevel va TYS imtihonlari uchun batafsil natija ko'rsatish API
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Multilevel/TYS imtihon natijasini olish",
        operation_description="""
        Multilevel va TYS imtihonlari uchun batafsil natija qaytaradi:
        - Har bir section balli (max 75)
        - Umumiy ball (max 300)
        - Daraja (B1, B2, C1)
        - Imtihon holati
        """,
        manual_parameters=[
            openapi.Parameter(
                name='user_test_id',
                in_=openapi.IN_QUERY,
                description="UserTest ID - imtihon natijasini olish uchun",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: MultilevelTysExamResultSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        }
    )
    def get(self, request):
        """
        Multilevel va TYS imtihon natijasini olish
        """
        user_test_id = request.query_params.get('user_test_id')
        
        if not user_test_id:
            return Response({
                'success': False,
                'error': 'user_test_id parametri majburiy'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_test_id = int(user_test_id)
        except ValueError:
            return Response({
                'success': False,
                'error': 'user_test_id to\'g\'ri son bo\'lishi kerak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # UserTest ni topish va ruxsatni tekshirish (faqat UserTest ID qabul qilinadi)
        try:
            user_test = UserTest.objects.get(id=user_test_id, user=request.user)
        except UserTest.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Imtihon topilmadi yoki ruxsatingiz yo\'q'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Faqat multilevel va tys imtihonlari uchun
        if user_test.exam.level not in ['multilevel', 'tys']:
            return Response({
                'success': False,
                'error': 'Bu API faqat multilevel va tys imtihonlari uchun mo\'ljallangan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Barcha section natijalarini olish
        test_results = TestResult.objects.filter(
            user_test=user_test
        ).select_related('section').order_by('section__type')
        
        # Section natijalarini tayyorlash
        section_results = {
            'listening': {'section_name': 'Listening', 'score': 0, 'max_score': 75, 'status': 'not_started', 'completed_at': None},
            'reading': {'section_name': 'Reading', 'score': 0, 'max_score': 75, 'status': 'not_started', 'completed_at': None},
            'writing': {'section_name': 'Writing', 'score': 0, 'max_score': 75, 'status': 'not_started', 'completed_at': None},
            'speaking': {'section_name': 'Speaking', 'score': 0, 'max_score': 75, 'status': 'not_started', 'completed_at': None},
        }
        
        total_score = 0
        completed_sections = 0
        
        # Har bir section natijasini to'ldirish
        for test_result in test_results:
            section_type = test_result.section.type.lower()
            if section_type in section_results:
                section_results[section_type].update({
                    'score': test_result.score,
                    'status': test_result.status,
                    'completed_at': test_result.end_time.isoformat() if test_result.end_time else None
                })
                
                if test_result.status == 'completed':
                    total_score += test_result.score
                    completed_sections += 1
        
        # Umumiy natijani hisoblash
        max_possible_score = 300  # 4 section * 75 ball
        average_score = total_score / 4 if completed_sections == 4 else 0
        level = get_level_from_score(average_score)
        
        # Daraja tavsifini aniqlash
        level_descriptions = {
            'B1': 'O\'rta daraja - mustaqil foydalanuvchi',
            'B2': 'O\'rtadan yuqori daraja - mustaqil foydalanuvchi',
            'C1': 'Yuqori daraja - tajribali foydalanuvchi',
            'Below B1': 'Boshlang\'ich daraja'
        }
        
        # Daraja oralig'lari
        level_ranges = {
            'B1': '38-50 ball',
            'B2': '51-64 ball', 
            'C1': '65-75 ball'
        }
        
        # Response tayyorlash
        response_data = {
            'success': True,
            'exam_info': {
                'exam_id': user_test.exam.id,
                'exam_name': user_test.exam.title,
                'exam_level': user_test.exam.level.upper(),
                'language': user_test.exam.language.name if user_test.exam.language else 'Unknown',
                'status': user_test.status,
                'created_at': user_test.created_at.isoformat(),
                'completed_at': user_test.updated_at.isoformat() if user_test.status == 'completed' else None,
            },
            'section_results': section_results,
            'overall_result': {
                'total_score': total_score,
                'max_possible_score': max_possible_score,
                'average_score': round(average_score, 2),
                'level': level,
                'level_description': level_descriptions.get(level, 'Noma\'lum daraja'),
                'completed_sections': completed_sections,
                'total_sections': 4,
                'is_complete': completed_sections == 4,
            },
            'level_ranges': level_ranges
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class MultilevelTysExamListResultView(APIView):
    """
    Foydalanuvchining barcha multilevel va tys imtihon natijalarini olish
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Barcha multilevel va tys imtihon natijalarini olish",
        operation_description="""
        Foydalanuvchining barcha multilevel va tys imtihon natijalarini qaytaradi.
        Har bir imtihon uchun qisqacha ma'lumot va umumiy natija ko'rsatiladi.
        """,
        manual_parameters=[
            openapi.Parameter(
                name='exam_level',
                in_=openapi.IN_QUERY,
                description="Imtihon turi: multilevel, tys yoki ikkalasi (bo'sh qoldirilsa)",
                type=openapi.TYPE_STRING,
                required=False,
                enum=['multilevel', 'tys', 'all']
            ),
            openapi.Parameter(
                name='limit',
                in_=openapi.IN_QUERY,
                description="Natijalar soni (default: 10)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={
            200: MultilevelTysExamListSerializer,
        }
    )
    def get(self, request):
        """
        Barcha multilevel va tys imtihon natijalarini olish
        """
        exam_level = request.query_params.get('exam_level', 'all')
        limit = int(request.query_params.get('limit', 10))
        
        # Filtrlash
        if exam_level in ['multilevel', 'tys']:
            user_tests = UserTest.objects.filter(
                user=request.user,
                exam__level=exam_level
            ).order_by('-created_at')[:limit]
        else:
            user_tests = UserTest.objects.filter(
                user=request.user,
                exam__level__in=['multilevel', 'tys']
            ).order_by('-created_at')[:limit]
        
        exams_data = []
        
        for user_test in user_tests:
            # Har bir imtihon uchun natijani hisoblash
            test_results = TestResult.objects.filter(
                user_test=user_test
            ).select_related('section')
            
            total_score = 0
            completed_sections = 0
            
            for test_result in test_results:
                if test_result.status == 'completed':
                    total_score += test_result.score
                    completed_sections += 1
            
            average_score = total_score / 4 if completed_sections == 4 else 0
            level = get_level_from_score(average_score)
            
            # Oxirgi tugatilgan section vaqtini topish
            last_completed = test_results.filter(status='completed').order_by('-end_time').first()
            completed_at = last_completed.end_time.isoformat() if last_completed and last_completed.end_time else None
            
            exams_data.append({
                'user_test_id': user_test.id,
                'exam_name': user_test.exam.title,
                'exam_level': user_test.exam.level.upper(),
                'language': user_test.exam.language.name if user_test.exam.language else 'Unknown',
                'status': user_test.status,
                'total_score': total_score,
                'average_score': round(average_score, 2),
                'level': level,
                'completed_sections': completed_sections,
                'total_sections': 4,
                'is_complete': completed_sections == 4,
                'created_at': user_test.created_at.isoformat(),
                'completed_at': completed_at,
            })
        
        response_data = {
            'success': True,
            'total_exams': len(exams_data),
            'exams': exams_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
