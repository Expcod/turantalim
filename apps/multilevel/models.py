import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MaxValueValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.main.models import Language
from apps.users.models import User
from apps.payment.models import ExamPayment
from apps.common.models import BaseModel

# Choices
SECTION_CHOICES = [
    ("listening", "Listening"),
    ("reading", "Reading"),
    ("writing", "Writing"),
    ("speaking", "Speaking"),
]
LEVEL_CHOICES = [
    ("a1", "A1"),
    ("a2", "A2"),
    ("b1", "B1"),
    ("b2", "B2"),
    ("c1", "C1"),
    ("multilevel", "Multilevel"),
]

# Exam Model
class Exam(models.Model):
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, verbose_name="Til")
    title = models.CharField(max_length=150, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Tavsif", null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="multilevel", verbose_name="Daraja")
    price = models.IntegerField(default=0, verbose_name="Narxi")

    def __str__(self):
        return self.title[:70]

    def is_paid_by_user(self, user):
        return ExamPayment.objects.filter(user=user, exam=self, status='completed').exists()
    
    class Meta:
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

# Section Model
class Section(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Imtihon")  # Section Examga bog‘lanadi
    type = models.CharField(max_length=20, choices=SECTION_CHOICES, verbose_name="Bo'lim turi")
    title = models.CharField(max_length=150, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Tavsif", null=True, blank=True)
    duration = models.PositiveSmallIntegerField(default=5, verbose_name="Test vaqti (daqiqa)")

    def clean(self):
        if self.duration < 1:
            raise ValidationError("Test vaqti 1 daqiqadan kam bo‘lmasligi kerak")

    def __str__(self):
        return self.title[:70]

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"

# Test Model
class Test(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="Bo'lim")
    title = models.CharField(max_length=150, verbose_name="Sarlavha", null=True, blank=True)
    description = models.TextField(verbose_name="Tavsif", null=True, blank=True)
    picture = models.ImageField(upload_to='tests/pictures/', null=True, blank=True, verbose_name="Rasm")
    audio = models.FileField(upload_to='tests/audio/', null=True, blank=True, verbose_name="Audio")
    text_title = models.CharField(max_length=255, verbose_name="Matn sarlavhasi", null=True, blank=True)
    text = models.TextField(verbose_name="Test matni", null=True, blank=True)
    options_array = models.TextField(verbose_name="Variantlar JSON", null=True, blank=True)
    sample = models.TextField(verbose_name="Misol", null=True, blank=True)
    constraints = models.TextField(verbose_name="Shartlar", null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Tartib raqami")

    def get_options(self):
        return json.loads(self.options_array) if self.options_array else []

    def set_options(self, options_list):
        self.options_array = json.dumps(options_list)
        self.save()

    def clean(self):
        if not (self.title or self.description or self.text or self.constraints):
            raise ValidationError("Testda hech bo‘lmaganda bitta matn bo‘lishi kerak")

        # Exam va Section level mosligini tekshirish
        if self.section and self.section.exam and self.section.exam.level != self.section.exam.level:
            raise ValidationError("Testning Exam va Section darajalari mos bo‘lishi kerak")

    def __str__(self):
        return self.title or str(self.pk)

    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Testlar"

# Question Model (o‘zgarmadi)
class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Savol testi")
    text = models.TextField(verbose_name="Savol matni")
    picture = models.ImageField(upload_to='questions/', null=True, blank=True, verbose_name="Test Rasmi")
    answer = models.CharField(max_length=150, null=True, blank=True, verbose_name="Javob")
    has_options = models.BooleanField(default=True, verbose_name="Variantlar mavjud")

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

# Option Model
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Variant savoli")
    text = models.CharField(max_length=255, verbose_name="Variant")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri variant")

    def __str__(self):
        return self.text[:50]

    class Meta:
        verbose_name = "Variant"
        verbose_name_plural = "Variantlar"

# UserTest Model
class UserTest(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, verbose_name="Til")
    status = models.CharField(
        max_length=20,
        choices=[('created', "Yaratildi"), ('started', 'Boshlangan'), ('completed', 'Yakunlangan')],
        default='created',
        verbose_name="Holati"
    )
    score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name="Natija"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Kutilmoqda'), ('paid', 'To‘langan'), ('failed', 'Muvaffaqiyatsiz')],
        default='pending',
        verbose_name="To‘lov holati"
    )
    transaction_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Tranzaksiya ID")  # Payme uchun
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="Imtihon", null=False )

    def clean(self):
        if not self.exam:
            raise ValidationError("UserTest uchun Exam majburiy bo‘lishi kerak!")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.language}"

    class Meta:
        verbose_name = "Foydalanuvchi testi"
        verbose_name_plural = "Foydalanuvchi testlari"

# TestResult Model
class TestResult(models.Model):
    user_test = models.ForeignKey(UserTest, on_delete=models.CASCADE, verbose_name="Foydalanuvchi testi")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="Bo'lim")
    status = models.CharField(
        max_length=20,
        choices=[('started', 'Boshlangan'), ('completed', 'Yakunlangan')],
        default='started',
        verbose_name="Holati"
    )
    score = models.PositiveSmallIntegerField(default=0, verbose_name="Natija")
    start_time = models.DateTimeField(default=timezone.now, verbose_name="Boshlanish vaqti")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Tugash vaqti")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    def clean(self):
        if self.user_test.exam != self.section.exam:
            raise ValidationError("UserTest va Section ning Exam lari mos bo‘lishi kerak!")
        
    def save(self, *args, **kwargs):
        if self.status == 'started' and not self.start_time:
            self.start_time = timezone.now()
        if self.status == 'completed' and not self.end_time:
            self.end_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_test.user.get_full_name()} - {self.section.title}"

    class Meta:
        verbose_name = "Foydalanuvchi testi natijasi"
        verbose_name_plural = "Foydalanuvchi testi natijalari"

# UserAnswer Model
class UserAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, verbose_name="Foydalanuvchi testi")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Savol")
    user_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Variant")
    user_answer = models.CharField(max_length=200, verbose_name="Foydalanuvchi javobi", null=True, blank=True)
    is_correct = models.BooleanField(default=False, verbose_name="To‘g‘ri javob")

    def clean(self):
        if self.question.has_options and not self.user_option:
            raise ValidationError("Variantli savolda user_option majburiy")
        if not self.question.has_options and not self.user_answer:
            raise ValidationError("Variantsiz savolda user_answer majburiy")

    def __str__(self):
        return f"{self.test_result.user_test.user.get_full_name()} - {self.question.text[:50]}"

    class Meta:
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "Foydalanuvchi javoblari"