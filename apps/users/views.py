from drf_yasg import openapi
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from datetime import timedelta

from .models import User, VerificationCode
from .serializers import *
from .utils import generate_verification_code, send_sms_via_eskiz, send_verification_email
from .tasks import send_verification_email_task, send_sms_task


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegistrationSerializer,
        responses={201: openapi.Response("Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi.")}
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Token olish (Login)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['identifier', 'password'],
            properties={
                'identifier': openapi.Schema(type=openapi.TYPE_STRING, description='Telefon raqami yoki email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Parol'),
            }
        ),
        responses={
            200: openapi.Response("Token muvaffaqiyatli olingan"),
            401: openapi.Response("Autentifikatsiya xatosi")
        },
        operation_description="Telefon raqami yoki email orqali login qilish"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# ✅ Profil ma'lumotlarini olish
class ProfileDetailView(generics.RetrieveUpdateAPIView):  # RetrieveUpdateAPIView ga o'zgartirdik
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: UserSerializer,
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Foydalanuvchi profilini va multilevel test natijalarini (listening, reading, writing, speaking bo'limlari bo'yicha) qaytaradi"
    )
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        if not user:
            return Response({"error": "Foydalanuvchi topilmadi!"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: openapi.Response("Validation xatosi"),
            404: openapi.Response("Foydalanuvchi topilmadi")
        },
        operation_description="Foydalanuvchi profiliga yangi test natijasini qo'shadi"
    )
    def put(self, request, *args, **kwargs):
        user = self.get_object()
        if not user:
            return Response({"error": "Foydalanuvchi topilmadi!"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Agar new_test_result maydoni bo'lsa, yangi TestResult yaratamiz
        if 'new_test_result' in serializer.validated_data:
            test_result_serializer = TestResultInputSerializer(data=serializer.validated_data['new_test_result'])
            test_result_serializer.is_valid(raise_exception=True)
            test_result_serializer.create(user)

        # Yangilangan user ma'lumotlarini qaytarish
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_object(self):
        return self.request.user


# ✅ Profil ma'lumotlarini yangilash
class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Balansni o'zgartirish
class ChangeBalanceView(generics.UpdateAPIView):
    serializer_class = ChangeBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ✅ Parolni o'zgartirish (foydalanuvchi login qilgan holda)
class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        operation_description="Parolni almashtirish (foydalanuvchi login qilgan holda)"
    )
    def update(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(old_password):
            return Response({"error": "Eski parol noto'g'ri!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi!"}, status=status.HTTP_200_OK)


# ✅ Parolni tiklash so'rovi (SMS yoki Email orqali)
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response("Tasdiqlash kodi yuborildi."),
            400: openapi.Response("Validation xatosi")
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data['identifier']
        user = None
        if identifier.startswith('+998'):
            user = User.objects.filter(phone=identifier).first()
        else:
            user = User.objects.filter(email=identifier).first()
            
        if not user:
            return Response({"error": "Foydalanuvchi topilmadi!"}, status=status.HTTP_404_NOT_FOUND)

        # Tasdiqlash kodi generatsiya qilish
        code = generate_verification_code()
        expires_at = timezone.now() + timedelta(minutes=3)

        # Eski kodlarni o'chirish
        VerificationCode.objects.filter(user=user, is_used=False).delete()

        # Yangi kodni saqlash
        VerificationCode.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )

        # SMS yoki Email orqali yuborish
        if identifier.startswith('+998'):
            # Direct SMS sending for testing
            sms_sent = send_sms_via_eskiz(identifier, code)
            if not sms_sent:
                return Response({"error": "SMS yuborishda xatolik yuz berdi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"message": "Tasdiqlash kodi SMS orqali yuborildi."}, status=status.HTTP_200_OK)
        else:
            # Asinxron email yuborish
            send_verification_email_task.delay(identifier, code)
            return Response({"message": "Tasdiqlash kodi email orqali yuborildi."}, status=status.HTTP_200_OK)
        
# ✅ Tasdiqlash kodini tekshirish
class PasswordResetVerifyView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetVerifySerializer,
        responses={
            200: openapi.Response("Tasdiqlash kodi to'g'ri."),
            400: openapi.Response("Validation xatosi")
        }
    )
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Serializer validatsiyasi o'tganligi uchun, user va verification_code mavjud
        verification_code = serializer.validated_data['verification_code']
        
        return Response({"message": "Tasdiqlash kodi to'g'ri."}, status=status.HTTP_200_OK)


# ✅ Yangi parolni o'rnatish
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response("Parol muvaffaqiyatli o'zgartirildi."),
            400: openapi.Response("Validation xatosi")
        }
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        verification_code = serializer.validated_data['verification_code']
        new_password = serializer.validated_data['new_password']

        # Kodni ishlatilgan deb belgilash
        verification_code.is_used = True
        verification_code.save()

        # Yangi parolni o'rnatish
        user.set_password(new_password)
        user.save()

        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi!"}, status=status.HTTP_200_OK)
