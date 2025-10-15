from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from .models import *
from apps.multilevel.serializers import OverallTestResultSerializer
import re
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from apps.multilevel.models import TestResult, UserTest, Section
from apps.multilevel.serializers import TestResultDetailSerializer
from apps.payment.models import UserBalance
from django.utils import timezone
from apps.multilevel.multilevel_score import calculate_overall_test_result


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
            raise ValidationError("Tasdiqlash kodi noto'g'ri!")
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

class TestResultInputSerializer(serializers.Serializer):
    section_id = serializers.IntegerField(required=True)
    status = serializers.ChoiceField(choices=[('started', 'Boshlangan'), ('completed', 'Yakunlangan')], default='started')
    score = serializers.IntegerField(min_value=0, required=True)
    start_time = serializers.DateTimeField(required=False, default=timezone.now)
    end_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate_section_id(self, value):
        if not Section.objects.filter(id=value).exists():
            raise serializers.ValidationError("Bunday bo'lim mavjud emas!")
        return value

    def create(self, user):
        # UserTest obyektini yaratish yoki olish
        user_test, _ = UserTest.objects.get_or_create(user=user, defaults={'exam': None})
        
        # TestResult yaratish
        test_result = TestResult.objects.create(
            user_test=user_test,
            section_id=self.validated_data['section_id'],
            status=self.validated_data['status'],
            score=self.validated_data['score'],
            start_time=self.validated_data['start_time'],
            end_time=self.validated_data['end_time']
        )
        return test_result

class UserSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    language = serializers.CharField(source='language.name', read_only=True)
    picture = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField(read_only=True)  # Payment app'dagi balansdan olish
    user_test_result = serializers.SerializerMethodField(read_only=True)
    new_test_result = TestResultInputSerializer(write_only=True, required=False)  # Yangi test natijasini qabul qilish uchun

    def get_picture(self, obj):
        request = self.context.get("request")
        if obj.picture:
            if request is not None:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return None

    def get_balance(self, obj):
        """Payment app'dagi UserBalance modelidan balansni olish"""
        try:
            user_balance = UserBalance.objects.get(user=obj)
            return user_balance.balance
        except UserBalance.DoesNotExist:
            return 0

    def get_user_test_result(self, obj):
        return OverallTestResultSerializer(obj, context=self.context).data

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email',
            'picture', 'region', 'language', 'balance', 'created_at',
            'gender', 'user_test_result', 'new_test_result'  # Yangi maydon qo'shildi
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
            raise serializers.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo'lishi kerak!")
        if value and User.objects.filter(phone=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ishlatilgan!")
        return value

    def validate_email(self, value):
        # Email bo'sh bo'lsa, validatsiya qilmaslik
        if not value:
            return value
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
            raise serializers.ValidationError("Email formati noto'g'ri!")
        if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
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
            raise ValidationError("Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak!")
        # Parol murakkabligini tekshirish
        if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
            raise ValidationError("Parolda kamida bitta harf va bitta raqam bo'lishi kerak!")
        return data


class ChangeBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['balance']

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Balans manfiy bo'lishi mumkin emas!")
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'password', 'confirm_password']

    def validate_phone(self, value):
        if value and not re.match(r'^\+998\d{9}$', value):
            raise serializers.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo'lishi kerak!")
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqami allaqachon ishlatilgan!")
        return value

    def validate_email(self, value):
        # Email bo'sh bo'lsa, validatsiya qilmaslik
        if not value:
            return value
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
            raise serializers.ValidationError("Email formati noto'g'ri!")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ishlatilgan!")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "Parollar mos kelmaydi!"})
        if not re.search(r'[A-Za-z]', data['password']) or not re.search(r'\d', data['password']):
            raise serializers.ValidationError("Parolda kamida bitta harf va bitta raqam bo'lishi kerak!")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        # Email bo'sh bo'lsa, None yuborish
        email = validated_data.get('email')
        if not email:
            email = None
        return User.objects.create_user(
            phone=validated_data.get('phone'),
            email=email,
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password'),
        )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'identifier'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identifier'] = serializers.CharField(required=True)
        self.fields.pop('username', None)

    def validate_identifier(self, value):
        value = value.strip().replace(" ", "")
        if value.startswith('+998'):
            if value.startswith('+'):
                value = value[1:]
            if value.startswith('998') and len(value) == 12:
                value = f"+{value}"
            if not value.startswith('+998') or len(value) != 13:
                raise serializers.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo‘lishi kerak!")
        else:
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
                raise serializers.ValidationError("Email formati noto‘g‘ri!")
        return value

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')

        if identifier and password:
            if identifier.startswith('+998'):
                user = authenticate(request=self.context.get('request'), phone=identifier, password=password)
            else:
                user = authenticate(request=self.context.get('request'), email=identifier, password=password)

            if not user:
                msg = _('Kiritilgan ma\'lumotlar bo\'yicha foydalanuvchi topilmadi yoki parol noto\'g\'ri.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Identifikator va parol kiritilishi shart.')
            raise serializers.ValidationError(msg, code='authorization')

        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi faollashtirilmagan.")

        refresh = self.get_token(user)

        # Faqat kerakli maydonlarni qaytarish
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

        return response_data


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, help_text="Telefon raqami yoki email")

    def validate_identifier(self, value):
        user = None
        if value.startswith('+998'):
            user = User.objects.filter(phone=value).first()
        else:
            user = User.objects.filter(email=value).first()
            
        if not user:
            raise ValidationError("Foydalanuvchi topilmadi!")
            
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=6)

    def validate(self, data):
        identifier = data.get('identifier')
        code = data.get('code')

        user = None
        if identifier.startswith('+998'):
            user = User.objects.filter(phone=identifier).first()
        else:
            user = User.objects.filter(email=identifier).first()
            
        if not user:
            raise ValidationError("Foydalanuvchi topilmadi!")
            
        verification_code = VerificationCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).first()
        
        if not verification_code:
            raise ValidationError("Tasdiqlash kodi noto'g'ri!")
            
        if verification_code.is_expired():
            raise ValidationError("Tasdiqlash kodi muddati tugagan!")
            
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
            raise serializers.ValidationError("Parolda kamida bitta harf va bitta raqam bo'lishi kerak!")

        identifier = data.get('identifier')
        code = data.get('code')

        user = None
        if identifier.startswith('+998'):
            user = User.objects.filter(phone=identifier).first()
        else:
            user = User.objects.filter(email=identifier).first()
            
        if not user:
            raise serializers.ValidationError("Foydalanuvchi topilmadi!")
            
        verification_code = VerificationCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).first()
        
        if not verification_code:
            raise serializers.ValidationError("Tasdiqlash kodi noto'g'ri!")
            
        if verification_code.is_expired():
            raise serializers.ValidationError("Tasdiqlash kodi muddati tugagan!")
            
        data['user'] = user
        data['verification_code'] = verification_code
        return data


class UserTestResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='exam.title', read_only=True)
    exam_level = serializers.CharField(source='exam.level', read_only=True)
    language = serializers.CharField(source='exam.language.name', read_only=True)
    overall_result = serializers.SerializerMethodField()

    class Meta:
        model = UserTest
        fields = ['id', 'exam_name', 'exam_level', 'language', 'score', 'status', 'created_at', 'overall_result']

    def get_overall_result(self, obj):
        if obj.status == 'completed' and obj.exam.level == 'multilevel':
            result = calculate_overall_test_result(obj.id)
            if 'error' not in result:
                return {
                    'total_score': result['total_score'],
                    'average_score': result['average_score'],
                    'level': result['level'],
                    'is_complete': result['is_complete']
                }
        return None


class SectionTestResultSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='user_test.exam.title', read_only=True)
    exam_level = serializers.CharField(source='user_test.exam.level', read_only=True)
    language = serializers.CharField(source='user_test.exam.language.name', read_only=True)
    section_name = serializers.CharField(source='section.title', read_only=True)
    section_type = serializers.CharField(source='section.type', read_only=True)

    class Meta:
        model = TestResult
        fields = ['id', 'exam_name', 'exam_level', 'language', 'section_name', 'section_type', 'score', 'status', 'start_time', 'end_time']


class UserProfileWithTestResultsSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    language = serializers.CharField(source='language.name', read_only=True)
    multilevel_results = serializers.SerializerMethodField()
    section_results = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email', 'picture', 
            'gender', 'region', 'language', 'created_at',
            'multilevel_results', 'section_results'
        ]
        read_only_fields = ['id', 'created_at']

    def get_multilevel_results(self, obj):
        """Multilevel imtihon natijalarini olish"""
        multilevel_exams = UserTest.objects.filter(
            user=obj,
            exam__level='multilevel',
            status='completed'
        ).order_by('-created_at')[:5]  # Eng so'nggi 5 ta
        
        return UserTestResultSerializer(multilevel_exams, many=True).data

    def get_section_results(self, obj):
        """Section natijalarini olish (a1, a2, b1, b2, c1 uchun)"""
        section_results = TestResult.objects.filter(
            user_test__user=obj,
            user_test__exam__level__in=['a1', 'a2', 'b1', 'b2', 'c1'],
            status='completed'
        ).select_related('user_test', 'user_test__exam', 'section').order_by('-created_at')[:10]  # Eng so'nggi 10 ta
        
        return SectionTestResultSerializer(section_results, many=True).data
