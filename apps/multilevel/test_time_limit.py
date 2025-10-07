"""
Vaqt chegarasi tizimini test qilish uchun test fayli
"""
import time
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Language, Exam, Section, Test, Question, Option, UserTest, TestResult
from .tasks import auto_complete_test, check_expired_tests, schedule_test_completion
from .utils import check_test_time_limit, schedule_test_time_limit

User = get_user_model()

class TimeLimitSystemTestCase(TestCase):
    def setUp(self):
        """Test uchun ma'lumotlarni tayyorlash"""
        # Foydalanuvchi yaratish
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Til yaratish
        self.language = Language.objects.create(name='English')
        
        # Imtihon yaratish
        self.exam = Exam.objects.create(
            language=self.language,
            title='Test Exam',
            level='multilevel',
            status='active'
        )
        
        # Section yaratish (1 daqiqa vaqt bilan)
        self.section = Section.objects.create(
            exam=self.exam,
            type='listening',
            title='Test Section',
            duration=1  # 1 daqiqa
        )
        
        # Test yaratish
        self.test = Test.objects.create(
            section=self.section,
            title='Test Question',
            text='Test question text'
        )
        
        # Savol yaratish
        self.question = Question.objects.create(
            test=self.test,
            text='Test question?',
            has_options=True
        )
        
        # Variantlar yaratish
        self.correct_option = Option.objects.create(
            question=self.question,
            text='Correct answer',
            is_correct=True
        )
        self.wrong_option = Option.objects.create(
            question=self.question,
            text='Wrong answer',
            is_correct=False
        )
        
        # UserTest yaratish
        self.user_test = UserTest.objects.create(
            user=self.user,
            language=self.language,
            exam=self.exam,
            status='started'
        )
        
        # TestResult yaratish
        self.test_result = TestResult.objects.create(
            user_test=self.user_test,
            section=self.section,
            status='started',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(minutes=1)
        )
        
        # API client yaratish
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_check_test_time_limit_not_expired(self):
        """Vaqt chegarasi tugaganini tekshirish - vaqt tugagan emas"""
        result = check_test_time_limit(self.test_result)
        self.assertFalse(result)
        self.assertEqual(self.test_result.status, 'started')

    def test_check_test_time_limit_expired(self):
        """Vaqt chegarasi tugaganini tekshirish - vaqt tugagan"""
        # Vaqtni o'tmishga o'tkazish
        self.test_result.end_time = timezone.now() - timedelta(minutes=1)
        self.test_result.save()
        
        result = check_test_time_limit(self.test_result)
        self.assertTrue(result)
        
        # TestResult ni yangilash
        self.test_result.refresh_from_db()
        self.assertEqual(self.test_result.status, 'completed')

    def test_auto_complete_test_task(self):
        """Avtomatik test yakunlash task'ini test qilish"""
        result = auto_complete_test(self.test_result.id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['test_result_id'], self.test_result.id)
        
        # TestResult ni yangilash
        self.test_result.refresh_from_db()
        self.assertEqual(self.test_result.status, 'completed')

    def test_schedule_test_completion_task(self):
        """Test uchun vaqt chegarasi rejalashtirish task'ini test qilish"""
        result = schedule_test_completion(self.test_result.id, 1)
        
        # Task muvaffaqiyatli rejalashtirilganini tekshirish
        self.assertIsNotNone(result)

    def test_check_expired_tests_task(self):
        """Muntazam tekshirish task'ini test qilish"""
        # Vaqtni o'tmishga o'tkazish
        self.test_result.end_time = timezone.now() - timedelta(minutes=1)
        self.test_result.save()
        
        result = check_expired_tests()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['completed_count'], 1)
        
        # TestResult ni yangilash
        self.test_result.refresh_from_db()
        self.assertEqual(self.test_result.status, 'completed')

    def test_time_info_api(self):
        """Vaqt ma'lumotlari API'sini test qilish"""
        url = f'/api/multilevel/test/time-info/?test_result_id={self.test_result.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['test_result_id'], self.test_result.id)
        self.assertEqual(data['section_title'], self.section.title)
        self.assertEqual(data['section_type'], self.section.type)
        self.assertEqual(data['duration_minutes'], self.section.duration)
        self.assertFalse(data['is_expired'])
        self.assertEqual(data['status'], 'active')

    def test_time_info_api_expired(self):
        """Vaqt ma'lumotlari API'sini test qilish - vaqt tugagan"""
        # Vaqtni o'tmishga o'tkazish
        self.test_result.end_time = timezone.now() - timedelta(minutes=1)
        self.test_result.save()
        
        url = f'/api/multilevel/test/time-info/?test_result_id={self.test_result.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['is_expired'])
        self.assertEqual(data['status'], 'expired')
        self.assertEqual(data['remaining_minutes'], 0)
        self.assertEqual(data['remaining_seconds'], 0)

    def test_listening_check_with_expired_time(self):
        """Listening test tekshirish - vaqt tugagan"""
        # Vaqtni o'tmishga o'tkazish
        self.test_result.end_time = timezone.now() - timedelta(minutes=1)
        self.test_result.save()
        
        url = '/api/multilevel/testcheck/listening/'
        data = {
            'test_result_id': self.test_result.id,
            'answers': [
                {
                    'question': self.question.id,
                    'user_option': self.correct_option.id
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Test vaqti tugagan', response.json()['error'])

    def test_reading_check_with_expired_time(self):
        """Reading test tekshirish - vaqt tugagan"""
        # Vaqtni o'tmishga o'tkazish
        self.test_result.end_time = timezone.now() - timedelta(minutes=1)
        self.test_result.save()
        
        url = '/api/multilevel/testcheck/reading/'
        data = {
            'test_result_id': self.test_result.id,
            'answers': [
                {
                    'question': self.question.id,
                    'user_option': self.correct_option.id
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Test vaqti tugagan', response.json()['error'])

    def test_schedule_test_time_limit_utility(self):
        """Vaqt chegarasi rejalashtirish utility funksiyasini test qilish"""
        # Bu funksiya celery task'ini chaqiradi, shuning uchun faqat xatolik yo'qligini tekshiramiz
        try:
            schedule_test_time_limit(self.test_result)
            # Agar xatolik bo'lmasa, test muvaffaqiyatli
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"schedule_test_time_limit xatolik qaytardi: {e}")

    def test_user_test_completion_when_all_tests_completed(self):
        """Barcha testlar tugaganda UserTest yakunlanishini test qilish"""
        # TestResult ni completed ga o'tkazish
        self.test_result.status = 'completed'
        self.test_result.save()
        
        # UserTest ni yangilash
        self.user_test.refresh_from_db()
        
        # Faqat bitta section bo'lgani uchun UserTest ham completed bo'lishi kerak
        self.assertEqual(self.user_test.status, 'completed')

    def test_multiple_sections_time_limit(self):
        """Bir nechta section'lar uchun vaqt chegarasi"""
        # Ikkinchi section yaratish
        section2 = Section.objects.create(
            exam=self.exam,
            type='reading',
            title='Reading Section',
            duration=2
        )
        
        # Ikkinchi TestResult yaratish
        test_result2 = TestResult.objects.create(
            user_test=self.user_test,
            section=section2,
            status='started',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(minutes=2)
        )
        
        # Birinchi testni tugatish
        self.test_result.status = 'completed'
        self.test_result.save()
        
        # UserTest hali started bo'lishi kerak (chunki ikkinchi test faol)
        self.user_test.refresh_from_db()
        self.assertEqual(self.user_test.status, 'started')
        
        # Ikkinchi testni ham tugatish
        test_result2.status = 'completed'
        test_result2.save()
        
        # Endi UserTest completed bo'lishi kerak
        self.user_test.refresh_from_db()
        self.assertEqual(self.user_test.status, 'completed')
