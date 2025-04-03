# apps/multilevel/apps.py
from django.apps import AppConfig

class MultilevelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.multilevel'

    def ready(self):
        import apps.multilevel.models  