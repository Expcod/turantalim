# Writing Submission - Order Field Fix

**Muammo sanasi:** 2025-10-09  
**Yechim:** Question modelida mavjud bo'lmagan 'order' fieldi o'rniga 'id' ishlatish

---

## ❌ Muammo Tavsifi

### Xato Xabari:
```
Writing submission error: Error: Ma'lumotlar noto'g'ri formatda yuborilgan: 
Cannot resolve keyword 'order' into field. 
Choices are: answer, has_options, id, images, option, picture, 
preparation_time, response_time, test, test_id, text, useranswer
```

### Sabab:
`Question` modelida `order` fieldi mavjud emas, lekin kod `order_by('order')` ishlatmoqda.

---

## 📊 Model Tuzilmasi

### Question Model (apps/multilevel/models.py):

```python
class Question(models.Model):
    test = models.ForeignKey(Test, ...)
    text = models.TextField(...)
    picture = models.ImageField(...)
    answer = models.CharField(...)
    has_options = models.BooleanField(...)
    preparation_time = models.PositiveSmallIntegerField(...)
    response_time = models.PositiveSmallIntegerField(...)
    
    # ❌ 'order' field yo'q!
```

**Mavjud fieldlar:**
- test, text, picture, answer, has_options, preparation_time, response_time, id, images, option, useranswer

### Test Model (apps/multilevel/models.py):

```python
class Test(models.Model):
    section = models.ForeignKey(Section, ...)
    title = models.CharField(...)
    order = models.PositiveSmallIntegerField(...)  # ✅ Test da order bor!
```

---

## 🐛 Xato Kod

### writing_views.py (Line 219-221):

```python
# ❌ XATO - Question modelida 'order' yo'q
questions = list(Question.objects.filter(
    test__section=section
).order_by('test__order', 'order'))  # <- Bu yerda xato!
```

**Muammo:**
- `test__order` - ✅ ishlaydi (Test modelida order bor)
- `order` - ❌ ishlamaydi (Question modelida order yo'q)

---

## ✅ Yechim

### O'zgartirilgan Kod:

```python
# ✅ TO'G'RI - 'id' ishlatildi
questions = list(Question.objects.filter(
    test__section=section
).order_by('test__order', 'id'))  # <- 'order' o'rniga 'id'
```

**Tushuntirish:**
1. `test__order` - Testlarni tartib bo'yicha tartiblash (Test 1, Test 2, Test 3)
2. `id` - Bir xil test ichidagi savollarni ID bo'yicha tartiblash

---

## 🔄 Order by Logikasi

### Misol: Exam Structure

```
Exam: CEFR A1
  Section: Writing
    Test 1 (order=1)
      Question 1 (id=100)
      Question 2 (id=101)
    Test 2 (order=2)
      Question 3 (id=102)
      Question 4 (id=103)
```

### Query Natijasi:

```python
.order_by('test__order', 'id')
# Natija:
# [Question(id=100), Question(id=101), Question(id=102), Question(id=103)]
```

**Tartib:**
1. Avval Test order bo'yicha (Test 1 → Test 2)
2. Keyin Question ID bo'yicha (100 → 101 → 102 → 103)

---

## 🧪 Test Qilish

### 1. Django Shell Test:

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py shell
```

```python
from apps.multilevel.models import Question, Section, Exam

# Get section
exam = Exam.objects.first()
section = Section.objects.get(exam=exam, type='writing')

# Test query
questions = Question.objects.filter(
    test__section=section
).order_by('test__order', 'id')

print(f"Found {questions.count()} questions")
for q in questions:
    print(f"Test Order: {q.test.order}, Question ID: {q.id}, Text: {q.text[:50]}")
```

### 2. API Test:

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

---

## 📝 Kod O'zgarishlari

### Fayl: apps/multilevel/writing_views.py

**Line 221:**

**Eski:**
```python
).order_by('test__order', 'order'))
```

**Yangi:**
```python
).order_by('test__order', 'id'))
```

---

## 🔍 Debugging

### Server Logs:

```bash
# Real-time logs
sudo supervisorctl tail -f turantalim stderr

# Specific error
sudo supervisorctl tail -100 turantalim stderr | grep "Cannot resolve"
```

### Django Check:

```bash
cd /home/user/turantalim
python manage.py check
# Output: System check identified no issues (0 silenced).
```

---

## 💡 Kelajak Yaxshilanishlar

### Agar Question ga 'order' fieldi qo'shmoqchi bo'lsangiz:

**1. Migration yaratish:**

```python
# apps/multilevel/models.py
class Question(models.Model):
    test = models.ForeignKey(Test, ...)
    order = models.PositiveSmallIntegerField(default=0)  # Yangi field
    text = models.TextField(...)
    # ...
```

**2. Migration ishga tushirish:**

```bash
python manage.py makemigrations multilevel
python manage.py migrate
```

**3. Kodda ishlatish:**

```python
questions = list(Question.objects.filter(
    test__section=section
).order_by('test__order', 'order'))  # Endi ishlaydi!
```

---

## ⚠️ Muhim Eslatmalar

### 1. Field Mavjudligini Tekshiring

Modelda field mavjud ekanligini tekshiring:
```bash
python manage.py shell
```

```python
from apps.multilevel.models import Question
print([f.name for f in Question._meta.get_fields()])
# ['id', 'test', 'text', 'picture', 'answer', ...]
```

### 2. Django ORM Error Messages

Django agar field topilmasa, aniq xabar beradi:
```
Cannot resolve keyword 'FIELD_NAME' into field.
Choices are: [list of available fields]
```

### 3. Related Field Access

Related field orqali access:
- ✅ `test__order` - Test modelining order fieldi
- ✅ `test__section__exam` - Exam modeliga access
- ❌ `order` - Question modelida yo'q

---

## 📊 Loglar

### Muvaffaqiyatli Submission:

```
INFO [WRITING] User 15 submitting writing test
INFO [WRITING] Content-Type: multipart/form-data
INFO [WRITING] Files keys: ['task1_image1', 'task2_image1']
INFO [WRITING] Legacy format detected: task1_image1 -> task=1, order=1
INFO [WRITING] Using LEGACY format, found 2 tasks
INFO [WRITING] Found 3 questions for section
INFO [WRITING] Task 1 -> Question 123, 1 images
INFO [WRITING] Task 2 -> Question 456, 1 images
INFO [WRITING] TestResult: 241
INFO [WRITING] Created ManualReview: 789
INFO [WRITING] TestResult 241 marked as completed
INFO Telegram message sent successfully
```

### Xato (Order field mavjud emas):

```
ERROR [WRITING] Parse error: Cannot resolve keyword 'order' into field.
Choices are: answer, has_options, id, images, option, picture, 
preparation_time, response_time, test, test_id, text, useranswer
```

---

## 📞 Support

Muammo bo'lsa:
1. Modellarni tekshiring: `python manage.py shell`
2. Loglarni ko'ring: `sudo supervisorctl tail -f turantalim stderr`
3. Django check: `python manage.py check`

**Email:** support@turantalim.uz

---

**Yaratildi:** 2025-10-09  
**Muallif:** Turantalim Development Team  
**Versiya:** 1.2 (Order Field Fix)
