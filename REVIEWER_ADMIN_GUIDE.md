# Tekshiruvchilar Admin Panel - To'liq Qo'llanma

## 🎯 Yangi Imkoniyatlar

Admin panelda endi **"Tekshiruvchilar"** bo'limi mavjud bo'lib, quyidagi imkoniyatlarni beradi:

### ✨ Asosiy Funksiyalar

1. **Tekshiruvchilarni Boshqarish**
   - Yangi tekshiruvchi yaratish (login va parol bilan)
   - Mavjud tekshiruvchilarni tahrirlash
   - Tekshiruvchilarni faolsizlantirish/o'chirish

2. **To'liq Statistika**
   - Jami tekshiruvlar soni
   - Writing bo'limi tekshiruvlari
   - Speaking bo'limi tekshiruvlari
   - O'rtacha berilgan ball
   - Oxirgi tekshiruv sanasi

3. **Tekshiruvlar Tarixi**
   - Har bir tekshiruvchining barcha baholagan natijalarini ko'rish
   - ID, talaba, bo'lim, imtihon, ball, sana
   - Faqat status=checked bo'lgan tekshiruvlar

## 📋 Admin Panelda Tekshiruvchilar Bo'limi

### Kirish

1. Django admin panelga kiring: `http://your-domain.com/admin/`
2. Chap menyuda **"MULTILEVEL"** bo'limini toping
3. **"Tekshiruvchilar"** (Reviewers) ni bosing

### Tekshiruvchilar Ro'yxati

Ro'yxatda quyidagi ma'lumotlar ko'rsatiladi:

| Ustun | Tavsif | Rangli Ko'rsatkich |
|-------|--------|-------------------|
| **Telefon** | Login uchun telefon raqami | - |
| **To'liq Ism** | Ism va familiya | - |
| **Email** | Email manzil | - |
| **Jami Tekshiruvlar** | Umumiy tekshiruvlar soni | 🟢 10+, 🟠 1-10, ⚪ 0 |
| **Writing** | Writing tekshiruvlari | ✍️ Soni |
| **Speaking** | Speaking tekshiruvlari | 🎤 Soni |
| **O'rtacha Ball** | Berilgan o'rtacha ball | 🟢 70+, 🟠 50-69, 🔴 <50 |
| **Oxirgi Tekshiruv** | Oxirgi baholash sanasi | Nisbiy vaqt |
| **Faol** | Aktiv holati | ✅/❌ |
| **Qo'shilgan** | Ro'yxatdan o'tgan sana | Sana |

## ➕ Yangi Tekshiruvchi Qo'shish

### 1. Admin Paneldan

#### Qadamlar:

1. **Tekshiruvchilar** sahifasiga o'ting
2. O'ng yuqori burchakda **"ADD TEKSHIRUVCHI"** tugmasini bosing
3. Formani to'ldiring:

**Formadagi Maydonlar:**

```
┌─────────────────────────────────────┐
│ YANGI TEKSHIRUVCHI YARATISH         │
├─────────────────────────────────────┤
│                                     │
│ 📱 Telefon raqami *                 │
│    [+998901234567]                  │
│    Login sifatida ishlatiladi       │
│                                     │
│ 👤 Ism *                            │
│    [Ali]                            │
│                                     │
│ 👥 Familiya *                       │
│    [Valiyev]                        │
│                                     │
│ 📧 Email                            │
│    [ali@example.com]                │
│    Ixtiyoriy                        │
│                                     │
│ 🔒 Parol *                          │
│    [••••••••]                       │
│    Kamida 8 belgi                   │
│                                     │
│ 🔒 Parolni Tasdiqlash *             │
│    [••••••••]                       │
│    Parolni qayta kiriting           │
│                                     │
│  [SAVE]  [SAVE AND ADD ANOTHER]    │
└─────────────────────────────────────┘
```

4. **"SAVE"** tugmasini bosing

✅ **Avtomatik Sozlanadi:**
- Reviewer guruhiga qo'shiladi
- `is_staff = False` (Django admin kirmasligi)
- `is_superuser = False`
- `is_active = True`

### 2. Misollar

#### Misol 1: Oddiy Tekshiruvchi

```
Telefon: +998901111111
Ism: Aziza
Familiya: Rahimova
Email: aziza@example.com
Parol: Reviewer@123
```

#### Misol 2: Bir Nechta Tekshiruvchi

```python
# Django shell orqali
python manage.py shell

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
reviewer_group = Group.objects.get(name='Reviewer')

reviewers = [
    {
        'phone': '+998901111111',
        'first_name': 'Aziza',
        'last_name': 'Rahimova',
        'password': 'Reviewer@123'
    },
    {
        'phone': '+998902222222',
        'first_name': 'Jamshid',
        'last_name': 'Karimov',
        'password': 'Reviewer@456'
    },
]

for data in reviewers:
    user = User.objects.create_user(**data)
    user.groups.add(reviewer_group)
    user.is_staff = False
    user.save()
    print(f"✓ {user.get_full_name()} yaratildi")
```

## 📊 Tekshiruvchi Sahifasi

Tekshiruvchini bosganingizda quyidagi ma'lumotlarni ko'rasiz:

### 1. Asosiy Ma'lumotlar

```
┌─────────────────────────────────────┐
│ ASOSIY MA'LUMOTLAR                  │
├─────────────────────────────────────┤
│ Telefon:     +998901234567          │
│ Ism:         Ali                    │
│ Familiya:    Valiyev                │
│ Email:       ali@example.com        │
└─────────────────────────────────────┘
```

### 2. Statistika Blok

```
┌─────────────────────────────────────┐
│ TEKSHIRUVCHI STATISTIKASI           │
├─────────────────────────────────────┤
│ Jami Tekshiruvlar:         45       │
│ Writing Bo'limi:       ✍️ 25        │
│ Speaking Bo'limi:      🎤 20        │
│ O'rtacha Ball:             68.5     │
│ Oxirgi Tekshiruv:  15.10.2025 14:30│
└─────────────────────────────────────┘
```

### 3. Tekshiruvlar Tarixi (Inline Jadval)

Sahifaning pastida **barcha baholangan natijalar** ko'rsatiladi:

| Review ID | Talaba | Bo'lim | Imtihon | Ball | Baholagan Sana | Status |
|-----------|--------|--------|---------|------|----------------|--------|
| [#123](link) | Otabek Azimov | writing | CEFR A1 | 75.0 | 15.10.2025 14:30 | checked |
| [#122](link) | Nodira Karimova | speaking | TYS | 68.0 | 15.10.2025 12:15 | checked |
| [#121](link) | Sardor Usmanov | writing | CEFR B1 | 82.5 | 14.10.2025 16:45 | checked |

**Xususiyatlar:**
- ✅ Faqat `status='checked'` bo'lgan reviewlar
- ✅ Review ID bosilsa, batafsil sahifaga o'tadi
- ✅ Eng yangi tekshiruvlar yuqorida
- ✅ Talaba va imtihon ma'lumotlari

## 🔧 Tekshiruvchini Tahrirlash

### O'zgartirish Mumkin:

- ✅ Ism
- ✅ Familiya
- ✅ Email
- ✅ Faol/Nofaol holati

### O'zgartirib Bo'lmaydi:

- ❌ Telefon raqami (login)
- ❌ Tekshiruvlar tarixi
- ❌ Statistika

### Parolni O'zgartirish:

1. Tekshiruvchini oching
2. Parol maydonida **"this form"** linkini bosing
3. Yangi parolni ikki marta kiriting
4. Save

## 🗑️ Tekshiruvchini O'chirish

### O'chirish Jarayoni:

1. Tekshiruvchini tanlang
2. Action dropdown dan **"Delete selected"** ni tanlang
3. Tasdiqlang

### ⚠️ Muhim:

- ❌ Faqat **superuser** o'chira oladi
- ✅ Tekshiruvchining **barcha tekshiruvlari saqlanib qoladi**
- ✅ O'chirilgan tekshiruvchi ma'lumotlari ManualReview da ko'rinadi
- ⚠️ Login qilolmaydi

### Faolsizlantirish (Yaxshiroq):

O'chirish o'rniga **"is_active = False"** qiling:
- ✅ Ma'lumotlar saqlanadi
- ✅ Statistika ko'rinadi
- ❌ Login qila olmaydi
- ✅ Kerak bo'lsa qayta faollashtirish mumkin

## 📈 Statistika Tushuntirish

### Jami Tekshiruvlar

```python
# Faqat status='checked' bo'lganlar
total = reviewer.reviews.filter(status='checked').count()
```

**Rangli Ko'rsatkich:**
- 🟢 10+ tekshiruv (yaxshi)
- 🟠 1-9 tekshiruv (o'rtacha)
- ⚪ 0 tekshiruv (yangi)

### Writing / Speaking Soni

```python
writing = reviewer.reviews.filter(
    status='checked', 
    section='writing'
).count()

speaking = reviewer.reviews.filter(
    status='checked', 
    section='speaking'
).count()
```

### O'rtacha Ball

```python
from django.db.models import Avg

avg = reviewer.reviews.filter(
    status='checked'
).aggregate(Avg('total_score'))['total_score__avg']
```

**Rangli Ko'rsatkich:**
- 🟢 70+ (yuqori)
- 🟠 50-69 (o'rtacha)
- 🔴 <50 (past)

### Oxirgi Tekshiruv

```python
latest = reviewer.reviews.filter(
    status='checked'
).order_by('-reviewed_at').first()
```

**Ko'rsatiladi:**
- "Bugun" - shu kun
- "Kecha" - 1 kun oldin
- "5 kun oldin" - 1 hafta ichida
- "15.10.2025" - 1 haftadan ortiq

## 🔍 Qidiruv va Filtrlash

### Qidiruv

Qidiruv maydoniga yozishingiz mumkin:
- 📱 Telefon raqami
- 👤 Ism
- 👥 Familiya
- 📧 Email

**Misol:**
```
Ali
+99890
@gmail.com
```

### Filtrlar

O'ng tomonda filtrlar:
- **is_active** - Faol/Nofaol
- **date_joined** - Qo'shilgan sana
- **groups__name** - Guruh (Reviewer)

## 🔗 Boshqa Bo'limlar Bilan Integratsiya

### Manual Reviews Bo'limi

Manual Reviews sahifasida endi:
- ✅ Reviewer filtri qo'shildi
- ✅ Reviewer nomi link (tekshiruvchi profiliga o'tadi)
- ✅ Reviewer bo'yicha qidiruv

**Misol:**

ManualReview ro'yxatida:

| ID | Talaba | Bo'lim | Imtihon | Status | Ball | Tekshiruvchi | Sana |
|----|--------|--------|---------|--------|------|--------------|------|
| 123 | Otabek | writing | A1 | checked | 75 | [Ali Valiyev](link) | 15.10.2025 |

Ali Valiyev linkini bossangiz, uning profiliga o'tasiz.

## 🛠️ Troubleshooting

### Muammo: Reviewer yaratilmadi

**Sabab:** Reviewer guruhi topilmadi

**Yechim:**
```bash
python manage.py setup_reviewers
```

### Muammo: Statistika ko'rinmayapti

**Sabab:** Reviewer hali tekshirmagan

**Yechim:** Bu normal, tekshiruvchi biror natijani baholaganda statistika paydo bo'ladi

### Muammo: Inline jadval bo'sh

**Sabab:** Faqat `status='checked'` ko'rsatiladi

**Yechim:** Tekshiruvchi natijalarni to'liq baholashi kerak

### Muammo: Telefon raqami o'zgartirilmayapti

**Bu xususiyat!** Telefon raqami login sifatida ishlatiladi va o'zgartirib bo'lmaydi.

**Agar o'zgartirish kerak bo'lsa:**
1. Yangi akkaunt yarating
2. Eskisini faolsizlantiring

## 📋 Foydalanish Namunalari

### Use Case 1: Yangi Tekshiruvchi Qo'shish

```
1. Admin panelga kirish
2. Tekshiruvchilar → Add Tekshiruvchi
3. Ma'lumotlarni to'ldirish:
   - Telefon: +998901111111
   - Ism: Aziza
   - Familiya: Rahimova
   - Parol: Reviewer@123
4. Save
5. ✓ Tekshiruvchi yaratildi
```

### Use Case 2: Tekshiruvchi Ishlashini Kuzatish

```
1. Tekshiruvchilar ro'yxatidan Aziza Rahimova ni tanlang
2. Statistika bloкida ko'ring:
   - Jami: 25 tekshiruv
   - Writing: 15
   - Speaking: 10
   - O'rtacha: 72.5
3. Pastda barcha 25 ta tekshiruvni ko'ring
4. Istalgan review ID ni bosib batafsil ko'ring
```

### Use Case 3: Eng Yaxshi Tekshiruvchini Topish

```
1. Tekshiruvchilar sahifasida
2. "Jami Tekshiruvlar" ustunni bosing (sort)
3. Eng ko'p tekshirgan yuqorida
4. Yoki "O'rtacha Ball" bo'yicha sort qiling
```

### Use Case 4: Tekshiruvchini Faolsizlantirish

```
1. Tekshiruvchini oching
2. "Holati" bo'limida
3. "is_active" ni uncheck qiling
4. Save
5. ✓ Tekshiruvchi faolsizlantirildi (lekin ma'lumotlar saqlanadi)
```

## 📊 Hisobotlar

### Barcha Tekshiruvchilar Statistikasi

Django admin sahifasidan:

```python
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg

User = get_user_model()

stats = User.objects.filter(
    groups__name='Reviewer'
).annotate(
    total=Count('reviews', filter=Q(reviews__status='checked')),
    avg_score=Avg('reviews__total_score', filter=Q(reviews__status='checked'))
)

for reviewer in stats:
    print(f"{reviewer.get_full_name()}: {reviewer.total} tekshiruv, o'rtacha {reviewer.avg_score}")
```

## 🎓 Best Practices

### 1. Tekshiruvchilarni Tez-Tez Tekshiring

- Haftada 1 marta statistikani ko'ring
- Kam ishlayotganlarni aniqlang
- Yuqori balllar berayotganlarni tekshiring

### 2. Balans Saqlang

- Writing va Speaking tekshiruvlarni teng taqsimlang
- Bir tekshiruvchiga juda ko'p yuk bermaslik

### 3. Sifatni Nazorat Qiling

- O'rtacha balllar 50-80 oralig'ida bo'lishi kerak
- Juda yuqori (90+) yoki past (30-) balllar shubhali

### 4. Parollarni Boshqaring

- Kuchli parollar ishlating
- Har 3 oyda parolni o'zgartiring
- Parollarni xavfsiz saqlang

## 🆘 Yordam

Savollar bo'lsa:
- **Email:** support@turantalim.uz
- **Telegram:** @turantalim_support
- **Dokumentatsiya:** `/home/user/turantalim/REVIEWER_SETUP_GUIDE.md`

---

**Yaratilgan:** 2025-10-08  
**Versiya:** 2.0  
**Muallif:** Turantalim Development Team

