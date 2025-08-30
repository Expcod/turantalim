from rest_framework import serializers
from .models import ExamPayment, UserBalance, BalanceTransaction
from payme.models import PaymeTransactions
import pytz

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
        read_only_fields = ["user", "amount", "is_paid", "payment_method"]

class BalanceTopUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceTransaction
        fields = ["id", "user", "amount", "transaction_type", "description"]
        read_only_fields = ["user", "transaction_type", "description"]

    def validate(self, data):
        if data["amount"] <= 0:
            raise serializers.ValidationError("Miqdor 0 dan katta bo'lishi kerak!")
        return data

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBalance
        fields = ["user", "balance"]

class BalanceTransactionSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = BalanceTransaction
        fields = ["id", "amount", "description", "created_at"]
    
    def get_created_at(self, obj):
        """Sana vaqtni chiroyli formatda qaytarish"""
        # Tashkent timezone ga o'tkazish
        tz = pytz.timezone('Asia/Tashkent')
        local_time = obj.created_at.astimezone(tz)
        return local_time.strftime("%d.%m.%Y %H:%M")

class PaymeTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymeTransactions to display successful transactions
    """
    amount_in_sum = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymeTransactions
        fields = [
            'id',
            'amount_in_sum',
            'created_at'
        ]
    
    def get_amount_in_sum(self, obj):
        """Convert amount from tiyin to sum"""
        return float(obj.amount) / 100
    
    def get_created_at(self, obj):
        """Sana vaqtni chiroyli formatda qaytarish"""
        # Tashkent timezone ga o'tkazish
        tz = pytz.timezone('Asia/Tashkent')
        local_time = obj.created_at.astimezone(tz)
        return local_time.strftime("%d.%m.%Y %H:%M")