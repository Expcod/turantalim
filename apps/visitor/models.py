from django.db import models
from django.utils.translation import gettext_lazy as _


class Visitor(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = 'new', _('Yangi')
        IN_REVIEW = 'in_review', _('Ko\'rib chiqilmoqda')
        APPROVED = 'approved', _('Qabul qilindi')

    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Ism'),
        help_text=_('Foydalanuvchining ismi')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Familiya'),
        help_text=_('Foydalanuvchining familiyasi')
    )
    phone_number = models.CharField(
        max_length=20,
        verbose_name=_('Telefon raqami'),
        help_text=_('Telefon raqami (+998 formatida)')
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
        verbose_name=_('Holat'),
        help_text=_('Ariza holati')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Yaratilgan vaqti')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Yangilangan vaqti')
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Izohlar'),
        help_text=_('Admin izohlari')
    )

    class Meta:
        verbose_name = _('Kursga ro\'yxatdan o\'tgan foydalanuvchi')
        verbose_name_plural = _('Kursga ro\'yxatdan o\'tgan foydalanuvchilar')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
