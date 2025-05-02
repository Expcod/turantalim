from rest_framework import serializers
from .models import ExamPayment, UserBalance, BalanceTransaction

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

class BalanceTopUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceTransaction
        fields = ["id", "user", "amount", "transaction_type", "description"]
        read_only_fields = ["transaction_type", "description"]

    def validate(self, data):
        if data["amount"] <= 0:
            raise serializers.ValidationError("Miqdor 0 dan katta bo‘lishi kerak!")
        return data

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBalance
        fields = ["user", "balance"]

class BalanceTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceTransaction
        fields = ["id", "user", "amount", "transaction_type", "description", "created_at"]