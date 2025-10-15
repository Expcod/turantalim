# Postman Collection - Imtihon Natijalari API

Bu fayl Postman da API endpointlarni test qilish uchun collection yaratish bo'yicha qo'llanma.

## 🔧 Environment Variables

Postman da quyidagi environment variables yarating:

```json
{
  "base_url": "https://api.turantalim.uz/multilevel",
  "token": "YOUR_JWT_TOKEN_HERE"
}
```

## 📋 Collection Structure

### 1. Imtihon Natijasini Olish

**Request:**
```
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=123
```

**Headers:**
```
Authorization: Bearer {{token}}
Content-Type: application/json
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

### 2. Barcha Imtihon Natijalarini Olish

**Request:**
```
GET {{base_url}}/exam-results/multilevel-tys/list/
```

**Headers:**
```
Authorization: Bearer {{token}}
Content-Type: application/json
```

**Query Parameters (Optional):**
- `exam_level`: multilevel, tys, all
- `limit`: 10

**Example Request with Parameters:**
```
GET {{base_url}}/exam-results/multilevel-tys/list/?exam_level=multilevel&limit=5
```

**Example Response:**
```json
{
  "success": true,
  "total_exams": 2,
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

### 3. Test SMS Notification

**Request:**
```
GET {{base_url}}/test/sms-notification/?phone_number=+998901234567
```

**Headers:**
```
Authorization: Bearer {{token}}
Content-Type: application/json
```

**Example Response:**
```json
{
  "success": true,
  "message": "Test SMS sent successfully to +998901234567",
  "phone_number": "+998901234567"
}
```

## 🧪 Test Scenarios

### 1. Valid Test Cases

```javascript
// Test Case 1: Valid user_test_id
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=123

// Test Case 2: All exams list
GET {{base_url}}/exam-results/multilevel-tys/list/

// Test Case 3: Multilevel exams only
GET {{base_url}}/exam-results/multilevel-tys/list/?exam_level=multilevel

// Test Case 4: TYS exams only
GET {{base_url}}/exam-results/multilevel-tys/list/?exam_level=tys

// Test Case 5: Limited results
GET {{base_url}}/exam-results/multilevel-tys/list/?limit=3
```

### 2. Error Test Cases

```javascript
// Test Case 1: Missing user_test_id
GET {{base_url}}/exam-results/multilevel-tys/

// Expected Response:
{
  "success": false,
  "error": "user_test_id parametri majburiy"
}

// Test Case 2: Invalid user_test_id
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=99999

// Expected Response:
{
  "success": false,
  "error": "Imtihon topilmadi yoki ruxsatingiz yo'q"
}

// Test Case 3: Non-multilevel exam
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=456

// Expected Response:
{
  "success": false,
  "error": "Bu API faqat multilevel va tys imtihonlari uchun mo'ljallangan"
}

// Test Case 4: Invalid exam_level parameter
GET {{base_url}}/exam-results/multilevel-tys/list/?exam_level=invalid

// Test Case 5: Missing phone number for SMS test
GET {{base_url}}/test/sms-notification/

// Expected Response:
{
  "success": false,
  "error": "phone_number parameter is required"
}
```

### 3. Authentication Test Cases

```javascript
// Test Case 1: No Authorization header
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=123

// Expected Response: 401 Unauthorized

// Test Case 2: Invalid token
Authorization: Bearer invalid_token
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=123

// Expected Response: 401 Unauthorized

// Test Case 3: Expired token
Authorization: Bearer expired_token
GET {{base_url}}/exam-results/multilevel-tys/?user_test_id=123

// Expected Response: 401 Unauthorized
```

## 📊 Response Status Codes

| Status Code | Description | Example |
|-------------|-------------|---------|
| 200 | Success | Valid request with data |
| 400 | Bad Request | Missing required parameters |
| 401 | Unauthorized | Invalid or missing token |
| 404 | Not Found | Exam not found |
| 500 | Internal Server Error | Server-side error |

## 🔍 Pre-request Scripts

Postman da Pre-request Script yozing (token avtomatik olish uchun):

```javascript
// Token ni environment dan olish
const token = pm.environment.get("token");

// Agar token yo'q bo'lsa, login API ga murojaat qilish
if (!token) {
    // Login API ga murojaat qilish
    pm.sendRequest({
        url: pm.environment.get("base_url").replace("/multilevel", "/auth/login"),
        method: 'POST',
        header: {
            'Content-Type': 'application/json'
        },
        body: {
            mode: 'raw',
            raw: JSON.stringify({
                username: "test_user",
                password: "test_password"
            })
        }
    }, function (err, response) {
        if (response.json().access) {
            pm.environment.set("token", response.json().access);
        }
    });
}
```

## 🧪 Tests Scripts

Har bir request uchun test script yozing:

```javascript
// Response status code tekshirish
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Success field tekshirish
pm.test("Response has success field", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
});

// Success true ekanligini tekshirish
pm.test("Success is true", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
});

// Response time tekshirish (3 soniya dan kam)
pm.test("Response time is less than 3000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(3000);
});

// Content-Type tekshirish
pm.test("Content-Type is application/json", function () {
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
});
```

## 📱 Mobile Testing

Mobile testing uchun:

```javascript
// Mobile user agent header qo'shish
pm.request.headers.add({
    key: 'User-Agent',
    value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
});

// Mobile screen size header qo'shish
pm.request.headers.add({
    key: 'X-Screen-Size',
    value: '375x667'
});
```

Bu Postman collection orqali API endpointlarni to'liq test qilish mumkin! 🚀
