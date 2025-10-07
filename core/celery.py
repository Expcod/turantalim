import os
from celery import Celery

# Django sozlamalarini o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Celery app yaratish
app = Celery('core')

# Celery sozlamalarini Django settings dan olish
app.config_from_object('django.conf:settings', namespace='CELERY')

# Avtomatik task'larni topish
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
