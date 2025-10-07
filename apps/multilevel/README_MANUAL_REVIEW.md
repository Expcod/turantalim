# Turantalim Manual Review System

Bu tizim Turantalim platformasi uchun Writing va Speaking seksiyalarini qo'lda tekshirish uchun yaratilgan. Bu README faylida tizimning arxitekturasi va uni o'rnatish bo'yicha ko'rsatmalar keltirilgan.

## Tizim Arxitekturasi

Qo'lda tekshirish tizimi quyidagi komponentlardan iborat:

### 1. Modellar

- **SubmissionMedia**: Foydalanuvchi yuklagan fayllar (rasmlar va audiolar)
- **ManualReview**: Tekshirish ma'lumotlari (status, ball, tekshiruvchi)
- **QuestionScore**: Har bir savol uchun alohida ballar
- **ReviewLog**: Audit log (kimning nima qilgani, qachon va eski/yangi qiymatlar)

### 2. API Endpointlar

- `GET /api/admin/submissions/` - Tekshirish kerak bo'lgan barcha topshiriqlar ro'yxati
- `GET /api/admin/submissions/{id}/` - Aniq bir topshiriq ma'lumotlari
- `PATCH /api/admin/submissions/{id}/writing/` - Writing seksiyasi ballari yangilash
- `PATCH /api/admin/submissions/{id}/speaking/` - Speaking seksiyasi ballari yangilash
- `GET /api/admin/submissions/{id}/media/` - Topshiriq fayllari (rasmlar/audiolar)

### 3. Frontend

- Admin dashboard HTML/CSS/JS fayllari `/admin_dashboard` papkasida joylashgan
- Login, imtihonlar ro'yxati, va tekshirish sahifalari

## O'rnatish Ko'rsatmalari

### 1. Migratsiyalarni bajarish

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Admin foydalanuvchilarni yaratish

```bash
python manage.py createsuperuser
```

Yaratilgan foydalanuvchini adminlar guruhiga qo'shish kerak:

```python
from django.contrib.auth.models import User, Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Admin guruhini yaratish
admin_group, created = Group.objects.get_or_create(name='exam_reviewers')

# Guruhga kerakli ruxsatlarni berish
content_type = ContentType.objects.get_for_model(ManualReview)
permissions = Permission.objects.filter(content_type=content_type)
admin_group.permissions.add(*permissions)

# Foydalanuvchini guruhga qo'shish
user = User.objects.get(username='your_admin_username')
user.groups.add(admin_group)
```

### 3. Frontend fayllarini joylashtirish

Admin dashboard fayllarini static fayllar joylashgan papkaga nusxalash:

```bash
cp -r admin_dashboard/* /path/to/static/admin/
```

### 4. Media fayllar uchun to'g'ri sozlash

`settings.py` faylida media fayllar uchun to'g'ri sozlash:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 5. URL manzillarini qo'shish

Asosiy `urls.py` faylida admin dashboard URL manzilini qo'shish:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ...existing urls
    path('admin-dashboard/', TemplateView.as_view(template_name='admin/index.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Tizimni ishlatish

1. Admin dashboard: `/admin-dashboard/` URL manzili orqali
2. Login qilish: Admin foydalanuvchi ma'lumotlari bilan
3. Imtihonlarni tekshirish: Ro'yxatdan kerakli imtihonni tanlash
4. Ballari saqlash: "Qoralama saqlash" yoki "Topshirish" tugmalari orqali

## API Endpointlar Dokumentatsiyasi

### 1. Imtihonlar ro'yxati

**Request:**
```
GET /api/admin/submissions/?status=pending&section=writing
```

**Parameters:**
- `status`: pending, reviewing, checked
- `section`: writing, speaking
- `exam_level`: tys, multilevel, cefr1, etc.
- `search`: Foydalanuvchi ismi yoki username

### 2. Imtihon ma'lumotlari

**Request:**
```
GET /api/admin/submissions/123/
```

### 3. Writing ballari yangilash

**Request:**
```
PATCH /api/admin/submissions/123/writing/
```

**Body:**
```json
{
  "question_scores": {
    "1": {"score": 85, "comment": "Yaxshi ish, lekin grammatik xatolar bor."},
    "2": {"score": 90, "comment": "Aniq tuzilgan javob."}
  },
  "total_score": 87.5,
  "notified": true
}
```

### 4. Speaking ballari yangilash

**Request:**
```
PATCH /api/admin/submissions/123/speaking/
```

**Body:**
```json
{
  "question_scores": {
    "1": {"score": 80, "comment": "Yaxshi talaffuz, lekin so'z boyligi cheklangan."},
    "2": {"score": 85, "comment": "Mavzu bo'yicha to'liq javob."}
  },
  "total_score": 82.5,
  "notified": true
}
```

## Xavfsizlik

- API endpointlar faqat adminlar uchun ochiq
- Autentifikatsiya Django token-based auth orqali amalga oshiriladi
- Barcha API so'rovlar HTTPS orqali yuborilishi kerak
- Audit log barcha o'zgarishlarni qayd etadi
