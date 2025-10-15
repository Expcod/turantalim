# Manual Review Timeout System

Bu tizim 12 soatdan eski "reviewing" statusdagi manual review larni avtomatik "pending" statusga qaytarish uchun yaratilgan.

## Asosiy Xususiyatlar

### 1. Avtomatik Timeout
- Har bir manual review "reviewing" statusiga o'tganda `updated_at` field yangilanadi
- 12 soatdan keyin agar hali "reviewing" da qolsa, avtomatik "pending" ga qaytadi
- Bu natijada boshqa tekshiruvchilar uni ko'ra oladi va baholay oladi

### 2. Celery Background Tasks
- `reset_stale_manual_reviews`: 12 soatdan eski review larni pending ga qaytaradi
- Har 30 daqiqada ishga tushadi (Celery Beat orqali)
- Management command ni chaqiradi

### 3. Management Command
- `python manage.py reset_stale_reviews`: Manual ishga tushirish
- `python manage.py reset_stale_reviews --dry-run`: Preview mode
- `python manage.py reset_stale_reviews --hours 6`: Custom timeout (6 soat)

## Foydalanish

### 1. Celery Beat Ishga Tushirish
```bash
# Celery worker
celery -A core worker -l info

# Celery beat (periodic tasks)
celery -A core beat -l info

# Redis server
redis-server
```

### 2. Manual Command
```bash
# Preview mode (hech narsa o'zgartirmaydi)
python manage.py reset_stale_reviews --dry-run

# Custom timeout (6 soat)
python manage.py reset_stale_reviews --hours 6

# Normal (12 soat timeout)
python manage.py reset_stale_reviews
```

### 3. Production Deployment
Supervisor allaqachon celery beat ni ishga tushiradi (`supervisor/turantalim.conf`):
```ini
[program:turantalim_celery_beat]
command=/home/user/turantalim/venv/bin/celery -A core beat -l info
```

## Ishlash Logikasi

### 1. Review Ochilganda
```python
# ManualReview modelida
review.status = 'reviewing'
review.reviewer = request.user
review.updated_at = timezone.now()  # Avtomatik yangilanadi
review.save()
```

### 2. Periodic Check (30 daqiqada)
```python
# Celery task
@shared_task
def reset_stale_manual_reviews():
    # 12 soatdan eski review larni topish
    stale_reviews = ManualReview.objects.filter(
        status='reviewing',
        updated_at__lt=timezone.now() - timedelta(hours=12)
    )
    
    # Pending ga qaytarish
    for review in stale_reviews:
        review.status = 'pending'
        review.reviewer = None
        review.save()
```

### 3. Result
- Eski review lar boshqa tekshiruvchilarga ko'rinadi
- Tekshiruvchining 10 ta limit ga ta'sir qilmaydi
- Fast turnaround time ta'minlanadi

## Konfiguratsiya

### Celery Beat Schedule (core/settings/base.py)
```python
CELERY_BEAT_SCHEDULE = {
    'reset-stale-reviews': {
        'task': 'apps.multilevel.tasks.reset_stale_manual_reviews',
        'schedule': 1800.0,  # 30 daqiqa
    },
}
```

### Timeout Sozlash
Management command da `--hours` parametri orqali:
```bash
python manage.py reset_stale_reviews --hours 6  # 6 soat
python manage.py reset_stale_reviews --hours 24 # 24 soat
```

## Monitoring

### Logs
- Celery beat log: `/home/user/turantalim/logs/celery_beat.log`
- Django log: Console output

### Admin Panel
- ManualReview modelida `updated_at` field ni kuzatish
- Status o'zgarishlarini kuzatish

## Test Qilish

### 1. Test Review Yaratish
```python
# Django shell
from apps.multilevel.models import ManualReview
from django.utils import timezone
from datetime import timedelta

# Eski review yaratish
review = ManualReview.objects.get(id=1)
review.updated_at = timezone.now() - timedelta(hours=13)
review.save()
```

### 2. Command Ishga Tushirish
```bash
python manage.py reset_stale_reviews --dry-run
```

### 3. Natijani Tekshirish
```python
# Django shell
review = ManualReview.objects.get(id=1)
print(review.status)  # 'pending' bo'lishi kerak
print(review.reviewer)  # None bo'lishi kerak
```
