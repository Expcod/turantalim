"""
Multilevel va TYS imtihon natijalari API test fayli
Bu fayl API funksionalligini tekshirish uchun mo'ljallangan
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Exam, Section, UserTest, TestResult, Language
from .multilevel_score import get_level_from_score

User = get_user_model()


class MultilevelTysExamResultsAPITest(APITestCase):
    """Multilevel va TYS imtihon natijalari API testlari"""
    
    def setUp(self):
        """Test uchun ma'lumotlarni tayyorlash"""
        # Test foydalanuvchisi yaratish
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test tili yaratish
        self.language = Language.objects.create(
            name='English',
            code='en'
        )
        
        # Test imtihonlari yaratish
        self.multilevel_exam = Exam.objects.create(
            title='CEFR Multilevel Test',
            level='multilevel',
            language=self.language,
            price=0
        )
        
        self.tys_exam = Exam.objects.create(
            title='TYS Test',
            level='tys',
            language=self.language,
            price=0
        )
        
        # Sectionlar yaratish
        self.sections = {}
        for section_type in ['listening', 'reading', 'writing', 'speaking']:
            section = Section.objects.create(
                exam=self.multilevel_exam,
                type=section_type,
                title=f'{section_type.title()} Section',
                duration=30
            )
            self.sections[section_type] = section
        
        # UserTest yaratish
        self.user_test = UserTest.objects.create(
            user=self.user,
            language=self.language,
            exam=self.multilevel_exam,
            status='completed'
        )
        
        # TestResult lar yaratish
        self.test_results = {}
        scores = {'listening': 65, 'reading': 58, 'writing': 62, 'speaking': 60}
        
        for section_type, score in scores.items():
            test_result = TestResult.objects.create(
                user_test=self.user_test,
                section=self.sections[section_type],
                status='completed',
                score=score
            )
            self.test_results[section_type] = test_result
    
    def test_get_exam_result_success(self):
        """Muvaffaqiyatli imtihon natijasini olish testi"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(
            f'/api/multilevel/exam-results/multilevel-tys/?user_test_id={self.user_test.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Asosiy tekshirishlar
        self.assertTrue(data['success'])
        self.assertEqual(data['exam_info']['exam_name'], 'CEFR Multilevel Test')
        self.assertEqual(data['exam_info']['exam_level'], 'MULTILEVEL')
        
        # Section natijalarini tekshirish
        self.assertEqual(data['section_results']['listening']['score'], 65)
        self.assertEqual(data['section_results']['reading']['score'], 58)
        self.assertEqual(data['section_results']['writing']['score'], 62)
        self.assertEqual(data['section_results']['speaking']['score'], 60)
        
        # Umumiy natijani tekshirish
        self.assertEqual(data['overall_result']['total_score'], 245)
        self.assertEqual(data['overall_result']['average_score'], 61.25)
        self.assertEqual(data['overall_result']['level'], 'B2')
        self.assertTrue(data['overall_result']['is_complete'])
    
    def test_get_exam_result_not_found(self):
        """Mavjud bo'lmagan imtihon natijasini olish testi"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(
            '/api/multilevel/exam-results/multilevel-tys/?user_test_id=99999'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('topilmadi', data['error'])
    
    def test_get_exam_result_unauthorized(self):
        """Ruxsatsiz foydalanuvchi testi"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=other_user)
        
        response = self.client.get(
            f'/api/multilevel/exam-results/multilevel-tys/?user_test_id={self.user_test.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_exam_result_missing_parameter(self):
        """Parametr yo'qligi testi"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/multilevel/exam-results/multilevel-tys/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('majburiy', data['error'])
    
    def test_get_exam_list_success(self):
        """Imtihonlar ro'yxatini olish testi"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/multilevel/exam-results/multilevel-tys/list/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['total_exams'], 1)
        self.assertEqual(len(data['exams']), 1)
        
        exam = data['exams'][0]
        self.assertEqual(exam['exam_name'], 'CEFR Multilevel Test')
        self.assertEqual(exam['total_score'], 245)
        self.assertEqual(exam['level'], 'B2')
    
    def test_level_calculation(self):
        """Daraja hisoblash testi"""
        # Test ballar va kutilgan darajalar
        test_cases = [
            (35, 'Below B1'),
            (40, 'B1'),
            (55, 'B2'),
            (70, 'C1'),
        ]
        
        for score, expected_level in test_cases:
            calculated_level = get_level_from_score(score)
            self.assertEqual(calculated_level, expected_level, 
                           f"Score {score} uchun daraja noto'g'ri: {calculated_level}, kutilgan: {expected_level}")


class ExamResultsIntegrationTest(TestCase):
    """Integratsiya testlari"""
    
    def setUp(self):
        """Test ma'lumotlarini tayyorlash"""
        self.client = Client()
        
        # Test foydalanuvchisi
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        
        # Test tili
        self.language = Language.objects.create(
            name='Turkish',
            code='tr'
        )
        
        # TYS imtihoni
        self.tys_exam = Exam.objects.create(
            title='TYS Integration Test',
            level='tys',
            language=self.language,
            price=0
        )
        
        # Sectionlar
        self.sections = {}
        for section_type in ['listening', 'reading', 'writing', 'speaking']:
            section = Section.objects.create(
                exam=self.tys_exam,
                type=section_type,
                title=f'{section_type.title()} Section',
                duration=30
            )
            self.sections[section_type] = section
        
        # UserTest
        self.user_test = UserTest.objects.create(
            user=self.user,
            language=self.language,
            exam=self.tys_exam,
            status='started'
        )
        
        # Faqat 2 section tugatilgan
        scores = {'listening': 45, 'reading': 52}
        for section_type, score in scores.items():
            TestResult.objects.create(
                user_test=self.user_test,
                section=self.sections[section_type],
                status='completed',
                score=score
            )
        
        # 2 section boshlanmagan
        for section_type in ['writing', 'speaking']:
            TestResult.objects.create(
                user_test=self.user_test,
                section=self.sections[section_type],
                status='started',
                score=0
            )
    
    def test_incomplete_exam_result(self):
        """Tugatilmagan imtihon natijasi testi"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(
            f'/api/multilevel/exam-results/multilevel-tys/?user_test_id={self.user_test.id}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Tugatilmagan imtihon tekshirishlari
        self.assertFalse(data['overall_result']['is_complete'])
        self.assertEqual(data['overall_result']['completed_sections'], 2)
        self.assertEqual(data['overall_result']['total_sections'], 4)
        
        # Section holatlarini tekshirish
        self.assertEqual(data['section_results']['listening']['status'], 'completed')
        self.assertEqual(data['section_results']['reading']['status'], 'completed')
        self.assertEqual(data['section_results']['writing']['status'], 'started')
        self.assertEqual(data['section_results']['speaking']['status'], 'started')


def run_manual_tests():
    """Qo'lda test qilish uchun funksiya"""
    print("=== Multilevel va TYS Exam Results API Test ===\n")
    
    # Daraja hisoblash testlari
    print("1. Daraja hisoblash testlari:")
    test_scores = [35, 40, 55, 70, 75]
    for score in test_scores:
        level = get_level_from_score(score)
        print(f"   {score} ball -> {level} daraja")
    
    print("\n2. Ball tizimi:")
    print("   - Har bir section: 0-75 ball")
    print("   - Umumiy ball: 0-300 ball (4 section)")
    print("   - O'rtacha ball: Umumiy ball ÷ 4")
    
    print("\n3. Daraja oralig'lari:")
    print("   - B1: 38-50 ball")
    print("   - B2: 51-64 ball") 
    print("   - C1: 65-75 ball")
    print("   - Below B1: 37 va undan past")
    
    print("\n4. API Endpointlar:")
    print("   - GET /api/multilevel/exam-results/multilevel-tys/?user_test_id={id}")
    print("   - GET /api/multilevel/exam-results/multilevel-tys/list/?exam_level={level}&limit={limit}")
    
    print("\nTest muvaffaqiyatli yakunlandi! ✅")


if __name__ == "__main__":
    run_manual_tests()
