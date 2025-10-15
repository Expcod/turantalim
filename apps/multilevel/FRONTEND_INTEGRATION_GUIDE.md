# Frontend Integration Guide - Imtihon Natijalari API

Bu qo'llanma frontend dasturchilari uchun imtihon natijalarini olish bo'yicha API endpointlari va ularni qanday ishlatish haqida to'liq ma'lumot beradi.

## 📋 API Endpointlari

### 1. 🎯 Bitta Imtihon Natijasini Olish

**Endpoint:** `GET https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/`

**Maqsad:** Bitta multilevel yoki TYS imtihonining batafsil natijasini olish

**Parametrlar:**
- `user_test_id` (required) - Imtihon ID si

**Example Request:**
```javascript
// JavaScript fetch
const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id=123', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

**Example Response:**
```json
{
  "success": true,
  "exam_info": {
    "exam_id": 1,
    "exam_name": "Multilevel English Test",
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
      "completed_at": "2024-01-15T11:00:00Z"
    },
    "reading": {
      "section_name": "Reading",
      "score": 58,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T12:00:00Z"
    },
    "writing": {
      "section_name": "Writing",
      "score": 45,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T13:30:00Z"
    },
    "speaking": {
      "section_name": "Speaking",
      "score": 52,
      "max_score": 75,
      "status": "completed",
      "completed_at": "2024-01-15T14:45:00Z"
    }
  },
  "overall_result": {
    "total_score": 220,
    "max_possible_score": 300,
    "final_score": 55.0,
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

### 2. 📝 Barcha Imtihon Natijalarini Olish

**Endpoint:** `GET https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/`

**Maqsad:** Foydalanuvchining barcha multilevel va TYS imtihonlarining qisqacha ro'yxatini olish

**Parametrlar:**
- `exam_level` (optional) - "multilevel", "tys", yoki "all" (default: "all")
- `limit` (optional) - Natijalar soni (default: 10)

**Example Request:**
```javascript
// Barcha imtihonlar
const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
});

// Faqat multilevel imtihonlar
const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/?exam_level=multilevel', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
});

// Faqat TYS imtihonlar
const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/?exam_level=tys', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  }
});
```

**Example Response:**
```json
{
  "success": true,
  "total_exams": 3,
  "exams": [
    {
      "user_test_id": 123,
      "exam_name": "Multilevel English Test",
      "exam_level": "MULTILEVEL",
      "language": "English",
      "status": "completed",
      "total_score": 220,
      "final_score": 55.0,
      "level": "B2",
      "completed_sections": 4,
      "total_sections": 4,
      "is_complete": true,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T14:45:00Z"
    },
    {
      "user_test_id": 124,
      "exam_name": "TYS English Test",
      "exam_level": "TYS",
      "language": "English",
      "status": "completed",
      "total_score": 85,
      "final_score": 85.0,
      "level": "B2",
      "completed_sections": 4,
      "total_sections": 4,
      "is_complete": true,
      "created_at": "2024-01-10T09:00:00Z",
      "completed_at": "2024-01-10T13:15:00Z"
    }
  ]
}
```

## 🔧 Frontend Implementation Examples

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const ExamResults = () => {
  const [exams, setExams] = useState([]);
  const [selectedExam, setSelectedExam] = useState(null);
  const [loading, setLoading] = useState(true);

  // Barcha imtihonlarni olish
  useEffect(() => {
    const fetchExams = async () => {
      try {
        const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        if (data.success) {
          setExams(data.exams);
        }
      } catch (error) {
        console.error('Error fetching exams:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchExams();
  }, []);

  // Bitta imtihon natijasini olish
  const fetchExamDetail = async (userTestId) => {
    try {
      const response = await fetch(`https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      if (data.success) {
        setSelectedExam(data);
      }
    } catch (error) {
      console.error('Error fetching exam detail:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="exam-results">
      <h2>Imtihon Natijalari</h2>
      
      {/* Imtihonlar ro'yxati */}
      <div className="exams-list">
        {exams.map(exam => (
          <div key={exam.user_test_id} className="exam-item">
            <h3>{exam.exam_name}</h3>
            <p>Daraja: {exam.level} ({exam.final_score} ball)</p>
            <p>Holat: {exam.is_complete ? 'Tugatilgan' : 'Jarayonda'}</p>
            <button onClick={() => fetchExamDetail(exam.user_test_id)}>
              Batafsil ko'rish
            </button>
          </div>
        ))}
      </div>

      {/* Batafsil natija */}
      {selectedExam && (
        <div className="exam-detail">
          <h3>{selectedExam.exam_info.exam_name}</h3>
          
          {/* Section natijalari */}
          <div className="sections">
            {Object.entries(selectedExam.section_results).map(([key, section]) => (
              <div key={key} className="section">
                <h4>{section.section_name}</h4>
                <p>Ball: {section.score}/{section.max_score}</p>
                <p>Holat: {section.status}</p>
              </div>
            ))}
          </div>

          {/* Umumiy natija */}
          <div className="overall-result">
            <h4>Umumiy Natija</h4>
            <p>Yakuniy ball: {selectedExam.overall_result.final_score}</p>
            <p>Daraja: {selectedExam.overall_result.level}</p>
            <p>Tavsif: {selectedExam.overall_result.level_description}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExamResults;
```

### Vue.js Component Example

```vue
<template>
  <div class="exam-results">
    <h2>Imtihon Natijalari</h2>
    
    <!-- Loading state -->
    <div v-if="loading" class="loading">Loading...</div>
    
    <!-- Exams list -->
    <div v-else class="exams-list">
      <div 
        v-for="exam in exams" 
        :key="exam.user_test_id" 
        class="exam-item"
        @click="fetchExamDetail(exam.user_test_id)"
      >
        <h3>{{ exam.exam_name }}</h3>
        <p>Daraja: {{ exam.level }} ({{ exam.final_score }} ball)</p>
        <p>Holat: {{ exam.is_complete ? 'Tugatilgan' : 'Jarayonda' }}</p>
      </div>
    </div>

    <!-- Exam detail -->
    <div v-if="selectedExam" class="exam-detail">
      <h3>{{ selectedExam.exam_info.exam_name }}</h3>
      
      <!-- Sections -->
      <div class="sections">
        <div 
          v-for="(section, key) in selectedExam.section_results" 
          :key="key" 
          class="section"
        >
          <h4>{{ section.section_name }}</h4>
          <p>Ball: {{ section.score }}/{{ section.max_score }}</p>
          <p>Holat: {{ section.status }}</p>
        </div>
      </div>

      <!-- Overall result -->
      <div class="overall-result">
        <h4>Umumiy Natija</h4>
        <p>Yakuniy ball: {{ selectedExam.overall_result.final_score }}</p>
        <p>Daraja: {{ selectedExam.overall_result.level }}</p>
        <p>Tavsif: {{ selectedExam.overall_result.level_description }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      exams: [],
      selectedExam: null,
      loading: true
    };
  },
  
  async mounted() {
    await this.fetchExams();
  },
  
  methods: {
    async fetchExams() {
      try {
        const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`,
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        if (data.success) {
          this.exams = data.exams;
        }
      } catch (error) {
        console.error('Error fetching exams:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchExamDetail(userTestId) {
      try {
        const response = await fetch(`https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id=${userTestId}`, {
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`,
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        if (data.success) {
          this.selectedExam = data;
        }
      } catch (error) {
        console.error('Error fetching exam detail:', error);
      }
    }
  }
};
</script>
```

## 📊 Data Structure Explanation

### Exam Types va Scoring

#### Multilevel Exam:
- **Max Score per Section:** 75 points
- **Total Max Score:** 300 points (4 sections × 75)
- **Final Score Calculation:** Total Score ÷ 4 = Final Score (0-75)
- **Level Determination:** Based on final score (B1: 38-50, B2: 51-64, C1: 65-75)

#### TYS Exam:
- **Max Score per Section:** 25 points
- **Total Max Score:** 100 points (4 sections × 25)
- **Final Score Calculation:** Total Score = Final Score (0-100)
- **Level Determination:** Based on final score (B1: 51+, B2: 68+, C1: 87+)

### Section Statuses:
- `not_started` - Section boshlanmagan
- `started` - Section boshlangan, lekin tugatilmagan
- `completed` - Section tugatilgan

### Exam Statuses:
- `created` - Imtihon yaratilgan
- `started` - Imtihon boshlangan
- `completed` - Imtihon tugatilgan

## 🚨 Error Handling

```javascript
const handleApiCall = async () => {
  try {
    const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id=123', {
      headers: {
        'Authorization': 'Bearer YOUR_TOKEN',
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      // API xatosi
      console.error('API Error:', data.error);
      return;
    }
    
    // Muvaffaqiyatli response
    console.log('Success:', data);
    
  } catch (error) {
    // Network yoki boshqa xatolar
    console.error('Network Error:', error);
  }
};
```

## 🔐 Authentication

Barcha API endpointlari authentication talab qiladi:

```javascript
// Token bilan request
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Token olish (login dan keyin)
const token = localStorage.getItem('auth_token');
```

## 📱 Mobile Integration

React Native uchun:

```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';

const fetchExamResults = async () => {
  try {
    const token = await AsyncStorage.getItem('auth_token');
    
    const response = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## 🎨 UI/UX Recommendations

1. **Loading States:** API call paytida loading spinner ko'rsating
2. **Error Messages:** Foydalanuvchiga tushunarli xato xabarlari ko'rsating
3. **Progress Indicators:** Section natijalarida progress bar ishlating
4. **Level Colors:** Daraja uchun ranglar belgilang (B1: sariq, B2: ko'k, C1: yashil)
5. **Responsive Design:** Barcha qurilmalarda yaxshi ko'rinish

Bu qo'llanma orqali frontend dasturchilar imtihon natijalarini olish va ko'rsatish uchun to'liq ma'lumotga ega bo'ladilar! 🎉
