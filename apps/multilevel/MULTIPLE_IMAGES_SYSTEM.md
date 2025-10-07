# Ko'p Rasmli Writing Test Tizimi

Bu tizim writing section uchun bir question'ga maximum 3 ta rasm yuklash imkoniyatini ta'minlaydi.

## Asosiy Xususiyatlar

### 1. Ko'p Rasmli Javob
- Bir question'ga 1-3 ta rasm yuklash mumkin
- Har bir rasm order bilan belgilanadi (1, 2, 3)
- Rasmlar order bo'yicha OCR qilinadi va birlashtiriladi

### 2. Order Tizimi
- Order 1: Birinchi rasm
- Order 2: Ikkinchi rasm (1-rasmning davomi bo'lishi mumkin)
- Order 3: Uchinchi rasm (2-rasmning davomi bo'lishi mumkin)

### 3. OCR va Birlashtirish
- Har bir rasm alohida OCR qilinadi
- Matnlar order bo'yicha birlashtiriladi
- ChatGPT to'liq matnni baholaydi

## API Format

### Request Format
```json
{
    "test_result_id": 123,
    "answers": [
        {
            "question": 1,
            "writing_images": [
                {
                    "image": "file1.jpg",
                    "order": 1
                },
                {
                    "image": "file2.jpg", 
                    "order": 2
                },
                {
                    "image": "file3.jpg",
                    "order": 3
                }
            ]
        }
    ]
}
```

### Form-Data Format
```
answers[0][question]: 1
answers[0][writing_images][1][image]: file1.jpg
answers[0][writing_images][1][order]: 1
answers[0][writing_images][2][image]: file2.jpg
answers[0][writing_images][2][order]: 2
answers[0][writing_images][3][image]: file3.jpg
answers[0][writing_images][3][order]: 3
```

## Validation Qoidalari

### 1. Rasm Soni
- Minimum: 1 ta rasm
- Maximum: 3 ta rasm
- 0 ta yoki 4+ ta rasm xatolik

### 2. Order Qoidalari
- Order 1-3 oralig'ida bo'lishi kerak
- Order'lar takrorlanmasligi kerak
- Order'lar ketma-ket bo'lishi kerak (1, 2, 3)

### 3. Fayl Qoidalari
- Format: PNG, JPG, JPEG
- Hajm: Maximum 5MB
- Har bir rasm uchun alohida fayl

## OCR va Baholash Jarayoni

### 1. Har bir rasm uchun OCR
```python
# Har bir rasm uchun
ocr_response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Bu rasmda yozilgan matnni o'qib bering. Bu {order}-rasm."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ],
    max_tokens=500,
)
```

### 2. Matnlarni Birlashtirish
```python
# Barcha matnlarni order bo'yicha birlashtirish
all_texts = []
for image_data in writing_images:
    order = image_data['order']
    processed_text = ocr_response.choices[0].message.content
    all_texts.append(f"[Rasm {order}]: {processed_text}")

# Yakuniy matn
processed_answer = "\n\n".join(all_texts)
```

### 3. ChatGPT Baholash
```python
prompt = (
    f"Foydalanuvchi javobi ({len(writing_images)} ta rasmdan OCR'dan): {processed_answer}\n"
    f"Savol: {question.text}\n"
    "Javobni grammatika, so'z boyligi, mazmun va tuzilishi bo'yicha tekshirib, "
    "batafsil izoh bilan 0-100 oralig'ida baho bering."
)
```

## Response Format

### Muvaffaqiyatli Response
```json
{
    "answers": [
        {
            "message": "Savol 1 uchun writing test (3 ta rasm) muvaffaqiyatli tekshirildi",
            "result": "Javob baholandi",
            "score": 85,
            "test_completed": true,
            "user_answer": "[Rasm 1]: Birinchi rasm matni...\n\n[Rasm 2]: Ikkinchi rasm matni...\n\n[Rasm 3]: Uchinchi rasm matni...",
            "question_text": "Describe your favorite hobby in detail.",
            "images_count": 3,
            "word_count": 150,
            "min_required": 70,
            "target_words": 150
        }
    ],
    "test_completed": true,
    "score": 85
}
```

### Xatolik Response
```json
{
    "error": "Rasmlar order'i [1, 2, 3] bo'lishi kerak!"
}
```

## Xatolik Xabarlari

### 1. Validation Xatoliklari
- `"Maksimum 3 ta rasm yuklash mumkin!"`
- `"Rasmlar order'i takrorlanmasligi kerak!"`
- `"Rasmlar order'i [1, 2, 3] bo'lishi kerak!"`
- `"Rasm hajmi 5MB dan katta bo'lmasligi kerak!"`
- `"Faqat PNG yoki JPG formatidagi rasmlar qabul qilinadi!"`

### 2. OCR Xatoliklari
- `"Barcha rasmlarda matn aniqlanmadi yoki OCR xatolik yuz berdi."`
- `"OCR xatolik rasm 2 uchun: API limit exceeded"`

## Frontend Integratsiyasi

### 1. Rasm Yuklash
```javascript
const formData = new FormData();
formData.append('test_result_id', testResultId);

// Har bir savol uchun
formData.append('answers[0][question]', questionId);

// Har bir rasm uchun
images.forEach((image, index) => {
    formData.append(`answers[0][writing_images][${index + 1}][image]`, image.file);
    formData.append(`answers[0][writing_images][${index + 1}][order]`, index + 1);
});
```

### 2. Rasm Qo'shish/O'chirish
```javascript
// Rasm qo'shish
if (images.length < 3) {
    images.push(newImage);
}

// Rasm o'chirish
images.splice(index, 1);
// Order'larni qayta tartiblash
images.forEach((image, index) => {
    image.order = index + 1;
});
```

## Testlash

### 1. Unit Testlar
```python
# Bitta rasm test
def test_single_image_validation(self):
    # Test kodi...

# Ko'p rasm test
def test_three_images_validation(self):
    # Test kodi...

# Xatolik testlari
def test_four_images_validation_fails(self):
    # Test kodi...
```

### 2. Integration Testlar
```python
# API test
def test_writing_api_with_multiple_images(self):
    # API so'rov test...
```

## Performance Optimizatsiyasi

### 1. Parallel OCR
- Har bir rasm uchun alohida OCR
- Vaqtinchalik fayllarni tozalash
- Xatoliklarni log qilish

### 2. Memory Management
- Vaqtinchalik fayllarni avtomatik o'chirish
- Katta fayllarni stream qilish
- Memory leak'larni oldini olish

## Xavfsizlik

### 1. Fayl Validatsiyasi
- Format tekshirish
- Hajm cheklash
- Malware tekshirish

### 2. Rate Limiting
- API so'rovlarini cheklash
- OCR xizmatini himoya qilish
- Spam oldini olish

## Monitoring va Logging

### 1. Log Fayllar
```python
logger.info(f"Writing test ({len(writing_images)} ta rasm) muvaffaqiyatli tekshirildi")
logger.error(f"OCR xatolik rasm {order} uchun: {str(e)}")
logger.warning(f"Rasm hajmi chegaradan oshib ketdi: {image_size}MB")
```

### 2. Analytics
- Rasm soni statistikasi
- OCR muvaffaqiyat darajasi
- Baholash natijalari

## Kelajakdagi Yaxshilanishlar

1. **Real-time Preview**: Rasm yuklanganda matn ko'rsatish
2. **Auto-save**: Javoblarni avtomatik saqlash
3. **Image Enhancement**: Rasm sifatini yaxshilash
4. **Multi-language OCR**: Ko'p tilli OCR
5. **Voice Input**: Ovozli javob qo'shish
