"""
Ko'p rasmli writing test tizimini test qilish uchun test fayli
"""
import tempfile
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Language, Exam, Section, Test, Question, UserTest, TestResult
from .writing_serializers import WritingTestAnswerSerializer, BulkWritingTestCheckSerializer
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class MultipleImagesWritingTestCase(TestCase):
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
        
        # Section yaratish
        self.section = Section.objects.create(
            exam=self.exam,
            type='writing',
            title='Writing Section',
            duration=30
        )
        
        # Test yaratish
        self.test = Test.objects.create(
            section=self.section,
            title='Writing Test',
            text='Write about your favorite hobby.'
        )
        
        # Savol yaratish
        self.question = Question.objects.create(
            test=self.test,
            text='Describe your favorite hobby in detail.',
            has_options=False
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
            end_time=timezone.now() + timedelta(minutes=30)
        )
        
        # API client yaratish
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def create_test_image(self, filename="test.jpg"):
        """Test uchun rasm yaratish"""
        # Oddiy test rasm fayli yaratish
        image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\xf7\xa0\xd8\x00\x00\x00\x00IEND\xaeB`\x82'
        return SimpleUploadedFile(filename, image_content, content_type='image/jpeg')

    def test_single_image_validation(self):
        """Bitta rasm bilan test"""
        image1 = self.create_test_image("test1.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_two_images_validation(self):
        """Ikki rasm bilan test"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                },
                {
                    'image': image2,
                    'order': 2
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_three_images_validation(self):
        """Uch rasm bilan test"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        image3 = self.create_test_image("test3.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                },
                {
                    'image': image2,
                    'order': 2
                },
                {
                    'image': image3,
                    'order': 3
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_four_images_validation_fails(self):
        """To'rt rasm bilan test - xatolik bo'lishi kerak"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        image3 = self.create_test_image("test3.jpg")
        image4 = self.create_test_image("test4.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                },
                {
                    'image': image2,
                    'order': 2
                },
                {
                    'image': image3,
                    'order': 3
                },
                {
                    'image': image4,
                    'order': 4
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_length', serializer.errors['writing_images'])

    def test_duplicate_order_validation_fails(self):
        """Takroriy order bilan test - xatolik bo'lishi kerak"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                },
                {
                    'image': image2,
                    'order': 1  # Takroriy order
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('writing_images', serializer.errors)

    def test_wrong_order_sequence_validation_fails(self):
        """Noto'g'ri order ketma-ketligi bilan test - xatolik bo'lishi kerak"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 1
                },
                {
                    'image': image2,
                    'order': 3  # 2 o'tirib ketgan
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('writing_images', serializer.errors)

    def test_zero_images_validation_fails(self):
        """Rasm yo'q bilan test - xatolik bo'lishi kerak"""
        data = {
            'question': self.question.id,
            'writing_images': []
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('min_length', serializer.errors['writing_images'])

    def test_bulk_serializer_validation(self):
        """Bulk serializer bilan test"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        
        data = {
            'test_result_id': self.test_result.id,
            'answers': [
                {
                    'question': self.question.id,
                    'writing_images': [
                        {
                            'image': image1,
                            'order': 1
                        },
                        {
                            'image': image2,
                            'order': 2
                        }
                    ]
                }
            ]
        }
        
        serializer = BulkWritingTestCheckSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_bulk_serializer_duplicate_questions_fails(self):
        """Bulk serializer bilan takroriy savollar - xatolik bo'lishi kerak"""
        image1 = self.create_test_image("test1.jpg")
        image2 = self.create_test_image("test2.jpg")
        
        data = {
            'test_result_id': self.test_result.id,
            'answers': [
                {
                    'question': self.question.id,
                    'writing_images': [
                        {
                            'image': image1,
                            'order': 1
                        }
                    ]
                },
                {
                    'question': self.question.id,  # Takroriy savol
                    'writing_images': [
                        {
                            'image': image2,
                            'order': 1
                        }
                    ]
                }
            ]
        }
        
        serializer = BulkWritingTestCheckSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('answers', serializer.errors)

    def test_image_size_validation_fails(self):
        """Katta hajmli rasm bilan test - xatolik bo'lishi kerak"""
        # 6MB rasm yaratish
        large_image_content = b'x' * (6 * 1024 * 1024)
        large_image = SimpleUploadedFile("large.jpg", large_image_content, content_type='image/jpeg')
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': large_image,
                    'order': 1
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors['writing_images'][0])

    def test_invalid_image_format_validation_fails(self):
        """Noto'g'ri formatdagi rasm bilan test - xatolik bo'lishi kerak"""
        # PDF fayli yaratish
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type='application/pdf')
        
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': pdf_file,
                    'order': 1
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image', serializer.errors['writing_images'][0])

    def test_order_range_validation(self):
        """Order diapazonini tekshirish"""
        image1 = self.create_test_image("test1.jpg")
        
        # Order 0 bilan test - xatolik bo'lishi kerak
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 0
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order', serializer.errors['writing_images'][0])
        
        # Order 4 bilan test - xatolik bo'lishi kerak
        data = {
            'question': self.question.id,
            'writing_images': [
                {
                    'image': image1,
                    'order': 4
                }
            ]
        }
        
        serializer = WritingTestAnswerSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('order', serializer.errors['writing_images'][0])
