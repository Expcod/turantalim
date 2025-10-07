# Parol O'zgartirish API Qo'llanmasi

Bu qo'llanma frontend dasturchi uchun parol o'zgartirish funksiyalarini to'g'ri ishlatish uchun tayyorlangan.

## 📋 Mundarija

1. [Parol o'zgartirish (login qilgan foydalanuvchi uchun)](#1-parol-ozgartirish-login-qilgan-foydalanuvchi-uchun)
2. [Parolni tiklash jarayoni](#2-parolni-tiklash-jarayoni)
   - [2.1 Parol tiklash so'rovini yuborish](#21-parol-tiklash-sorovini-yuborish)
   - [2.2 Tasdiqlash kodini tekshirish](#22-tasdiqlash-kodini-tekshirish)
   - [2.3 Yangi parolni o'rnatish](#23-yangi-parolni-ornatish)

---

## 1. Parol O'zgartirish (Login qilgan foydalanuvchi uchun)

### Endpoint
```
PUT https://api.turantalim.uz/user/profile/change-password/
```

### Autentifikatsiya
```
Authorization: Bearer <access_token>
```

### Request Body (JSON)
```json
{
    "old_password": "eski_parol123",
    "new_password": "yangi_parol456"
}
```

### Parol talablari
- **Minimal uzunlik**: 6 ta belgi
- **Majburiy elementlar**: 
  - Kamida 1 ta harf (A-Z yoki a-z)
  - Kamida 1 ta raqam (0-9)

### Response holatlari

#### ✅ Muvaffaqiyatli (200 OK)
```json
{
    "message": "Parol muvaffaqiyatli o'zgartirildi!"
}
```

#### ❌ Xatolik holatlari

**400 Bad Request - Eski parol noto'g'ri:**
```json
{
    "error": "Eski parol noto'g'ri!"
}
```

**400 Bad Request - Validation xatosi:**
```json
{
    "new_password": [
        "Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak!"
    ]
}
```

```json
{
    "new_password": [
        "Parolda kamida bitta harf va bitta raqam bo'lishi kerak!"
    ]
}
```

**401 Unauthorized - Token yo'q yoki noto'g'ri:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Frontend misoli (JavaScript/Fetch)
```javascript
const changePassword = async (oldPassword, newPassword) => {
    try {
        const response = await fetch('/api/users/profile/change-password/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Parol muvaffaqiyatli o\'zgartirildi!');
            // Qo'shimcha logika...
        } else {
            if (data.error) {
                alert(data.error);
            } else if (data.new_password) {
                alert(data.new_password[0]);
            }
        }
    } catch (error) {
        console.error('Xatolik:', error);
        alert('Tarmoq xatosi yuz berdi!');
    }
};
```

---

## 2. Parolni Tiklash Jarayoni

Parolni tiklash 3 bosqichdan iborat:

### 2.1 Parol Tiklash So'rovini Yuborish

#### Endpoint
```
POST https://api.turantalim.uz/user/password/reset/request/
```

#### Request Body (JSON)
```json
{
    "identifier": "+998901234567"
}
```
yoki
```json
{
    "identifier": "user@example.com"
}
```

#### Response holatlari

#### ✅ Muvaffaqiyatli (200 OK)
**Telefon raqami uchun:**
```json
{
    "message": "Tasdiqlash kodi SMS orqali yuborildi."
}
```

**Email uchun:**
```json
{
    "message": "Tasdiqlash kodi email orqali yuborildi."
}
```

#### ❌ Xatolik holatlari

**400 Bad Request - Foydalanuvchi topilmadi:**
```json
{
    "error": "Foydalanuvchi topilmadi!"
}
```

**500 Internal Server Error - SMS yuborishda xatolik:**
```json
{
    "error": "SMS yuborishda xatolik yuz berdi!"
}
```

### 2.2 Tasdiqlash Kodini Tekshirish

#### Endpoint
```
POST https://api.turantalim.uz/user/password/reset/verify/
```

#### Request Body (JSON)
```json
{
    "identifier": "+998901234567",
    "code": "123456"
}
```

#### Response holatlari

#### ✅ Muvaffaqiyatli (200 OK)
```json
{
    "message": "Tasdiqlash kodi to'g'ri."
}
```

#### ❌ Xatolik holatlari

**400 Bad Request - Validation xatosi:**
```json
{
    "error": "Foydalanuvchi topilmadi!"
}
```

```json
{
    "error": "Tasdiqlash kodi noto'g'ri!"
}
```

```json
{
    "error": "Tasdiqlash kodi muddati tugagan!"
}
```

### 2.3 Yangi Parolni O'rnatish

#### Endpoint
```
POST https://api.turantalim.uz/user/password/reset/confirm/
```

#### Request Body (JSON)
```json
{
    "identifier": "+998901234567",
    "code": "123456",
    "new_password": "yangi_parol123",
    "confirm_password": "yangi_parol123"
}
```

#### Response holatlari

#### ✅ Muvaffaqiyatli (200 OK)
```json
{
    "message": "Parol muvaffaqiyatli o'zgartirildi!"
}
```

#### ❌ Xatolik holatlari

**400 Bad Request - Validation xatosi:**
```json
{
    "error": "Parollar mos kelmaydi!"
}
```

```json
{
    "error": "Parolda kamida bitta harf va bitta raqam bo'lishi kerak!"
}
```

```json
{
    "error": "Foydalanuvchi topilmadi!"
}
```

```json
{
    "error": "Tasdiqlash kodi noto'g'ri!"
}
```

```json
{
    "error": "Tasdiqlash kodi muddati tugagan!"
}
```

---

## 📝 Frontend Implementatsiya Misoli

### Parol tiklash to'liq jarayoni

```javascript
class PasswordReset {
    constructor() {
        this.identifier = '';
        this.code = '';
    }

    // 1. Parol tiklash so'rovini yuborish
    async requestReset(identifier) {
        try {
            const response = await fetch('/api/users/password/reset/request/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ identifier })
            });

            const data = await response.json();

            if (response.ok) {
                this.identifier = identifier;
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            return { success: false, message: 'Tarmoq xatosi yuz berdi!' };
        }
    }

    // 2. Tasdiqlash kodini tekshirish
    async verifyCode(code) {
        try {
            const response = await fetch('/api/users/password/reset/verify/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    identifier: this.identifier,
                    code: code
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.code = code;
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            return { success: false, message: 'Tarmoq xatosi yuz berdi!' };
        }
    }

    // 3. Yangi parolni o'rnatish
    async confirmNewPassword(newPassword, confirmPassword) {
        try {
            const response = await fetch('/api/users/password/reset/confirm/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    identifier: this.identifier,
                    code: this.code,
                    new_password: newPassword,
                    confirm_password: confirmPassword
                })
            });

            const data = await response.json();

            if (response.ok) {
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            return { success: false, message: 'Tarmoq xatosi yuz berdi!' };
        }
    }
}

// Foydalanish misoli
const passwordReset = new PasswordReset();

// 1-bosqich: So'rov yuborish
const step1 = await passwordReset.requestReset('+998901234567');
if (step1.success) {
    console.log('Kod yuborildi:', step1.message);
} else {
    console.error('Xatolik:', step1.message);
}

// 2-bosqich: Kodni tekshirish
const step2 = await passwordReset.verifyCode('123456');
if (step2.success) {
    console.log('Kod to\'g\'ri:', step2.message);
} else {
    console.error('Xatolik:', step2.message);
}

// 3-bosqich: Yangi parolni o'rnatish
const step3 = await passwordReset.confirmNewPassword('yangi123', 'yangi123');
if (step3.success) {
    console.log('Parol o\'zgartirildi:', step3.message);
} else {
    console.error('Xatolik:', step3.message);
}
```

---

## ⚠️ Muhim Eslatmalar

1. **Tasdiqlash kodi muddati**: 3 daqiqa
2. **Kod uzunligi**: 6 ta raqam
3. **Parol talablari**: 
   - Minimal 6 ta belgi
   - Kamida 1 ta harf va 1 ta raqam
4. **Autentifikatsiya**: Faqat parol o'zgartirish uchun token kerak
5. **Parol tiklash**: Token talab qilinmaydi

## 🔐 Xavfsizlik

- Barcha so'rovlar HTTPS orqali yuborilishi kerak
- Tokenlarni xavfsiz saqlang
- Parolni frontendda saqlamang
- Xatoliklarni foydalanuvchiga tushunarli ko'rsating

---

## 📞 Qo'llab-quvvatlash

Agar savollaringiz bo'lsa, backend jamoasi bilan bog'laning.
