from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class UserBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    balance = models.IntegerField(default=0, verbose_name="Balans (UZS)")

    class Meta:
        verbose_name = "Foydalanuvchi Balansi"
        verbose_name_plural = "Foydalanuvchi Balanslari"

    def __str__(self):
        return f"{self.user.username} - {self.balance} UZS"

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
        return f"{self.user.username} - {self.transaction_type} - {self.amount} UZS"

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