# Multilevel va TYS Imtihon Natijalari API Dokumentatsiyasi

Bu dokumentatsiya multilevel va TYS imtihonlari uchun natijalarni olish bo'yicha ikkita API endpoint haqida to'liq ma'lumot beradi.

## 📋 Mundarija

1. [API Endpointlar](#api-endpointlar)
2. [user_test_id vs test_result_id](#user_test_id-vs-test_result_id)
3. [Batafsil Imtihon Natijasi API](#batafsil-imtihon-natijasi-api)
4. [Imtihonlar Ro'yxati API](#imtihonlar-royxati-api)
5. [Frontend Integratsiya Namunalari](#frontend-integratsiya-namunalari)
6. [Xatoliklar](#xatoliklar)

---

## 🔗 API Endpointlar

### 1. Batafsil Imtihon Natijasi
```
GET /api/multilevel/exam-results/multilevel-tys/
```

### 2. Imtihonlar Ro'yxati
```
GET /api/multilevel/exam-results/multilevel-tys/list/
```

---

## 🔍 user_test_id vs test_result_id

### user_test_id
- **Model**: `UserTest` jadvalidan olinadi
- **Ma'nosi**: Foydalanuvchining bitta imtihonni boshlashini ifodalaydi
- **Tuzilishi**: 
  - Bir foydalanuvchi → Bir imtihon (multilevel yoki tys)
  - Barcha sectionlar (listening, reading, writing, speaking) shu UserTest ga bog'langan
  - Umumiy imtihon holati va balli saqlanadi

### test_result_id
- **Model**: `TestResult` jadvalidan olinadi
- **Ma'nosi**: Foydalanuvchining bitta section (bo'lim) natijasini ifodalaydi
- **Tuzilishi**:
  - Bir UserTest → Bir nechta TestResult (har section uchun)
  - Har bir section uchun alohida natija
  - Section balli va vaqt ma'lumotlari saqlanadi

### Bog'lanish
```
UserTest (user_test_id: 123)
├── TestResult (test_result_id: 456) - Listening section
├── TestResult (test_result_id: 457) - Reading section  
├── TestResult (test_result_id: 458) - Writing section
└── TestResult (test_result_id: 459) - Speaking section
```

---

## 📊 Batafsil Imtihon Natijasi API

### Endpoint
```
GET /api/multilevel/exam-results/multilevel-tys/
```

### Parametrlar
| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| `user_test_id` | Integer | ✅ | UserTest ID - imtihon natijasini olish uchun |

### Autentifikatsiya
```javascript
headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}
```

### So'rov Namuni
```javascript
const response = await fetch('/api/multilevel/exam-results/multilevel-tys/?user_test_id=123', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

### Muvaffaqiyatli Javob (200 OK)

```javascript
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

### Javob Maydonlari Tushuntirilishi

#### exam_info
| Maydon | Turi | Tavsif |
|--------|------|--------|
| `exam_id` | Integer | Imtihon ID |
| `exam_name` | String | Imtihon nomi |
| `exam_level` | String | Imtihon darajasi (MULTILEVEL/TYS) |
| `language` | String | Imtihon tili |
| `status` | String | Imtihon holati (created/started/completed) |
| `created_at` | String | Imtihon boshlangan vaqti |
| `completed_at` | String | Imtihon tugagan vaqti (null bo'lsa tugagan emas) |

#### section_results
Har bir section uchun:
| Maydon | Turi | Tavsif |
|--------|------|--------|
| `section_name` | String | Section nomi |
| `score` | Integer | Section balli (0-75) |
| `max_score` | Integer | Maksimal ball (75) |
| `status` | String | Section holati (not_started/completed) |
| `completed_at` | String | Section tugagan vaqti |

#### overall_result
| Maydon | Turi | Tavsif |
|--------|------|--------|
| `total_score` | Integer | Barcha section ballari yig'indisi |
| `max_possible_score` | Integer | Maksimal mumkin ball (300) |
| `average_score` | Number | O'rtacha ball |
| `level` | String | Daraja (B1/B2/C1) |
| `level_description` | String | Daraja tushuntirilishi |
| `completed_sections` | Integer | Tugatilgan sectionlar soni |
| `total_sections` | Integer | Jami sectionlar soni (4) |
| `is_complete` | Boolean | Imtihon to'liq tugatilganligi |

---

## 📋 Imtihonlar Ro'yxati API

### Endpoint
```
GET /api/multilevel/exam-results/multilevel-tys/list/
```

### Parametrlar
| Parametr | Turi | Majburiy | Tavsif |
|----------|------|----------|--------|
| `exam_level` | String | ❌ | Imtihon turi: "multilevel", "tys" yoki "all" (default: "all") |
| `limit` | Integer | ❌ | Natijalar soni (default: 10) |

### Autentifikatsiya
```javascript
headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}
```

### So'rov Namunlari

```javascript
// Barcha multilevel va tys imtihonlari
const response1 = await fetch('/api/multilevel/exam-results/multilevel-tys/list/', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// Faqat multilevel imtihonlari
const response2 = await fetch('/api/multilevel/exam-results/multilevel-tys/list/?exam_level=multilevel', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// Faqat tys imtihonlari, 5 ta natija
const response3 = await fetch('/api/multilevel/exam-results/multilevel-tys/list/?exam_level=tys&limit=5', {
    headers: { 'Authorization': `Bearer ${token}` }
});
```

### Muvaffaqiyatli Javob (200 OK)

```javascript
{
    "success": true,
    "total_exams": 3,
    "exams": [
        {
            "user_test_id": 123,
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
            "user_test_id": 124,
            "exam_name": "TYS Test",
            "exam_level": "TYS",
            "language": "Turkish",
            "status": "started",
            "total_score": 120,
            "average_score": 40.0,
            "level": "B1",
            "completed_sections": 2,
            "total_sections": 4,
            "is_complete": false,
            "created_at": "2024-01-10T09:15:00Z",
            "completed_at": null
        }
    ]
}
```

### Javob Maydonlari Tushuntirilishi

| Maydon | Turi | Tavsif |
|--------|------|--------|
| `success` | Boolean | So'rov muvaffaqiyatli |
| `total_exams` | Integer | Jami imtihonlar soni |
| `exams` | Array | Imtihonlar ro'yxati |

#### exams array elementi
| Maydon | Turi | Tavsif |
|--------|------|--------|
| `user_test_id` | Integer | UserTest ID (batafsil natija uchun) |
| `exam_name` | String | Imtihon nomi |
| `exam_level` | String | Imtihon darajasi |
| `language` | String | Imtihon tili |
| `status` | String | Imtihon holati |
| `total_score` | Integer | Jami ball |
| `average_score` | Number | O'rtacha ball |
| `level` | String | Daraja |
| `completed_sections` | Integer | Tugatilgan sectionlar |
| `total_sections` | Integer | Jami sectionlar |
| `is_complete` | Boolean | To'liq tugatilganligi |
| `created_at` | String | Boshlangan vaqti |
| `completed_at` | String | Tugatilgan vaqti |

---

## 💻 Frontend Integratsiya Namunalari

### user_test_id ni olish

```javascript
// 1. Imtihonlar ro'yxatidan user_test_id ni olish
const getExamList = async () => {
    try {
        const response = await fetch('/api/multilevel/exam-results/multilevel-tys/list/', {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Imtihonlar ro\'yxati olinmadi');
        }
        
        const data = await response.json();
        return data.exams; // user_test_id larni o'z ichiga oladi
        
    } catch (error) {
        console.error('Xatolik:', error);
        throw error;
    }
};

// 2. Batafsil natijani olish
const getExamDetail = async (userTestId) => {
    try {
        const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Batafsil natija olinmadi');
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Xatolik:', error);
        throw error;
    }
};
```

### To'liq Integratsiya Namuni

```javascript
class ExamResultsManager {
    constructor() {
        this.token = this.getToken();
    }
    
    // Imtihonlar ro'yxatini olish
    async getExamList(examLevel = 'all', limit = 10) {
        const params = new URLSearchParams();
        if (examLevel !== 'all') params.append('exam_level', examLevel);
        if (limit !== 10) params.append('limit', limit);
        
        const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/list/?${params}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Imtihonlar ro\'yxati olinmadi');
        }
        
        return await response.json();
    }
    
    // Batafsil natijani olish
    async getExamDetail(userTestId) {
        const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Batafsil natija olinmadi');
        }
        
        return await response.json();
    }
    
    // Natijalarni ko'rsatish
    displayExamResults(examData) {
        const { exam_info, section_results, overall_result } = examData;
        
        console.log(`Imtihon: ${exam_info.exam_name}`);
        console.log(`Daraja: ${exam_info.exam_level}`);
        console.log(`Holat: ${exam_info.status}`);
        
        // Section natijalari
        Object.entries(section_results).forEach(([section, data]) => {
            console.log(`${data.section_name}: ${data.score}/${data.max_score}`);
        });
        
        // Umumiy natija
        console.log(`Jami ball: ${overall_result.total_score}/${overall_result.max_possible_score}`);
        console.log(`O'rtacha ball: ${overall_result.average_score}`);
        console.log(`Daraja: ${overall_result.level}`);
        console.log(`Tugatilgan: ${overall_result.is_complete ? 'Ha' : 'Yo\'q'}`);
    }
    
    // Foydalanish
    async showUserExams() {
        try {
            // 1. Imtihonlar ro'yxatini olish
            const examList = await this.getExamList();
            console.log('Imtihonlar ro\'yxati:', examList);
            
            // 2. Birinchi imtihonning batafsil natijasini olish
            if (examList.exams.length > 0) {
                const firstExam = examList.exams[0];
                const examDetail = await this.getExamDetail(firstExam.user_test_id);
                this.displayExamResults(examDetail);
            }
            
        } catch (error) {
            console.error('Xatolik:', error);
        }
    }
}

// Foydalanish
const examManager = new ExamResultsManager();
examManager.showUserExams();
```

### React Hook Namuni

```javascript
import { useState, useEffect } from 'react';

const useExamResults = () => {
    const [examList, setExamList] = useState([]);
    const [examDetail, setExamDetail] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const token = getToken(); // Token olish funksiyasi
    
    // Imtihonlar ro'yxatini olish
    const fetchExamList = async (examLevel = 'all', limit = 10) => {
        setLoading(true);
        setError(null);
        
        try {
            const params = new URLSearchParams();
            if (examLevel !== 'all') params.append('exam_level', examLevel);
            if (limit !== 10) params.append('limit', limit);
            
            const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/list/?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Imtihonlar ro\'yxati olinmadi');
            }
            
            const data = await response.json();
            setExamList(data.exams);
            
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    // Batafsil natijani olish
    const fetchExamDetail = async (userTestId) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`/api/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Batafsil natija olinmadi');
            }
            
            const data = await response.json();
            setExamDetail(data);
            
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    return {
        examList,
        examDetail,
        loading,
        error,
        fetchExamList,
        fetchExamDetail
    };
};

// React komponentida foydalanish
const ExamResultsComponent = () => {
    const { examList, examDetail, loading, error, fetchExamList, fetchExamDetail } = useExamResults();
    
    useEffect(() => {
        fetchExamList();
    }, []);
    
    const handleExamClick = (userTestId) => {
        fetchExamDetail(userTestId);
    };
    
    if (loading) return <div>Yuklanmoqda...</div>;
    if (error) return <div>Xatolik: {error}</div>;
    
    return (
        <div>
            <h2>Imtihonlar ro'yxati</h2>
            {examList.map(exam => (
                <div key={exam.user_test_id} onClick={() => handleExamClick(exam.user_test_id)}>
                    <h3>{exam.exam_name}</h3>
                    <p>Ball: {exam.total_score}/{exam.total_sections * 75}</p>
                    <p>Daraja: {exam.level}</p>
                    <p>Holat: {exam.status}</p>
                </div>
            ))}
            
            {examDetail && (
                <div>
                    <h2>Batafsil natija</h2>
                    <h3>{examDetail.exam_info.exam_name}</h3>
                    <p>Jami ball: {examDetail.overall_result.total_score}/300</p>
                    <p>Daraja: {examDetail.overall_result.level}</p>
                </div>
            )}
        </div>
    );
};
```

---

## ❌ Xatoliklar

### 400 Bad Request

```javascript
{
    "success": false,
    "error": "user_test_id parametri majburiy"
}
```

```javascript
{
    "success": false,
    "error": "user_test_id to'g'ri son bo'lishi kerak"
}
```

```javascript
{
    "success": false,
    "error": "Bu API faqat multilevel va tys imtihonlari uchun mo'ljallangan"
}
```

### 404 Not Found

```javascript
{
    "success": false,
    "error": "Imtihon topilmadi yoki ruxsatingiz yo'q"
}
```

### Keng Tarqalgan Xatoliklar

| Xatolik Kodi | Sababi | Yechim |
|--------------|--------|--------|
| 400 | user_test_id kiritilmagan | user_test_id parametrini yuboring |
| 400 | user_test_id noto'g'ri format | To'g'ri son formatida yuboring |
| 400 | Imtihon turi noto'g'ri | Faqat multilevel yoki tys imtihonlari |
| 404 | Imtihon topilmadi | To'g'ri user_test_id yuboring |
| 403 | Ruxsat yo'q | Token to'g'ri ekanligini tekshiring |

---

## 📝 Muhim Eslatmalar

1. **user_test_id majburiy**: Batafsil natija uchun user_test_id parametri talab qilinadi
2. **Faqat multilevel va tys**: Bu API faqat multilevel va tys imtihonlari uchun mo'ljallangan
3. **Autentifikatsiya**: Har doim to'g'ri Authorization token yuboring
4. **Ball tizimi**: Har bir section 0-75 ball, jami 0-300 ball
5. **Daraja hisoblash**: O'rtacha ball asosida B1, B2, C1 darajalari aniqlanadi

---

## 🚀 Tezkor Boshlash

1. **Imtihonlar ro'yxatini olish**:
   ```javascript
   const examList = await fetch('/api/multilevel/exam-results/multilevel-tys/list/');
   ```

2. **user_test_id ni olish**:
   ```javascript
   const userTestId = examList.exams[0].user_test_id;
   ```

3. **Batafsil natijani olish**:
   ```javascript
   const examDetail = await fetch(`/api/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`);
   ```

Bu dokumentatsiya orqali frontend developer multilevel va tys imtihon natijalarini to'liq integratsiya qila oladi!
