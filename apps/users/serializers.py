from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token, RefreshToken
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class RegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    email_or_phone = serializers.CharField(max_length=100, required=True)
    country = serializers.CharField(max_length = 150, required = True)
    region = serializers.CharField(max_length = 150, required = True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_email_or_phone(self, value):
        if re.match(r"^\+?\d{10,13}$", value):  # Simple phone validation
            if User.objects.filter(phone=value).exists():
                raise ValidationError("Bu telefon raqami allaqachon ro'yxatdan o'tgan.")
        elif re.match(r"[^@]+@[^@]+\.[^@]+", value):  # Simple email validation
            if User.objects.filter(email=value).exists():
                raise ValidationError("Bu elektron pochta manzili allaqachon ro'yxatdan o'tgan.")
        else:
            raise ValidationError("Iltimos, to'g'ri telefon raqami yoki elektron pochta manzilini kiriting.")
        return value

    def create(self, validated_data):
        email_or_phone = validated_data['email_or_phone']
        if re.match(r"^\+?\d{10,13}$", email_or_phone):  # Phone number
            user = User(
                username=email_or_phone,
                phone=email_or_phone,
                first_name=validated_data['first_name']
            )
        else:  # Email
            user = User(
                username=email_or_phone,
                email=email_or_phone,
                first_name=validated_data['first_name']
            )
        user.set_password(validated_data['password'])
        user.save()
        return user



class CustomTokenObtainPairSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate(self, attrs):
        email_or_phone = attrs['email_or_phone']
        password = attrs['password']

        user = None
        if re.match(r"^\+?\d{10,13}$", email_or_phone):  # Phone number pattern
            user = User.objects.filter(phone=email_or_phone).first()
        elif re.match(r"[^@]+@[^@]+\.[^@]+", email_or_phone):  # Email pattern
            user = User.objects.filter(email=email_or_phone).first()
        else:
            raise ValidationError("Invalid email or phone number")

        if not user or not user.check_password(password):
            raise ValidationError("Invalid credentials")

        # Generate refresh and access tokens using RefreshToken class
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'region', 'password']

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateSerializer, self).__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['region'].required = False

    def validate_email(self, value):
        """
        Validate email to ensure uniqueness.
        """
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Ushbu elektron pochta manzili allaqachon ishlatilmoqda.")
        return value

    def validate_phone(self, value):
        """
        Validate phone to ensure uniqueness.
        """
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(phone=value).exists():
            raise serializers.ValidationError("Ushbu telefon raqami allaqachon ishlatilmoqda.")
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    email_or_phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email_or_phone', 'region']

    def get_email_or_phone(self, obj):
        if obj.email:
            return obj.email
        elif obj.phone:
            return obj.phone
        return None