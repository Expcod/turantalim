from rest_framework import serializers
from django.utils import timezone
from .models import Visitor


class VisitorSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_at_tashkent = serializers.SerializerMethodField()
    updated_at_tashkent = serializers.SerializerMethodField()
    
    class Meta:
        model = Visitor
        fields = [
            'id', 'first_name', 'last_name', 'phone_number', 
            'status', 'status_display', 'full_name', 
            'created_at', 'updated_at', 'created_at_tashkent', 'updated_at_tashkent', 'notes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'notes']
    
    def get_created_at_tashkent(self, obj):
        """Tashkent vaqti bilan ko'rsatish"""
        if obj.created_at:
            tashkent_time = timezone.localtime(obj.created_at, timezone=timezone.get_fixed_timezone(300))
            return tashkent_time.strftime('%d.%m.%Y %H:%M')
        return None
    
    def get_updated_at_tashkent(self, obj):
        """Tashkent vaqti bilan ko'rsatish"""
        if obj.updated_at:
            tashkent_time = timezone.localtime(obj.updated_at, timezone=timezone.get_fixed_timezone(300))
            return tashkent_time.strftime('%d.%m.%Y %H:%M')
        return None


class VisitorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ['first_name', 'last_name', 'phone_number']
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not value.startswith('+998'):
            raise serializers.ValidationError("Telefon raqami +998 bilan boshlanishi kerak")
        
        # Remove +998 and check if remaining part is numeric and has correct length
        number_part = value[4:]
        if not number_part.isdigit() or len(number_part) != 9:
            raise serializers.ValidationError("Telefon raqami noto'g'ri formatda")
        
        return value
    
    def validate_first_name(self, value):
        """Validate first name"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Ism kamida 2 ta harfdan iborat bo'lishi kerak")
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Familiya kamida 2 ta harfdan iborat bo'lishi kerak")
        return value.strip()


class VisitorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ['status', 'notes']
