# Turantalim Admin Dashboard

Bu loyiha Turantalim platformasi uchun ishlab chiqilgan admin dashboarddir. Dashboard orqali o'qituvchilar foydalanuvchilar tomonidan topshirilgan imtihonlarning Yozish va Gapirish sectionlarini tekshirish va baholash imkoniyatiga ega bo'ladilar.

## Kirish Ma'lumotlari

**URL:** `http://your-domain.com/admin-dashboard/`

**Test Server:** `http://localhost:8000/admin-dashboard/`

**Login sahifasi:** `/admin-dashboard/login.html`

**Foydalanuvchi ma'lumotlari:**
- Phone number: Sizning admin telefon raqamingiz (masalan: +998908410751)
- Password: Sizning parolingiz

## Asosiy funksiyalar

1. **Foydalanuvchi authenticate qilish**:
   - Faqat tayinlangan adminlar kirishi mumkin
   - Django admin panelida yaratilgan `is_staff=True` foydalanuvchilar kirishi mumkin

2. **Imtihonlar ro'yxati**:
   - Barcha yangi ishlangan imtihonlarni ko'rish (TYS, Multilevel)
   - Foydalanuvchi ismi, familiyasi, imtihon nomi, sanasi ko'rsatilgan
   - Status bo'yicha filterlash (Kutilmoqda / Ko'rilmoqda / Tekshirilgan)
   - Imtihon turi va bo'limlar bo'yicha qidirish

3. **Imtihon natijalarini ko'rish va baholash**:
   - 4 ta section (Tinglash, O'qish, Yozish, Gapirish)
   - Tinglash va O'qish - faqat ko'rish (read-only) - avtomatik tekshirilgan
   - Yozish - rasm javoblarni baholash
   - Gapirish - audio javoblarni baholash

4. **Media fayllarni ko'rish**:
   - Yozish uchun rasmlar (maximum 3 ta rasm har bir savolga)
   - Gapirish uchun audio player (play, pause, stop)

5. **Baholash va saqlash**:
   - Har bir savol uchun alohida ball qo'yish (0-100)
   - Izoh qoldirish imkoniyati
   - Qoralama saqlash yoki yakuniy topshirish
   - Foydalanuvchiga xabar berish

## Texnik ma'lumotlar

Frontend quyidagi texnologiyalar bilan ishlab chiqilgan:
- HTML5
- CSS
- Bootstrap 5
- Tailwind CSS
- JavaScript (ES6+)
- Lightbox2 (rasmlarni kattalashtirish uchun)

## Fayl tuzilishi

```
admin_dashboard/
├── index.html          # Bosh sahifa - imtihonlar ro'yxati
├── submission.html     # Imtihon natijalarini ko'rish va baholash
├── login.html          # Login sahifasi
├── styles.css          # Uslublar
├── js/
│   ├── api-client.js   # API bilan bog'lanish
│   └── main.js         # Asosiy JavaScript funksiyalar
├── images/             # Rasmlar (placeholder fayllar)
└── audio/              # Audio fayllar (placeholder fayllar)
```

## Foydalanish

### 1. Kirish

1. Brauzerda `/admin-dashboard/` yoki `/admin-dashboard/login.html` URL manziliga o'ting
2. Admin telefon raqami va parolini kiriting
3. "Kirish" tugmasini bosing

### 2. Imtihonlarni ko'rish

1. Bosh sahifada (index.html) barcha kutilmoqda imtihonlar ko'rinadi
2. Filtrlar orqali qidirish:
   - Imtihon turi: TYS, CEFR, Multilevel
   - Bo'lim: Yozish, Gapirish
   - Status: Kutilmoqda, Ko'rilmoqda, Tekshirilgan
   - Qidiruv: Foydalanuvchi ismi yoki telefon raqami

### 3. Imtihonni tekshirish

1. Imtihon ro'yxatidan kerakli imtihonni tanlang
2. "Ochish" tugmasini bosing
3. Submission sahifasida 4 ta bo'lim ko'rinadi:
   - **Tinglash**: Faqat ko'rish (avtomatik tekshirilgan)
   - **O'qish**: Faqat ko'rish (avtomatik tekshirilgan)
   - **Yozish**: Rasmlarni ko'rish va baholash
   - **Gapirish**: Audiolarni eshitish va baholash

### 4. Baholash

1. Yozish yoki Gapirish bo'limini tanlang
2. Har bir savol uchun rasmlar (Yozish) yoki audiolar (Gapirish) ko'rinadi
3. O'ng tarafdagi panelda:
   - Har bir savol uchun ball kiriting (0-100)
   - Ixtiyoriy izoh qoldiring
   - Umumiy ball avtomatik hisoblanadi
4. "Qoralama saqlash" yoki "Topshirish" tugmasini bosing
5. Foydalanuvchiga xabar berishni tanlashingiz mumkin

## API Endpointlar

Backend bilan bog'lanish uchun quyidagi API endpointlar ishlatiladi:

### 1. Imtihonlar ro'yxati
```
GET /multilevel/api/admin/submissions/
```
**Query parametrlari:**
- `status`: pending, reviewing, checked
- `section`: writing, speaking
- `exam_level`: tys, multilevel, cefr1
- `search`: Foydalanuvchi ismi yoki username

### 2. Imtihon ma'lumotlari
```
GET /multilevel/api/admin/submissions/{submission_id}/
```

### 3. Yozish ballari yangilash
```
PATCH /multilevel/api/admin/submissions/{submission_id}/writing/
```
**Body:**
```json
{
  "question_scores": {
    "1": {"score": 85, "comment": "Yaxshi ish"},
    "2": {"score": 90, "comment": "Aniq javob"}
  },
  "total_score": 87.5,
  "notified": true
}
```

### 4. Gapirish ballari yangilash
```
PATCH /multilevel/api/admin/submissions/{submission_id}/speaking/
```
**Body:**
```json
{
  "question_scores": {
    "1": {"score": 80, "comment": "Yaxshi talaffuz"},
    "2": {"score": 85, "comment": "To'liq javob"}
  },
  "total_score": 82.5,
  "notified": true
}
```

## Xavfsizlik

- API endpointlar faqat adminlar uchun ochiq (`IsAdminUser` permission)
- Autentifikatsiya Django Token-based auth orqali
- Barcha API so'rovlar HTTPS orqali yuborilishi kerak
- Audit log barcha o'zgarishlarni qayd etadi

## Troubleshooting

### Login ishlamayapti
- Admin foydalanuvchi yaratilganligini tekshiring: `python manage.py createsuperuser`
- Foydalanuvchi `is_staff=True` bo'lishi kerak
- To'g'ri telefon raqami va parol kiritilganligini tekshiring

### API xatolari
- Server ishlab turganligini tekshiring
- CORS sozlamalari to'g'ri ekanligini tekshiring
- Browser console'da xatolarni tekshiring

### Media fayllar ko'rinmayapti
- Media fayllar to'g'ri papkada (submissions/%Y/%m/%d/) ekanligini tekshiring
- Django settings'da MEDIA_URL va MEDIA_ROOT to'g'ri sozlanganligini tekshiring

## Qo'shimcha Ma'lumot

To'liq backend dokumentatsiyasi uchun: `/apps/multilevel/README_MANUAL_REVIEW.md` faylini ko'ring.