# Writing Test Vaqt Boshqarish Tizimi

Bu tizim writing testlari uchun javob berish va rasm yuklash vaqtini boshqarish imkonini beradi. Speaking testlardagi kabi oddiy vaqt boshqarish tizimi.

## Asosiy Xususiyatlar

### 1. Test Modeliga Qo'shilgan Maydonlar
- `response_time` - Javob berish vaqti (sekundlarda)
- `upload_time` - Rasm yuklash vaqti (sekundlarda)

### 2. Admin Panel
- Writing section uchun `response_time` va `upload_time` maydonlari ko'rsatiladi
- Boshqa sectionlar uchun bu maydonlar yashiriladi
- Writing bo'lmagan sectionlar uchun vaqt maydonlari avtomatik tozalab qo'yiladi

## Admin Panelda O'rnatish

### Test Modeli
1. Admin panelga kirish
2. Test modeliga o'tish
3. Writing section uchun testni tanlash
4. "Writing test vaqtlari" bo'limida:
   - `response_time` - Javob berish vaqti (sekundlarda)
   - `upload_time` - Rasm yuklash vaqti (sekundlarda)

## API Endpoint

### Test Vaqt Ma'lumotlarini Olish
```
GET /api/multilevel/test/time-info/?test_id={test_id}
```

**Response (Writing section uchun):**
```json
{
    "test_id": 123,
    "response_time": 300,
    "upload_time": 60,
    "section_type": "writing",
    "message": "Writing test vaqt ma'lumotlari"
}
```

**Response (Boshqa sectionlar uchun):**
```json
{
    "test_id": 123,
    "response_time": null,
    "upload_time": null,
    "section_type": "reading",
    "message": "Vaqt boshqarish faqat writing section uchun mavjud"
}
```

## Frontend Integratsiyasi

### 1. Test Vaqt Ma'lumotlarini Olish
```javascript
// Test vaqt ma'lumotlarini olish
const getTestTimeInfo = async (testId) => {
    const response = await fetch(`/api/multilevel/test/time-info/?test_id=${testId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
};
```

### 2. Vaqt Boshqarish Logikasi
```javascript
// Writing test uchun vaqt boshqarish
const handleWritingTest = async (testId) => {
    // Test vaqt ma'lumotlarini olish
    const timeInfo = await getTestTimeInfo(testId);
    
    if (timeInfo.section_type === 'writing' && timeInfo.response_time) {
        // Vaqt chegaralari mavjud
        const responseTimeLimit = timeInfo.response_time; // sekundlarda
        const uploadTimeLimit = timeInfo.upload_time; // sekundlarda
        
        // Frontend da vaqt boshqarish logikasi
        startTimer(responseTimeLimit, uploadTimeLimit);
    } else {
        // Vaqt chegarasi yo'q, oddiy test
        startNormalTest();
    }
};

// Vaqt boshqarish
const startTimer = (responseTimeLimit, uploadTimeLimit) => {
    let responseTimeUsed = 0;
    let uploadTimeUsed = 0;
    
    // Javob berish vaqtini boshlash
    const responseTimer = setInterval(() => {
        responseTimeUsed++;
        
        // Vaqt tugashini tekshirish
        if (responseTimeUsed >= responseTimeLimit) {
            clearInterval(responseTimer);
            alert('Javob berish vaqti tugadi!');
            // Javobni avtomatik yuborish yoki boshqa logika
        }
        
        // Qolgan vaqtni ko'rsatish
        updateResponseTimeDisplay(responseTimeLimit - responseTimeUsed);
    }, 1000);
    
    // Rasm yuklash vaqtini boshlash (upload boshlanganda)
    const startUploadTimer = () => {
        const uploadTimer = setInterval(() => {
            uploadTimeUsed++;
            
            if (uploadTimeUsed >= uploadTimeLimit) {
                clearInterval(uploadTimer);
                alert('Rasm yuklash vaqti tugadi!');
                // Upload ni to'xtatish
            }
            
            updateUploadTimeDisplay(uploadTimeLimit - uploadTimeUsed);
        }, 1000);
    };
    
    return {
        responseTimer,
        startUploadTimer,
        getResponseTimeUsed: () => responseTimeUsed,
        getUploadTimeUsed: () => uploadTimeUsed
    };
};
```

### 3. Vaqt Ko'rsatish
```javascript
// Vaqt ko'rsatish funksiyalari
const updateResponseTimeDisplay = (remainingTime) => {
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    document.getElementById('response-time').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const updateUploadTimeDisplay = (remainingTime) => {
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    document.getElementById('upload-time').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
};
```

## Xavfsizlik

- API endpoint authentication talab qiladi
- Foydalanuvchi faqat mavjud testlarga kirish huquqiga ega
- Vaqt ma'lumotlari faqat writing section uchun qaytariladi

## Foydalanish

### 1. Admin Panelda Vaqt O'rnatish
1. Admin panelga kirish
2. Test modeliga o'tish
3. Writing section uchun testni tanlash
4. "Writing test vaqtlari" bo'limida vaqtlarni belgilash

### 2. Frontend da Vaqt Boshqarish
1. Test boshlashda vaqt ma'lumotlarini olish
2. Vaqt chegarasi mavjud bo'lsa, timer boshlash
3. Foydalanuvchiga qolgan vaqtni ko'rsatish
4. Vaqt tugaganda tegishli amallarni bajarish

## Xatoliklar

### Keng Tarqalgan Xatoliklar
1. **Test topilmadi** - Test ID noto'g'ri yoki mavjud emas
2. **Writing section emas** - Vaqt boshqarish faqat writing section uchun mavjud

### Xatoliklarni Hal Qilish
- Test ID ni to'g'ri kiritish
- Writing section uchun test yaratish
- Admin panelda vaqt chegaralarini to'g'ri o'rnatish
