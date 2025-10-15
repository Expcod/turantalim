# 🚀 Turantalim Frontend Integration Guide

Bu dokumentatsiya **Nuxt3** frontend bilan **Django** backend integratsiyasi uchun to'liq qo'llanma.

---

## 📚 Documentation Files

Barcha dokumentatsiya fayllari:

1. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - To'liq API dokumentatsiyasi
   - Authentication
   - Writing & Speaking APIs
   - File Upload
   - Response Codes
   - Complete Nuxt3 Example Code

2. **[API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)** - Qisqacha API ma'lumotnoma
   - Quick endpoint list
   - Request/Response samples
   - Status codes
   - File requirements

3. **[postman_collection.json](./postman_collection.json)** - Postman Collection
   - Import in Postman
   - Test all endpoints
   - Pre-configured requests

4. **[frontend.env.example](./frontend.env.example)** - Environment variables example
   - Copy to `.env`
   - Update with your values

5. **[nuxt.config.example.ts](./nuxt.config.example.ts)** - Nuxt3 configuration
   - Runtime config
   - Environment setup

---

## 🎯 Quick Start

### 1. Setup Environment

```bash
# Frontend directory
cd your-nuxt-project

# Copy environment file
cp frontend.env.example .env

# Update .env with your values
nano .env
```

### 2. Install Postman Collection

1. Open Postman
2. Import → Upload Files → Select `postman_collection.json`
3. Set environment variables:
   - `base_url`: `http://localhost:8000`
   - `access_token`: (will be filled after login)

### 3. Test API Connection

```javascript
// Test in browser console or Nuxt app
fetch('http://localhost:8000/api/token/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    phone: '+998901234567',
    password: 'yourpassword'
  })
})
.then(r => r.json())
.then(data => console.log('Token:', data.access))
```

---

## 🎓 System Overview

### Exam Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXAM PROCESS                              │
└─────────────────────────────────────────────────────────────────┘

1. USER AUTHENTICATION
   ↓
   Frontend → POST /api/token/ → Backend
   Backend returns: { access, refresh, user }
   
2. START EXAM
   ↓
   Frontend → GET /multilevel/exams/ → Backend
   User selects exam and starts
   
3. COMPLETE SECTIONS
   
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  Listening  │  │   Reading   │  │   Writing   │  │  Speaking   │
   │  (Auto)     │  │   (Auto)    │  │  (Manual)   │  │  (Manual)   │
   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
        ↓                 ↓                 ↓                 ↓
    Instant           Instant         Admin            Admin
    Score             Score           Reviews          Reviews
                                         ↓                 ↓
4. MANUAL REVIEW (Writing & Speaking)
   
   Frontend → POST /multilevel/testcheck/writing/ → Backend
            (uploads images)                          ↓
                                              Status: pending
                                                     ↓
                                            Admin Dashboard
                                              Reviews & Scores
                                                     ↓
                                              Status: checked
   
5. CHECK RESULTS
   ↓
   Frontend → GET /multilevel/test-result/{id}/ → Backend
   Backend returns: { score, feedback, status }
   
6. VIEW OVERALL RESULT
   ↓
   Frontend → GET /multilevel/exam-results/multilevel-tys/ → Backend
   Backend calculates: total score from all sections
```

---

## 📝 Scoring System

### Writing Section (Max: 75 points)

| Task | Description | Max Score | Weight |
|------|-------------|-----------|--------|
| Task 1 | Letter (150 words, 20 min) | 24.75 | 33% |
| Task 2 | Essay (250 words, 40 min) | 50.25 | 67% |
| **Total** | | **75** | **100%** |

**Calculation:**
```
Total Score = Task 1 Score + Task 2 Score
Example: 20.5 + 45.0 = 65.5
```

### Speaking Section (Max: 75 points)

| Part | Description | Time | Score |
|------|-------------|------|-------|
| Part 1 | Introduction & Interview | 3 min | |
| Part 2 | Long Turn | 4 min | |
| Part 3 | Discussion | 5 min | |
| **Total** | Combined score for all parts | | **75** |

**Note:** Speaking bo'limida barcha partlar bitta ball bilan baholanadi (0-75).

---

## 🔄 Data Structure

### Writing Submission
```typescript
interface WritingSubmission {
  user_test_id: number
  exam_id: number
  section_id: number
  question_1_image_1: File   // Task 1 images
  question_1_image_2?: File  // optional
  question_2_image_1: File   // Task 2 images
  question_2_image_2?: File  // optional
  question_2_image_3?: File  // optional
}
```

### Speaking Submission
```typescript
interface SpeakingSubmission {
  user_test_id: number
  exam_id: number
  section_id: number
  question_1_audio: File  // Part 1
  question_2_audio: File  // Part 2
  question_3_audio: File  // Part 3
}
```

### Test Result Response
```typescript
interface TestResult {
  id: number
  status: 'pending' | 'reviewing' | 'checked'
  score: number
  max_score: number
  created_at: string
  reviewed_at?: string
  feedback?: {
    task1?: {
      score: number
      max_score: number
      comment: string
    }
    task2?: {
      score: number
      max_score: number
      comment: string
    }
    // or for speaking:
    comment?: string
  }
  reviewer?: {
    name: string
  }
}
```

---

## 📤 File Upload Validation

### Frontend Validation (Recommended)

```typescript
// composables/useFileValidation.ts
export const useFileValidation = () => {
  const config = useRuntimeConfig()
  
  const validateImage = (file: File): { valid: boolean; error?: string } => {
    // Check file type
    const allowedTypes = config.public.imageTypes.split(',')
    if (!allowedTypes.includes(file.type)) {
      return { valid: false, error: 'Faqat JPG va PNG formatlar qo'llab-quvvatlanadi' }
    }
    
    // Check file size (10 MB)
    if (file.size > config.public.maxImageSize) {
      return { valid: false, error: 'Fayl hajmi 10MB dan oshmasligi kerak' }
    }
    
    return { valid: true }
  }
  
  const validateAudio = (file: File): { valid: boolean; error?: string } => {
    // Check file type
    const allowedTypes = config.public.audioTypes.split(',')
    if (!allowedTypes.includes(file.type)) {
      return { valid: false, error: 'Faqat MP3, WAV, WebM formatlar qo'llab-quvvatlanadi' }
    }
    
    // Check file size (50 MB)
    if (file.size > config.public.maxAudioSize) {
      return { valid: false, error: 'Fayl hajmi 50MB dan oshmasligi kerak' }
    }
    
    return { valid: true }
  }
  
  return {
    validateImage,
    validateAudio
  }
}
```

---

## 🔐 Authentication Flow

### Login & Token Management

```typescript
// composables/useAuth.ts
export const useAuth = () => {
  const config = useRuntimeConfig()
  const accessToken = ref('')
  const refreshToken = ref('')
  
  // Login
  const login = async (phone: string, password: string) => {
    try {
      const response = await $fetch('/api/token/', {
        method: 'POST',
        baseURL: config.public.apiBase,
        body: { phone, password }
      })
      
      // Store tokens
      accessToken.value = response.access
      refreshToken.value = response.refresh
      
      // Save to localStorage
      if (process.client) {
        localStorage.setItem(config.public.tokenKey, response.access)
        localStorage.setItem(config.public.refreshTokenKey, response.refresh)
      }
      
      return { success: true, user: response.user }
    } catch (error) {
      return { success: false, error: 'Login failed' }
    }
  }
  
  // Logout
  const logout = async () => {
    try {
      await $fetch('/api/logout/', {
        method: 'POST',
        baseURL: config.public.apiBase,
        headers: {
          'Authorization': `Bearer ${accessToken.value}`
        }
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear tokens
      accessToken.value = ''
      refreshToken.value = ''
      
      if (process.client) {
        localStorage.removeItem(config.public.tokenKey)
        localStorage.removeItem(config.public.refreshTokenKey)
      }
    }
  }
  
  // Check if authenticated
  const isAuthenticated = computed(() => !!accessToken.value)
  
  // Initialize tokens from localStorage
  onMounted(() => {
    if (process.client) {
      accessToken.value = localStorage.getItem(config.public.tokenKey) || ''
      refreshToken.value = localStorage.getItem(config.public.refreshTokenKey) || ''
    }
  })
  
  return {
    accessToken,
    refreshToken,
    login,
    logout,
    isAuthenticated
  }
}
```

---

## 🎨 UI Components

### File Upload Component Example

```vue
<!-- components/ImageUpload.vue -->
<template>
  <div class="image-upload">
    <input
      type="file"
      @change="handleUpload"
      accept="image/jpeg,image/png"
      multiple
      ref="fileInput"
      class="hidden"
    />
    <button @click="triggerUpload" class="upload-btn">
      <i class="icon-upload"></i>
      {{ label }}
    </button>
    
    <div v-if="previews.length" class="previews">
      <div v-for="(preview, idx) in previews" :key="idx" class="preview-item">
        <img :src="preview" :alt="`Preview ${idx + 1}`" />
        <button @click="removeFile(idx)" class="remove-btn">×</button>
      </div>
    </div>
    
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  label: string
  maxFiles?: number
}>()

const emit = defineEmits<{
  filesSelected: [files: File[]]
}>()

const { validateImage } = useFileValidation()

const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<File[]>([])
const previews = ref<string[]>([])
const error = ref('')

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const selectedFiles = Array.from(target.files || [])
  
  error.value = ''
  
  // Check max files
  if (props.maxFiles && selectedFiles.length > props.maxFiles) {
    error.value = `Maksimal ${props.maxFiles} ta fayl yuklash mumkin`
    return
  }
  
  // Validate each file
  for (const file of selectedFiles) {
    const validation = validateImage(file)
    if (!validation.valid) {
      error.value = validation.error || 'Fayl validatsiyasi muvaffaqiyatsiz'
      return
    }
  }
  
  files.value = selectedFiles
  
  // Create previews
  previews.value = []
  selectedFiles.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      previews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  })
  
  emit('filesSelected', selectedFiles)
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
  previews.value.splice(index, 1)
  emit('filesSelected', files.value)
}
</script>

<style scoped>
.hidden {
  display: none;
}

.upload-btn {
  padding: 1rem 2rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.previews {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.preview-item {
  position: relative;
  width: 200px;
}

.preview-item img {
  width: 100%;
  height: auto;
  border: 2px solid #ddd;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.error {
  color: #dc3545;
  margin-top: 0.5rem;
}
</style>
```

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should fail)
- [ ] Upload writing images (Task 1 & Task 2)
- [ ] Upload speaking audio (Part 1, 2, 3)
- [ ] Check file size validation (> 10MB for images)
- [ ] Check file type validation (non-image/audio files)
- [ ] Check submission status (pending → reviewing → checked)
- [ ] View results after admin review
- [ ] View overall exam result
- [ ] Logout

### Unit Test Example

```typescript
// tests/composables/useWritingSubmit.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useWritingSubmit } from '~/composables/useWritingSubmit'

describe('useWritingSubmit', () => {
  it('should submit writing with valid data', async () => {
    const { submitWriting } = useWritingSubmit()
    
    const mockFile = new File(['content'], 'test.jpg', { type: 'image/jpeg' })
    
    const result = await submitWriting({
      userTestId: 123,
      examId: 456,
      task1Images: [mockFile],
      task2Images: [mockFile]
    })
    
    expect(result.success).toBe(true)
    expect(result.data).toHaveProperty('id')
  })
})
```

---

## 🐛 Common Issues & Solutions

### Issue 1: CORS Error
**Problem:** `Access to fetch has been blocked by CORS policy`

**Solution:**
```python
# Backend: core/settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://turantalim.uz',
]
```

### Issue 2: File Upload Fails (413)
**Problem:** `Request Entity Too Large`

**Solution:**
```nginx
# Nginx configuration
client_max_body_size 100M;
```

### Issue 3: Token Expired
**Problem:** `401 Unauthorized` after some time

**Solution:**
```typescript
// Implement token refresh logic
const refreshAccessToken = async () => {
  const response = await $fetch('/api/token/refresh/', {
    method: 'POST',
    body: { refresh: refreshToken.value }
  })
  accessToken.value = response.access
  localStorage.setItem('access_token', response.access)
}
```

### Issue 4: Image Preview Not Showing
**Problem:** Uploaded images don't show preview

**Solution:**
```typescript
// Use FileReader API
const reader = new FileReader()
reader.onload = (e) => {
  preview.value = e.target?.result as string
}
reader.readAsDataURL(file)
```

---

## 📞 Support & Contact

- **Backend Developer:** backend@turantalim.uz
- **API Documentation:** http://localhost:8000/swagger/
- **Admin Dashboard:** http://localhost:8000/admin-dashboard/
- **GitHub Issues:** [Project Repository]

---

## 📝 Additional Resources

- [Django REST Framework Docs](https://www.django-rest-framework.org/)
- [Nuxt 3 Documentation](https://nuxt.com/docs)
- [File Upload Best Practices](https://web.dev/file-upload/)
- [Audio Recording API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)

---

**Last Updated:** October 8, 2025  
**Version:** 1.0.0  
**Backend:** Django 4.2 + DRF  
**Frontend:** Nuxt 3

---

## ✅ Integration Checklist

Frontend developer uchun tekshirish ro'yxati:

- [ ] Read API_DOCUMENTATION.md
- [ ] Read API_QUICK_REFERENCE.md
- [ ] Import Postman collection
- [ ] Test all endpoints in Postman
- [ ] Setup .env file
- [ ] Configure nuxt.config.ts
- [ ] Implement authentication flow
- [ ] Implement writing submission
- [ ] Implement speaking submission
- [ ] Implement result viewing
- [ ] Add file validation
- [ ] Add error handling
- [ ] Test on development server
- [ ] Test on production server

**Good luck! 🚀**
