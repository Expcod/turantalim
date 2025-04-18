from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class ExamPayment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    exam = models.ForeignKey('multilevel.Exam', on_delete=models.CASCADE, verbose_name="Imtihon")
    amount = models.IntegerField(verbose_name="To‘lov miqdori")
    is_paid = models.BooleanField(default=False, verbose_name="To‘langanmi")
    payment_method = models.CharField(max_length=50, verbose_name="To‘lov usuli", default="payme")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Exam Payment"
        verbose_name_plural = "Exam Payments"