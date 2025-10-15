# Telegram Bot O'rnatish - Qadamma-Qadam Qo'llanma

**Yaratilgan:** 2025-10-08  
**Maqsad:** Yangi o'qituvchilar guruhi va bot sozlash

---

## 📝 1. Telegram Bot Yaratish

### 1.1. BotFather Bilan Gaplashish

1. Telegram da `@BotFather` ni toping
2. `/start` yozing
3. `/newbot` buyrug'ini yuboring

### 1.2. Bot Nomi Berish

```
BotFather: Alright, a new bot. How are we going to call it?
Siz: Turantalim Notification Bot

BotFather: Good. Now let's choose a username for your bot.
Siz: turantalim_notify_bot
```

### 1.3. Token Olish

```
BotFather: Done! Here is your token:
8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8

Use this token to access the HTTP API...
```

✅ **Bu tokenni .env fayliga kiriting!**

---

## 👥 2. O'qituvchilar Guruhi Yaratish

### 2.1. Guruh Yaratish

1. Telegram da yangi guruh yarating
2. Nom: "Turantalim O'qituvchilar" (yoki boshqa nom)
3. Private guruh bo'lishi kerak

### 2.2. Botni Guruhga Qo'shish

1. Guruhga kiring
2. Guruh sozlamalariga kiring
3. "Administrators" → "Add admin"
4. `@turantalim_notify_bot` ni qidiring
5. Admin sifatida qo'shing
6. Ruxsatlar:
   - ✅ **Post Messages** (boshqa ruxsatlar kerak emas)

### 2.3. Guruh ID ni Olish

**Usul 1: Bot orqali**
```python
# 1. Botni guruhga xabar yuboring: /start
# 2. Python script ishga tushiring:

import requests

BOT_TOKEN = "8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

response = requests.get(url)
print(response.json())

# Output dan "chat": {"id": -1002923935883} ni toping
```

**Usul 2: @userinfobot**
```
1. @userinfobot ni guruhga qo'shing
2. Bot guruh ID ni ko'rsatadi
3. Botni guruhdan o'chiring
```

**Usul 3: Manual**
```
1. Guruhda biror xabar forward qiling (masalan Saved Messages ga)
2. Forward qilingan xabar ustiga bosing
3. "Forward from: Turantalim O'qituvchilar"
4. Guruh linkini oching
5. URL dan ID ni oling
```

✅ **Guruh ID: -1002923935883**

---

## 🔧 3. .env Faylini To'ldirish

### 3.1. .env Faylni Ochish

```bash
cd /home/user/turantalim
nano .env
```

### 3.2. Quyidagilarni Qo'shing

```env
# Telegram Bot Settings (Manual Review Notifications)
BOT_TOKEN=8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8
ADMIN_ID=6608824701
TEACHER_GROUP_ID=-1002923935883
```

**Tushuntirish:**
- `BOT_TOKEN`: Telegram bot tokeni (BotFather dan olingan)
- `ADMIN_ID`: Asosiy admin Telegram ID (maxsus xabarlar uchun)
- `TEACHER_GROUP_ID`: O'qituvchilar guruhi ID

### 3.3. Saqlash

```bash
# Ctrl+X, Y, Enter
```

---

## 🧪 4. Test Qilish

### 4.1. Server Qayta Ishga Tushirish

```bash
sudo supervisorctl restart turantalim
sudo supervisorctl status turantalim
```

### 4.2. Django Shell da Test

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py shell
```

```python
# Test 1: Check configuration
from apps.multilevel.telegram_notifications import telegram_notifier

print("Configured:", telegram_notifier.is_configured())
print("Bot Token:", telegram_notifier.bot_token[:20] + "...")
print("Group ID:", telegram_notifier.teacher_group_id)

# Test 2: Send test message
success = telegram_notifier.send_message(
    chat_id=telegram_notifier.teacher_group_id,
    message="🎉 <b>Bot muvaffaqiyatli sozlandi!</b>\n\nTurantalim Notification Bot test xabari."
)
print("Message sent:", success)

# Test 3: Send submission notification
from apps.multilevel.models import TestResult
test_result = TestResult.objects.filter(section__name='writing').first()
if test_result:
    telegram_notifier.notify_new_submission(test_result, section='writing')
    print("Notification sent for TestResult:", test_result.id)
```

### 4.3. Telegram Guruhni Tekshiring

✅ Guruhga xabar kelishi kerak!

---

## 📱 5. Admin ID ni Olish

### 5.1. O'zingizning Telegram ID

**Usul 1: @userinfobot**
```
1. @userinfobot ga xabar yuboring
2. Bot sizning ID ngizni ko'rsatadi
```

**Usul 2: @getidsbot**
```
1. @getidsbot ga /start yuboring
2. Bot ID ni beradi
```

**Usul 3: Bot orqali**
```python
import requests

BOT_TOKEN = "YOUR_TOKEN"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

response = requests.get(url)
data = response.json()

# Botga biror xabar yuboring
# Keyin getUpdates chaqiring
for update in data['result']:
    print(update['message']['from']['id'])  # Bu sizning ID ngiz
```

✅ **Admin ID: 6608824701**

---

## 🔒 6. Xavfsizlik

### 6.1. Bot Tokenni Himoyalash

```bash
# .env faylni .gitignore ga qo'shing
echo ".env" >> .gitignore

# .env fayl ruxsatlarini cheklang
chmod 600 /home/user/turantalim/.env
```

### 6.2. Guruhni Private Qilish

1. Guruh sozlamalariga kiring
2. "Group type" → "Private"
3. Link yaratish kerak bo'lsa, invite link yarating

### 6.3. Bot Ruxsatlarini Cheklash

Bot guruhda faqat:
- ✅ Post Messages
- ❌ Delete Messages
- ❌ Ban Users
- ❌ Pin Messages

---

## 🚨 7. Muammolarni Hal Qilish

### Xabar Yuborilmayapti

**1. Bot tokenni tekshiring**
```bash
cat /home/user/turantalim/.env | grep BOT_TOKEN
```

**2. Bot API ni test qiling**
```bash
curl "https://api.telegram.org/bot8301998106:AAFORRCWS_5RJ7hED9hOXp6DVoGOJNZNbS8/getMe"
```

**3. Guruh ID ni tekshiring**
```bash
cat /home/user/turantalim/.env | grep TEACHER_GROUP_ID
```

**4. Loglarni ko'ring**
```bash
sudo supervisorctl tail -f turantalim stderr | grep -i telegram
```

### "Forbidden: bot is not a member of the group"

**Sabab:** Bot guruhda emas yoki ruxsati yo'q

**Yechim:**
1. Botni guruhdan o'chiring
2. Botni qayta admin sifatida qo'shing
3. "Post Messages" ruxsatini yoqing

### "Bad Request: chat not found"

**Sabab:** Guruh ID noto'g'ri

**Yechim:**
1. Guruh ID ni qayta oling (yuqoridagi 2.3 bo'limga qarang)
2. ID manfiy son bo'lishi kerak: `-1002923935883`
3. .env faylni yangilang

---

## 📊 8. Xabar Formatini O'zgartirish

### 8.1. Emoji O'zgartirish

```python
# apps/multilevel/telegram_notifications.py
def notify_new_submission(self, test_result, section='writing'):
    # Emoji o'zgartiring:
    section_emoji = "📝" if section == 'writing' else "🗣️"  # Yangi
```

### 8.2. Matn O'zgartirish

```python
message = f"""
🔔 <b>Yangi Test!</b>  # <- Bu yerni o'zgartiring

{section_emoji} <b>Bo'lim:</b> {section_name}
...
"""
```

### 8.3. Til O'zgartirish

```python
# O'zbek tilidan ingliz tiliga:
message = f"""
🔔 <b>New Exam Submission!</b>

{section_emoji} <b>Section:</b> {section_name}

👤 <b>Student:</b> {user.get_full_name()}
...
"""
```

---

## 🎨 9. HTML Formatting

Telegram HTML qo'llab-quvvatlaydi:

```html
<b>Bold</b>
<i>Italic</i>
<u>Underline</u>
<s>Strikethrough</s>
<code>Code</code>
<pre>Preformatted</pre>
<a href="URL">Link text</a>
```

**Misol:**
```python
message = f"""
🔔 <b>Yangi Test!</b>

<i>Talaba:</i> <b>{user.get_full_name()}</b>
<code>ID: {test_result.id}</code>

<a href="https://api.turantalim.uz/admin-dashboard/submission.html?id={test_result.id}">
📊 Admin Panelda Ochish
</a>
"""
```

---

## 🔗 10. Qo'shimcha Funksiyalar

### 10.1. Inline Buttons (Kelajakda)

```python
import json

keyboard = {
    "inline_keyboard": [
        [{"text": "✅ Tekshirish", "url": f"https://...?id={test_result.id}"}],
        [{"text": "📊 Statistika", "callback_data": "stats"}]
    ]
}

payload = {
    'chat_id': chat_id,
    'text': message,
    'parse_mode': 'HTML',
    'reply_markup': json.dumps(keyboard)
}
```

### 10.2. Photo Bilan Xabar

```python
def send_photo(self, chat_id, photo_url, caption):
    url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
    payload = {
        'chat_id': chat_id,
        'photo': photo_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=payload)
    return response.status_code == 200
```

### 10.3. Document Yuborish

```python
def send_document(self, chat_id, document_path):
    url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
    with open(document_path, 'rb') as doc:
        files = {'document': doc}
        data = {'chat_id': chat_id}
        response = requests.post(url, files=files, data=data)
    return response.status_code == 200
```

---

## 📚 11. Foydali Linklar

- **Telegram Bot API:** https://core.telegram.org/bots/api
- **BotFather:** https://t.me/botfather
- **HTML Formatting:** https://core.telegram.org/bots/api#html-style
- **Inline Keyboards:** https://core.telegram.org/bots/features#inline-keyboards

---

## ✅ 12. Checklist

Sozlashdan oldin tekshiring:

- [ ] Telegram bot yaratildi (@BotFather)
- [ ] Bot tokeni olingan
- [ ] O'qituvchilar guruhi yaratildi
- [ ] Bot guruhga admin sifatida qo'shildi
- [ ] "Post Messages" ruxsati berildi
- [ ] Guruh ID olingan
- [ ] .env fayliga ma'lumotlar kiritildi
- [ ] Server qayta ishga tushirildi
- [ ] Test xabar yuborildi va qabul qilindi
- [ ] Loglar tekshirildi

---

**Omad!** 🚀

**Support:** support@turantalim.uz  
**Versiya:** 1.0  
**Sanasi:** 2025-10-08
