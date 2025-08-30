# Telegram Bot Setup Guide

## Bitta botni 2 ta guruhda ishlatish

Siz bitta botni 2 ta maqsadda ishlatayapsiz:
1. **Payment guruh** - To'lovlar haqida xabarlar
2. **Visitor guruh** - Kursga ro'yxatdan o'tish arizalari

Bu juda yaxshi yechim! Bitta botni bir nechta guruhda admin qilib, har bir guruh uchun alohida chat ID ishlatish mumkin.

## .env fayl sozlamalari

```env
# Telegram Bot Token (bitta bot uchun)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Payment guruh uchun chat ID
TELEGRAM_CHAT_ID=payment_group_chat_id

# Visitor guruh uchun chat ID  
TELEGRAM_VISITOR_CHAT_ID=visitor_group_chat_id
```

## Chat ID larni olish

### 1. Bot yaratish
1. @BotFather ga boring
2. `/newbot` buyrug'ini yuboring
3. Bot nomi va username bering
4. Bot token ni saqlang

### 2. Botni guruhlarga qo'shish
1. Har bir guruhga botni qo'shing
2. Botga admin huquqlarini bering (xabar yuborish uchun)

### 3. Chat ID larni olish
```bash
# Bot token bilan chat ID larni olish
curl -X GET "https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates"
```

Yoki botga guruhda xabar yuboring va keyin:
```bash
curl -X GET "https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates"
```

Response da `chat.id` ni toping:
```json
{
  "ok": true,
  "result": [
    {
      "message": {
        "chat": {
          "id": -1001234567890,  // Bu chat ID
          "title": "Turantalim Payment",
          "type": "supergroup"
        }
      }
    }
  ]
}
```

## Xabarlar turlari

### Payment guruhga yuboriladigan xabarlar
- To'lov muvaffaqiyatli amalga oshirildi
- To'lov xatosi
- To'lov ma'lumotlari

### Visitor guruhga yuboriladigan xabarlar
```
🆕 Yangi kursga ro'yxatdan o'tish arizasi!

👤 Foydalanuvchi: Aziz Karimov
📱 Telefon: +998901234567
📅 Sana: 15.01.2024 10:30
🔗 Admin panel: /admin/visitor/visitor/1/
```

## Test qilish

### 1. Bot token ni tekshirish
```bash
curl -X GET "https://api.telegram.org/botYOUR_BOT_TOKEN/getMe"
```

### 2. Xabar yuborish testi
```bash
# Payment guruhga
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "PAYMENT_CHAT_ID",
    "text": "Test xabar - Payment guruh"
  }'

# Visitor guruhga  
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "VISITOR_CHAT_ID", 
    "text": "Test xabar - Visitor guruh"
  }'
```

## Xavfsizlik maslahatlari

1. **Bot token ni hech kimga bermang**
2. **Chat ID larni ham himoya qiling**
3. **Guruhda faqat kerakli admin huquqlarini bering**
4. **Botni faqat o'z guruhlaringizda ishlating**

## Muammolarni hal qilish

### Bot xabar yubormayapti
1. Bot guruhda admin ekanligini tekshiring
2. Chat ID to'g'ri ekanligini tekshiring
3. Bot token to'g'ri ekanligini tekshiring

### Chat ID noto'g'ri
1. Guruhda botga xabar yuboring
2. `getUpdates` orqali yangi chat ID ni oling
3. .env faylga yangi chat ID ni yozing

### Bot guruhda ko'rinmayapti
1. Botni guruhga qo'shganingizni tekshiring
2. Bot username to'g'ri ekanligini tekshiring
3. Bot faol ekanligini tekshiring
