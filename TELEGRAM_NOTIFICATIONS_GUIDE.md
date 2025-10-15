# Telegram Notifications - Manual Review System

**Yaratilgan:** 2025-10-08  
**Versiya:** 1.0

---

## 🎯 Maqsad

Writing va Speaking testlari admin-dashboard ga kelganda, o'qituvchilar guruhiga avtomatik xabar yuboriladi. Bu orqali o'qituvchilar yangi test javoblaridan darhol xabardor bo'lishadi va tezroq tekshirish imkoniyatiga ega bo'ladilar.

---

## 📋 Tizim Qanday Ishlaydi?

### 1. Talaba Test Topshiradi
```
Talaba → Frontend → POST /multilevel/testcheck/writing/
                      POST /multilevel/testcheck/speaking/
```

### 2. Backend Jarayoni
```python
# writing_views.py / speaking_views.py
with transaction.atomic():
    # 1. Fayllarni saqlash
    SubmissionMedia.objects.create(...)
    
    # 2. ManualReview yaratish
    ManualReview.objects.create(status='pending')
    
    # 3. TestResult yakunlash
    test_result.status = 'completed'
    test_result.save()
    
    # 4. TELEGRAM XABAR YUBORISH ✅
    telegram_notifier.notify_new_submission(test_result, section='writing')
```

### 3. Telegram Guruhga Xabar
```
🔔 Yangi Imtihon Javobi!

✍️ Bo'lim: Writing
👤 Talaba: Shaxzodbek Abdumutalipov
📱 Telefon: +998901234567
📝 Imtihon: CEFR 1. Sinav
📊 Level: A1

🆔 Test Result ID: 390
📅 Topshirgan vaqti: 03.09.2025 14:30

⏰ Status: Tekshirish kutilmoqda (Pending)

🔗 Admin Dashboard:
https://api.turantalim.uz/admin-dashboard/submission.html?id=390

Iltimos, imkon qadar tezroq tekshiring! ⚡
```

### 4. O'qituvchi Ko'radi va Tekshiradi
```
O'qituvchi → Admin Dashboard → Baholaydi → Natija chiqadi
```

---

## ⚙️ Konfiguratsiya

### .env Fayli

```env
# Telegram Bot Token
BOT_TOKEN=8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8

# Admin ID (adminlarga maxsus xabarlar uchun)
ADMIN_ID=6608824701

# O'qituvchilar Guruh ID (asosiy xabarlar shu yerga)
TEACHER_GROUP_ID=-1002923935883
```

### settings/base.py

```python
# Telegram settings
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN") or env.str("BOT_TOKEN", default="")
TELEGRAM_ADMIN_ID = os.environ.get("ADMIN_ID") or env.str("ADMIN_ID", default="")
TELEGRAM_TEACHER_GROUP_ID = os.environ.get("TEACHER_GROUP_ID") or env.str("TEACHER_GROUP_ID", default="")
```

---

## 📁 Fayl Tuzilmasi

### Yangi Fayllar

```
apps/multilevel/
└── telegram_notifications.py  # Telegram notification class
```

### O'zgartirilgan Fayllar

```
apps/multilevel/
├── writing_views.py    # Telegram notification qo'shildi
├── speaking_views.py   # Telegram notification qo'shildi

core/settings/
└── base.py            # Telegram settings qo'shildi
```

---

## 🔧 TelegramNotifier Class

### Asosiy Metodlar

#### 1. `is_configured()`
```python
# Telegram sozlangan yoki yo'qligini tekshiradi
telegram_notifier.is_configured()  # True/False
```

#### 2. `send_message(chat_id, message)`
```python
# Biror chat ga xabar yuboradi
telegram_notifier.send_message(
    chat_id="-1002923935883",
    message="Test xabar",
    parse_mode='HTML'
)
```

#### 3. `notify_new_submission(test_result, section)`
```python
# Yangi submission haqida xabar yuboradi
telegram_notifier.notify_new_submission(
    test_result=test_result,
    section='writing'  # yoki 'speaking'
)
```

#### 4. `notify_submission_checked(manual_review)` (Ixtiyoriy)
```python
# Tekshirish tugagandan keyin xabar (hozircha ishlamaydi)
telegram_notifier.notify_submission_checked(manual_review)
```

---

## 📨 Xabar Formatlari

### Writing Submission
```
🔔 Yangi Imtihon Javobi!

✍️ Bo'lim: Writing

👤 Talaba: Ali Valiyev
📱 Telefon: +998901111111
📧 Email: ali@example.com

📝 Imtihon: CEFR 1. Sinav
📊 Level: A1

🆔 Test Result ID: 240
📅 Topshirgan vaqti: 08.10.2025 18:30

⏰ Status: Tekshirish kutilmoqda (Pending)

🔗 Admin Dashboard:
https://api.turantalim.uz/admin-dashboard/submission.html?id=240

Iltimos, imkon qadar tezroq tekshiring! ⚡
```

### Speaking Submission
```
🔔 Yangi Imtihon Javobi!

🎤 Bo'lim: Speaking

👤 Talaba: Nodira Karimova
📱 Telefon: +998902222222
📧 Email: nodira@example.com

📝 Imtihon: CEFR 2. Sinav
📊 Level: A2

🆔 Test Result ID: 391
📅 Topshirgan vaqti: 08.10.2025 19:15

⏰ Status: Tekshirish kutilmoqda (Pending)

🔗 Admin Dashboard:
https://api.turantalim.uz/admin-dashboard/submission.html?id=391

Iltimos, imkon qadar tezroq tekshiring! ⚡
```

---

## 🔍 Logging

### Log Qayerda?

```bash
# Supervisor logs
sudo supervisorctl tail -f turantalim stderr

# Django logs
tail -f /var/log/django.log
```

### Log Formatlari

```
INFO [WRITING] User 123 submitting writing test
INFO [WRITING] TestResult 240 marked as completed
INFO Telegram message sent successfully to -1002923935883
INFO Notified teachers about writing submission 240

ERROR Failed to send Telegram message: Connection timeout
ERROR [WRITING] Failed to send Telegram notification: Bot token not configured
```

---

## 🧪 Test Qilish

### 1. Manual Test

```python
# Django shell
python manage.py shell

from apps.multilevel.telegram_notifications import telegram_notifier
from apps.multilevel.models import TestResult

# Get test result
test_result = TestResult.objects.get(id=390)

# Send notification
telegram_notifier.notify_new_submission(test_result, section='speaking')
```

### 2. cURL Test

```bash
# Submit writing test
curl -X POST https://api.turantalim.uz/multilevel/testcheck/writing/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "test_result_id=240" \
  -F "answers[0][question]=123" \
  -F "answers[0][writing_images][1][image]=@image1.jpg"

# Check Telegram group for notification!
```

### 3. Frontend Test

```javascript
// Submit writing test
const formData = new FormData();
formData.append('test_result_id', 240);
formData.append('answers[0][question]', 123);
formData.append('answers[0][writing_images][1][image]', imageFile);

const response = await fetch('/multilevel/testcheck/writing/', {
  method: 'POST',
  headers: { 'Authorization': `Token ${token}` },
  body: formData
});

// Telegram guruhga xabar keladi!
```

---

## 🛠️ Troubleshooting

### Xabar Yuborilmayapti

**Sabab 1:** Bot token noto'g'ri
```bash
# .env faylni tekshiring
cat /home/user/turantalim/.env | grep BOT_TOKEN
```

**Sabab 2:** Guruh ID noto'g'ri
```bash
# TEACHER_GROUP_ID ni tekshiring
cat /home/user/turantalim/.env | grep TEACHER_GROUP_ID
```

**Sabab 3:** Bot guruhga qo'shilmagan
```
1. Telegram bot ni toping: @YourBotName
2. Guruhga admin sifatida qo'shing
3. Botga "Can post messages" ruxsatini bering
```

**Sabab 4:** Network muammosi
```python
# Test qiling:
import requests
response = requests.get('https://api.telegram.org/botYOUR_TOKEN/getMe')
print(response.json())
```

### Xabar Formati Buzilgan

```python
# HTML parse_mode ishlatiladi
# <b>bold</b>, <i>italic</i>, <code>code</code>
# Maxsus belgilar escape qilinishi kerak: <, >, &
```

### Xabar Juda Ko'p (Spam)

```python
# Hozirgi tizim: har bir submission uchun bitta xabar
# Agar spam bo'lsa, batching qilish mumkin (kelajakda)
```

---

## 📊 Statistika

### Xabarlar Soni

```python
# Django shell
from apps.multilevel.models import ManualReview

# Bugun yuborilgan xabarlar
from django.utils import timezone
today = timezone.now().date()
count = ManualReview.objects.filter(
    created_at__date=today
).count()
print(f"Bugun {count} ta xabar yuborildi")
```

---

## 🔐 Xavfsizlik

### Bot Token

- ❌ Bot tokenni kodga yozMANG
- ✅ Faqat .env faylda saqlang
- ✅ .env faylni .gitignore ga qo'shing
- ✅ Production serverda environment variable sifatida sozlang

### Guruh ID

- ✅ Faqat o'qituvchilar guruhiga yuborish
- ❌ Public kanalga yuborMANG
- ✅ Guruhni private qiling
- ✅ Botga minimal ruxsatlar bering (faqat post messages)

---

## 🚀 Kelajak Rejalari

### Versiya 1.1
- [ ] Batching: 5 daqiqada bir marta barcha yangi submissionlarni birgalikda yuborish
- [ ] Inline buttons: "Tekshirish" tugmasi bilan to'g'ri submission ga o'tish
- [ ] Notification preferences: O'qituvchilar qaysi section uchun xabar olishini tanlashi
- [ ] Statistics: Kunlik/haftalik submission statistikasi

### Versiya 1.2
- [ ] Talabaga notification: Tekshirish tugaganda talabaga xabar
- [ ] Reminder: 1 kundan oshgan pending submissionlar uchun eslatma
- [ ] Performance: Async telegram notifications (Celery)

---

## 📞 Yordam

Savollar bo'lsa:
- **Email:** support@turantalim.uz
- **Telegram:** @turantalim_support

---

**Muallif:** Turantalim Development Team  
**Versiya:** 1.0  
**Sanasi:** 2025-10-08
