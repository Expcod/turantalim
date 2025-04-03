from rest_framework import serializers
from .models import  ExamPayment

# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamPayment
        fields = [
            "id",
            "user",
            "exam",
            "amount",
            "is_paid",
            "payment_method",
        ]