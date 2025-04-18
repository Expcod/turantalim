from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from .models import *
from apps.multilevel.serializers import OverallTestResultSerializer
import re

User = get_user_model()


# Umumiy validatsiya funksiyasi (takrorlanadigan kodni olib tashlash uchun)
def validate_user_and_code(identifier, code=None):
    user = None
    if identifier.startswith('+998'):
        user = User.objects.filter(phone=identifier).first()
    else:
        user = User.objects.filter(email=identifier).first()

    if not user:
        raise ValidationError("Tasdiqlash kodi yuborilgan identifikator bilan davom eting.")

    if code:
        verification_code = VerificationCode.objects.filter(user=user, code=code, is_used=False).first()
        if not verification_code:
            raise ValidationError("Tasdiqlash kodi noto‘g‘ri!")
        if verification_code.is_expired():
            raise ValidationError("Tasdiqlash kodi muddati tugagan!")
        return user, verification_code
    return user, None


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name']


class RegionSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Region
        fields = ['id', 'name', 'country']


class UserSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    language = serializers.CharField(source='language.name', read_only=True)
    picture = serializers.SerializerMethodField()
    user_test_result = serializers.SerializerMethodField()  # Yangi maydon

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            if request is not None:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None

    def get_user_test_result(self, obj):
        # Foydalanuvchining umumiy test natijalarini olish
        return OverallTestResultSerializer(obj, context=self.context).data

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email',
            'picture', 'region', 'language', 'balance', 'created_at',
            'gender', 'user_test_result'  # Yangi maydon qo'shildi
        ]

        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)
    picture = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'picture', 'region', 'language', 'gender']

    def validate_phone(self, value):
        if value and not re.match(r'^\+998\d{9}$', value):
            raise serializers.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo‘lishi kerak!")
        if value and User.objects.filter(phone=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ishlatilgan!")
        return value

    def validate_email(self, value):
        if value and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
            raise serializers.ValidationError("Email formati noto‘g‘ri!")
        if value and User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan!")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        if len(new_password) < 6:
            raise ValidationError("Yangi parol kamida 6 ta belgidan iborat bo‘lishi kerak!")
        # Parol murakkabligini tekshirish
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            raise ValidationError("Parolda kamida bitta harf va bitta raqam bo‘lishi kerak!")
        return data


class ChangeBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['balance']

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balans manfiy bo‘lishi mumkin emas!")
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password']

    def validate_phone(self, value):
        if value and not re.match(r'^\+998\d{9}$', value):
            raise serializers.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo‘lishi kerak!")
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ishlatilgan!")
        return value

    def validate_email(self, value):
        if value and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
            raise serializers.ValidationError("Email formati noto‘g‘ri!")
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan!")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "Parollar mos kelmaydi!"})
        if not re.search(r'[A-Za-z]', data['password']) or not re.search(r'\d', data['password']):
            raise serializers.ValidationError("Parolda kamida bitta harf va bitta raqam bo‘lishi kerak!")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            phone=validated_data.get('phone'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password'),
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faollashtirilmagan.")

        token = super().get_token(user)
        token['phone'] = user.phone
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        token['balance'] = user.balance
        token['language'] = user.language.id if user.language else None

        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, help_text="Telefon raqami yoki email")

    def validate_identifier(self, value):
        user, _ = validate_user_and_code(value)
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=6)

    def validate(self, data):
        identifier = data.get('identifier')
        code = data.get('code')

        user, verification_code = validate_user_and_code(identifier, code)
        data['user'] = user
        data['verification_code'] = verification_code
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True, min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmaydi!")

        if not re.search(r'[A-Za-z]', data['new_password']) or not re.search(r'\d', data['new_password']):
            raise serializers.ValidationError("Parolda kamida bitta harf va bitta raqam bo‘lishi kerak!")

        identifier = data.get('identifier')
        code = data.get('code')

        user, verification_code = validate_user_and_code(identifier, code)
        data['user'] = user
        data['verification_code'] = verification_code
        return data