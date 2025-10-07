# SMS Yuborish Muammosini Tuzatish

## Muammo
SMS yuborish `127.0.0.1:8000` da ishlayapti, lekin `api.turantalim.uz` da ishlamayapti.

## Tahlil
- ✅ SMS funksiyasi to'g'ri ishlayapti
- ✅ API view to'g'ri ishlayapti  
- ✅ Foydalanuvchi ma'lumotlar bazasida mavjud
- ✅ ESKIZ_TOKEN to'g'ri sozlangan
- ❌ Web server orqali 500 xatosi qaytarayapti

## Yechim

### 1. Nginx konfiguratsiyasini tekshirish
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Gunicorn loglarini tekshirish
```bash
sudo journalctl -u gunicorn --since "10 minutes ago"
```

### 3. Django loglarini tekshirish
```bash
sudo tail -f /var/log/django.log
```

### 4. API endpointni test qilish
```bash
curl -X POST https://api.turantalim.uz/user/password/reset/request/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "+998908400751"}' \
  -v
```

### 5. Agar muammo davom etsa, quyidagi qadamlarni bajarish:

#### A. Gunicorn konfiguratsiyasini yangilash
```bash
sudo systemctl stop gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

#### B. Nginx konfiguratsiyasini qayta yuklash
```bash
sudo systemctl reload nginx
sudo systemctl status nginx
```

#### C. Firewall sozlamalarini tekshirish
```bash
sudo ufw status
```

### 6. Test qilish
API endpointni test qilish uchun:
```bash
curl -X POST https://api.turantalim.uz/user/password/reset/request/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "+998908400751"}'
```

Kutilgan natija:
```json
{"message": "Tasdiqlash kodi SMS orqali yuborildi."}
```

## Qo'shimcha ma'lumot
- SMS funksiyasi to'g'ri ishlayapti
- Foydalanuvchi ma'lumotlar bazasida mavjud
- Muammo web server konfiguratsiyasida

