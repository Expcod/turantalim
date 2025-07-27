#!/usr/bin/env python
"""
Imtihonlar ma'lumotlarini database'ga qo'shish uchun script
"""
import os
import sys
import django

# Django sozlamalarini yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.main.models import Language
from apps.multilevel.models import Exam

def populate_exams():
    """Turli xil imtihonlarni database'ga qo'shish"""
    
    # Ingliz tili mavjudligini tekshirish
    english, created = Language.objects.get_or_create(name="English")
    if created:
        print("✅ English tili yaratildi")
    else:
        print("ℹ️  English tili allaqachon mavjud")
    
    # Rus tili mavjudligini tekshirish
    russian, created = Language.objects.get_or_create(name="Russian")
    if created:
        print("✅ Russian tili yaratildi")
    else:
        print("ℹ️  Russian tili allaqachon mavjud")
    
    # Imtihonlar ro'yxati
    exams_data = [
        # Ingliz tili imtihonlari
        {
            "language": english,
            "title": "IELTS Preparation Test",
            "description": "IELTS imtihoniga tayyorgarlik uchun multilevel test",
            "level": "multilevel",
            "price": 50000,
            "status": "aktiv"
        },
        {
            "language": english,
            "title": "Elementary English Test",
            "description": "Boshlang'ich daraja ingliz tili testi",
            "level": "a1",
            "price": 25000,
            "status": "aktiv"
        },
        {
            "language": english,
            "title": "Pre-Intermediate English Test",
            "description": "Pre-Intermediate daraja ingliz tili testi",
            "level": "a2",
            "price": 30000,
            "status": "aktiv"
        },
        {
            "language": english,
            "title": "Intermediate English Test",
            "description": "O'rta daraja ingliz tili testi",
            "level": "b1",
            "price": 35000,
            "status": "aktiv"
        },
        {
            "language": english,
            "title": "Upper-Intermediate English Test",
            "description": "Upper-Intermediate daraja ingliz tili testi",
            "level": "b2",
            "price": 40000,
            "status": "aktiv"
        },
        {
            "language": english,
            "title": "Advanced English Test",
            "description": "Yuqori daraja ingliz tili testi",
            "level": "c1",
            "price": 45000,
            "status": "aktiv"
        },
        # Rus tili imtihonlari
        {
            "language": russian,
            "title": "Русский язык - Базовый уровень",
            "description": "Базовый уровень русского языка",
            "level": "a1",
            "price": 20000,
            "status": "aktiv"
        },
        {
            "language": russian,
            "title": "Русский язык - Элементарный уровень",
            "description": "Элементарный уровень русского языка",
            "level": "a2",
            "price": 25000,
            "status": "aktiv"
        },
        {
            "language": russian,
            "title": "Русский язык - Средний уровень",
            "description": "Средний уровень русского языка",
            "level": "b1",
            "price": 30000,
            "status": "aktiv"
        },
        # TYS imtihonlari
        {
            "language": english,
            "title": "TYS English Preparation",
            "description": "TYS imtihoniga ingliz tilidan tayyorgarlik",
            "level": "tys",
            "price": 60000,
            "status": "aktiv"
        },
        # Nofaol imtihon (test uchun)
        {
            "language": english,
            "title": "Inactive Test",
            "description": "Bu test nofaol holatda",
            "level": "b2",
            "price": 35000,
            "status": "off"
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for exam_data in exams_data:
        exam, created = Exam.objects.get_or_create(
            title=exam_data["title"],
            defaults=exam_data
        )
        if created:
            created_count += 1
            print(f"✅ {exam_data['title']} ({exam_data['level']}) yaratildi")
        else:
            existing_count += 1
            print(f"ℹ️  {exam_data['title']} allaqachon mavjud")
    
    print(f"\n📊 Natija:")
    print(f"   - Yangi yaratilgan imtihonlar: {created_count}")
    print(f"   - Mavjud imtihonlar: {existing_count}")
    print(f"   - Jami imtihonlar: {Exam.objects.count()}")
    print(f"   - Aktiv imtihonlar: {Exam.objects.filter(status='aktiv').count()}")

if __name__ == "__main__":
    populate_exams()
