from datetime import timezone
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
# from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

from django.db import models
from apps.main.models import Language
from django.core.exceptions import ValidationError

# Create your models here.
# class User(AbstractUser, BaseModel):
#     class Meta:
#         verbose_name = _("User")
#         verbose_name_plural = _("Users")  



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
    balance = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()  # Set the custom manager

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email"]

    def clean(self):
        """Email yoki telefon bo‘lishi shart. Bo‘sh stringlarni (`""`) None qilib saqlaymiz."""
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

class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at