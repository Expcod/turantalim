# Tekshiruvchi Tizimi - Tezkor Boshlash

## ✅ Tayyor!

Tekshiruvchi (Reviewer) tizimi muvaffaqiyatli sozlandi!

## 🎯 Imkoniyatlar

- ✅ Django admin orqali tekshiruvchilarni boshqarish
- ✅ Tekshiruvchilar admin-dashboard ga kira oladilar
- ✅ Tekshiruvchilar Django admin panelga kira olmaydilar
- ✅ Har bir tekshiruvchi uchun alohida login va parol

## 🚀 Test Qilish

### Test Reviewer Ma'lumotlari

```
URL: http://your-domain.com/admin-dashboard/login.html
Telefon: +998901234567
Parol: test123
```

### Login Qilish

1. Admin-dashboard login sahifasiga o'ting
2. Telefon: `+998901234567`
3. Parol: `test123`
4. Login tugmasini bosing
5. Muvaffaqiyatli kirsangiz, submissions ro'yxatini ko'rasiz

## 📝 Yangi Tekshiruvchi Qo'shish

### Django Admin Orqali (Eng Oson)

1. **Admin panelga kiring:** http://your-domain.com/admin/
2. **Users** bo'limiga o'ting
3. **"Add User"** tugmasini bosing
4. Quyidagi ma'lumotlarni kiriting:
   - **Phone:** Telefon raqami (masalan: +998901111111)
   - **Password:** Kuchli parol
   - **First name:** Ism
   - **Last name:** Familiya
5. **Groups** da **"Reviewer"** ni tanlang
6. **MUHIM:** `is_staff` va `is_superuser` ni belgilamang!
7. **Save** tugmasini bosing

### Shell Orqali (Tezroq)

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Yangi reviewer yaratish
reviewer = User.objects.create_user(
    phone='+998901111111',        # Telefon
    password='kuchli_parol_123',  # Parol
    first_name='Ali',             # Ism
    last_name='Valiyev'           # Familiya
)

# Reviewer guruhiga qo'shish
reviewer_group = Group.objects.get(name='Reviewer')
reviewer.groups.add(reviewer_group)
reviewer.is_active = True
reviewer.is_staff = False  # MUHIM!
reviewer.save()

print(f"✓ {reviewer.get_full_name()} tekshiruvchi yaratildi!")
```

## 🔧 Amaliy Misollar

### Bir Nechta Tekshiruvchi Yaratish

```python
reviewers_data = [
    {
        'phone': '+998901111111',
        'password': 'Reviewer@123',
        'first_name': 'Aziza',
        'last_name': 'Rahimova'
    },
    {
        'phone': '+998902222222',
        'password': 'Reviewer@456',
        'first_name': 'Jamshid',
        'last_name': 'Karimov'
    },
    {
        'phone': '+998903333333',
        'password': 'Reviewer@789',
        'first_name': 'Nodira',
        'last_name': 'Usmonova'
    }
]

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
reviewer_group = Group.objects.get(name='Reviewer')

for data in reviewers_data:
    reviewer = User.objects.create_user(**data)
    reviewer.groups.add(reviewer_group)
    reviewer.is_active = True
    reviewer.is_staff = False
    reviewer.save()
    print(f"✓ {reviewer.get_full_name()} yaratildi")
```

### Tekshiruvchini O'chirish

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Telefon raqami bo'yicha
reviewer = User.objects.get(phone='+998901234567')
reviewer.delete()
print("✓ Tekshiruvchi o'chirildi")
```

### Parolni O'zgartirish

```python
from django.contrib.auth import get_user_model
User = get_user_model()

reviewer = User.objects.get(phone='+998901234567')
reviewer.set_password('yangi_parol')
reviewer.save()
print("✓ Parol o'zgartirildi")
```

## 🔐 Xavfsizlik

### ✅ To'g'ri
- Har bir tekshiruvchi uchun alohida account
- Kuchli parollar (kamida 8 ta belgi, raqam va harf)
- Reviewer guruhiga qo'shish
- `is_staff = False` qoldirish
- Kerak bo'lmaganda o'chirish

### ❌ Noto'g'ri
- `is_staff = True` qilish (Django admin ga kirish beradi)
- `is_superuser = True` qilish (barcha ruxsatlar beradi)
- Oddiy parollar (123456)
- Bir accountni ko'p kishi bilan bo'lishish

## 📊 Ruxsatlar

Tekshiruvchilar faqat quyidagilarni qila oladi:

| Amal | Ruxsat |
|------|--------|
| Writing natijalarini ko'rish | ✅ |
| Speaking natijalarini ko'rish | ✅ |
| Ball qo'yish va izoh yozish | ✅ |
| Yuklangan rasmlar/audio ni ko'rish | ✅ |
| Audit log ni ko'rish | ✅ |
| Django admin panel | ❌ |
| User ma'lumotlarini o'zgartirish | ❌ |
| Exam/Test yaratish yoki o'zgartirish | ❌ |

## 🆘 Muammolar va Yechimlar

### "Sizda admin panelga kirish huquqi yo'q"

**Sabab:** User Reviewer guruhida emas  
**Yechim:**
```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
reviewer_group = Group.objects.get(name='Reviewer')

user = User.objects.get(phone='+998901234567')
user.groups.add(reviewer_group)
user.save()
```

### Tekshiruvchi Django admin ga kira olmoqda

**Sabab:** `is_staff=True` qolgan  
**Yechim:**
```python
user = User.objects.get(phone='+998901234567')
user.is_staff = False
user.is_superuser = False
user.save()
```

### "Reviewer" guruhi topilmadi

**Sabab:** Setup command ishlatilmagan  
**Yechim:**
```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py setup_reviewers
```

## 📚 To'liq Dokumentatsiya

Batafsil ma'lumot uchun:
- `/home/user/turantalim/REVIEWER_SETUP_GUIDE.md`

## 📞 Kontakt

Savollar bo'lsa:
- Telegram: @your_support
- Email: support@turantalim.uz

---

**Oxirgi yangilanish:** 2025-10-08  
**Versiya:** 1.0
