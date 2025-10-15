# Telegram Notification - Tez Test

**Maqsad:** Telegram notificationlarni tezda test qilish

---

## ✅ 1. Server Holatini Tekshirish

```bash
sudo supervisorctl status turantalim
# RUNNING bo'lishi kerak
```

---

## ✅ 2. Django Shell da Test

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py shell
```

### Test 1: Configuration Tekshirish

```python
from apps.multilevel.telegram_notifications import telegram_notifier

print("✅ Bot configured:", telegram_notifier.is_configured())
print("🤖 Bot Token:", telegram_notifier.bot_token[:30] + "..." if telegram_notifier.bot_token else "MISSING")
print("👥 Group ID:", telegram_notifier.teacher_group_id)
print("👤 Admin ID:", telegram_notifier.admin_id)
```

**Kutilayotgan natija:**
```
✅ Bot configured: True
🤖 Bot Token: 8301998106:AAFORRCWS_5RJ7hED...
👥 Group ID: -1002923935883
👤 Admin ID: 6608824701
```

### Test 2: Test Xabar Yuborish

```python
success = telegram_notifier.send_message(
    chat_id=telegram_notifier.teacher_group_id,
    message="🎉 <b>Test Xabar</b>\n\n<i>Turantalim Notification Bot</i> ishlayapti!"
)
print("📨 Message sent:", success)
```

**Kutilayotgan natija:**
```
📨 Message sent: True
```

✅ **Telegram guruhga xabar kelishi kerak!**

### Test 3: Submission Notification

```python
from apps.multilevel.models import TestResult

# Writing test
test_result = TestResult.objects.filter(section__name='writing').first()
if test_result:
    success = telegram_notifier.notify_new_submission(test_result, section='writing')
    print(f"✍️ Writing notification sent for ID {test_result.id}:", success)

# Speaking test
test_result = TestResult.objects.filter(section__name='speaking').first()
if test_result:
    success = telegram_notifier.notify_new_submission(test_result, section='speaking')
    print(f"🎤 Speaking notification sent for ID {test_result.id}:", success)
```

**Kutilayotgan natija:**
```
✍️ Writing notification sent for ID 240: True
🎤 Speaking notification sent for ID 391: True
```

✅ **Telegram guruhga 2 ta xabar kelishi kerak!**

---

## ✅ 3. Frontend/Postman Test

### Writing Test Submit

```bash
curl -X POST https://api.turantalim.uz/multilevel/testcheck/writing/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -F "test_result_id=240" \
  -F "answers[0][question]=123" \
  -F "answers[0][writing_images][1][image]=@/path/to/image.jpg"
```

✅ **Telegram guruhga xabar kelishi kerak!**

### Speaking Test Submit

```bash
curl -X POST https://api.turantalim.uz/multilevel/testcheck/speaking/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -F "test_result_id=391" \
  -F "answers[0][question]=456" \
  -F "answers[0][speaking_audio]=@/path/to/audio.mp3"
```

✅ **Telegram guruhga xabar kelishi kerak!**

---

## ✅ 4. Loglarni Tekshirish

```bash
# Real-time log
sudo supervisorctl tail -f turantalim stderr

# Telegram ga oid loglar
sudo supervisorctl tail -f turantalim stderr | grep -i telegram
```

**Muvaffaqiyatli log:**
```
INFO Telegram message sent successfully to -1002923935883
INFO Notified teachers about writing submission 240
```

**Xatolik log:**
```
ERROR Failed to send Telegram message: Connection timeout
ERROR Telegram notifications not configured
WARNING Telegram bot token not configured
```

---

## ❌ 5. Muammolarni Hal Qilish

### Xabar Yuborilmayapti

1. **.env tekshirish:**
```bash
cat /home/user/turantalim/.env | grep -E "BOT_TOKEN|ADMIN_ID|TEACHER"
```

2. **Bot API test:**
```bash
BOT_TOKEN="8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8"
curl "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

3. **Guruh ID test:**
```python
# Django shell
from apps.multilevel.telegram_notifications import telegram_notifier
telegram_notifier.send_message("-1002923935883", "Test")
```

### "Forbidden: bot is not a member of the group"

✅ **Yechim:**
1. Botni guruhdan o'chiring
2. Qayta admin sifatida qo'shing
3. "Post Messages" ruxsatini yoqing

### "Bad Request: chat not found"

✅ **Yechim:**
1. Guruh ID to'g'ri ekanligini tekshiring
2. ID manfiy son bo'lishi kerak: `-1002923935883`
3. Guruh private bo'lishi kerak

---

## ✅ 6. Production Test Checklist

- [ ] Server ishga tushgan
- [ ] Django check o'tkazilgan (0 issues)
- [ ] `.env` faylda `BOT_TOKEN`, `ADMIN_ID`, `TEACHER_GROUP_ID` mavjud
- [ ] Bot guruhga admin sifatida qo'shilgan
- [ ] "Post Messages" ruxsati berilgan
- [ ] Test xabar yuborildi va qabul qilindi
- [ ] Writing submission test o'tdi
- [ ] Speaking submission test o'tdi
- [ ] Loglar to'g'ri
- [ ] Guruh xabar oldi

---

## 📞 Yordam

Muammo bo'lsa:
1. Loglarni ko'ring: `sudo supervisorctl tail -f turantalim stderr`
2. Bot tokenni tekshiring: `cat .env | grep BOT_TOKEN`
3. Django shell da test qiling (yuqoridagi Test 2)
4. Support: support@turantalim.uz

---

**Omad!** 🚀
