# Turantalim API Documentation
## Frontend (Nuxt3) → Backend Integration

---

---



### Base URL
```
Production: https://api.turantalim.uz
```


---

## ✍️ Writing Section APIs

### 1. Submit Writing Answers (Image Upload)

**Endpoint:** `POST /multilevel/testcheck/writing/`

**Description:** Talaba Writing bo'limi uchun javoblarini (rasmlar) yuklaydi.

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body (FormData):**
```javascript
{
  user_test_id: 123,           // Integer (UserTest ID)
  exam_id: 456,                // Integer (Exam ID)
  section_type: "writing",     // String
  
  // Task 1 (Letter) - rasmlar
  task1_image1: File,          // File object (image/jpeg, image/png)
  task1_image2: File,          // File object (optional)
  
  // Task 2 (Essay) - rasmlar
  task2_image1: File,          // File object (image/jpeg, image/png)
  task2_image2: File,          // File object (optional)
  task2_image3: File,          // File object (optional)
}
```

**Response (Success 201):**
```json
{
  "id": 789,
  "user_test_id": 123,
  "exam_id": 456,
  "section_type": "writing",
  "status": "pending",
  "submitted_at": "2025-10-08T12:30:45.123456Z",
  "questions": [
    {
      "question_number": 1,
      "question_type": "letter",
      "images": [
        {
          "id": 1,
          "url": "/media/writing/task1/image1.jpg",
          "uploaded_at": "2025-10-08T12:30:45Z"
        }
      ]
    },
    {
      "question_number": 2,
      "question_type": "essay",
      "images": [
        {
          "id": 2,
          "url": "/media/writing/task2/image1.jpg",
          "uploaded_at": "2025-10-08T12:30:45Z"
        }
      ]
    }
  ]
}
```

**Response (Error 400):**
```json
{
  "error": "Missing required fields",
  "details": {
    "user_test_id": ["This field is required."],
    "task1_image1": ["No file was submitted."]
  }
}
```

---

### 2. Get Writing Result (Check Status)

**Endpoint:** `GET /multilevel/test-result/{test_result_id}/`

**Description:** Talaba o'z Writing natijasini ko'rish uchun.

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (Success 200):**
```json
{
  "id": 789,
  "user_test_id": 123,
  "section_type": "writing",
  "status": "checked",
  "submitted_at": "2025-10-08T12:30:45Z",
  "reviewed_at": "2025-10-08T15:45:30Z",
  "score": {
    "task1_score": 20.5,
    "task2_score": 45.0,
    "total_score": 65.5,
    "max_score": 75
  },
  "feedback": {
    "task1_comment": "Good structure, but grammar needs improvement.",
    "task2_comment": "Excellent essay with clear arguments."
  },
  "reviewer": {
    "name": "Admin User",
    "reviewed_at": "2025-10-08T15:45:30Z"
  }
}
```

---

## 🎤 Speaking Section APIs

### 1. Submit Speaking Answers (Audio Upload)

**Endpoint:** `POST /multilevel/testcheck/speaking/`

**Description:** Talaba Speaking bo'limi uchun javoblarini (audio fayllar) yuklaydi.

**Headers:**
```
Content-Type: multipart/form-data
Authorization: Token YOUR_TOKEN
```

**Request Body (FormData):**
```javascript
{
  test_result_id: 123,                    // Integer (TestResult ID) - optional
  
  // Speaking test - 8 ta savol uchun audio fayllar
  answers[0][question]: 101,              // Integer (Question ID)
  answers[0][speaking_audio]: File,       // Audio file (Question 1)
  
  answers[1][question]: 102,
  answers[1][speaking_audio]: File,       // Audio file (Question 2)
  
  answers[2][question]: 103,
  answers[2][speaking_audio]: File,       // Audio file (Question 3)
  
  answers[3][question]: 104,
  answers[3][speaking_audio]: File,       // Audio file (Question 4)
  
  answers[4][question]: 105,
  answers[4][speaking_audio]: File,       // Audio file (Question 5)
  
  answers[5][question]: 106,
  answers[5][speaking_audio]: File,       // Audio file (Question 6)
  
  answers[6][question]: 107,
  answers[6][speaking_audio]: File,       // Audio file (Question 7)
  
  answers[7][question]: 108,
  answers[7][speaking_audio]: File,       // Audio file (Question 8)
}
```

**Supported Audio Formats:**
- MP3 (audio/mpeg, audio/mp3)
- WAV (audio/wav, audio/wave)
- WEBM (audio/webm, video/webm)
- M4A (audio/aac, audio/x-m4a)
- OGG (audio/ogg, audio/vorbis)
- FLAC (audio/flac)
- MP4 (audio/mp4, video/mp4)

**Max File Size:** 25 MB per audio file

**Response (Success 201):**
```json
{
  "test_result_id": 390,
  "status": "pending",
  "message": "Speaking test muvaffaqiyatli yuklandi. Admin tomonidan tekshiriladi.",
  "manual_review_id": 123,
  "audios_count": 8
}
```

**Tushuntirish:**
- `test_result_id`: Test natijasi ID si
- `status`: "pending" - admin tekshirishi kutilmoqda
- `message`: Muvaffaqiyat xabari
- `manual_review_id`: Manual review record ID si
- `audios_count`: Yuklangan audio fayllar soni (8 ta)

**Response (Error 400):**
```json
{
  "error": "Ma'lumotlar noto'g'ri formatda yuborilgan: Kamida bitta javob yuborilishi kerak"
}
```

**Possible Errors:**
- `Content-Type multipart/form-data bo'lishi kerak` - Content-Type noto'g'ri
- `Kamida bitta javob yuborilishi kerak` - Hech qanday audio yuborilmagan
- `Question {id} not found` - Savol topilmadi
- `TestResult yaratishda xatolik` - TestResult yaratilmadi

---

### 2. Get Speaking Result (Check Status)

**Endpoint:** `GET /multilevel/test-result/{test_result_id}/`

**Description:** Talaba o'z Speaking natijasini ko'rish uchun.

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (Success 200):**
```json
{
  "id": 790,
  "user_test_id": 123,
  "section_type": "speaking",
  "status": "checked",
  "submitted_at": "2025-10-08T12:30:45Z",
  "reviewed_at": "2025-10-08T16:20:15Z",
  "score": {
    "total_score": 70,
    "max_score": 75
  },
  "feedback": {
    "comment": "Good pronunciation and fluency. Grammar needs some work."
  },
  "reviewer": {
    "name": "Admin User",
    "reviewed_at": "2025-10-08T16:20:15Z"
  }
}
```

---

## 📤 File Upload

### Accepted File Types

**Images (Writing):**
- `image/jpeg` (.jpg, .jpeg)
- `image/png` (.png)
- Maximum size: 10 MB per image
- Recommended: 1920x1080px or lower

**Audio (Speaking):**
- `audio/mpeg` (.mp3)
- `audio/wav` (.wav)
- `audio/webm` (.webm)
- `audio/ogg` (.ogg)
- Maximum size: 50 MB per audio
- Recommended: 128kbps or higher quality

### File Naming Convention
Frontend'dan yuborish vaqtida fayllarni quyidagicha nomlanganizni tavsiya qilamiz:
- Writing: `writing_task1_page1.jpg`, `writing_task2_page1.jpg`
- Speaking: `speaking_part1.mp3`, `speaking_part2.mp3`, `speaking_part3.mp3`

---

## 📊 Response Codes

| Status Code | Meaning | Description |
|-------------|---------|-------------|
| 200 | OK | Request muvaffaqiyatli bajarildi |
| 201 | Created | Yangi resurs yaratildi (file uploaded) |
| 400 | Bad Request | Request'da xato bor (validation error) |
| 401 | Unauthorized | Authentication kerak |
| 403 | Forbidden | Ruxsat yo'q |
| 404 | Not Found | Resurs topilmadi |
| 413 | Payload Too Large | Fayl hajmi juda katta |
| 415 | Unsupported Media Type | Fayl formati qo'llab-quvvatlanmaydi |
| 500 | Internal Server Error | Server xatosi |

---

## 💻 Example Code (Nuxt3)

### 1. Writing Submit (Composable)

`composables/useWritingSubmit.ts`:

```typescript
export const useWritingSubmit = () => {
  const config = useRuntimeConfig()
  const { $api } = useNuxtApp()

  const submitWriting = async (data: {
    userTestId: number
    examId: number
    task1Images: File[]
    task2Images: File[]
  }) => {
    try {
      const formData = new FormData()
      
      // Add metadata
      formData.append('user_test_id', data.userTestId.toString())
      formData.append('exam_id', data.examId.toString())
      formData.append('section_type', 'writing')
      
      // Add Task 1 images
      data.task1Images.forEach((file, index) => {
        formData.append(`task1_image${index + 1}`, file)
      })
      
      // Add Task 2 images
      data.task2Images.forEach((file, index) => {
        formData.append(`task2_image${index + 1}`, file)
      })
      
      const response = await $fetch('/multilevel/testcheck/writing/', {
        method: 'POST',
        baseURL: config.public.apiBase,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      })
      
      return { success: true, data: response }
    } catch (error: any) {
      console.error('Writing submit error:', error)
      return { 
        success: false, 
        error: error.data?.error || 'Xatolik yuz berdi' 
      }
    }
  }
  
  return { submitWriting }
}
```

### 2. Writing Submit Component

`pages/exam/writing.vue`:

```vue
<template>
  <div class="writing-exam">
    <h2>Writing Bo'limi</h2>
    
    <!-- Task 1 (Letter) -->
    <div class="task-section">
      <h3>Task 1: Letter (33%)</h3>
      <p>Maksimal ball: 24.75</p>
      
      <div class="upload-area">
        <label>Javobingiz rasmini yuklang:</label>
        <input 
          type="file" 
          @change="handleTask1Upload"
          accept="image/jpeg,image/png"
          multiple
          ref="task1Input"
        />
        <div v-if="task1Images.length" class="preview">
          <img 
            v-for="(img, idx) in task1Previews" 
            :key="idx"
            :src="img" 
            alt="Task 1 Preview"
          />
        </div>
      </div>
    </div>
    
    <!-- Task 2 (Essay) -->
    <div class="task-section">
      <h3>Task 2: Essay (67%)</h3>
      <p>Maksimal ball: 50.25</p>
      
      <div class="upload-area">
        <label>Javobingiz rasmini yuklang:</label>
        <input 
          type="file" 
          @change="handleTask2Upload"
          accept="image/jpeg,image/png"
          multiple
          ref="task2Input"
        />
        <div v-if="task2Images.length" class="preview">
          <img 
            v-for="(img, idx) in task2Previews" 
            :key="idx"
            :src="img" 
            alt="Task 2 Preview"
          />
        </div>
      </div>
    </div>
    
    <!-- Submit Button -->
    <button 
      @click="submitExam"
      :disabled="!canSubmit || isSubmitting"
      class="btn-submit"
    >
      {{ isSubmitting ? 'Yuklanmoqda...' : 'Topshirish' }}
    </button>
    
    <!-- Error Message -->
    <div v-if="errorMessage" class="error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { submitWriting } = useWritingSubmit()

// Data
const task1Images = ref<File[]>([])
const task2Images = ref<File[]>([])
const task1Previews = ref<string[]>([])
const task2Previews = ref<string[]>([])
const isSubmitting = ref(false)
const errorMessage = ref('')

// Computed
const canSubmit = computed(() => {
  return task1Images.value.length > 0 && task2Images.value.length > 0
})

// Methods
const handleTask1Upload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  
  // Validate file size (max 10MB per file)
  const invalidFiles = files.filter(f => f.size > 10 * 1024 * 1024)
  if (invalidFiles.length) {
    errorMessage.value = 'Fayl hajmi 10MB dan oshmasligi kerak'
    return
  }
  
  task1Images.value = files
  
  // Create previews
  task1Previews.value = []
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      task1Previews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  })
}

const handleTask2Upload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  
  // Validate file size (max 10MB per file)
  const invalidFiles = files.filter(f => f.size > 10 * 1024 * 1024)
  if (invalidFiles.length) {
    errorMessage.value = 'Fayl hajmi 10MB dan oshmasligi kerak'
    return
  }
  
  task2Images.value = files
  
  // Create previews
  task2Previews.value = []
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      task2Previews.value.push(e.target?.result as string)
    }
    reader.readAsDataURL(file)
  })
}

const submitExam = async () => {
  if (!canSubmit.value) {
    errorMessage.value = 'Iltimos, barcha topshiriqlar uchun rasm yuklang'
    return
  }
  
  isSubmitting.value = true
  errorMessage.value = ''
  
  const result = await submitWriting({
    userTestId: Number(route.params.userTestId),
    examId: Number(route.params.examId),
    task1Images: task1Images.value,
    task2Images: task2Images.value
  })
  
  isSubmitting.value = false
  
  if (result.success) {
    // Success - redirect to results page
    router.push(`/exam/result/${result.data.id}`)
  } else {
    errorMessage.value = result.error
  }
}
</script>

<style scoped>
.writing-exam {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.task-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.upload-area {
  margin-top: 1rem;
}

.preview {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.preview img {
  width: 200px;
  height: auto;
  border: 2px solid #ddd;
  border-radius: 4px;
}

.btn-submit {
  padding: 1rem 2rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
}

.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 1rem;
  background: #fee;
  color: #c00;
  border-radius: 4px;
}
</style>
```

### 3. Speaking Submit (Composable)

`composables/useSpeakingSubmit.ts`:

```typescript
export const useSpeakingSubmit = () => {
  const config = useRuntimeConfig()
  const { $api } = useNuxtApp()

  const submitSpeaking = async (data: {
    userTestId: number
    examId: number
    part1Audio: File
    part2Audio: File
    part3Audio: File
  }) => {
    try {
      const formData = new FormData()
      
      // Add metadata
      formData.append('user_test_id', data.userTestId.toString())
      formData.append('exam_id', data.examId.toString())
      formData.append('section_type', 'speaking')
      
      // Add audio files
      formData.append('part1_audio', data.part1Audio)
      formData.append('part2_audio', data.part2Audio)
      formData.append('part3_audio', data.part3Audio)
      
      const response = await $fetch('/multilevel/testcheck/speaking/', {
        method: 'POST',
        baseURL: config.public.apiBase,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      })
      
      return { success: true, data: response }
    } catch (error: any) {
      console.error('Speaking submit error:', error)
      return { 
        success: false, 
        error: error.data?.error || 'Xatolik yuz berdi' 
      }
    }
  }
  
  return { submitSpeaking }
}
```

### 4. Speaking Submit Component

`pages/exam/speaking.vue`:

```vue
<template>
  <div class="speaking-exam">
    <h2>Speaking Bo'limi</h2>
    <p>Maksimal ball: 75</p>
    
    <!-- Part 1 -->
    <div class="part-section">
      <h3>Part 1: Introduction & Interview</h3>
      <AudioRecorder 
        @recorded="handlePart1Record"
        :maxDuration="180"
      />
    </div>
    
    <!-- Part 2 -->
    <div class="part-section">
      <h3>Part 2: Long Turn</h3>
      <AudioRecorder 
        @recorded="handlePart2Record"
        :maxDuration="240"
      />
    </div>
    
    <!-- Part 3 -->
    <div class="part-section">
      <h3>Part 3: Discussion</h3>
      <AudioRecorder 
        @recorded="handlePart3Record"
        :maxDuration="300"
      />
    </div>
    
    <!-- Submit Button -->
    <button 
      @click="submitExam"
      :disabled="!canSubmit || isSubmitting"
      class="btn-submit"
    >
      {{ isSubmitting ? 'Yuklanmoqda...' : 'Topshirish' }}
    </button>
    
    <!-- Error Message -->
    <div v-if="errorMessage" class="error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { submitSpeaking } = useSpeakingSubmit()

// Data
const part1Audio = ref<File | null>(null)
const part2Audio = ref<File | null>(null)
const part3Audio = ref<File | null>(null)
const isSubmitting = ref(false)
const errorMessage = ref('')

// Computed
const canSubmit = computed(() => {
  return part1Audio.value && part2Audio.value && part3Audio.value
})

// Methods
const handlePart1Record = (file: File) => {
  // Validate file size (max 50MB)
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = 'Audio fayl hajmi 50MB dan oshmasligi kerak'
    return
  }
  part1Audio.value = file
}

const handlePart2Record = (file: File) => {
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = 'Audio fayl hajmi 50MB dan oshmasligi kerak'
    return
  }
  part2Audio.value = file
}

const handlePart3Record = (file: File) => {
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = 'Audio fayl hajmi 50MB dan oshmasligi kerak'
    return
  }
  part3Audio.value = file
}

const submitExam = async () => {
  if (!canSubmit.value) {
    errorMessage.value = 'Iltimos, barcha qismlar uchun audio yozing'
    return
  }
  
  isSubmitting.value = true
  errorMessage.value = ''
  
  const result = await submitSpeaking({
    userTestId: Number(route.params.userTestId),
    examId: Number(route.params.examId),
    part1Audio: part1Audio.value!,
    part2Audio: part2Audio.value!,
    part3Audio: part3Audio.value!
  })
  
  isSubmitting.value = false
  
  if (result.success) {
    // Success - redirect to results page
    router.push(`/exam/result/${result.data.id}`)
  } else {
    errorMessage.value = result.error
  }
}
</script>

<style scoped>
.speaking-exam {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.part-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.btn-submit {
  padding: 1rem 2rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
}

.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  margin-top: 1rem;
  padding: 1rem;
  background: #fee;
  color: #c00;
  border-radius: 4px;
}
</style>
```

### 5. Audio Recorder Component (Bonus)

`components/AudioRecorder.vue`:

```vue
<template>
  <div class="audio-recorder">
    <div v-if="!isRecording && !audioURL" class="controls">
      <button @click="startRecording" class="btn-record">
        <i class="fas fa-microphone"></i> Yozishni boshlash
      </button>
    </div>
    
    <div v-if="isRecording" class="recording">
      <div class="recording-indicator">
        <span class="pulse"></span>
        <span>Yozilmoqda... {{ formattedTime }}</span>
      </div>
      <button @click="stopRecording" class="btn-stop">
        <i class="fas fa-stop"></i> To'xtatish
      </button>
    </div>
    
    <div v-if="audioURL" class="preview">
      <audio :src="audioURL" controls></audio>
      <button @click="reset" class="btn-reset">
        <i class="fas fa-redo"></i> Qayta yozish
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  maxDuration?: number // seconds
}>()

const emit = defineEmits<{
  recorded: [file: File]
}>()

// Data
const isRecording = ref(false)
const audioURL = ref('')
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const recordingTime = ref(0)
const timer = ref<NodeJS.Timeout | null>(null)

// Computed
const formattedTime = computed(() => {
  const minutes = Math.floor(recordingTime.value / 60)
  const seconds = recordingTime.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

// Methods
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream, {
      mimeType: 'audio/webm'
    })
    
    audioChunks.value = []
    
    mediaRecorder.value.addEventListener('dataavailable', (event) => {
      audioChunks.value.push(event.data)
    })
    
    mediaRecorder.value.addEventListener('stop', () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      audioURL.value = URL.createObjectURL(audioBlob)
      
      // Create file
      const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, {
        type: 'audio/webm'
      })
      
      emit('recorded', audioFile)
      
      // Stop all tracks
      stream.getTracks().forEach(track => track.stop())
    })
    
    mediaRecorder.value.start()
    isRecording.value = true
    recordingTime.value = 0
    
    // Start timer
    timer.value = setInterval(() => {
      recordingTime.value++
      
      // Auto-stop if max duration reached
      if (props.maxDuration && recordingTime.value >= props.maxDuration) {
        stopRecording()
      }
    }, 1000)
    
  } catch (error) {
    console.error('Error starting recording:', error)
    alert('Mikrofonga ruxsat berilmadi')
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false
    
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
  }
}

const reset = () => {
  audioURL.value = ''
  recordingTime.value = 0
  audioChunks.value = []
}

// Cleanup
onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
  if (audioURL.value) {
    URL.revokeObjectURL(audioURL.value)
  }
})
</script>

<style scoped>
.audio-recorder {
  padding: 1rem;
  border: 2px dashed #ddd;
  border-radius: 8px;
  text-align: center;
}

.btn-record, .btn-stop, .btn-reset {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-record {
  background: #28a745;
  color: white;
}

.btn-stop {
  background: #dc3545;
  color: white;
}

.btn-reset {
  background: #6c757d;
  color: white;
  margin-top: 1rem;
}

.recording-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.pulse {
  width: 12px;
  height: 12px;
  background: #dc3545;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.preview audio {
  width: 100%;
  margin-bottom: 1rem;
}
</style>
```

---

## 🔄 Data Flow

```
Frontend (Nuxt3)                    Backend (Django)              Admin Dashboard
     │                                   │                              │
     ├─── Submit Writing ─────────────> │                              │
     │    (POST https://api.turantalim.uz/multilevel/testcheck/writing)                         │
     │                                   │                              │
     │    <──── 201 Created ────────────┤                              │
     │    (test_result_id: 789)         │                              │
     │                                   │                              │
     │                                   ├───> Save to Database         │
     │                                   │     status: "pending"        │
     │                                   │                              │
     │                                   │     <──── Admin sees ────────┤
     │                                   │           new submission     │
     │                                   │                              │
     │                                   │     ───── Admin grades ─────>│
     │                                   │                              │
     │                                   │     <──── Status: checked ───┤
     │    <──── Get Result ─────────────┤     (score, feedback)        │
     │    (GET https://api.turantalim.uz/multilevel/test-result/789)                            │
     │                                   │                              │
     └─── Display score & feedback      │                              │
```

---

## ⚠️ Important Notes

### 1. File Size Limits
- **Images**: Max 10 MB per file
- **Audio**: Max 50 MB per file
- Backend'da bu limitlar enforce qilingan

### 2. File Format Validation
- Backend faqat ruxsat berilgan format'larni qabul qiladi
- Frontend'da ham validate qilish tavsiya etiladi

### 3. Authentication
- Har bir request'da valid Bearer token yuborilishi kerak
- Token expire bo'lsa 401 error qaytadi

### 4. CORS Configuration
- Backend'da CORS sozlanmalari to'g'ri configured
- Development uchun `localhost:3000` allowed
- Production uchun actual domain qo'shilishi kerak

### 5. Media Files Access
- Uploaded files `/media/` URL pattern orqali accessible
- Full URL: `https://api.turantalim.uz/media/writing/task1/image.jpg`

---

**Last Updated:** October 8, 2025
**API Version:** v1.0
**Backend Framework:** Django 4.2 + DRF
**Frontend Framework:** Nuxt3
