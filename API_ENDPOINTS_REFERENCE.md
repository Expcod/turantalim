# API Endpoints To'liq Ro'yxati

**Oxirgi yangilanish:** 2025-10-08  
**Versiya:** 2.0  
**Base URL:** `http://api.turantalim.uz` yoki `http://127.0.0.1:8000`

---

## 📋 Talaba APIs

### 1. Authentication
```
POST /user/login/                    - Kirish
POST /user/register/                 - Ro'yxatdan o'tish
POST /user/logout/                   - Chiqish
GET  /user/profile/                  - Profil ma'lumotlari
```

### 2. Exams
```
GET  /multilevel/exams/              - Imtihonlar ro'yxati
GET  /multilevel/test/               - Test olish
POST /multilevel/test/               - Test boshlash
```

### 3. Test Submission

#### Listening
```
POST /multilevel/testcheck/listening/
```

#### Reading
```
POST /multilevel/testcheck/reading/
```

#### Writing (with images)
```
POST /multilevel/testcheck/writing/
Content-Type: multipart/form-data

Body:
  - test_result_id: Integer
  - question_images[1][]: File (multiple)
  - question_images[2][]: File (multiple)
```

#### Speaking (with audio)
```
POST /multilevel/testcheck/speaking/
Content-Type: multipart/form-data

Body:
  - test_result_id: Integer
  - question_audios[1][]: File (multiple)
  - question_audios[2][]: File (multiple)
```

### 4. Results
```
GET  /multilevel/test-result/{id}/          - Test natijasi
GET  /multilevel/test-results/              - Barcha natijalar
GET  /multilevel/test-result/overall/       - Umumiy natija
GET  /multilevel/exam-results/multilevel-tys/ - CEFR/TYS natijalar
```

---

## 🔐 Admin Dashboard APIs

### 1. Authentication
```
POST /api/token/                    - Admin login
POST /api/logout/                   - Admin logout
```

### 2. Manual Review

#### List Submissions
```
GET  /multilevel/api/admin/submissions/

Query params:
  - status: pending, reviewing, checked
  - section: writing, speaking
  - exam_level: a1, a2, b1, b2, c1, tys, multilevel
  - search: user name/username
```

#### Get Submission Detail
```
GET  /multilevel/api/admin/submissions/{id}/
```

#### Get Media Files
```
GET  /multilevel/api/admin/submissions/{id}/media/
```

#### Update Writing Scores
```
PATCH /multilevel/api/admin/submissions/{id}/writing/

Body:
{
  "question_scores": {
    "1": {"score": 75.0, "comment": "Good work"},
    "2": {"score": 80.0, "comment": "Excellent"}
  },
  "total_score": 77.5,
  "notified": true,
  "is_draft": false
}
```

#### Update Speaking Scores
```
PATCH /multilevel/api/admin/submissions/{id}/speaking/

Body:
{
  "question_scores": {
    "1": {"score": 70.0, "comment": "Clear pronunciation"}
  },
  "total_score": 70.0,
  "notified": true,
  "is_draft": false
}
```

---

## 🗺️ URL Mapping

### Core URLs (`core/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),              # Django admin
    path('user/', include("apps.users.urls")),    # User auth
    path('multilevel/', include("apps.multilevel.urls")),  # Main app
    path('api/token/', AdminLoginView.as_view()), # Admin login
    path('admin-dashboard/', serve_admin_dashboard),  # Dashboard
]
```

### Multilevel URLs (`apps/multilevel/urls.py`)
```python
urlpatterns = [
    # ViewSet routes
    path('api/', include(router.urls)),
    
    # Exams
    path('exams/', ExamListView.as_view()),
    
    # Tests
    path('test/', TestRequestApiView.as_view()),
    path('testcheck/listening/', ListeningTestCheckApiView.as_view()),
    path('testcheck/reading/', ReadingTestCheckApiView.as_view()),
    path('testcheck/writing/', WritingTestCheckApiView.as_view()),
    path('testcheck/speaking/', SpeakingTestCheckApiView.as_view()),
    
    # Results
    path('test-result/<int:test_result_id>/', TestResultDetailView.as_view()),
    path('test-results/', TestResultListView.as_view()),
    path('test-result/overall/', OverallTestResultView.as_view()),
    path('exam-results/multilevel-tys/', MultilevelTysExamResultView.as_view()),
]
```

### ViewSet Router
```python
router = DefaultRouter()
router.register(r'admin/submissions', ManualReviewViewSet, basename='admin-submissions')

# Bu quyidagi URLlarni yaratadi:
# GET    /multilevel/api/admin/submissions/
# POST   /multilevel/api/admin/submissions/
# GET    /multilevel/api/admin/submissions/{id}/
# PUT    /multilevel/api/admin/submissions/{id}/
# PATCH  /multilevel/api/admin/submissions/{id}/
# DELETE /multilevel/api/admin/submissions/{id}/
# GET    /multilevel/api/admin/submissions/{id}/media/
# PATCH  /multilevel/api/admin/submissions/{id}/writing/
# PATCH  /multilevel/api/admin/submissions/{id}/speaking/
```

---

## 📝 Endpoint Naming Convention

### ❌ Noto'g'ri (Old)
```
POST /api/exams/speaking/submit/    # MAVJUD EMAS!
POST /api/exams/writing/submit/     # MAVJUD EMAS!
GET  /api/exams/writing/result/123/ # MAVJUD EMAS!
```

### ✅ To'g'ri (Current)
```
POST /multilevel/testcheck/speaking/
POST /multilevel/testcheck/writing/
GET  /multilevel/test-result/123/
```

---

## 🔍 Quick Reference

### Test Submission Pattern
```
POST /multilevel/testcheck/{section_type}/

section_type: listening, reading, writing, speaking
```

### Admin Review Pattern
```
GET    /multilevel/api/admin/submissions/
GET    /multilevel/api/admin/submissions/{id}/
PATCH  /multilevel/api/admin/submissions/{id}/{section}/

section: writing, speaking
```

### Results Pattern
```
GET /multilevel/test-result/{id}/        # Single result
GET /multilevel/test-results/            # All results
GET /multilevel/test-result/overall/     # Overall score
```

---

## 🚀 Usage Examples

### Submit Writing (Fetch API)
```javascript
const formData = new FormData();
formData.append('test_result_id', 123);

// Question 1 images
formData.append('question_images[1][]', imageFile1);
formData.append('question_images[1][]', imageFile2);

// Question 2 images
formData.append('question_images[2][]', imageFile3);

const response = await fetch('http://api.turantalim.uz/multilevel/testcheck/writing/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`
  },
  body: formData
});
```

### Submit Speaking (Axios)
```javascript
const formData = new FormData();
formData.append('test_result_id', 123);
formData.append('question_audios[1][]', audioFile1);
formData.append('question_audios[2][]', audioFile2);

const response = await axios.post('/multilevel/testcheck/speaking/', formData, {
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'multipart/form-data'
  }
});
```

### Admin Review Writing
```javascript
const response = await fetch('http://api.turantalim.uz/multilevel/api/admin/submissions/123/writing/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Token ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question_scores: {
      "1": {score: 75, comment: "Good"},
      "2": {score: 80, comment: "Excellent"}
    },
    total_score: 77.5,
    notified: true,
    is_draft: false
  })
});
```

---

## 🛠️ Testing with cURL

### Submit Writing
```bash
curl -X POST http://api.turantalim.uz/multilevel/testcheck/writing/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "test_result_id=123" \
  -F "question_images[1][]=@image1.jpg" \
  -F "question_images[1][]=@image2.jpg" \
  -F "question_images[2][]=@image3.jpg"
```

### Get Submissions (Admin)
```bash
curl -X GET "http://api.turantalim.uz/multilevel/api/admin/submissions/?status=pending" \
  -H "Authorization: Token ADMIN_TOKEN"
```

### Update Writing Scores (Admin)
```bash
curl -X PATCH http://api.turantalim.uz/multilevel/api/admin/submissions/123/writing/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_scores": {
      "1": {"score": 75, "comment": "Good work"},
      "2": {"score": 80, "comment": "Excellent"}
    },
    "total_score": 77.5,
    "notified": true,
    "is_draft": false
  }'
```

---

## 📊 Status Codes

| Code | Ma'nosi | Qachon |
|------|---------|--------|
| 200 | OK | Successful GET/PATCH |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Token yo'q yoki noto'g'ri |
| 403 | Forbidden | Ruxsat yo'q |
| 404 | Not Found | Endpoint/Resource topilmadi |
| 500 | Server Error | Backend xatosi |

---

## 🔗 Related Documentation

- **Full API Docs:** `/home/user/turantalim/API_DOCUMENTATION.md`
- **Quick Reference:** `/home/user/turantalim/API_QUICK_REFERENCE.md`
- **Manual Review:** `/home/user/turantalim/apps/multilevel/README_MANUAL_REVIEW.md`
- **Reviewer Guide:** `/home/user/turantalim/REVIEWER_SETUP_GUIDE.md`

---

**⚠️ Muhim:** Barcha `/api/exams/` bilan boshlanadigan URLlar noto'g'ri! To'g'ri yo'llar `/multilevel/testcheck/` va `/multilevel/test-result/` dan boshlanadi.
