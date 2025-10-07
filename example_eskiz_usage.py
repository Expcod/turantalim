#!/usr/bin/env python3
"""
Eskiz token avtomatik yangilash funksiyasini ishlatish misoli
"""

import os
import sys
import django

# Django settings ni sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.develop')
django.setup()

from apps.users.utils import send_sms_via_eskiz, refresh_eskiz_token
from core.settings import base as settings

def example_sms_sending():
    """SMS yuborish misoli - token avtomatik yangilanadi"""
    print("=== SMS Yuborish Misoli ===")
    
    # Test ma'lumotlari
    phone_number = "+998901234567"  # O'zgartiring
    verification_code = "123456"
    
    print(f"📱 Telefon raqami: {phone_number}")
    print(f"🔢 Tasdiqlash kodi: {verification_code}")
    
    # SMS yuborish - token avtomatik yangilanadi
    print("\n📤 SMS yuborilmoqda...")
    success = send_sms_via_eskiz(phone_number, verification_code)
    
    if success:
        print("✅ SMS muvaffaqiyatli yuborildi!")
        print("💡 Eslatma: Agar token eskirgan bo'lsa, avtomatik yangilandi!")
    else:
        print("❌ SMS yuborilmadi!")
        print("🔍 Xatolik sabablarini tekshiring!")

def example_manual_token_refresh():
    """Qo'lda token yangilash misoli"""
    print("\n=== Qo'lda Token Yangilash Misoli ===")
    
    # Joriy token ko'rsatish
    current_token = getattr(settings, 'ESKIZ_TOKEN', 'NOT_SET')
    print(f"🔑 Joriy token: {current_token[:20]}..." if current_token != 'NOT_SET' else "🔑 Joriy token: NOT_SET")
    
    # Token yangilash
    print("\n🔄 Token yangilash urinilmoqda...")
    success = refresh_eskiz_token()
    
    if success:
        new_token = getattr(settings, 'ESKIZ_TOKEN', 'NOT_SET')
        print(f"✅ Token yangilandi: {new_token[:20]}...")
    else:
        print("❌ Token yangilanmadi!")

def example_error_handling():
    """Xatoliklar bilan ishlash misoli"""
    print("\n=== Xatoliklar Bilan Ishlash Misoli ===")
    
    # Noto'g'ri telefon raqami bilan urinish
    invalid_phone = "invalid_phone"
    code = "123456"
    
    print(f"📱 Noto'g'ri telefon raqami: {invalid_phone}")
    print("📤 SMS yuborish urinilmoqda...")
    
    success = send_sms_via_eskiz(invalid_phone, code)
    
    if not success:
        print("❌ Kutilganidek xatolik yuz berdi!")
        print("✅ Xatoliklar bilan ishlash to'g'ri ishlayapti!")

def main():
    """Asosiy funksiya"""
    print("🚀 Eskiz Token Avtomatik Yangilash Tizimi Misollari")
    print("=" * 60)
    
    # 1. Qo'lda token yangilash
    example_manual_token_refresh()
    
    # 2. SMS yuborish (avtomatik token yangilash bilan)
    example_sms_sending()
    
    # 3. Xatoliklar bilan ishlash
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 Barcha misollar yakunlandi!")
    print("\n💡 Foydalanish uchun:")
    print("   - Telefon raqamini o'zgartiring")
    print("   - ESKIZ_TOKEN ni to'g'ri sozlang")
    print("   - Network ulanishini tekshiring")

if __name__ == "__main__":
    main()
