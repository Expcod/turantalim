# Telegram Xabarlarni Avtomatik O'chirish Funksiyasi

## Umumiy Ma'lumot

Yangi writing va speaking natijalarini telegram guruhga jo'natish zo'r ishlamoqda. Bunga qo'shimcha sifatida, telegram guruhga jo'natilgan natijani statusi `reviewing` ga o'tishi bilan xabar avtomatik ravishda o'chib ketadi. Bu boshqa tekshiruvchilar bu xabarni keyinroq ko'rib, bir xil natijani tekshirmoqchi bo'lishlarining oldini oladi.

## Qanday Ishlaydi?

### 1. Xabar Jo'natish va ID Saqlash

Talaba writing yoki speaking testini topshirganda:
- Telegram guruhga yangi submission haqida xabar jo'natiladi
- Telegram API dan qaytgan `message_id` saqlanadi
- Bu ID `ManualReview` modelining `telegram_message_id` maydoniga yoziladi

### 2. Xabarni Avtomatik O'chirish

Tekshiruvchi submissionni ochib ko'rishni boshlaganda:
- Submission ning statusi `pending` dan `reviewing` ga o'zgaradi
- Django signal (`pre_save`) bu o'zgarishni aniqlaydi
- Telegram bot API orqali guruhdan xabar o'chiriladi
- Boshqa tekshiruvchilar endi bu xabarni ko'rmaydi

## O'zgartirilgan Fayllar

### 1. `apps/multilevel/models.py`
```python
# ManualReview modeliga yangi maydon qo'shildi:
telegram_message_id = models.BigIntegerField(null=True, blank=True, verbose_name='Telegram xabar ID')
```

### 2. `apps/multilevel/telegram_notifications.py`
```python
# send_message metodi endi message_id qaytaradi
def send_message(self, chat_id, message, parse_mode='HTML'):
    # ... Telegram API dan message_id ni oladi va qaytaradi
    return message_id

# notify_new_submission endi message_id qaytaradi
def notify_new_submission(self, test_result, section='writing'):
    # ... xabar jo'natadi va message_id ni qaytaradi
    return message_id

# Yangi metodlar qo'shildi:
def delete_message(self, chat_id, message_id):
    """Telegram guruhdan xabarni o'chiradi"""
    # ...

def delete_submission_notification(self, manual_review):
    """Submission notification xabarini o'chiradi"""
    # ...
```

### 3. `apps/multilevel/signals.py`
```python
# Yangi signal qo'shildi - status 'reviewing' ga o'tganda xabarni o'chiradi
@receiver(pre_save, sender='multilevel.ManualReview')
def delete_telegram_notification_on_reviewing(sender, instance, **kwargs):
    """
    Status 'pending' dan 'reviewing' ga o'tganda Telegram xabarini o'chiradi
    """
    # ...
```

### 4. `apps/multilevel/writing_views.py` va `speaking_views.py`
```python
# Xabar jo'natilganda message_id saqlanadi:
message_id = telegram_notifier.notify_new_submission(test_result, section='writing')
if message_id:
    manual_review.telegram_message_id = message_id
    manual_review.save(update_fields=['telegram_message_id'])
```

### 5. Migration
```
apps/multilevel/migrations/0034_add_telegram_message_id.py
```

## Foydalanish

### Migratsiyani Bajarish

```bash
cd /home/user/turantalim
source venv/bin/activate
python manage.py migrate multilevel
```

### Test Qilish

1. **Yangi submission yarating:**
   - Talaba sifatida writing yoki speaking testini topshiring
   - Telegram guruhda yangi xabar paydo bo'ladi

2. **Submission ochish:**
   - Tekshiruvchi sifatida submission ni oching
   - Status avtomatik `reviewing` ga o'zgaradi
   - Telegram guruhdan xabar o'chadi

3. **Log'larni tekshirish:**
   ```bash
   tail -f logs/gunicorn_error.log
   ```
   
   Quyidagi log'larni ko'rishingiz kerak:
   - `[WRITING/SPEAKING] Saved telegram_message_id: {message_id}`
   - `Telegram notification deleted for submission {test_result.id}`

## Afzalliklari

1. **Ikki marta tekshirishni oldini oladi:** Xabar o'chirilgach, boshqa tekshiruvchilar uni ko'rmaydi
2. **Guruhni tozaligini saqlaydi:** Faqat hali tekshirilmagan natijalar ko'rinadi
3. **Avtomatik:** Hech qanday qo'shimcha aralashuv kerak emas
4. **Xavfsiz:** Agar xatolik yuz bersa, save jarayoni to'xtamaydi (faqat log'ga yoziladi)

## Texnik Tafsilotlar

### Telegram Bot API

- **deleteMessage** metodi ishlatiladi
- Parametrlar: `chat_id` va `message_id`
- Bot guruhda xabarlarni o'chirish huquqiga ega bo'lishi kerak

### Django Signals

- **pre_save** signal ishlatiladi (post_save emas)
- Status o'zgarishini tekshirish uchun database'dan oldingi holatni oladi
- Xatoliklar log'ga yoziladi, lekin save jarayonini to'xtatmaydi

### Database

- `telegram_message_id` - BigInteger (Telegram message ID'lar katta bo'lishi mumkin)
- `null=True, blank=True` - eski natijalar uchun ham ishlaydi

## Kelajakda Qo'shimcha Imkoniyatlar

1. **Timeout tizimi:** Agar tekshiruvchi uzoq vaqt tekshirmasa, xabarni qaytarish
2. **Edit xabar:** O'chirish o'rniga xabarni tahrirlash va kim tekshirayotganini ko'rsatish
3. **Notification boshqa kanallar:** Email, SMS va h.k.

## Muammolar va Yechimlar

### Xabar o'chirilmasa

1. **Bot huquqlarini tekshiring:**
   - Bot guruhda admin bo'lishi kerak
   - "Delete messages" huquqi bo'lishi kerak

2. **Message ID ni tekshiring:**
   ```bash
   # Django shell'da:
   python manage.py shell
   >>> from apps.multilevel.models import ManualReview
   >>> mr = ManualReview.objects.get(id=ID)
   >>> print(mr.telegram_message_id)
   ```

3. **Log'larni tekshiring:**
   ```bash
   grep "telegram" logs/gunicorn_error.log
   ```

## Xulosa

Bu funksiya Telegram guruhida faqat haqiqatda tekshirish kutayotgan natijalarni ko'rsatadi. Tekshiruv boshlanganda xabar o'chiriladi, shu bilan boshqa tekshiruvchilar bir xil natijani tekshirishga urinmaydi. Sistema avtomatik va xavfsiz ishlaydi.

