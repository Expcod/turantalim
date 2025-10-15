# O'zgarishlar Jurnali - Tekshiruvchi Tizimi

**Sana:** 2025-10-08  
**Versiya:** 1.0  
**Muallif:** Turantalim Development Team

## 🎯 Yangi Funksiyalar

### 1. Reviewer (Tekshiruvchi) Tizimi

Admin panel orqali admin-dashboard uchun alohida tekshiruvchilarni boshqarish tizimi qo'shildi.

#### Imkoniyatlar:
- ✅ Tekshiruvchilar admin-dashboard ga kira oladilar
- ✅ Writing va Speaking natijalarini tekshirishlari mumkin
- ✅ Ball qo'yishlari va izohlar yozishlari mumkin
- ✅ Django admin panel orqali boshqariladi
- ❌ Tekshiruvchilar Django admin panelga kira olmaydilar

## 📁 Yangi Fayllar

### 1. `apps/multilevel/permissions.py`
**Maqsad:** Custom permission class  
**Funksiya:** `IsReviewerOrAdmin` - Staff yoki Reviewer guruhidagi userlarni tekshiradi

```python
class IsReviewerOrAdmin(BasePermission):
    """Allow access to staff users or users in Reviewer group"""
```

### 2. `apps/multilevel/management/commands/setup_reviewers.py`
**Maqsad:** Reviewer group va permissionlarni avtomatik sozlash  
**Ishlatish:** `python manage.py setup_reviewers`

**Yaratilgan permissions:**
- view_manualreview
- change_manualreview
- view_questionscore
- add_questionscore
- change_questionscore
- view_reviewlog
- view_submissionmedia

### 3. `apps/multilevel/reviewer_admin.py`
**Maqsad:** Reviewer userlar uchun admin interface  
**Funksiya:** Django admin da tekshiruvchilarni yaratish va boshqarish

### 4. `REVIEWER_SETUP_GUIDE.md`
**Maqsad:** To'liq dokumentatsiya  
**Tarkib:** Setup, foydalanish, troubleshooting

### 5. `REVIEWER_QUICK_START.md`
**Maqsad:** Tezkor qo'llanma  
**Tarkib:** Asosiy amallar va misollar

### 6. `CHANGES_LOG.md`
**Maqsad:** O'zgarishlar tarixi  
**Tarkib:** Bu fayl

## 🔄 O'zgartirilgan Fayllar

### 1. `apps/multilevel/admin.py`
**O'zgarishlar:**
- `ReviewerUserAdmin` class qo'shildi
- User modelni reviewer sifatida boshqarish imkoniyati
- Faqat non-staff userlarni ko'rsatish filtri

**Qo'shilgan kod:**
```python
class ReviewerUserAdmin(admin.ModelAdmin):
    """Simplified admin interface for managing Reviewer users"""
    list_display = ['phone', 'get_full_name', 'email', 'is_active', 'is_reviewer', 'date_joined']
    # ...
```

### 2. `apps/multilevel/auth_views.py`
**O'zgarishlar:**
- Login authentication da Reviewer guruhini tekshirish qo'shildi
- Staff yoki Reviewer bo'lsa login qilish mumkin
- Response da `is_reviewer` field qo'shildi

**O'zgartirish:**
```python
# OLDIN:
if not user.is_staff:
    return Response({'error': 'Sizda admin panelga kirish huquqi yo\'q'})

# KEYIN:
is_reviewer = user.groups.filter(name='Reviewer').exists()
if not user.is_staff and not user.is_superuser and not is_reviewer:
    return Response({'error': 'Sizda admin panelga kirish huquqi yo\'q'})
```

### 3. `apps/multilevel/manual_review_views.py`
**O'zgarishlar:**
- Permission class `IsAdminUser` dan `IsReviewerOrAdmin` ga o'zgartirildi

**O'zgartirish:**
```python
# OLDIN:
permission_classes = [IsAdminUser]

# KEYIN:
permission_classes = [IsReviewerOrAdmin]
```

### 4. `admin_dashboard/js/api-client.js`
**O'zgarishlar:**
- Logout URL tuzatildi: `/admin_dashboard/` → `/admin-dashboard/`

**O'zgartirish (144-qator):**
```javascript
// OLDIN:
window.location.href = '/admin_dashboard/login.html';

// KEYIN:
window.location.href = '/admin-dashboard/login.html';
```

## 🔑 Asosiy Kontseptsiyalar

### Django Groups va Permissions

Tizimda 3 xil user mavjud:

1. **Superuser**
   - `is_superuser = True`
   - `is_staff = True`
   - Barcha ruxsatlar

2. **Staff User**
   - `is_staff = True`
   - Django admin panel
   - Admin-dashboard

3. **Reviewer** (YANGI!)
   - `is_staff = False`
   - `groups = ['Reviewer']`
   - Faqat admin-dashboard
   - Cheklangan ruxsatlar

### Permission Flow

```
User Login
    ↓
Phone/Password Check
    ↓
is_superuser? → ✅ Allow
    ↓ No
is_staff? → ✅ Allow
    ↓ No
In 'Reviewer' group? → ✅ Allow
    ↓ No
❌ Deny Access
```

## 🧪 Test Ma'lumotlari

### Test Reviewer Account

```
Telefon: +998901234567
Parol: test123
Ism: Test
Familiya: Reviewer
Guruh: Reviewer
is_staff: False
is_active: True
```

### Test Qilish

1. Admin-dashboard login: http://your-domain.com/admin-dashboard/login.html
2. Test reviewer bilan login qiling
3. Submissions ro'yxatini ko'ring
4. Writing/Speaking natijalarini tekshiring

## 📋 Migration va Setup

### Commands

```bash
# 1. Reviewer group yaratish
python manage.py setup_reviewers

# 2. Test reviewer yaratish (ixtiyoriy)
python manage.py shell
# ... (see REVIEWER_QUICK_START.md)

# 3. Server restart
sudo supervisorctl restart turantalim
```

### Database O'zgarishlari

- **Yangi modellar:** Yo'q
- **Yangi migration:** Yo'q (faqat Group va Permission ishlatildi)
- **Yangi Group:** "Reviewer"
- **Yangi Permission:** 7 ta (setup_reviewers command orqali)

## 🔐 Xavfsizlik

### Himoya Choralari

1. ✅ Tekshiruvchilar faqat manual review API ga kiradi
2. ✅ Django admin panelga kirish yo'q
3. ✅ User ma'lumotlarini o'zgartirish yo'q
4. ✅ Exam/Test yaratish/o'zgartirish yo'q
5. ✅ Faqat view va change ruxsatlari
6. ✅ Delete ruxsati yo'q

### Permission Matrix

| Model | View | Add | Change | Delete |
|-------|------|-----|--------|--------|
| ManualReview | ✅ | ❌ | ✅ | ❌ |
| QuestionScore | ✅ | ✅ | ✅ | ❌ |
| ReviewLog | ✅ | ❌ | ❌ | ❌ |
| SubmissionMedia | ✅ | ❌ | ❌ | ❌ |

## 🚀 Deploy Qilish

### Production Serverda

1. Git pull yoki yangi kodlarni yuklash
2. Virtual environment faollashtirish
3. Setup command ishlatish:
   ```bash
   python manage.py setup_reviewers
   ```
4. Server restart:
   ```bash
   sudo supervisorctl restart turantalim
   ```

### Nginx/Apache

Hech qanday o'zgarish kerak emas - barcha yo'llar oldingi kabi ishlaydi.

## 📊 API Endpoints

### Yangi yoki O'zgargan

Yo'q - barcha endpoints oldingi kabi, faqat permission class o'zgartirildi.

### Mavjud Endpoints (Reviewerlar uchun)

```
GET    /multilevel/api/admin/submissions/           - List submissions
GET    /multilevel/api/admin/submissions/{id}/      - Get submission detail
GET    /multilevel/api/admin/submissions/{id}/media/ - Get media files
PATCH  /multilevel/api/admin/submissions/{id}/writing/ - Update writing scores
PATCH  /multilevel/api/admin/submissions/{id}/speaking/ - Update speaking scores
```

## 🐛 Bug Fixes

### 1. Logout Redirect Bug

**Muammo:** Logout qilganda `/admin_dashboard/` ga redirect qilar edi (404)  
**Yechim:** `/admin-dashboard/` ga o'zgartirildi  
**Fayl:** `admin_dashboard/js/api-client.js:144`

## 📈 Kelajak Rejalari

### Version 1.1 (kelgusida)

- [ ] Reviewer activity dashboard
- [ ] Reviewer performance statistics
- [ ] Email notifications for reviewers
- [ ] Reviewer shift management
- [ ] Bulk reviewer creation tool

## 🎓 O'rganish Manbaalari

1. **Django Groups and Permissions:**
   - https://docs.djangoproject.com/en/stable/topics/auth/default/#groups

2. **Django REST Framework Permissions:**
   - https://www.django-rest-framework.org/api-guide/permissions/

3. **Django Admin Customization:**
   - https://docs.djangoproject.com/en/stable/ref/contrib/admin/

## ✅ Checklist

### Development
- [x] Permission class yaratish
- [x] Management command yaratish
- [x] Admin interface sozlash
- [x] Auth views yangilash
- [x] API views yangilash
- [x] Logout bug tuzatish
- [x] Test reviewer yaratish
- [x] Dokumentatsiya yozish

### Testing
- [x] Reviewer login test
- [x] Permission test
- [x] API access test
- [ ] Load testing (production da)

### Documentation
- [x] Setup guide
- [x] Quick start
- [x] Changes log
- [x] Code comments

### Deployment
- [x] Server restart
- [x] Setup command run
- [ ] Production testing

## 🤝 Contributors

- Development Team: Turantalim
- Date: 2025-10-08
- Version: 1.0

---

**Keyingi yangilanish:** Yangi features qo'shilganda  
**Versiya:** 1.0
