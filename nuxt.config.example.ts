// Nuxt 3 Configuration Example for Turantalim Frontend
// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  devtools: { enabled: true },
  
  // Runtime config for environment variables
  runtimeConfig: {
    // Private keys (only available on server-side)
    // apiSecret: process.env.API_SECRET,
    
    // Public keys (exposed to client-side)
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
      mediaUrl: process.env.NUXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media',
      tokenKey: process.env.NUXT_PUBLIC_TOKEN_KEY || 'turantalim_access_token',
      refreshTokenKey: process.env.NUXT_PUBLIC_REFRESH_TOKEN_KEY || 'turantalim_refresh_token',
      
      // File upload limits
      maxImageSize: parseInt(process.env.NUXT_PUBLIC_MAX_IMAGE_SIZE || '10485760'),
      maxAudioSize: parseInt(process.env.NUXT_PUBLIC_MAX_AUDIO_SIZE || '52428800'),
      
      // Accepted file types
      imageTypes: process.env.NUXT_PUBLIC_IMAGE_TYPES || 'image/jpeg,image/png',
      audioTypes: process.env.NUXT_PUBLIC_AUDIO_TYPES || 'audio/mpeg,audio/wav,audio/webm,audio/ogg',
      
      // Exam settings
      writingTimeLimit: parseInt(process.env.NUXT_PUBLIC_WRITING_TIME_LIMIT || '3600'),
      speakingTimeLimit: parseInt(process.env.NUXT_PUBLIC_SPEAKING_TIME_LIMIT || '900'),
      
      // Audio recording settings
      speakingPart1Duration: parseInt(process.env.NUXT_PUBLIC_SPEAKING_PART1_DURATION || '180'),
      speakingPart2Duration: parseInt(process.env.NUXT_PUBLIC_SPEAKING_PART2_DURATION || '240'),
      speakingPart3Duration: parseInt(process.env.NUXT_PUBLIC_SPEAKING_PART3_DURATION || '300'),
    }
  },
  
  // App configuration
  app: {
    head: {
      title: 'Turantalim - Online Exam System',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Turantalim online exam system for CEFR and TYS tests' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  },
  
  // CSS configuration
  css: [
    '~/assets/css/main.css',
  ],
  
  // Modules
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  
  // Auto-import components
  components: true,
  
  // Build configuration
  build: {
    transpile: []
  },
  
  // Development server configuration
  devServer: {
    port: 3000,
    host: '0.0.0.0'
  },
  
  // Experimental features
  experimental: {
    payloadExtraction: false
  }
})
