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
    picture = serializers.SerializerMethodField()

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url)  # ✅ To‘liq URL qaytarish
        return None

    class Meta:
        model = User
        fields = [
            'id',  'first_name', 'last_name', 'phone', 'email',
            'picture', 'region', 'language', 'balance', 'created_at','gender'
        ]

        extra_kwargs = {
            'password': {'write_only': True}
        }
    def create(self, validated_data):
        # `username` ni ishlatmaymiz, chunki uni modeldan olib tashlaganmiz
        user = User(
            phone=validated_data.get('phone', None),
            email=validated_data.get('email', None),
        )
        user.set_password(validated_data['password'])  # Parolni hash qilish
        user.save()
        return user
class UserUpdateSerializer(serializers.ModelSerializer):
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), required=False)  
    picture = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'picture', 'region', 'language','gender']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


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



class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "Parollar mos kelmaydi!"})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # confirm_password bazaga yozilmaydi
        return User.objects.create_user(
            phone=validated_data.get('phone'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password'),
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token olish uchun serializer (telefon raqami yoki email qo‘shilgan)"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Token ichiga qo‘shimcha maydonlarni qo‘shamiz
        token['phone'] = user.phone
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        token['balance'] = user.balance
        token['language'] = user.language.id if user.language else None

        return token