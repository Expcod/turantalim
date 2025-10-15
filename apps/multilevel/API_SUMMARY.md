# 🎯 Imtihon Natijalari API - Qisqacha Ma'lumot

## 📋 Asosiy API Endpointlari

### 1. 🎯 Bitta Imtihon Natijasini Olish
```
GET https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id={id}
```
**Maqsad:** Bitta multilevel/TYS imtihonining batafsil natijasini olish

### 2. 📝 Barcha Imtihon Natijalarini Olish  
```
GET https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/?exam_level={level}&limit={count}
```
**Maqsad:** Foydalanuvchining barcha imtihonlarining ro'yxatini olish


---

## 🔧 Authentication

Barcha endpointlarda authentication kerak:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN',
  'Content-Type': 'application/json'
}
```

---

## 📊 Response Structure

### Success Response:
```json
{
  "success": true,
  "exam_info": { /* imtihon ma'lumotlari */ },
  "section_results": { /* section natijalari */ },
  "overall_result": { /* umumiy natija */ },
  "level_ranges": { /* daraja oralig'lari */ }
}
```

### Error Response:
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## 🎯 Imtihon Turlari

### Multilevel Exam:
- **Max Score:** 75 ball/section (300 jami)
- **Final Score:** Total ÷ 4 = Final (0-75)
- **Levels:** B1 (38-50), B2 (51-64), C1 (65-75)

### TYS Exam:
- **Max Score:** 25 ball/section (100 jami)  
- **Final Score:** Total = Final (0-100)
- **Levels:** B1 (51+), B2 (68+), C1 (87+)

---

## 🚀 Tez Boshlash

### JavaScript Example:
```javascript
// 1. Barcha imtihonlarni olish
const exams = await fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// 2. Bitta imtihon natijasini olish
const detail = await fetch(`https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/?user_test_id=${examId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

### React Hook Example:
```javascript
const useExamResults = () => {
  const [exams, setExams] = useState([]);
  
  useEffect(() => {
    fetch('https://api.turantalim.uz/multilevel/exam-results/multilevel-tys/list/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(r => r.json())
    .then(data => setExams(data.exams));
  }, []);
  
  return exams;
};
```

---

## 📱 Status Codes

| Code | Description |
|------|-------------|
| 200 | ✅ Success |
| 400 | ❌ Bad Request |
| 401 | 🔒 Unauthorized |
| 404 | 🔍 Not Found |
| 500 | ⚠️ Server Error |

---

## 🎨 Frontend Integration Tips

1. **Loading States:** API call paytida loading ko'rsating
2. **Error Handling:** Foydalanuvchiga tushunarli xato xabarlari
3. **Progress Bars:** Section natijalarida progress ko'rsating
4. **Level Colors:** Daraja uchun ranglar (B1: sariq, B2: ko'k, C1: yashil)
5. **Responsive:** Barcha qurilmalarda yaxshi ko'rinish

---

## 📚 To'liq Qo'llanmalar

- **Frontend Integration:** `FRONTEND_INTEGRATION_GUIDE.md`
- **Postman Collection:** `POSTMAN_COLLECTION.md`

---

## 🔗 Base URL

```
Production: https://api.turantalim.uz/multilevel
```

---

**🎉 Imtihon natijalarini olish endi juda oson!**
