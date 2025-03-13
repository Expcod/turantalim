from django.db import models
from django.utils.html import format_html


class Language(models.Model):
    name = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='languages/', null=True, blank=True)
    flag = models.CharField(max_length=8)

    def show_picture(self):
        if self.picture:
            return format_html(
                '<img src="{}" width="100" style="max-height:50px; object-fit: cover;" />',
                self.picture.url
            )
        return "(No Image)"

    def __str__(self):
        return self.name