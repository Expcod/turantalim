# 🚀 API Quick Reference - Frontend Developer

## Base URL
```
Production: https://api.turantalim.uz
```

---
---

## ✍️ Writing Section

### Submit Writing Answers
```http
POST /multilevel/testcheck/writing/
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

FormData:
- user_test_id: 123
- exam_id: 456
- section_id: 789  // Writing section ID
- question_1_image_1: File
- question_1_image_2: File (optional)
- question_2_image_1: File
- question_2_image_2: File (optional)
- question_2_image_3: File (optional)
```

**Response:**
```json
{
  "id": 890,
  "user_test_id": 123,
  "section": {
    "id": 789,
    "type": "writing",
    "title": "Writing Section"
  },
  "status": "pending",
  "created_at": "2025-10-08T12:30:45.123456Z",
  "answers": [
    {
      "question_id": 1,
      "images": [
        "/media/writing/question_1_image_1.jpg"
      ]
    },
    {
      "question_id": 2,
      "images": [
        "/media/writing/question_2_image_1.jpg"
      ]
    }
  ]
}
```

### Get Writing Result
```http
GET /multilevel/test-result/{test_result_id}/
Authorization: Bearer YOUR_TOKEN

Response:
{
  "id": 890,
  "status": "checked",
  "score": 65.5,
  "max_score": 75,
  "created_at": "2025-10-08T12:30:45Z",
  "reviewed_at": "2025-10-08T15:45:30Z",
  "feedback": {
    "task1": {
      "score": 20.5,
      "max_score": 24.75,
      "comment": "Good structure, but grammar needs improvement."
    },
    "task2": {
      "score": 45.0,
      "max_score": 50.25,
      "comment": "Excellent essay with clear arguments."
    }
  },
  "reviewer": {
    "name": "Admin User"
  }
}
```

---

## 🎤 Speaking Section

### Submit Speaking Answers
```http
POST /multilevel/testcheck/speaking/
Content-Type: multipart/form-data
Authorization: Bearer YOUR_TOKEN

FormData:
- user_test_id: 123
- exam_id: 456
- section_id: 790  // Speaking section ID
- question_1_audio: File  // Part 1
- question_2_audio: File  // Part 2
- question_3_audio: File  // Part 3
```

**Response:**
```json
{
  "id": 891,
  "user_test_id": 123,
  "section": {
    "id": 790,
    "type": "speaking",
    "title": "Speaking Section"
  },
  "status": "pending",
  "created_at": "2025-10-08T12:30:45.123456Z",
  "answers": [
    {
      "question_id": 1,
      "audio": "/media/speaking/question_1_audio.mp3"
    },
    {
      "question_id": 2,
      "audio": "/media/speaking/question_2_audio.mp3"
    },
    {
      "question_id": 3,
      "audio": "/media/speaking/question_3_audio.mp3"
    }
  ]
}
```

### Get Speaking Result
```http
GET /multilevel/test-result/{test_result_id}/
Authorization: Bearer YOUR_TOKEN

Response:
{
  "id": 891,
  "status": "checked",
  "score": 70,
  "max_score": 75,
  "created_at": "2025-10-08T12:30:45Z",
  "reviewed_at": "2025-10-08T16:20:15Z",
  "feedback": {
    "comment": "Good pronunciation and fluency. Grammar needs some work."
  },
  "reviewer": {
    "name": "Admin User"
  }
}
```

---

## 📋 All User Test Results

### Get User's Test Results List
```http
GET /multilevel/test-results/
Authorization: Bearer YOUR_TOKEN

Response:
{
  "count": 3,
  "results": [
    {
      "id": 890,
      "section_type": "writing",
      "status": "checked",
      "score": 65.5,
      "max_score": 75,
      "created_at": "2025-10-08T12:30:45Z"
    },
    {
      "id": 891,
      "section_type": "speaking",
      "status": "checked",
      "score": 70,
      "max_score": 75,
      "created_at": "2025-10-08T13:15:30Z"
    },
    {
      "id": 892,
      "section_type": "listening",
      "status": "checked",
      "score": 85,
      "max_score": 100,
      "created_at": "2025-10-08T10:20:15Z"
    }
  ]
}
```

---

## 📊 Overall Exam Result

### Calculate Overall Score
```http
GET /multilevel/exam-results/multilevel-tys/?user_test_id={user_test_id}
Authorization: Bearer YOUR_TOKEN

Response:
{
  "user_test_id": 123,
  "exam": {
    "id": 456,
    "title": "CEFR 1. Sinav",
    "level": "multilevel"
  },
  "overall_score": 290.5,
  "max_score": 350,
  "percentage": 83,
  "passed": true,
  "sections": [
    {
      "type": "listening",
      "score": 85,
      "max_score": 100,
      "status": "checked"
    },
    {
      "type": "reading",
      "score": 90,
      "max_score": 100,
      "status": "checked"
    },
    {
      "type": "writing",
      "score": 65.5,
      "max_score": 75,
      "status": "checked"
    },
    {
      "type": "speaking",
      "score": 70,
      "max_score": 75,
      "status": "checked"
    }
  ],
  "completed_at": "2025-10-08T16:20:15Z"
}
```

---

## 🔢 Status Values

| Status | Meaning | User Can See |
|--------|---------|--------------|
| `pending` | Yuborilgan, tekshirilmagan | ❌ Score yo'q |
| `reviewing` | Tekshirilmoqda | ❌ Score yo'q |
| `checked` | Tekshirilgan | ✅ Score va feedback bor |

---

## 📁 File Requirements

### Images (Writing)
- **Format:** JPG, PNG
- **Max Size:** 10 MB per image
- **Recommended:** 1920x1080px or less

### Audio (Speaking)
- **Format:** MP3, WAV, WebM, OGG
- **Max Size:** 50 MB per audio
- **Recommended:** 128kbps or higher

---

## ⚠️ Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "details": {
    "user_test_id": ["This field is required."],
    "question_1_image_1": ["No file was submitted."]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 413 Payload Too Large
```json
{
  "error": "File too large",
  "details": "Maximum file size is 10 MB"
}
```

---

## 🌐 CORS Configuration

Backend allows requests from:
- `https://turantalim.uz` (Production)

---

## 📱 Example: Complete Flow

```javascript
// 1. Login
const loginResponse = await fetch('https://api.turantalim.uz/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    phone: '+998901234567',
    password: 'password123'
  })
})
const { access } = await loginResponse.json()

// 2. Submit Writing
const formData = new FormData()
formData.append('user_test_id', '123')
formData.append('exam_id', '456')
formData.append('section_id', '789')
formData.append('question_1_image_1', imageFile1)
formData.append('question_2_image_1', imageFile2)

const submitResponse = await fetch('https://api.turantalim.uz/multilevel/testcheck/writing/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access}` },
  body: formData
})
const result = await submitResponse.json()

// 3. Check result later
const resultResponse = await fetch(`https://api.turantalim.uz/multilevel/test-result/${result.id}/`, {
  headers: { 'Authorization': `Bearer ${access}` }
})
const finalResult = await resultResponse.json()

if (finalResult.status === 'checked') {
  console.log('Score:', finalResult.score)
  console.log('Feedback:', finalResult.feedback)
}
```

---

## 📞 Need Help?

- **Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) (full version)
- **Backend:** Django REST Framework
- **Admin Dashboard:** https://api.turantalim.uz/admin-dashboard/
- **Swagger API Docs:** https://api.turantalim.uz/swagger/

---

**Last Updated:** October 8, 2025  
**API Version:** v1.0
