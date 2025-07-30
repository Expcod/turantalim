from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone

class UserBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    balance = models.IntegerField(default=0, verbose_name="Balans (UZS)")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yaratilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqti")

    class Meta:
        verbose_name = "Foydalanuvchi Balansi"
        verbose_name_plural = "Foydalanuvchi Balanslari"

    def __str__(self):
        user_info = getattr(self.user, 'phone', None) or getattr(self.user, 'email', None) or str(self.user)
        return f"{user_info} - {self.balance} UZS"

class BalanceTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('topup', 'Balans To‘ldirish'),
        ('deduct', 'Balansdan Ayirish'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    amount = models.IntegerField(verbose_name="Miqdor (UZS)")
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        verbose_name="Tranzaksiya Turi"
    )
    description = models.CharField(max_length=255, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Balans Tranzaksiyasi"
        verbose_name_plural = "Balans Tranzaksiyalari"

    def __str__(self):
        user_info = getattr(self.user, 'phone', None) or getattr(self.user, 'email', None) or str(self.user)
        return f"{user_info} - {self.transaction_type} - {self.amount} UZS"

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