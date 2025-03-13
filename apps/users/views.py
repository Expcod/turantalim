from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase
from rest_framework_simplejwt.settings import api_settings
from .serializers import RegistrationSerializer, CustomTokenObtainPairSerializer, ProfileUpdateSerializer, \
    ProfileSerializer
from .models import User

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegistrationSerializer,
        responses={
            201: "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tkazildi.",
            400: "Notog'ri ma'lumot.",
        }
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tkazildi."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenViewBase):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email_or_phone': openapi.Schema(type=openapi.TYPE_STRING, description='Email or Phone number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            required=['email_or_phone', 'password'],
        ),
        responses={
            200: openapi.Response('Token created successfully'),
            401: openapi.Response('Authentication error'),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ProfileUpdateAPIView(UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        request_body=ProfileUpdateSerializer,
        responses={
            200: 'Profil muvaffaqiyatli yangilandi',
            400: 'So\'rov xatosi yoki validatsiya xatosi',
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ProfileUpdateSerializer,
        responses={
            200: 'Profil muvaffaqiyatli yangilandi',
            400: 'So\'rov xatosi yoki validatsiya xatosi',
        }       
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_description="Retrieve the profile details of the currently authenticated user",
        responses={
            200: ProfileSerializer,
            401: 'Unauthorized',
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)