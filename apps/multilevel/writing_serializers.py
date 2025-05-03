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
    answers = serializers.ListField(child=WritingTestAnswerSerializer(), min_length=1)

    def validate(self, data):
        if 'answers' not in data:
            raise serializers.ValidationError("Answers maydoni kiritilishi shart!")
        question_ids = [answer['question'].id for answer in data['answers']]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Bir xil savol ID'si bir nechta kiritilgan.")
        return data