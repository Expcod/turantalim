# Reviewer (Tekshiruvchi) Tizimi - Qo'llanma

## Umumiy Ma'lumot

Bu tizim superadminlarga admin-dashboard uchun alohida tekshiruvchilar yaratish imkonini beradi. Tekshiruvchilar:
- ✅ Admin-dashboard ga kira oladilar
- ✅ Writing va Speaking natijalarini tekshira oladilar
- ✅ Balllar qo'yishlari va izohlar yozishlari mumkin
- ❌ Django admin panelga kira olmaydilar
- ❌ Boshqa ma'lumotlarni o'zgartira olmaydilar

## 1. Boshlang'ich Sozlash

### Reviewer Group Yaratish

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py setup_reviewers
```

Bu command:
- "Reviewer" guruhini yaratadi
- Kerakli ruxsatlarni beradi
- Tekshiruvchilar uchun permissions sozlaydi

## 2. Tekshiruvchi Qo'shish

### Usul 1: Django Admin Orqali (Mavjud User)

1. Admin panelga kiring: http://your-domain.com/admin/
2. "Users" bo'limiga o'ting
3. Tekshiruvchi qilmoqchi bo'lgan userni tanlang
4. "Groups" bo'limida "Reviewer" guruhini tanlang
5. **MUHIM:** `is_staff` va `is_superuser` belgini QOLDIRMASLIK kerak
6. Userni saqlang

### Usul 2: Django Shell Orqali (Yangi User)

```python
python manage.py shell

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Yangi tekshiruvchi yaratish
reviewer = User.objects.create_user(
    phone='+998901234567',  # Telefon raqami
    password='qwerty123',   # Parol
    first_name='Ali',       # Ism
    last_name='Valiyev',    # Familiya
    email='ali@example.com' # Email (ixtiyoriy)
)

# Reviewer guruhiga qo'shish
reviewer_group = Group.objects.get(name='Reviewer')
reviewer.groups.add(reviewer_group)

# Aktivlashtirish
reviewer.is_active = True
reviewer.is_staff = False  # MUHIM: False bo'lishi kerak
reviewer.save()

print(f"✓ Tekshiruvchi yaratildi: {reviewer.get_full_name()}")
```

### Usul 3: Superuser Account Orqali

Admin panelda "Users" bo'limida yangi user yaratishda:
1. Telefon, parol va boshqa ma'lumotlarni kiriting
2. "Groups" da "Reviewer" ni tanlang
3. `is_staff` va `is_superuser` ni belgilamang
4. Saqlang

## 3. Tekshiruvchi Login Ma'lumotlari

### Admin-Dashboard Login

URL: `http://your-domain.com/admin-dashboard/login.html`

**Login:** Telefon raqami (masalan: +998901234567)
**Parol:** Yaratishda belgilangan parol

## 4. Tekshiruvchini O'chirish yoki O'zgartirish

### Reviewer Statusini Olib Tashlash

1. Admin panelga kiring
2. "Users" → Tekshiruvchini tanlang
3. "Groups" dan "Reviewer" ni olib tashlang
4. Saqlang

### Tekshiruvchini To'liq O'chirish

1. Admin panelga kiring
2. "Users" → Tekshiruvchini tanlang
3. "Delete" tugmasini bosing
4. Tasdiqlang

## 5. Ruxsatlar

Tekshiruvchilar quyidagi ruxsatlarga ega:

| Ruxsat | Tavsif |
|--------|--------|
| view_manualreview | Manual review natijalarini ko'rish |
| change_manualreview | Manual review natijalarini o'zgartirish |
| view_questionscore | Savol ballarini ko'rish |
| add_questionscore | Savol ballarini qo'shish |
| change_questionscore | Savol ballarini o'zgartirish |
| view_reviewlog | Audit log ni ko'rish |
| view_submissionmedia | Yuklangan fayllarni ko'rish |

## 6. Tizim Arxitekturasi

### Fayllar

1. **permissions.py** - IsReviewerOrAdmin permission class
2. **management/commands/setup_reviewers.py** - Setup command
3. **admin.py** - ReviewerUserAdmin interface
4. **auth_views.py** - Login authentication
5. **manual_review_views.py** - API endpoints

### API Endpoints

Tekshiruvchilar quyidagi endpoint larga kirish huquqiga ega:

- `GET /multilevel/api/admin/submissions/` - Barcha submissionlar
- `GET /multilevel/api/admin/submissions/{id}/` - Bitta submission
- `GET /multilevel/api/admin/submissions/{id}/media/` - Submission media
- `PATCH /multilevel/api/admin/submissions/{id}/writing/` - Writing baholash
- `PATCH /multilevel/api/admin/submissions/{id}/speaking/` - Speaking baholash

## 7. Troubleshooting

### Tekshiruvchi login qila olmayapti

**Sabab:** User `is_active=False` bo'lishi mumkin
**Yechim:** Django admin da userni ochib, `is_active=True` qiling

### Tekshiruvchi admin panelga kirmoqda

**Sabab:** User `is_staff=True` bo'lib qolgan
**Yechim:** Django admin da `is_staff=False` qiling

### "Sizda admin panelga kirish huquqi yo'q" xatosi

**Sabab:** User "Reviewer" guruhida emas
**Yechim:** Django admin da "Reviewer" guruhini qo'shing

### Ruxsatlar ishlamayapti

**Sabab:** Reviewer group setup qilinmagan
**Yechim:** `python manage.py setup_reviewers` commandni qayta ishga tushiring

## 8. Xavfsizlik

### Tavsiyalar

1. ✅ Har bir tekshiruvchi uchun alohida account yarating
2. ✅ Kuchli parollar ishlating
3. ✅ Kerak bo'lmaganda reviewerlarni o'chirib qo'ying
4. ✅ Audit loglarni muntazam tekshiring
5. ❌ is_staff ruxsatini bermang
6. ❌ is_superuser ruxsatini bermang

### Parolni O'zgartirish

#### Django Admin Orqali
1. Users → Userni tanlang
2. Parol maydonida "change password" tugmasini bosing
3. Yangi parolni kiriting va saqlang

#### Shell Orqali
```python
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(phone='+998901234567')
user.set_password('yangi_parol')
user.save()
```

## 9. Misol: To'liq Setup

```bash
# 1. Reviewer group yaratish
cd /home/user/turantalim
source venv/bin/activate
python manage.py setup_reviewers

# 2. Yangi reviewer yaratish (Python shell)
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Reviewer 1
reviewer1 = User.objects.create_user(
    phone='+998901111111',
    password='Reviewer@123',
    first_name='Aziza',
    last_name='Rahimova',
    email='aziza@example.com'
)
reviewer_group = Group.objects.get(name='Reviewer')
reviewer1.groups.add(reviewer_group)
reviewer1.is_active = True
reviewer1.is_staff = False
reviewer1.save()

# Reviewer 2
reviewer2 = User.objects.create_user(
    phone='+998902222222',
    password='Reviewer@456',
    first_name='Jamshid',
    last_name='Karimov',
    email='jamshid@example.com'
)
reviewer2.groups.add(reviewer_group)
reviewer2.is_active = True
reviewer2.is_staff = False
reviewer2.save()

print("✓ 2 ta tekshiruvchi yaratildi")
```

## 10. Qo'shimcha Ma'lumot

### Admin Dashboard
- Login: http://your-domain.com/admin-dashboard/login.html
- Dashboard: http://your-domain.com/admin-dashboard/

### Django Admin Panel
- URL: http://your-domain.com/admin/
- Faqat superadminlar kirishi mumkin

### API Documentation
- API docs: http://your-domain.com/api/docs/
- API reference: `/home/user/turantalim/API_QUICK_REFERENCE.md`

---

**Yaratilgan sana:** 2025-10-08
**Versiya:** 1.0
**Muallif:** Turantalim Development Team
