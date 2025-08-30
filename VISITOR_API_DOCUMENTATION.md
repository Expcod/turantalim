# Visitor API Documentation

Bu API kursga ro'yxatdan o'tish arizalarini boshqarish uchun ishlatiladi.

## Base URL
```
http://localhost:8000/visitor/api/
```

## Endpoints

### 1. Kursga ro'yxatdan o'tish (Create Visitor)

**POST** `/visitors/`

Kursga ro'yxatdan o'tish arizasini yaratadi va Telegram guruhiga avtomatik xabar yuboradi.

**Request Body:**
```json
{
    "first_name": "Aziz",
    "last_name": "Karimov", 
    "phone_number": "+998901234567"
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "+998901234567",
    "status": "new",
    "status_display": "Yangi",
    "full_name": "Aziz Karimov",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "created_at_tashkent": "15.01.2024 15:30",
    "updated_at_tashkent": "15.01.2024 15:30",
    "notes": null
}
```

**Validation Rules:**
- `first_name`: Kamida 2 ta harf, bo'sh joylar olib tashlanadi
- `last_name`: Kamida 2 ta harf, bo'sh joylar olib tashlanadi  
- `phone_number`: +998 bilan boshlanishi va 9 ta raqam bo'lishi kerak

### 2. Barcha arizalarni olish (List Visitors)

**GET** `/visitors/`

Barcha kursga ro'yxatdan o'tgan foydalanuvchilarni qaytaradi.

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "first_name": "Aziz",
        "last_name": "Karimov",
        "phone_number": "+998901234567",
        "status": "new",
        "status_display": "Yangi",
        "full_name": "Aziz Karimov",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "notes": null
    }
]
```

### 3. Bitta arizani olish (Retrieve Visitor)

**GET** `/visitors/{id}/`

Kursga ro'yxatdan o'tgan foydalanuvchi ma'lumotlarini qaytaradi.

**Response (200 OK):**
```json
{
    "id": 1,
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "+998901234567",
    "status": "new",
    "status_display": "Yangi",
    "full_name": "Aziz Karimov",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "notes": null
}
```

### 4. Ariza holatini yangilash (Update Visitor)

**PUT** `/visitors/{id}/`

Kursga ro'yxatdan o'tgan foydalanuvchi holatini yangilaydi.

**Request Body:**
```json
{
    "status": "in_review",
    "notes": "Ariza ko'rib chiqilmoqda"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "+998901234567",
    "status": "in_review",
    "status_display": "Ko'rib chiqilmoqda",
    "full_name": "Aziz Karimov",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "notes": "Ariza ko'rib chiqilmoqda"
}
```

### 5. Holatni o'zgartirish (Change Status)

**POST** `/visitors/{id}/change_status/`

Kursga ro'yxatdan o'tgan foydalanuvchi holatini o'zgartiradi.

**Request Body:**
```json
{
    "status": "approved"
}
```

**Status Options:**
- `new` - Yangi
- `in_review` - Ko'rib chiqilmoqda
- `approved` - Qabul qilindi

**Response (200 OK):**
```json
{
    "id": 1,
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "+998901234567",
    "status": "approved",
    "status_display": "Qabul qilindi",
    "full_name": "Aziz Karimov",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:40:00Z",
    "notes": "Ariza ko'rib chiqilmoqda"
}
```

### 6. Statistika (Statistics)

**GET** `/visitors/statistics/`

Kursga ro'yxatdan o'tgan foydalanuvchilar statistikasini qaytaradi.

**Response (200 OK):**
```json
{
    "total": 25,
    "new": 10,
    "in_review": 8,
    "approved": 7
}
```

### 7. Holat bo'yicha filtrlash (Filter by Status)

**GET** `/visitors/by_status/?status=new`

Holat bo'yicha filtrlangan kursga ro'yxatdan o'tgan foydalanuvchilarni qaytaradi.

**Query Parameters:**
- `status` (optional): `new`, `in_review`, `approved`

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "first_name": "Aziz",
        "last_name": "Karimov",
        "phone_number": "+998901234567",
        "status": "new",
        "status_display": "Yangi",
        "full_name": "Aziz Karimov",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "notes": null
    }
]
```

## Error Responses

### 400 Bad Request
```json
{
    "first_name": ["Ism kamida 2 ta harfdan iborat bo'lishi kerak"],
    "phone_number": ["Telefon raqami +998 bilan boshlanishi kerak"]
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```



## Authentication

- **Barcha endpointlar**: Authentication talab qilinmaydi
- **JWT token kerak emas**

## Telegram Integration

Har safar yangi ariza yaratilganda, quyidagi ma'lumotlar Telegram guruhiga avtomatik yuboriladi:

```
🆕 Yangi kursga ro'yxatdan o'tish arizasi!

👤 Foydalanuvchi: Aziz Karimov
📱 Telefon: +998901234567
📅 Sana: 15.01.2024 10:30
🔗 Admin panel: /admin/visitor/visitor/1/
```

## Swagger Documentation

API dokumentatsiyasini ko'rish uchun:
```
http://localhost:8000/swagger/
```

## Admin Panel

Arizalarni boshqarish uchun admin panel:
```
http://localhost:8000/admin/visitor/visitor/
```

Admin panelda quyidagi imkoniyatlar mavjud:
- Barcha arizalarni ko'rish
- Holat bo'yicha filtrlash
- Bir nechta arizalarni tanlab holatini o'zgartirish
- Izohlar qo'shish
- Statistika ko'rish
