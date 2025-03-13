from django.contrib.auth.models import AbstractUser
# from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel

from django.db import models
from django.utils.html import format_html
from django.utils.text import slugify

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


class User(AbstractUser):
    phone = models.CharField(max_length=30, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, blank=True, null=True)
    balance = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
