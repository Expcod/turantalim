from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from rest_framework.exceptions import ValidationError

User = get_user_model()


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

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'phone', 'email',
            'picture', 'region', 'language', 'balance', 'created_at','gender'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'picture', 'region', 'language','gender']



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if len(new_password) < 6:
            raise ValidationError("Yangi parol kamida 6 ta belgidan iborat bo‘lishi kerak!")
        return data


class ChangeBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['balance']

class ChangeLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['language']

class ChangeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class ChangePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['picture']
    
    def update(self, instance, validated_data):
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.save()
        return instance

class ChangeGenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['gender']
    

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "Parollar mos kelmaydi!"})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    """JWT token olish uchun moslashtirilgan serializer"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['phone'] = user.phone
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        return token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token olish uchun serializer (telefon raqami qo‘shilgan)"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Token ichiga qo‘shimcha maydonlarni qo‘shamiz
        token['username'] = user.username
        token['phone'] = user.phone
        token['email'] = user.email
        token['balance'] = user.balance
        token['language'] = user.language.id if user.language else None

        return token
