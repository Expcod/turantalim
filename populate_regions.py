#!/usr/bin/env python
"""
O'zbekiston viloyatlari va shaharlarini database'ga qo'shish uchun script
"""
import os
import sys
import django

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.users.models import Country, Region

def populate_regions():
    """O'zbekiston va uning viloyatlarini database'ga qo'shish"""
    
    # O'zbekiston mamlakatini yaratish
    uzbekistan, created = Country.objects.get_or_create(name="O'zbekiston")
    if created:
        print("✅ O'zbekiston mamlakati yaratildi")
    else:
        print("ℹ️  O'zbekiston mamlakati allaqachon mavjud")
    
    # O'zbekiston viloyatlari ro'yxati
    regions_list = [
        "Andijon viloyati",
        "Buxoro viloyati", 
        "Farg'ona viloyati",
        "Jizzax viloyati",
        "Xorazm viloyati",
        "Namangan viloyati",
        "Navoiy viloyati",
        "Qashqadaryo viloyati",
        "Qoraqalpog'iston Respublikasi",
        "Samarqand viloyati",
        "Sirdaryo viloyati",
        "Surxondaryo viloyati",
        "Toshkent viloyati",
        "Toshkent shahri"
    ]
    
    created_count = 0
    existing_count = 0
    
    for region_name in regions_list:
        region, created = Region.objects.get_or_create(
            name=region_name,
            country=uzbekistan
        )
        if created:
            created_count += 1
            print(f"✅ {region_name} yaratildi")
        else:
            existing_count += 1
            print(f"ℹ️  {region_name} allaqachon mavjud")
    
    print(f"\n📊 Natija:")
    print(f"   - Yangi yaratilgan viloyatlar: {created_count}")
    print(f"   - Mavjud viloyatlar: {existing_count}")
    print(f"   - Jami viloyatlar: {Region.objects.count()}")

if __name__ == "__main__":
    populate_regions()
