from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VisitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.visitor'
    verbose_name = _('Kursga ro\'yxatdan o\'tish')
