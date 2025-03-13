from random import choice
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from datetime import datetime

from .models import *
from apps.payment.models import *
from .serializers import *

from apps.main.models import Language

#  Section uchun API'lar
class SectionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    @swagger_auto_schema(
        operation_description="Barcha Section savollari ro‘yxatini olish yoki yangisini yaratish",
        responses={200: SectionSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Yangi Section savolini yaratish",
        request_body=SectionSerializer,
        responses={201: SectionSerializer()}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SectionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    @swagger_auto_schema(
        operation_description="Section savolini ID bo‘yicha olish",
        responses={200: SectionSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Section savolini yangilash",
        request_body=SectionSerializer,
        responses={200: SectionSerializer()}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Section savolini o‘chirish",
        responses={204: "O‘chirildi"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TestListCreateAPIView(generics.ListCreateAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

    @swagger_auto_schema(
        operation_summary="Testlar ro‘yxatini olish yoki yangi test yaratish",
        responses={200: TestSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Yangi test yaratish",
        request_body=TestSerializer,
        responses={201: TestSerializer()},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TestDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

    @swagger_auto_schema(
        operation_summary="Bitta test ma'lumotlarini olish",
        responses={200: TestSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Testni yangilash",
        request_body=TestSerializer,
        responses={200: TestSerializer()},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Testni o‘chirish",
        responses={204: "Test muvaffaqiyatli o‘chirildi"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# Question API
class QuestionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @swagger_auto_schema(
        operation_summary="Savollar ro‘yxatini olish yoki yangi savol yaratish",
        responses={200: QuestionSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Yangi savol yaratish",
        request_body=QuestionSerializer,
        responses={201: QuestionSerializer()},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class QuestionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @swagger_auto_schema(
        operation_summary="Bitta savol ma'lumotlarini olish",
        responses={200: QuestionSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Savolni yangilash",
        request_body=QuestionSerializer,
        responses={200: QuestionSerializer()},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Savolni o‘chirish",
        responses={204: "Savol muvaffaqiyatli o‘chirildi"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


#  Option API


class OptionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer



class OptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

#  UserTest API
class UserTestListCreateAPIView(generics.ListCreateAPIView):
    queryset = UserTest.objects.all()
    serializer_class = UserTestSerializer

    @swagger_auto_schema(
        operation_summary="Foydalanuvchilarning test natijalari ro‘yxatini olish yoki yangi natija qo‘shish",
        responses={200: UserTestSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Foydalanuvchi uchun yangi test natijasini yaratish",
        request_body=UserTestSerializer,
        responses={201: UserTestSerializer()},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserTestDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserTest.objects.all()
    serializer_class = UserTestSerializer

    @swagger_auto_schema(
        operation_summary="Bitta foydalanuvchi test natijasini olish",
        responses={200: UserTestSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Foydalanuvchi test natijasini yangilash",
        request_body=UserTestSerializer,
        responses={200: UserTestSerializer()},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Foydalanuvchi test natijasini o‘chirish",
        responses={204: "Test natijasi muvaffaqiyatli o‘chirildi"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
############################################################################################################
    #Test uchun API'lar

class TestRequestApiView(APIView):
    @swagger_auto_schema(
        operation_summary="Test so‘rash",
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Tilni tanlang (Language ID orqali)",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'test',
                openapi.IN_QUERY,
                description="Test turini tanlang: Listening, Writing, Reading, Speaking",
                type=openapi.TYPE_STRING,
                enum=['Listening', 'Writing', 'Reading', 'Speaking']
            )
        ],
        responses={200: MultilevelTestSerializer()},
    )
    def get(self, request):
        language_id = request.GET.get('language')
        test_type = request.GET.get('test')

        if not language_id or not test_type:
            return Response({"error": "Language ID va Test turi kiritilishi shart!"}, status=400)

        try:
            language = Language.objects.get(pk=language_id)
        except Language.DoesNotExist:
            return Response({"error": "Til topilmadi!"}, status=404)

        # Validate test type
        TEST_TYPES = ['Listening', 'Writing', 'Reading', 'Speaking']
        if test_type not in TEST_TYPES:
            return Response({"error": f"Noto‘g‘ri test turi! Test turi quyidagilardan biri bo‘lishi kerak: {', '.join(TEST_TYPES)}."}, status=400)

        # Check for payment
        # payment_exists = Payment.objects.filter(
        #     user=request.user, 
        #     test_type=test_type, 
        #     status='paid'
        #     ).order_by('-payment_date').first()
        # if not payment_exists or payment_exists.expiry_date < datetime.now():
        #     return Response(
        #         {"error": "Siz ushbu test uchun to‘lov qilmagansiz! Iltimos, to‘lovni amalga oshiring."}, 
        #         status=402
        #         )
        
        # Check for existing test
        # existing_test = TestResult.objects.filter(user_test__user=request.user, status='created').last()
        # if existing_test:
        #     test_data = {
        #         "test_type": test_type,
        #         "part": MultilevelSectionSerializer(existing_test.section).data
        #     }
        #     return Response(test_data)
        
        # Fetch random test section efficiently
        section_ids = Section.objects.filter(language=language, type=test_type).values_list('id', flat=True)
        if not section_ids:
            return Response({"error": "Ushbu turdagi testlar mavjud emas!"}, status=404)

        main_section = Section.objects.get(id=choice(section_ids))
        test_data = {
            "test_type": test_type,
            "duration": main_section.duration,
            "part": MultilevelSectionSerializer(main_section).data
        }

        # Create UserTest and TestResult entries
        user_test = UserTest.objects.create(
            user=request.user, 
            language=language
            )
        TestResult.objects.create(
            user_test=user_test, 
            section=main_section
            )

        return Response(test_data)



class TestCheckApiView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TestCheckSerializer
    queryset = UserAnswer.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        user = request.user

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        question = serializer.validated_data.get('question')
        user_option = serializer.validated_data.get('user_option')
        user_answer = serializer.validated_data.get('user_answer')

        # Get the current active test result
        current_test_result = TestResult.objects.filter(
            user_test__user=user
        ).exclude(status="ended", user_test__status='ended')

        if not current_test_result.exists():
            return Response(
                {"message": "User has no active tests"},
                status=status.HTTP_403_FORBIDDEN
            )

        current_test = current_test_result.last()
        if question.test.section != current_test.section:
            return Response(
                {"message": "Question does not belong to the current test section"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if a UserAnswer already exists for this test_result and question
        existing_answer = UserAnswer.objects.filter(
            test_result=current_test,
            question=question
        ).first()

        if existing_answer:
            # Update existing UserAnswer
            existing_answer.user_option = user_option
            existing_answer.user_answer = user_answer
            if question.has_options:
                correct_option = Option.objects.filter(question=question, is_correct=True).first()
                existing_answer.is_correct = correct_option == user_option
            else:
                existing_answer.is_correct = question.answer == user_answer
            existing_answer.save()
            # Serialize the updated instance
            serializer = self.get_serializer(existing_answer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new UserAnswer
            serializer.validated_data['test_result'] = current_test
            if question.has_options:
                correct_option = Option.objects.filter(question=question, is_correct=True).first()
                serializer.validated_data["is_correct"] = correct_option == user_option
            else:
                serializer.validated_data['is_correct'] = question.answer == user_answer

            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)




from rest_framework.pagination import PageNumberPagination

class UserTestResultListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        user = request.user
        results = TestResult.objects.filter(user_test__user=user).order_by('-created_at')

        # Paginate results
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(results, request)
        if page is not None:
            serializer = UserTestResultSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserTestResultSerializer(results, many=True)
        return Response(serializer.data, status=200)
