# Turantalim.uz Multilevel Admin Panel

Bu admin paneli test va savollarni oson boshqarish uchun yaratilgan. Jazzmin admin framework asosida qurilgan.

## Xususiyatlar

### 1. Test Qo'shish
- **Avval imtihon tanlash**: Test qo'shishda avval qaysi imtihonga qo'shish kerakligini belgilaysiz
- **Avtomatik bo'limlar**: Imtihon tanlangandan keyin shu imtihonga oid bo'limlar avtomatik ko'rsatiladi
- **Ma'lumot ko'rsatish**: Bo'lim tanlanganda uning turi, davomiyligi va boshqa ma'lumotlari ko'rsatiladi

### 2. Savol Qo'shish
- **Avtomatik testlar**: Bo'lim tanlangandan keyin shu bo'limga oid testlar avtomatik ko'rsatiladi
- **Variantli/Variantsiz savollar**: Savol turiga qarab javob maydoni yoki variantlar ko'rsatiladi
- **Dinamik variantlar**: Variantli savollarda variantlarni dinamik qo'shish/o'chirish mumkin
- **Validatsiya**: Savol qo'shishda avtomatik validatsiya

### 3. Qulayliklar
- **Jazzmin admin**: Chiroyli va zamonaviy interfeys
- **AJAX**: Sahifani qayta yuklamasdan ma'lumotlarni yangilash
- **Responsive**: Barcha qurilmalarda yaxshi ko'rinish
- **Xatolarni oldini olish**: Avtomatik validatsiya va xatolarni ko'rsatish

## Fayllar tuzilishi

```
staticfiles/
└── admin/
    └── js/
        ├── test_admin.js      # Test admin paneli uchun JavaScript
        └── question_admin.js  # Savol admin paneli uchun JavaScript

apps/multilevel/
├── admin.py                  # Admin paneli sozlamalari
├── views.py                  # AJAX endpointlari
└── urls.py                   # URL patternlari
```

## JavaScript fayllari

### test_admin.js
- Exam tanlanganda sectionlarni yangilash
- Section tanlanganda ma'lumot ko'rsatish
- Jazzmin admin uchun qo'shimcha stillar

### question_admin.js
- Section tanlanganda testlarni yangilash
- Variantli/variantsiz savollar uchun interfeys
- Dinamik variant qo'shish/o'chirish
- Form validatsiyasi

## AJAX Endpointlari

### Test Admin
- `GET /admin/multilevel/sections/get-sections-by-exam/` - Imtihon bo'yicha bo'limlarni olish
- `GET /admin/multilevel/sections/get-section-info/` - Bo'lim ma'lumotlarini olish

### Savol Admin
- `GET /admin/multilevel/tests/get-tests-by-section/` - Bo'lim bo'yicha testlarni olish
- `GET /admin/multilevel/tests/get-test-info/` - Test ma'lumotlarini olish

## Qo'llash

1. **Test qo'shish**:
   - Admin panelida "Tests" bo'limiga o'ting
   - "Add Test" tugmasini bosing
   - Avval "Exam" tanlang
   - Keyin "Section" tanlang (avtomatik yangilanadi)
   - Test ma'lumotlarini kiriting

2. **Savol qo'shish**:
   - Admin panelida "Questions" bo'limiga o'ting
   - "Add Question" tugmasini bosing
   - Avval "Section" tanlang
   - Keyin "Test" tanlang (avtomatik yangilanadi)
   - Savol turini belgilang (variantli/variantsiz)
   - Savol matni va javobni kiriting

## Validatsiya qoidalari

### Test uchun
- Imtihon va bo'lim majburiy
- Test nomi va tavsifi to'ldirilishi kerak

### Savol uchun
- **Variantli savollar**:
  - Kamida 2 ta variant bo'lishi kerak
  - Faqat bitta to'g'ri variant bo'lishi mumkin
  - Barcha variantlar to'ldirilishi kerak

- **Variantsiz savollar**:
  - Javob maydoni majburiy
  - Javob to'g'ri formatda bo'lishi kerak

## Xavfsizlik

- Barcha AJAX endpointlari `@staff_member_required` dekoratori bilan himoyalangan
- Faqat admin huquqiga ega foydalanuvchilar foydalana oladi
- CSRF token himoyasi faol

## Muammolarni hal qilish

### JavaScript ishlamayapti
1. Static fayllar to'g'ri joyda ekanligini tekshiring
2. `python manage.py collectstatic` buyrug'ini ishga tushiring
3. Brauzer konsolida xatolarni tekshiring

### AJAX so'rovlar ishlamayapti
1. URL patternlari to'g'ri ekanligini tekshiring
2. Admin huquqlarini tekshiring
3. Django server loglarini tekshiring

### Validatsiya ishlamayapti
1. JavaScript fayllar yuklangani ekanligini tekshiring
2. Form elementlari ID lari to'g'ri ekanligini tekshiring
3. Brauzer konsolida xatolarni tekshiring 