# Writing Submission - Frontend Format Fix

**Muammo sanasi:** 2025-10-08  
**Yechim:** Backend Legacy Format Support qo'shildi

---

## ❌ Muammo Tavsifi

### Xato Xabari:
```
Writing submission error: Error: Kamida bitta javob yuborilishi kerak
Response status: 400
```

### Sabab:
Frontend va Backend formatlar bir-biriga mos kelmaydi!

---

## 📊 Format Farqlari

### Frontend Yuborayotgan Format (Legacy):

```javascript
FormData:
  user_test_id: 241
  exam_id: 12
  section_type: writing
  task1_image1: [File: 2025-08-23 21.13.20.jpg, 367.2 KB]
  task2_image1: [File: 2025-08-23 21.13.31.jpg, 460.7 KB]
```

**Format tuzilmasi:**
- `task{N}_image{M}` - Task raqami va rasm tartibi
- `task1_image1` - 1-chi task, 1-chi rasm
- `task2_image1` - 2-chi task, 1-chi rasm

### Backend Kutayotgan Format (New):

```javascript
FormData:
  test_result_id: 241
  answers[0][question]: 123        // Question ID
  answers[0][writing_images][1][image]: [File]
  answers[0][writing_images][1][order]: 1
  answers[1][question]: 456
  answers[1][writing_images][1][image]: [File]
  answers[1][writing_images][1][order]: 1
```

**Format tuzilmasi:**
- `answers[N][question]` - Savol ID
- `answers[N][writing_images][M][image]` - Rasm fayli
- `answers[N][writing_images][M][order]` - Rasm tartibi

---

## ✅ Yechim

### Backend ni Ikki Formatni Ham Qabul Qilishi

`writing_views.py` dagi `_parse_form_data()` metodi yangilandi:

#### 1. Legacy Format Support (Frontend format):

```python
# LEGACY FORMAT: task1_image1, task2_image1
legacy_images = {}
for key, value in request.FILES.items():
    if key.startswith('task') and '_image' in key:
        task_num = int(key.split('task')[1].split('_')[0])  # 1, 2, 3...
        image_num = int(key.split('_image')[1])             # 1, 2, 3...
        
        if task_num not in legacy_images:
            legacy_images[task_num] = {}
        legacy_images[task_num][image_num] = value
```

#### 2. Exam ID dan Question topish:

```python
# Get section from exam_id
exam_id = request.data.get('exam_id')
section_type = request.data.get('section_type', 'writing')

exam = Exam.objects.get(id=int(exam_id))
section = Section.objects.get(exam=exam, type=section_type)

# Get all questions for this section
questions = list(Question.objects.filter(
    test__section=section
).order_by('test__order', 'order'))
```

#### 3. Task raqamini Question ga map qilish:

```python
# Map tasks to questions
answers = []
for task_num in sorted(legacy_images.keys()):
    if task_num - 1 < len(questions):
        question = questions[task_num - 1]  # task1 -> questions[0]
        images = legacy_images[task_num]
        
        answer_images = [
            {'order': order, 'file': img_file}
            for order, img_file in sorted(images.items())
        ]
        
        answers.append({
            'question': question,
            'images': answer_images
        })
```

---

## 🔄 Qanday Ishlaydi?

### Misol 1: Legacy Format (Frontend)

**Request:**
```
POST /multilevel/testcheck/writing/
Content-Type: multipart/form-data

user_test_id: 241
exam_id: 12
section_type: writing
task1_image1: file1.jpg
task1_image2: file2.jpg
task2_image1: file3.jpg
```

**Backend Parsing:**
```python
1. Legacy format aniqlandi: task1_image1, task2_image1
2. exam_id=12 dan Section topildi
3. Section dan Questions topildi: [Q1, Q2, Q3]
4. Mapping:
   - task1 -> Question Q1 (questions[0])
   - task2 -> Question Q2 (questions[1])
5. Result:
   answers = [
       {'question': Q1, 'images': [file1.jpg, file2.jpg]},
       {'question': Q2, 'images': [file3.jpg]}
   ]
```

### Misol 2: New Format

**Request:**
```
POST /multilevel/testcheck/writing/
Content-Type: multipart/form-data

test_result_id: 241
answers[0][question]: 123
answers[0][writing_images][1][image]: file1.jpg
answers[1][question]: 456
answers[1][writing_images][1][image]: file2.jpg
```

**Backend Parsing:**
```python
1. New format aniqlandi: answers[0][question]
2. Directly parse questions va images
3. Result:
   answers = [
       {'question': Question(123), 'images': [file1.jpg]},
       {'question': Question(456), 'images': [file2.jpg]}
   ]
```

---

## 📝 Kod O'zgarishlari

### Fayl: `apps/multilevel/writing_views.py`

**Qo'shilgan:**
- Legacy format detection
- `exam_id` dan section topish
- Task number -> Question mapping

**Saqlanib qolgan:**
- New format support (eski kod)
- Validation logic
- Error handling

---

## 🧪 Test Qilish

### 1. Legacy Format Test (Frontend format)

```bash
curl -X POST https://api.turantalim.uz/multilevel/testcheck/writing/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "user_test_id=241" \
  -F "exam_id=12" \
  -F "section_type=writing" \
  -F "task1_image1=@image1.jpg" \
  -F "task2_image1=@image2.jpg"
```

**Kutilayotgan natija:**
```json
{
  "test_result_id": 241,
  "status": "pending",
  "message": "Writing test muvaffaqiyatli yuklandi...",
  "manual_review_id": 123,
  "images_count": 2
}
```

### 2. New Format Test

```bash
curl -X POST https://api.turantalim.uz/multilevel/testcheck/writing/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "test_result_id=241" \
  -F "answers[0][question]=123" \
  -F "answers[0][writing_images][1][image]=@image1.jpg"
```

---

## 📊 Loglar

### Muvaffaqiyatli Submission (Legacy Format):

```
INFO [WRITING] User 15 submitting writing test
INFO [WRITING] Content-Type: multipart/form-data
INFO [WRITING] Files keys: ['task1_image1', 'task2_image1']
INFO [WRITING] Legacy format detected: task1_image1 -> task=1, order=1
INFO [WRITING] Legacy format detected: task2_image1 -> task=2, order=1
INFO [WRITING] Using LEGACY format, found 2 tasks
INFO [WRITING] Found 3 questions for section
INFO [WRITING] Task 1 -> Question 123, 1 images
INFO [WRITING] Task 2 -> Question 456, 1 images
INFO [WRITING] TestResult: 241
INFO [WRITING] Created SubmissionMedia for image
INFO [WRITING] Created ManualReview: 789
INFO [WRITING] TestResult 241 marked as completed
INFO Telegram message sent successfully to -1002923935883
INFO Notified teachers about writing submission 241
```

### Xato (Exam ID yo'q):

```
ERROR [WRITING] Parse error: exam_id maydoni kiritilishi shart!
```

---

## 🎯 Frontend Talablar

Frontend quyidagi maydonlarni yuborishi **SHART**:

### Legacy Format (Hozirgi):

```javascript
const formData = new FormData();

// Required fields:
formData.append('user_test_id', 241);          // ✅ SHART
formData.append('exam_id', 12);                // ✅ SHART
formData.append('section_type', 'writing');    // ✅ SHART

// Images:
formData.append('task1_image1', file1);        // ✅ 
formData.append('task1_image2', file2);        // Ixtiyoriy
formData.append('task2_image1', file3);        // ✅
```

### New Format (Kelajakda):

```javascript
const formData = new FormData();

// Required fields:
formData.append('test_result_id', 241);                    // ✅
formData.append('answers[0][question]', 123);              // ✅
formData.append('answers[0][writing_images][1][image]', file1);  // ✅
formData.append('answers[0][writing_images][1][order]', 1);      // ✅
```

---

## 🔍 Debugging

### Frontend Developer uchun:

**1. FormData ni console da ko'ring:**
```javascript
console.log('=== FormData Contents ===');
for (let [key, value] of formData.entries()) {
    console.log(key, ':', value);
}
```

**2. Response ni tekshiring:**
```javascript
const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
        'Authorization': `Token ${token}`
    }
});

const data = await response.json();
console.log('Response status:', response.status);
console.log('Response data:', data);

if (!response.ok) {
    console.error('Error:', data);
}
```

**3. Kerakli maydonlar:**
- ✅ `user_test_id` yoki `test_result_id`
- ✅ `exam_id` (Legacy format uchun)
- ✅ `section_type` (Legacy format uchun)
- ✅ Kamida bitta `task{N}_image{M}` fayli

---

## ⚠️ Muhim Eslatmalar

### 1. Format Autodetection
Backend avtomatik ravishda qaysi formatni ishlatishni aniqlaydi:
- `task1_image1` topilsa → Legacy format
- `answers[0][question]` topilsa → New format

### 2. Question Ordering
Legacy formatda tasklar **tartib bo'yicha** questionlarga map qilinadi:
- `task1` → Birinchi question (order=1)
- `task2` → Ikkinchi question (order=2)
- `task3` → Uchinchi question (order=3)

### 3. Backward Compatibility
Eski API hali ham ishlaydi! Ikki format ham qo'llab-quvvatlanadi.

---

## 📞 Support

Muammo bo'lsa:
1. Loglarni ko'ring: `sudo supervisorctl tail -f turantalim stderr`
2. FormData ni console da ko'ring
3. Request headers va body ni tekshiring

**Email:** support@turantalim.uz

---

**Yaratildi:** 2025-10-08  
**Muallif:** Turantalim Development Team  
**Versiya:** 1.1 (Legacy Format Support)
