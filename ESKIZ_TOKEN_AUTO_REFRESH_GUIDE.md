# Eskiz Token Avtomatik Yangilash Tizimi

## Tavsif

Bu tizim Eskiz.uz API tokenining avtomatik yangilanishini ta'minlaydi. Token eskirganda, tizim avtomatik ravishda yangi token olish uchun `notify.eskiz.uz/api/auth/refresh` endpointiga so'rov yuboradi.

## Asosiy Xususiyatlar

### 1. Avtomatik Token Yangilash
- SMS yuborishda 401 xatolik kelganda token avtomatik yangilanadi
- Yangi token bilan SMS yuborish qayta uriniladi
- Barcha jarayon foydalanuvchi uchun shaffof

### 2. Xatoliklar Bilan Ishlash
- Network xatoliklari uchun timeout (30 soniya)
- Token yangilashda xatolik bo'lsa, foydalanuvchiga ma'lumot beriladi
- Barcha xatoliklar log fayllariga yoziladi

### 3. Logging
- Barcha jarayonlar log fayllariga yoziladi
- Token yangilash natijalari kuzatiladi
- SMS yuborish natijalari qayd etiladi

## Foydalanish

### 1. Avtomatik Foydalanish
SMS yuborish funksiyasi endi avtomatik ravishda token yangilashni amalga oshiradi:

```python
from apps.users.utils import send_sms_via_eskiz

# Bu funksiya endi avtomatik ravishda token yangilashni amalga oshiradi
success = send_sms_via_eskiz("+998901234567", "123456")
```

### 2. Qo'lda Token Yangilash
Token yangilashni qo'lda amalga oshirish uchun:

```python
from apps.users.utils import refresh_eskiz_token

success = refresh_eskiz_token()
if success:
    print("Token muvaffaqiyatli yangilandi!")
else:
    print("Token yangilanmadi!")
```

### 3. Django Management Command
Terminal orqali token yangilash:

```bash
python manage.py refresh_eskiz_token
```

## API Endpoint

### Token Yangilash
- **URL**: `https://notify.eskiz.uz/api/auth/refresh`
- **Method**: `PATCH`
- **Headers**: 
  ```
  Authorization: Bearer {current_token}
  ```
- **Response**:
  ```json
  {
    "message": "token_generated",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "token_type": "bearer"
  }
  ```

## Xatoliklar

### 1. 401 Unauthorized
- Token eskirgan
- Avtomatik yangilash uriniladi

### 2. Network Xatoliklar
- Timeout (30 soniya)
- Connection xatoliklari
- DNS xatoliklari

### 3. API Xatoliklari
- Server xatoliklari (5xx)
- Client xatoliklari (4xx)

## Logging

Barcha jarayonlar quyidagi log darajalari bilan qayd etiladi:

- **INFO**: Muvaffaqiyatli operatsiyalar
- **WARNING**: Token eskirgan holatlar
- **ERROR**: Xatoliklar

### Log Fayllari
- Console: Barcha loglar
- File: `/var/log/django.log`

## Test Qilish

### 1. Test Script
```bash
python test_eskiz_token_refresh.py
```

### 2. Management Command
```bash
python manage.py refresh_eskiz_token
```

### 3. SMS Test
```python
from apps.users.utils import send_sms_via_eskiz
success = send_sms_via_eskiz("+998901234567", "123456")
```

## Sozlamalar

### Environment Variables
```bash
ESKIZ_TOKEN=your_eskiz_token_here
```

### Settings
```python
# core/settings/base.py
ESKIZ_TOKEN = os.environ.get("ESKIZ_TOKEN") or env.str("ESKIZ_TOKEN")
ESKIZ_CALLBACK_URL = ""
```

## Xavfsizlik

### 1. Token Saqlash
- Token environment variable sifatida saqlanadi
- Settings faylida to'g'ridan-to'g'ri yozilmaydi

### 2. Network Xavfsizlik
- HTTPS orqali barcha so'rovlar
- Timeout bilan xavfsizlik
- Error handling

### 3. Logging Xavfsizlik
- Token to'liq log fayllariga yozilmaydi
- Faqat birinchi 20 belgisi ko'rsatiladi

## Muammolarni Hal Qilish

### 1. Token Yangilanmaydi
- Network ulanishini tekshiring
- Token to'g'riligini tekshiring
- API endpoint mavjudligini tekshiring

### 2. SMS Yuborilmaydi
- Token yangilash natijasini tekshiring
- Telefon raqamini tekshiring
- API response ni tekshiring

### 3. Xatoliklar
- Log fayllarini tekshiring
- Network ulanishini tekshiring
- API dokumentatsiyasini tekshiring

## Yangilanishlar

### v1.0.0
- Avtomatik token yangilash
- Xatoliklar bilan ishlash
- Logging tizimi
- Management command
- Test script

## Yordam

Muammolar bo'lsa:
1. Log fayllarini tekshiring
2. Test scriptini ishga tushiring
3. Network ulanishini tekshiring
4. API dokumentatsiyasini o'qib chiqing
