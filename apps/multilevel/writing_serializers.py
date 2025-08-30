from rest_framework import serializers
from .models import Question

class WritingTestAnswerSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    writing_image = serializers.ImageField(required=True)

    def validate_writing_image(self, value):
        if value.size > 5 * 1024 * 1024:  # 5MB dan katta bo'lmasligi kerak
            raise serializers.ValidationError("Rasm hajmi 5MB dan katta bo'lmasligi kerak!")
        if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Faqat PNG yoki JPG formatidagi rasmlar qabul qilinadi!")
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
        
        # Check that all answers have image files
        missing_images = []
        for i, answer in enumerate(answers):
            has_image = answer.get('writing_image') is not None
            if not has_image:
                missing_images.append(f"Javob {i+1} (Savol ID: {question_ids[i]})")
        
        if missing_images:
            raise serializers.ValidationError(f"Quyidagi javoblar uchun rasm fayli kiritilmagan: {', '.join(missing_images)}")
        
        return data