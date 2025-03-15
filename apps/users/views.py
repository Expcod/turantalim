
from drf_yasg import openapi
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from .models import User
from .serializers import *


# class RegisterAPIView(APIView):
#     permission_classes = [AllowAny]
#     queryset = User.objects.all()
#     permission_classes = [IsAuthenticated]
#     serializer_class = RegistrationSerializer

#     @swagger_auto_schema(
#         request_body=RegistrationSerializer,
#         operation_description="Ro'yxatdan o'tish"
#     )

#     def get_object(self):
#         return self.request.user
    
#     def post(self, request):
#         serializer = RegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             return Response({"message": "Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi."}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegistrationSerializer,
        responses={201: openapi.Response("Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi.")}
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Foydalanuvchi muvaffaqiyatli ro‘yxatdan o‘tdi."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Token olish (Login)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ✅ Profil ma’lumotlarini olish
class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ✅ Profil ma’lumotlarini yangilash
class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
# Custom JWT Token View
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# User Profile Detail View
class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# Update User Profile
class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user()


# Change User Balance
class ChangeBalanceView(generics.UpdateAPIView):
    serializer_class = ChangeBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# Change Password View
class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        operation_description="Parolni almashtirish"
    )

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"error": "Eski parol noto‘g‘ri!"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password := request.data.get("new_password", "")) < 6:
            return Response({"error": "Yangi parol kamida 6 ta belgidan iborat bo‘lishi kerak!"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Parol muvaffaqiyatli o‘zgartirildi!"}, status=status.HTTP_200_OK)

class ChangeLanguageView(generics.UpdateAPIView):
    """
    Foydalanuvchi o‘z tilini o‘zgartirishi uchun view.
    """
    serializer_class = ChangeLanguageSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Til muvaffaqiyatli yangilandi!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeNameView(generics.UpdateAPIView):
    """
    Foydalanuvchi ism va familiyasini o‘zgartirish uchun view.
    """
    serializer_class = ChangeNameSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Ism muvaffaqiyatli yangilandi!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePictureView(generics.UpdateAPIView):
    """
    Foydalanuvchi rasmini o‘zgartirish uchun view.
    """
    serializer_class = ChangePictureSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Rasm muvaffaqiyatli yangilandi!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeGenderView(generics.UpdateAPIView):
    """
    Foydalanuvchi jinsini o‘zgartirish uchun view.
    """
    serializer_class = ChangeGenderSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Gender muvaffaqiyatli yangilandi!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)