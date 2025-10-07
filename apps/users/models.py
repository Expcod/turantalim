from datetime import timezone
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel
from django.db import models
from apps.main.models import Language
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.payment.models import UserBalance

class Country(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CustomUserManager(BaseUserManager):
    def create_user(self, phone=None, email=None, password=None, **extra_fields):
        if not phone and not email:
            raise ValueError("At least one of phone or email must be set")
        phone = phone.strip() if phone else None
        email = self.normalize_email(email) if email else None
        user = self.model(phone=phone, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if not phone and not email:
            raise ValueError("At least one of phone or email must be set for superuser")
        return self.create_user(phone, email, password, **extra_fields)
        
    def authenticate(self, request, phone=None, email=None, password=None, **kwargs):
        """
        Telefon raqami yoki email orqali autentifikatsiya
        """
        if phone:
            try:
                user = self.get_by_natural_key(phone)
            except self.model.DoesNotExist:
                return None
        elif email:
            try:
                user = self.model.objects.get(email=email)
            except self.model.DoesNotExist:
                return None
        else:
            return None

        if user.check_password(password):
            return user
        return None
        
    def get_by_natural_key(self, username):
        """
        Telefon raqami orqali foydalanuvchini topish
        """
        return self.get(phone=username)

class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Erkak'),
        ('female', 'Ayol'),
    ]

    username = None
    phone = models.CharField(max_length=30, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True, default=None)  
    picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()  # Set the custom manager

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email"]

    def clean(self):
        """Email yoki telefon bo'lishi shart. Bo'sh stringlarni (`""`) None qilib saqlaymiz."""
        self.phone = self.phone or None
        self.email = getattr(self, 'email', None) or None
        if not self.phone and not self.email:
            raise ValidationError("Kamida telefon raqami yoki email kiritilishi shart!")
        if self.phone and User.objects.filter(phone=self.phone).exclude(pk=self.pk).exists():
            raise ValidationError({"phone": "Bu telefon raqami allaqachon mavjud!"})
        if self.email and User.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({"email": "Bu email allaqachon mavjud!"})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone if self.phone else self.email or "No Contact"

    def get_test_results(self):
        """
        Foydalanuvchining barcha test natijalarini olish
        """
        from apps.multilevel.models import UserTest, TestResult
        
        # Multilevel imtihonlar (faqat yakunlanganlar)
        multilevel_results = UserTest.objects.filter(
            user=self,
            exam__level='multilevel',
            status='completed'
        ).order_by('-created_at')
        
        # Boshqa level'dagi imtihonlar (barcha section natijalari)
        other_level_results = TestResult.objects.filter(
            user_test__user=self,
            user_test__exam__level__in=['a1', 'a2', 'b1', 'b2', 'c1'],
            status='completed'
        ).select_related('user_test', 'user_test__exam', 'section').order_by('-created_at')
        
        return {
            'multilevel_exams': multilevel_results,
            'section_results': other_level_results
        }

    def get_latest_multilevel_result(self):
        """
        Eng so'nggi multilevel imtihon natijasini olish
        """
        from apps.multilevel.models import UserTest
        return UserTest.objects.filter(
            user=self,
            exam__level='multilevel',
            status='completed'
        ).order_by('-created_at').first()

    def get_latest_section_results(self):
        """
        Eng so'nggi section natijalarini olish (a1, a2, b1, b2, c1 uchun)
        """
        from apps.multilevel.models import TestResult
        return TestResult.objects.filter(
            user_test__user=self,
            user_test__exam__level__in=['a1', 'a2', 'b1', 'b2', 'c1'],
            status='completed'
        ).select_related('user_test', 'user_test__exam', 'section').order_by('-created_at')[:10]

class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at
