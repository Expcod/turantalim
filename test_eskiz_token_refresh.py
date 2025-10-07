#!/usr/bin/env python3
"""
Eskiz token yangilash funksiyasini test qilish uchun script
"""

import os
import sys
import django
import requests

# Django settings ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.develop')
django.setup()

from core.settings import base as settings
from apps.users.utils import refresh_eskiz_token, send_sms_via_eskiz

def test_token_refresh():
    """Eskiz token yangilash funksiyasini test qilish"""
    print("=== Eskiz Token Yangilash Testi ===")
    
    # Joriy token mavjudligini tekshirish
    if not hasattr(settings, 'ESKIZ_TOKEN') or not settings.ESKIZ_TOKEN:
        print("❌ ESKIZ_TOKEN topilmadi!")
        return False
    
    print(f"✅ Joriy token mavjud: {settings.ESKIZ_TOKEN[:20]}...")
    
    # Token yangilashni urinib ko'rish
    print("\n🔄 Token yangilash urinilmoqda...")
    success = refresh_eskiz_token()
    
    if success:
        print(f"✅ Token muvaffaqiyatli yangilandi: {settings.ESKIZ_TOKEN[:20]}...")
        return True
    else:
        print("❌ Token yangilanmadi!")
        return False

def test_sms_sending():
    """SMS yuborish funksiyasini test qilish"""
    print("\n=== SMS Yuborish Testi ===")
    
    # Test telefon raqami (o'zgartiring)
    test_phone = "+998901234567"  # Bu raqamni o'zgartiring
    test_code = "123456"
    
    print(f"📱 Test telefon raqami: {test_phone}")
    print(f"🔢 Test kodi: {test_code}")
    
    # SMS yuborishni urinib ko'rish
    print("\n📤 SMS yuborish urinilmoqda...")
    success = send_sms_via_eskiz(test_phone, test_code)
    
    if success:
        print("✅ SMS muvaffaqiyatli yuborildi!")
        return True
    else:
        print("❌ SMS yuborilmadi!")
        return False

def test_manual_refresh():
    """Qo'lda token yangilash testi"""
    print("\n=== Qo'lda Token Yangilash Testi ===")
    
    if not hasattr(settings, 'ESKIZ_TOKEN') or not settings.ESKIZ_TOKEN:
        print("❌ ESKIZ_TOKEN topilmadi!")
        return False
    
    try:
        url = "https://notify.eskiz.uz/api/auth/refresh"
        headers = {
            "Authorization": f"Bearer {settings.ESKIZ_TOKEN}"
        }
        
        print(f"🌐 URL: {url}")
        print(f"🔑 Authorization: Bearer {settings.ESKIZ_TOKEN[:20]}...")
        
        response = requests.patch(url, headers=headers, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📄 Response data: {response_data}")
            
            new_token = response_data.get('data', {}).get('token')
            if new_token:
                print(f"✅ Yangi token olingan: {new_token[:20]}...")
                return True
            else:
                print("❌ Yangi token topilmadi!")
                return False
        else:
            print(f"❌ Xatolik: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Xatolik: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Eskiz Token Yangilash Testi Boshlanmoqda...\n")
    
    # 1. Qo'lda token yangilash testi
    manual_success = test_manual_refresh()
    
    # 2. Funksiya orqali token yangilash testi
    if manual_success:
        function_success = test_token_refresh()
    else:
        print("❌ Qo'lda token yangilash muvaffaqiyatsiz, funksiya testini o'tkazib yuborilmoqda...")
        function_success = False
    
    # 3. SMS yuborish testi (faqat token yangilash muvaffaqiyatli bo'lsa)
    if function_success:
        sms_success = test_sms_sending()
    else:
        print("❌ Token yangilash muvaffaqiyatsiz, SMS testini o'tkazib yuborilmoqda...")
        sms_success = False
    
    # Natijalarni ko'rsatish
    print("\n" + "="*50)
    print("📊 TEST NATIJALARI:")
    print("="*50)
    print(f"🔧 Qo'lda token yangilash: {'✅ Muvaffaqiyatli' if manual_success else '❌ Muvaffaqiyatsiz'}")
    print(f"⚙️  Funksiya orqali yangilash: {'✅ Muvaffaqiyatli' if function_success else '❌ Muvaffaqiyatsiz'}")
    print(f"📱 SMS yuborish: {'✅ Muvaffaqiyatli' if sms_success else '❌ Muvaffaqiyatsiz'}")
    
    if manual_success and function_success:
        print("\n🎉 Barcha testlar muvaffaqiyatli o'tdi!")
        print("✅ Eskiz token avtomatik yangilash tizimi to'g'ri ishlayapti!")
    else:
        print("\n⚠️  Ba'zi testlar muvaffaqiyatsiz bo'ldi!")
        print("🔍 Xatolik sabablarini tekshiring va qayta urinib ko'ring!")
