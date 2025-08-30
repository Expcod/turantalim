# Multilevel va TYS Imtihon Natijalari API

Bu API multilevel va TYS imtihonlari uchun batafsil natija ko'rsatish uchun mo'ljallangan.

## API Endpointlar

### 1. Batafsil Imtihon Natijasi

**Endpoint:** `GET /api/multilevel/exam-results/multilevel-tys/`

**Tavsif:** Multilevel va TYS imtihonlari uchun batafsil natija qaytaradi.

**Parametrlar:**
- `user_test_id` (majburiy) - UserTest ID

**Response misoli:**
```json
{
  "success": true,
  "exam_info": {
    "exam_id": 1,
    "exam_name": "CEFR Multilevel Test",
    "exam_level": "MULTILEVEL",
    "language": "English",
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T14:45:00Z"
  },
  "section_results": {
    "listening": {
      "section_name": "Listening",
      "score": 65,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T11:15:00Z"
    },
    "reading": {
      "section_name": "Reading",
      "score": 58,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T12:30:00Z"
    },
    "writing": {
      "section_name": "Writing",
      "score": 62,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T13:45:00Z"
    },
    "speaking": {
      "section_name": "Speaking",
      "score": 60,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T14:45:00Z"
    }
  },
  "overall_result": {
    "total_score": 245,
    "max_possible_score": 300,
    "average_score": 61.25,
    "level": "B2",
    "level_description": "O'rtadan yuqori daraja - mustaqil foydalanuvchi",
    "completed_sections": 4,
    "total_sections": 4,
    "is_complete": true
  },
  "level_ranges": {
    "B1": "38-50 ball",
    "B2": "51-64 ball",
    "C1": "65-75 ball"
  }
}
```

### 2. Imtihonlar Ro'yxati

**Endpoint:** `GET /api/multilevel/exam-results/multilevel-tys/list/`

**Tavsif:** Foydalanuvchining barcha multilevel va tys imtihon natijalarini qaytaradi.

**Parametrlar:**
- `exam_level` (ixtiyoriy) - "multilevel", "tys" yoki "all" (default: "all")
- `limit` (ixtiyoriy) - Natijalar soni (default: 10)

**Response misoli:**
```json
{
  "success": true,
  "total_exams": 3,
  "exams": [
    {
      "user_test_id": 1,
      "exam_name": "CEFR Multilevel Test",
      "exam_level": "MULTILEVEL",
      "language": "English",
      "status": "completed",
      "total_score": 245,
      "average_score": 61.25,
      "level": "B2",
      "completed_sections": 4,
      "total_sections": 4,
      "is_complete": true,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T14:45:00Z"
    },
    {
      "user_test_id": 2,
      "exam_name": "TYS Test",
      "exam_level": "TYS",
      "language": "Turkish",
      "status": "started",
      "total_score": 120,
      "average_score": 30.0,
      "level": "Below B1",
      "completed_sections": 2,
      "total_sections": 4,
      "is_complete": false,
      "created_at": "2024-01-10T09:00:00Z",
      "completed_at": null
    }
  ]
}
```

## Daraja Hisoblash

### Ball Tizimi
- **Har bir section:** Maksimal 75 ball
- **Umumiy ball:** Maksimal 300 ball (4 section × 75 ball)
- **O'rtacha ball:** Umumiy ball ÷ 4

### Daraja Oralig'lari
- **B1:** 38-50 ball (O'rta daraja)
- **B2:** 51-64 ball (O'rtadan yuqori daraja)
- **C1:** 65-75 ball (Yuqori daraja)
- **Below B1:** 37 va undan past ball

## Xato Response

```json
{
  "success": false,
  "error": "Xato xabari"
}
```

## Xatolik Kodlari

- **400 Bad Request:** Noto'g'ri parametrlar
- **404 Not Found:** Imtihon topilmadi
- **403 Forbidden:** Ruxsat yo'q

## Frontend Integratsiyasi

### React misoli:

```javascript
// Batafsil natija olish
const getExamResult = async (userTestId) => {
  try {
    const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Natijani ko'rsatish
      console.log('Exam result:', data);
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};

// Imtihonlar ro'yxatini olish
const getExamList = async (examLevel = 'all', limit = 10) => {
  try {
    const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/list/?exam_level=${examLevel}&limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Ro'yxatni ko'rsatish
      console.log('Exam list:', data.exams);
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

## Muhim Eslatmalar

1. **Authentication:** Barcha API endpointlar authentication talab qiladi
2. **Ruxsat:** Foydalanuvchi faqat o'z imtihon natijalarini ko'ra oladi
3. **Imtihon turi:** Bu API faqat multilevel va tys imtihonlari uchun mo'ljallangan
4. **Section ballari:** Har bir section 0-75 ball oralig'ida baholanadi
5. **Umumiy ball:** 4 section ballining yig'indisi (0-300 ball)
6. **Daraja:** O'rtacha ball asosida aniqlanadi (rasmdagi jadvalga asosan)

## Test Qilish

API ni test qilish uchun:

```bash
# Batafsil natija
curl -X GET "http://localhost:8000/api/multilevel/exam-results/multilevel-tys/?user_test_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Imtihonlar ro'yxati
curl -X GET "http://localhost:8000/api/multilevel/exam-results/multilevel-tys/list/?exam_level=multilevel&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
