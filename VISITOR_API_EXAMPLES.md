# Visitor API - Test Examples

Bu fayl visitor API ni test qilish uchun curl command larini o'z ichiga oladi.

## 1. Kursga ro'yxatdan o'tish (Create Visitor)

```bash
curl -X POST http://localhost:8000/visitor/api/visitors/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "+998901234567"
  }'
```

**Expected Response:**
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

## 2. Barcha arizalarni olish (List Visitors)

```bash
curl -X GET http://localhost:8000/visitor/api/visitors/
```

## 3. Bitta arizani olish (Retrieve Visitor)

```bash
curl -X GET http://localhost:8000/visitor/api/visitors/1/
```

## 4. Ariza holatini yangilash (Update Visitor)

```bash
curl -X PUT http://localhost:8000/visitor/api/visitors/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_review",
    "notes": "Ariza ko\'rib chiqilmoqda"
  }'
```

## 5. Holatni o'zgartirish (Change Status)

```bash
curl -X POST http://localhost:8000/visitor/api/visitors/1/change_status/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved"
  }'
```

## 6. Statistika olish (Get Statistics)

```bash
curl -X GET http://localhost:8000/visitor/api/visitors/statistics/
```

**Expected Response:**
```json
{
    "total": 25,
    "new": 10,
    "in_review": 8,
    "approved": 7
}
```

## 7. Holat bo'yicha filtrlash (Filter by Status)

```bash
# Yangi arizalar
curl -X GET "http://localhost:8000/visitor/api/visitors/by_status/?status=new"

# Ko'rib chiqilmoqda
curl -X GET "http://localhost:8000/visitor/api/visitors/by_status/?status=in_review"

# Qabul qilinganlar
curl -X GET "http://localhost:8000/visitor/api/visitors/by_status/?status=approved"
```

## Test Script (Python)

```python
import requests
import json

BASE_URL = "http://localhost:8000/visitor/api"

# 1. Kursga ro'yxatdan o'tish
def create_visitor():
    data = {
        "first_name": "Aziz",
        "last_name": "Karimov",
        "phone_number": "+998901234567"
    }
    
    response = requests.post(f"{BASE_URL}/visitors/", json=data)
    print("Create Visitor:", response.status_code)
    print(response.json())
    return response.json()

# 2. Barcha arizalarni olish
def list_visitors():
    response = requests.get(f"{BASE_URL}/visitors/")
    print("List Visitors:", response.status_code)
    print(response.json())

# 3. Statistika olish
def get_statistics():
    response = requests.get(f"{BASE_URL}/visitors/statistics/")
    print("Statistics:", response.status_code)
    print(response.json())

# Test qilish
if __name__ == "__main__":
    # Yangi ariza yaratish
    visitor = create_visitor()
    
    # Barcha arizalarni olish
    list_visitors()
    
    # Statistika olish
    get_statistics()
```

## Validation Test Cases

### 1. Noto'g'ri telefon raqami
```bash
curl -X POST http://localhost:8000/visitor/api/visitors/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Aziz",
    "last_name": "Karimov",
    "phone_number": "901234567"
  }'
```

**Expected Error:**
```json
{
    "phone_number": ["Telefon raqami +998 bilan boshlanishi kerak"]
}
```

### 2. Qisqa ism
```bash
curl -X POST http://localhost:8000/visitor/api/visitors/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "A",
    "last_name": "Karimov",
    "phone_number": "+998901234567"
  }'
```

**Expected Error:**
```json
{
    "first_name": ["Ism kamida 2 ta harfdan iborat bo'lishi kerak"]
}
```

### 3. Noto'g'ri status
```bash
curl -X POST http://localhost:8000/visitor/api/visitors/1/change_status/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "invalid_status"
  }'
```

**Expected Error:**
```json
{
    "error": "Noto'g'ri status"
}
```

## Frontend Integration

### JavaScript/React uchun
```javascript
// Kursga ro'yxatdan o'tish
const registerForCourse = async (userData) => {
  try {
    const response = await fetch('http://localhost:8000/visitor/api/visitors/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Barcha arizalarni olish
const getVisitors = async () => {
  try {
    const response = await fetch('http://localhost:8000/visitor/api/visitors/');
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Vue.js uchun
```javascript
// Kursga ro'yxatdan o'tish
async registerForCourse(userData) {
  try {
    const response = await this.$http.post('/visitor/api/visitors/', userData);
    return response.data;
  } catch (error) {
    console.error('Error:', error);
  }
}
```
