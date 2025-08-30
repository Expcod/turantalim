# Frontend API Documentation - Speaking va Writing Testlar

Bu dokumentatsiya frontend developer uchun speaking va writing testlarini tekshirish uchun API so'rovlarini yuborish va javoblarni qabul qilish bo'yicha to'liq ma'lumot beradi.

## 📋 Mundarija

1. [Speaking Test API](#speaking-test-api)
2. [Writing Test API](#writing-test-api)
3. [Javob Formatlari](#javob-formatlari)
4. [Xatoliklar](#xatoliklar)
5. [Frontend Integratsiya Namunalari](#frontend-integratsiya-namunalari)

---

## 🎤 Speaking Test API

### Endpoint
```
POST /api/multilevel/testcheck/speaking/
```

### Autentifikatsiya
```javascript
headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}
```

### So'rov Formati (FormData)

Speaking test uchun `FormData` formatida so'rov yuboriladi:

```javascript
const formData = new FormData();

// Test result ID (ixtiyoriy)
formData.append('test_result_id', testResultId);

// Har bir savol uchun javob
answers.forEach((answer, index) => {
    formData.append(`answers[${index}][question]`, answer.questionId);
    formData.append(`answers[${index}][speaking_audio]`, answer.audioFile);
});
```

### So'rov Strukturasi

```javascript
{
    test_result_id: 123, // ixtiyoriy
    answers: [
        {
            question: 1, // Savol ID
            speaking_audio: File // Audio fayl
        },
        {
            question: 2,
            speaking_audio: File
        }
        // ... boshqa javoblar
    ]
}
```

### Qo'llab-quvvatlanadigan Audio Formatlar

- **MP3** (.mp3)
- **WAV** (.wav)
- **FLAC** (.flac)
- **M4A** (.m4a)
- **OGG** (.ogg)
- **WEBM** (.webm)
- **MP4** (.mp4) - audio track bilan
- **3GP** (.3gp) - audio track bilan

### Fayl Cheklovlari

- **Maksimal hajm**: 25 MB
- **Minimal hajm**: 1 KB
- **MIME tiplari**: Audio va video formatlar

---

## ✍️ Writing Test API

### Endpoint
```
POST /api/multilevel/testcheck/writing/
```

### Autentifikatsiya
```javascript
headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
}
```

### So'rov Formati (FormData)

Writing test uchun ham `FormData` formatida so'rov yuboriladi:

```javascript
const formData = new FormData();

// Test result ID (ixtiyoriy)
formData.append('test_result_id', testResultId);

// Har bir savol uchun javob
answers.forEach((answer, index) => {
    formData.append(`answers[${index}][question]`, answer.questionId);
    formData.append(`answers[${index}][writing_image]`, answer.imageFile);
});
```

### So'rov Strukturasi

```javascript
{
    test_result_id: 123, // ixtiyoriy
    answers: [
        {
            question: 1, // Savol ID
            writing_image: File // Rasm fayli
        },
        {
            question: 2,
            writing_image: File
        }
        // ... boshqa javoblar
    ]
}
```

### Qo'llab-quvvatlanadigan Rasm Formatlar

- **PNG** (.png)
- **JPG/JPEG** (.jpg, .jpeg)

### Fayl Cheklovlari

- **Maksimal hajm**: 5 MB
- **Minimal hajm**: 1 KB
- **MIME tiplari**: image/png, image/jpeg

---

## 📊 Javob Formatlari

### Speaking Test Javobi

```javascript
{
    "answers": [
        {
            "message": "Javob muvaffaqiyatli tekshirildi",
            "result": "Foydalanuvchi javobi: [AI tomonidan transkripsiya qilingan matn]",
            "score": 25, // 0-100 oralig'ida
            "test_completed": true,
            "user_answer": "[AI tomonidan transkripsiya qilingan matn]",
            "question_text": "Savol matni"
        },
        // ... boshqa javoblar
    ],
    "test_completed": true,
    "score": 75 // Umumiy ball (0-75 oralig'ida)
}
```

### Writing Test Javobi

```javascript
{
    "answers": [
        {
            "message": "Javob muvaffaqiyatli tekshirildi",
            "result": "AI tomonidan baholangan natija",
            "score": 30, // 0-100 oralig'ida
            "test_completed": true,
            "user_answer": "[AI tomonidan o'qilgan matn]",
            "question_text": "Savol matni"
        },
        // ... boshqa javoblar
    ],
    "test_completed": true,
    "score": 75 // Umumiy ball (0-75 oralig'ida)
}
```

### Javob Maydonlari Tushuntirilishi

| Maydon | Turi | Tushuntirish |
|--------|------|--------------|
| `answers` | Array | Har bir savol uchun javob ma'lumotlari |
| `answers[].message` | String | Tekshirish natijasi haqida xabar |
| `answers[].result` | String | AI tomonidan batafsil natija |
| `answers[].score` | Number | Har bir savol uchun ball (0-100) |
| `answers[].test_completed` | Boolean | Test yakunlanganligi |
| `answers[].user_answer` | String | AI tomonidan o'qilgan/transkripsiya qilingan matn |
| `answers[].question_text` | String | Savol matni |
| `test_completed` | Boolean | Butun test yakunlanganligi |
| `score` | Number | Umumiy test balli (0-75) |

---

## ❌ Xatoliklar

### 400 Bad Request

```javascript
{
    "error": "Validation xatosi",
    "details": {
        "answers": [
            "Kamida bitta javob kiritilishi shart!"
        ],
        "answers[0].speaking_audio": [
            "Fayl hajmi 25 MB dan katta bo'lmasligi kerak!"
        ]
    }
}
```

### 403 Forbidden

```javascript
{
    "error": "TestResult topilmadi yoki faol emas!"
}
```

### 500 Internal Server Error

```javascript
{
    "error": "Server xatosi",
    "message": "OpenAI API bilan bog'lanishda xatolik yuz berdi"
}
```

### Keng Tarqalgan Xatoliklar

| Xatolik Kodi | Sababi | Yechim |
|--------------|--------|--------|
| 400 | Fayl formati noto'g'ri | To'g'ri formatda fayl yuklang |
| 400 | Fayl hajmi katta | Kichikroq fayl yuklang |
| 400 | Savol ID mavjud emas | To'g'ri savol ID sini yuboring |
| 400 | Bir xil savol ID si | Har bir savol uchun bitta javob |
| 403 | TestResult topilmadi | To'g'ri test_result_id yuboring |
| 500 | OpenAI xatosi | Qaytadan urinib ko'ring |

---

## 💻 Frontend Integratsiya Namunalari

### Speaking Test Yuborish

```javascript
// Speaking test javoblarini yuborish
const submitSpeakingTest = async (testResultId, answers) => {
    try {
        const formData = new FormData();
        
        // Test result ID
        if (testResultId) {
            formData.append('test_result_id', testResultId);
        }
        
        // Har bir javob uchun
        answers.forEach((answer, index) => {
            formData.append(`answers[${index}][question]`, answer.questionId);
            formData.append(`answers[${index}][speaking_audio]`, answer.audioFile);
        });
        
        const response = await fetch('/api/multilevel/testcheck/speaking/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                // Content-Type ni yozmang, FormData uchun avtomatik o'rnatiladi
            },
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Xatolik yuz berdi');
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Speaking test yuborishda xatolik:', error);
        throw error;
    }
};

// Foydalanish
const handleSpeakingSubmit = async () => {
    try {
        const answers = [
            {
                questionId: 1,
                audioFile: audioFile1 // File obyekti
            },
            {
                questionId: 2,
                audioFile: audioFile2
            }
        ];
        
        const result = await submitSpeakingTest(testResultId, answers);
        console.log('Natija:', result);
        
        // Natijani ko'rsatish
        if (result.test_completed) {
            showSuccess(`Test yakunlandi! Ball: ${result.score}/75`);
        }
        
    } catch (error) {
        showError(error.message);
    }
};
```

### Writing Test Yuborish

```javascript
// Writing test javoblarini yuborish
const submitWritingTest = async (testResultId, answers) => {
    try {
        const formData = new FormData();
        
        // Test result ID
        if (testResultId) {
            formData.append('test_result_id', testResultId);
        }
        
        // Har bir javob uchun
        answers.forEach((answer, index) => {
            formData.append(`answers[${index}][question]`, answer.questionId);
            formData.append(`answers[${index}][writing_image]`, answer.imageFile);
        });
        
        const response = await fetch('/api/multilevel/testcheck/writing/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
            },
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Xatolik yuz berdi');
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Writing test yuborishda xatolik:', error);
        throw error;
    }
};

// Foydalanish
const handleWritingSubmit = async () => {
    try {
        const answers = [
            {
                questionId: 1,
                imageFile: imageFile1 // File obyekti
            },
            {
                questionId: 2,
                imageFile: imageFile2
            }
        ];
        
        const result = await submitWritingTest(testResultId, answers);
        console.log('Natija:', result);
        
        // Natijani ko'rsatish
        if (result.test_completed) {
            showSuccess(`Test yakunlandi! Ball: ${result.score}/75`);
        }
        
    } catch (error) {
        showError(error.message);
    }
};
```

### Progress Tracking

```javascript
// Progress tracking uchun
const trackProgress = (answers) => {
    const totalQuestions = answers.length;
    const completedQuestions = answers.filter(answer => 
        answer.audioFile || answer.imageFile
    ).length;
    
    const progress = (completedQuestions / totalQuestions) * 100;
    return {
        progress,
        completedQuestions,
        totalQuestions
    };
};

// Progress ko'rsatish
const showProgress = (answers) => {
    const { progress, completedQuestions, totalQuestions } = trackProgress(answers);
    
    console.log(`Progress: ${progress.toFixed(1)}% (${completedQuestions}/${totalQuestions})`);
    
    // UI da ko'rsatish
    updateProgressBar(progress);
    updateProgressText(`${completedQuestions}/${totalQuestions}`);
};
```

### Fayl Validatsiyasi

```javascript
// Audio fayl validatsiyasi
const validateAudioFile = (file) => {
    const maxSize = 25 * 1024 * 1024; // 25 MB
    const allowedTypes = [
        'audio/mp3', 'audio/wav', 'audio/flac', 'audio/m4a',
        'audio/ogg', 'audio/webm', 'video/mp4', 'video/webm'
    ];
    
    if (file.size > maxSize) {
        throw new Error('Fayl hajmi 25 MB dan katta bo\'lishi mumkin emas');
    }
    
    if (!allowedTypes.includes(file.type)) {
        throw new Error('Noto\'g\'ri fayl formati. Audio fayl yuklang');
    }
    
    return true;
};

// Rasm fayl validatsiyasi
const validateImageFile = (file) => {
    const maxSize = 5 * 1024 * 1024; // 5 MB
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    
    if (file.size > maxSize) {
        throw new Error('Rasm hajmi 5 MB dan katta bo\'lishi mumkin emas');
    }
    
    if (!allowedTypes.includes(file.type)) {
        throw new Error('Noto\'g\'ri rasm formati. PNG yoki JPG yuklang');
    }
    
    return true;
};
```

---

## 🔄 Test Natijalarini Olish

### Test Natijasi API

```javascript
// Test natijasini olish
const getTestResult = async (testResultId) => {
    try {
        const response = await fetch(`/api/multilevel/test-result/${testResultId}/`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Test natijasi olinmadi');
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Test natijasi olishda xatolik:', error);
        throw error;
    }
};

// Test natijasi strukturasi
const testResult = {
    "id": 195,
    "section": "Turan Talim CEFR 1. Sınav Konuşma Bölümü",
    "language": "TR",
    "status": "completed",
    "start_time": "2025-08-23T22:45:39.846222+05:00",
    "end_time": "2025-08-23T22:59:39.846232+05:00",
    "total_questions": 8,
    "correct_answers": 0,
    "incorrect_answers": 8,
    "percentage": 27, // Speaking/Writing uchun ball (0-75)
    "level": "Below B1"
};
```

---

## 📝 Muhim Eslatmalar

1. **FormData ishlatish**: Speaking va Writing testlar uchun har doim `FormData` ishlatiladi
2. **Content-Type**: FormData uchun `Content-Type` headerini yozmang, avtomatik o'rnatiladi
3. **Fayl validatsiyasi**: Frontend da ham fayl validatsiyasi qiling
4. **Progress tracking**: Katta fayllar uchun progress ko'rsating
5. **Error handling**: Barcha xatoliklarni to'g'ri handle qiling
6. **Token**: Har doim to'g'ri Authorization token yuboring

---

## 🚀 Tezkor Boshlash

1. **Speaking test uchun**:
   ```javascript
   const result = await submitSpeakingTest(testResultId, [
       { questionId: 1, audioFile: file1 },
       { questionId: 2, audioFile: file2 }
   ]);
   ```

2. **Writing test uchun**:
   ```javascript
   const result = await submitWritingTest(testResultId, [
       { questionId: 1, imageFile: file1 },
       { questionId: 2, imageFile: file2 }
   ]);
   ```

3. **Natijani ko'rish**:
   ```javascript
   console.log(`Ball: ${result.score}/75`);
   console.log(`Yakunlandi: ${result.test_completed}`);
   ```

Bu dokumentatsiya orqali frontend developer speaking va writing testlarini to'liq integratsiya qila oladi!
