import json
from django.db import models
from django.utils import timezone
# Create your models here.
from django.db import models
from apps.main.models import Language
from apps.users.models import User

SECTION_CHOICES = [
    ("Listening", "Listening"),
    ("Reading", "Reading"),
    ("Writing", "Writing"),
    ("Speaking", "Speaking")
]

class Section(models.Model):
    type = models.CharField(max_length=50, verbose_name="Bo'lim turi", choices=SECTION_CHOICES)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, verbose_name="Til")
    title = models.CharField(max_length=150, verbose_name="Sarlavha")
    description = models.TextField(verbose_name="Tavsif", null=True, blank=True)
    duration = models.PositiveSmallIntegerField(default=0, verbose_name="Test vaqti")
    submitters = models.IntegerField(default=0, verbose_name="Yuboruvchilar soni")

    def __str__(self):
        return str(self.title)[:70]



class Test(models.Model):
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Section")
    title = models.CharField(max_length=150, verbose_name="Sarlavha", null=True, blank=True)
    description = models.TextField(verbose_name="Tavsif", null=True, blank=True)
    picture = models.ImageField(upload_to='tests/pictures/', null=True, blank=True, verbose_name="Rasm")
    audio = models.FileField(upload_to='tests/audio/', null=True, blank=True, verbose_name="Audio")
    text_title = models.CharField(max_length=255, verbose_name="Matn sarlavhasi", null=True, blank=True)
    text = models.TextField(verbose_name="Test matni", null=True, blank=True)
    options = models.TextField(verbose_name="Variantlar", null=True, blank=True)
    options_array = models.CharField(max_length = 500, verbose_name="Variantlar textlari", null=True, blank=True)
    sample = models.TextField(verbose_name="Misol", null=True, blank=True)
    constraints = models.TextField(verbose_name="Shartlar", null=True, blank=True)
    order = models.PositiveSmallIntegerField()

    def get_options(self):
        """ JSON formatida massiv sifatida qaytaradi """
        return json.loads(self.options_array) if self.options_array else []

    def set_options(self, options_list):
        """ JSON massivini stringga o‘girib saqlaydi """
        self.options_array = json.dumps(options_list)
        self.save()
        
    def __str__(self):
        if self.title:
            return self.title
        elif self.description:
            return self.description
        elif self.text_title:
            return self.text_title
        elif self.constraints:
            return self.constraints
        else:
            return str(self.pk)
    
    class Meta:
        verbose_name = "Bo'lim "
        verbose_name_plural = "Bo'limlar "


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Savol testi")
    text = models.TextField(verbose_name="Savol matni")
    picture = models.ImageField(upload_to='questions/', null=True, blank=True, verbose_name="Test Rasmi")
    answer = models.CharField(max_length=150, null=True, blank=True, verbose_name="Javob")
    has_options = models.BooleanField(default=True, verbose_name="Variantlar mavjud")

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

    def __str__(self):
        return self.text

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Variant savoli")
    text = models.TextField(verbose_name="Variant")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri variant")

    class Meta:
        verbose_name = "Variant"
        verbose_name_plural = "Variantlar"

    def __str__(self):
        return self.text

##########################################################################################

class UserTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Foydalanuvchi")
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, verbose_name="Til")
    result = models.PositiveSmallIntegerField(default=0, verbose_name="Natija")
    status = models.CharField(
        max_length=20, 
        choices=[('created', "Created"), ('started', 'Started'), ('completed', 'Completed')], 
        default='created'
        )
    score = models.PositiveSmallIntegerField(default=0, verbose_name="Natija")
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi testi"
        verbose_name_plural = "Foydalanuvchi testlari"

    def __str__(self):
        return self.user.get_full_name() + " - " + self.test.title


class TestResult(models.Model):
    user_test = models.ForeignKey(UserTest, on_delete=models.CASCADE, verbose_name="Foydalanuvchi testi")
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, verbose_name="Bo'lim")
    status = models.CharField(
        max_length=20, 
        choices=[('created', "Created"), ('started', 'Started'), ('completed', 'Completed')],
        default='created'
    )
    score = models.PositiveSmallIntegerField(default=0, verbose_name="Natija")
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user_test.user.get_full_name() + " - " + self.section.title
    
    class Meta:
        verbose_name = "Foydalanuvchi testi natijasi"
        verbose_name_plural = "Foydalanuvchi testi natijalari"

    def save(self, *args, **kwargs):
        if self.status == 'completed':
            self.end_time = timezone.now()
        super().save(*args, **kwargs)

class UserAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, verbose_name="Foydalanuvchi testi")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Savol")
    user_option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Variant")
    user_answer = models.CharField(max_length=20, verbose_name="Foydalanuvchi javobi", null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "Foydalanuvchi javoblari"

    def __str__(self):
        return self.user_test.user.get_full_name() + " - " + self.question.text[:50] + " - " + self.option.text[:50]