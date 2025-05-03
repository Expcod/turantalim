from rest_framework import serializers
from .models import Question
import magic
import logging

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_FORMATS = {
    'audio/flac': 'flac',
    'audio/aac': 'm4a',
    'audio/x-m4a': 'm4a',
    'audio/mpeg': 'mp3',
    'audio/mp4': 'mp4',
    'audio/ogg': 'ogg',
    'audio/wav': 'wav',
    'audio/x-wav': 'wav',
    'audio/webm': 'webm',
    'video/webm': 'webm',
    'video/mp4': 'mp4',
    'audio/mp3': 'mp3',
    'audio/x-mpeg': 'mp3',
    'audio/x-mp3': 'mp3',
    'audio/x-mpg': 'mp3',
    'audio/x-mpeg-3': 'mp3',
    'video/x-mp4': 'mp4',
    'video/3gpp': '3gp',
    'audio/vnd.wave': 'wav',
    'audio/wave': 'wav',
    'audio/x-pn-wav': 'wav',
    'audio/vorbis': 'ogg',
    'application/ogg': 'ogg',
    'audio/x-flac': 'flac',
    'application/x-flac': 'flac',
}

class SpeakingTestAnswerSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        error_messages={
            'required': "Savol ID'si kiritilishi shart!",
            'does_not_exist': "Berilgan ID'ga mos savol topilmadi!",
            'invalid': "Savol ID'si noto'g'ri formatda!"
        }
    )
    speaking_audio = serializers.FileField(
        error_messages={
            'required': "Audio fayl yuklanishi shart!",
            'invalid': "Yuklanayotgan fayl audio fayl bo'lishi kerak!"
        }
    )

    def validate_speaking_audio(self, value):
        max_size = 25 * 1024 * 1024  # 25 MB (Whisper API limit)
        if value.size > max_size:
            raise serializers.ValidationError("Fayl hajmi 25 MB dan katta bo'lmasligi kerak!")
        
        # Fayl kengaytmasini tekshirish
        file_extension = value.name.lower().split('.')[-1] if '.' in value.name else ''
        supported_extensions = list(set(SUPPORTED_AUDIO_FORMATS.values()))
        
        if file_extension not in supported_extensions:
            raise serializers.ValidationError(
                f"Noto'g'ri fayl formati! Qo'llab-quvvatlanadigan formatlar: {', '.join(supported_extensions)}"
            )
        
        # Fayl MIME type ni tekshirish
        try:
            mime = magic.Magic(mime=True)
            file_mime = mime.from_buffer(value.read(1024))
            value.seek(0)  # Reset file pointer
            
            if file_mime not in SUPPORTED_AUDIO_FORMATS:
                raise serializers.ValidationError(
                    f"Noto'g'ri fayl formati! Qo'llab-quvvatlanadigan formatlar: {', '.join(SUPPORTED_AUDIO_FORMATS.keys())}"
                )
        except ImportError:
            logger.warning("python-magic library not installed, skipping MIME type check")
        
        return value

class BulkSpeakingTestCheckSerializer(serializers.Serializer):
    test_result_id = serializers.IntegerField(required=False, allow_null=True)
    answers = serializers.ListField(
        child=SpeakingTestAnswerSerializer(),
        min_length=1,
        error_messages={
            'required': "Kamida bitta javob kiritilishi shart!",
            'min_length': "Kamida bitta javob kiritilishi shart!"
        }
    )

    def validate(self, data):
        if 'answers' not in data:
            raise serializers.ValidationError("Answers maydoni kiritilishi shart!")
        question_ids = [answer['question'].id for answer in data['answers']]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Bir xil savol ID'si bir nechta kiritilgan.")
        return data