from rest_framework import serializers
from .models import  Payment

# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'test', 'amount', 'status', 'transaction_id', 'payment_url', 'created_at']