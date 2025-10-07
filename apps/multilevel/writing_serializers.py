from rest_framework import serializers
from .models import Question

class WritingTestSerializer(serializers.Serializer):
    """Writing test uchun serializer"""
    id = serializers.IntegerField()
    order = serializers.IntegerField()  # order_id emas, order
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    picture = serializers.ImageField(required=False, allow_null=True)
    images = serializers.SerializerMethodField()  # RelatedManager uchun maxsus
    audio = serializers.FileField(required=False, allow_null=True)
    options = serializers.JSONField(required=False)
    sample = serializers.CharField(allow_blank=True)
    text_title = serializers.CharField(allow_blank=True)
    text = serializers.CharField()
    constraints = serializers.CharField(allow_blank=True)
    questions = serializers.SerializerMethodField()
    response_time = serializers.SerializerMethodField()
    upload_time = serializers.SerializerMethodField()

    def get_images(self, obj):
        """Test uchun rasmlarni qaytarish"""
        if hasattr(obj, 'images') and obj.images.exists():
            return [
                {
                    'id': img.id,
                    'image': img.image.url if img.image else None,
                    'order': img.order
                }
                for img in obj.images.all().order_by('order')
            ]
        return []

    def get_questions(self, obj):
        """Test uchun savollarni qaytarish"""
        if hasattr(obj, 'questions') and obj.questions.exists():
            return [
                {
                    'id': q.id,
                    'text': q.text,
                    'picture': q.picture.url if q.picture else None
                }
                for q in obj.questions.all()
            ]
        return []

    def get_response_time(self, obj):
        """Response time ni qaytarish"""
        if hasattr(obj, 'response_time') and obj.response_time:
            return obj.response_time
        return None

    def get_upload_time(self, obj):
        """Upload time ni qaytarish"""
        if hasattr(obj, 'upload_time') and obj.upload_time:
            return obj.upload_time
        return None

class WritingImageSerializer(serializers.Serializer):
    """Har bir rasm uchun serializer"""
    image = serializers.ImageField(required=True)
    order = serializers.IntegerField(min_value=1, max_value=3, required=True)

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:  # 5MB dan katta bo'lmasligi kerak
            raise serializers.ValidationError("Rasm hajmi 5MB dan katta bo'lmasligi kerak!")
        if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Faqat PNG yoki JPG formatidagi rasmlar qabul qilinadi!")
        return value

class WritingTestAnswerSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    writing_images = serializers.ListField(
        child=WritingImageSerializer(),
        min_length=1,
        max_length=3,
        error_messages={
            'min_length': "Kamida bitta rasm yuklanishi shart!",
            'max_length': "Maksimum 3 ta rasm yuklash mumkin!"
        }
    )

    def validate_writing_images(self, value):
        """Rasmlar order'ini tekshirish"""
        if not value:
            raise serializers.ValidationError("Kamida bitta rasm yuklanishi shart!")
        
        if len(value) > 3:
            raise serializers.ValidationError("Maksimum 3 ta rasm yuklash mumkin!")
        
        # Order'larni tekshirish
        orders = [item['order'] for item in value]
        if len(orders) != len(set(orders)):
            raise serializers.ValidationError("Rasmlar order'i takrorlanmasligi kerak!")
        
        # Order'lar 1 dan boshlanishi kerak
        expected_orders = list(range(1, len(orders) + 1))
        if sorted(orders) != expected_orders:
            raise serializers.ValidationError(f"Rasmlar order'i {expected_orders} bo'lishi kerak!")
        
        return value

class BulkWritingTestCheckSerializer(serializers.Serializer):
    test_result_id = serializers.IntegerField(required=False, allow_null=True)
    answers = serializers.ListField(
        child=WritingTestAnswerSerializer(), 
        min_length=1,
        error_messages={
            'required': "Kamida bitta javob kiritilishi shart!",
            'min_length': "Kamida bitta javob kiritilishi shart!",
            'empty': "Javoblar ro'yxati bo'sh bo'lishi mumkin emas!"
        }
    )

    def validate(self, data):
        if 'answers' not in data:
            raise serializers.ValidationError("Answers maydoni kiritilishi shart!")
        
        answers = data.get('answers', [])
        if not answers:
            raise serializers.ValidationError("Kamida bitta javob kiritilishi shart!")
        
        # Check for duplicate question IDs
        question_ids = []
        for i, answer in enumerate(answers):
            if 'question' not in answer:
                raise serializers.ValidationError(f"Javob {i+1} da savol ID'si kiritilmagan!")
            
            question_id = answer['question'].id if hasattr(answer['question'], 'id') else answer['question']
            question_ids.append(question_id)
        
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Bir xil savol ID'si bir nechta kiritilgan.")
        
        # Check that all answers have images
        missing_images = []
        for i, answer in enumerate(answers):
            has_images = answer.get('writing_images') is not None and len(answer['writing_images']) > 0
            if not has_images:
                missing_images.append(f"Javob {i+1} (Savol ID: {question_ids[i]})")
        
        if missing_images:
            raise serializers.ValidationError(f"Quyidagi javoblar uchun rasm fayli kiritilmagan: {', '.join(missing_images)}")
        
        return data