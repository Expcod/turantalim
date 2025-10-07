# Vaqt Chegarasi Tizimi

Bu tizim online testlarda vaqt chegarasini avtomatik boshqarish uchun yaratilgan.

## Asosiy Xususiyatlar

### 1. Avtomatik Vaqt Chegarasi
- Har bir section uchun admin panelda belgilangan vaqt (daqiqada)
- Test boshlanganda vaqt chegarasi avtomatik rejalashtiriladi
- Vaqt tugaganda test avtomatik yakunlanadi

### 2. Celery Background Tasks
- `auto_complete_test`: Vaqt chegarasi tugaganda testni yakunlaydi
- `schedule_test_completion`: Test uchun vaqt chegarasi task'ini rejalashtiradi
- `check_expired_tests`: Muntazam tekshirish (har daqiqada)

### 3. Real-time Vaqt Tekshirish
- Har bir API so'rovida vaqt chegarasi tekshiriladi
- Vaqt tugagan bo'lsa, javob qabul qilinmaydi
- Test avtomatik completed holatiga o'tkaziladi

## API Endpointlar

### Test Vaqti Ma'lumotlari
```
GET /api/multilevel/test/time-info/?test_result_id={id}
```

**Response:**
```json
{
    "test_result_id": 123,
    "section_title": "Listening Section 1",
    "section_type": "listening",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T10:40:00Z",
    "duration_minutes": 40,
    "remaining_minutes": 25,
    "remaining_seconds": 30,
    "is_expired": false,
    "status": "active"
}
```

## Celery Sozlamalari

### 1. Celery Worker Ishga Tushirish
```bash
celery -A core worker -l info
```

### 2. Celery Beat Ishga Tushirish
```bash
celery -A core beat -l info
```

### 3. Redis Server Ishga Tushirish
```bash
redis-server
```

## Vaqt Chegarasi Logikasi

### 1. Test Boshlanganda
```python
# TestResult yaratilganda
existing_test_result = TestResult.objects.create(
    user_test=existing_user_test,
    section=selected_section,
    status='started',
    start_time=timezone.now(),
    end_time=timezone.now() + timedelta(minutes=selected_section.duration)
)

# Vaqt chegarasi task'ini rejalashtirish
schedule_test_time_limit(existing_test_result)
```

### 2. API So'rovlarda Tekshirish
```python
# Har bir API so'rovda
from .utils import check_test_time_limit
if check_test_time_limit(test_result):
    return Response({"error": "Test vaqti tugagan, javob qabul qilinmadi"}, status=400)
```

### 3. Avtomatik Yakunlash
```python
# Vaqt tugaganda
test_result.status = 'completed'
test_result.end_time = timezone.now()
test_result.save()

# UserTest ni ham tekshirish
user_test = test_result.user_test
active_tests = TestResult.objects.filter(user_test=user_test, status='started')
if not active_tests.exists():
    user_test.status = 'completed'
    user_test.save()
```

## Xavfsizlik

### 1. Vaqt Manipulyatsiyasiga Qarshi
- Server vaqti asosida tekshirish
- Client vaqtiga ishonmaslik
- Har so'rovda vaqt tekshirish

### 2. Muntazam Tekshirish
- Celery beat orqali har daqiqada tekshirish
- Vaqt chegarasi tugagan testlarni avtomatik topish
- Xatoliklarni log qilish

## Monitoring va Logging

### 1. Log Fayllar
```python
logger.info(f"Test {test_result_id} uchun vaqt chegarasi rejalashtirildi: {eta}")
logger.info(f"Test {test_result_id} vaqt chegarasi tugagani uchun avtomatik yakunlandi")
logger.error(f"Test {test_result_id} yakunlashda xatolik: {str(e)}")
```

### 2. Celery Task Monitoring
- Task natijalarini kuzatish
- Xatoliklarni aniqlash
- Performance monitoring

## Testlash

### 1. Vaqt Chegarasi Testlash
```python
# Qisqa vaqt bilan test yaratish
section.duration = 1  # 1 daqiqa
test_result = TestResult.objects.create(...)

# 1 daqiqadan keyin tekshirish
time.sleep(65)  # 65 soniya
# Test completed bo'lishi kerak
```

### 2. API Testlash
```python
# Vaqt tugagandan keyin API so'rov
response = client.post('/api/multilevel/testcheck/listening/', data)
assert response.status_code == 400
assert "Test vaqti tugagan" in response.json()['error']
```

## Muammo Hal Qilish

### 1. Celery Worker Ishlamayotgan
```bash
# Redis server ishlayotganini tekshirish
redis-cli ping

# Celery worker ishlayotganini tekshirish
celery -A core inspect active
```

### 2. Vaqt Chegarasi Ishlamayotgan
```python
# TestResult end_time ni tekshirish
test_result = TestResult.objects.get(id=test_result_id)
print(f"End time: {test_result.end_time}")
print(f"Current time: {timezone.now()}")
print(f"Time remaining: {test_result.end_time - timezone.now()}")
```

### 3. Task Rejalashtirish Muammosi
```python
# Celery beat schedule ni tekshirish
celery -A core inspect scheduled
```

## Kelajakdagi Yaxshilanishlar

1. **Real-time WebSocket**: Frontend'ga real-time vaqt ma'lumotlari
2. **Vaqt Uzaytirish**: Admin panel orqali vaqt uzaytirish imkoniyati
3. **Vaqt Ogohlantirishlari**: Vaqt tugashidan oldin ogohlantirish
4. **Performance Optimization**: Katta hajmli testlar uchun optimizatsiya
5. **Analytics**: Vaqt chegarasi statistikalarini kuzatish
