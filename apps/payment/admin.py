from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from .models import ExamPayment, UserBalance, BalanceTransaction
from payme.models import PaymeTransactions

@admin.register(ExamPayment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exam",
        "user",
        "amount",
        "is_paid",
        "payment_method",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_paid", "payment_method")
    search_fields = ("exam__title", "user__phone", "user__email")

@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "created_at", "updated_at")
    search_fields = ("user__phone", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("created_at",)
    
    def save_model(self, request, obj, form, change):
        if change:  # Agar mavjud obyektni tahrirlayotgan bo'lsa
            # Oldingi balansni olish
            old_obj = UserBalance.objects.get(pk=obj.pk)
            old_balance = old_obj.balance
            new_balance = obj.balance
            
            # Faqat balansni ko'paytirish mumkin
            if new_balance < old_balance:
                messages.error(request, f"Balansni kamaytirish mumkin emas! Joriy balans: {old_balance}, yangi balans: {new_balance}")
                return
            
            # Agar balans ko'paytirilgan bo'lsa, tranzaksiya yaratish
            if new_balance > old_balance:
                difference = new_balance - old_balance
                admin_info = getattr(request.user, 'phone', None) or getattr(request.user, 'email', None) or str(request.user)
                BalanceTransaction.objects.create(
                    user=obj.user,
                    amount=difference,
                    transaction_type="topup",
                    description=f"Admin tomonidan qo'shildi ({admin_info})"
                )
        
        super().save_model(request, obj, form, change)

@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "transaction_type", "description", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__phone", "user__email", "description")

class PaymeTransactionsAdmin(admin.ModelAdmin):
    """
    Admin for PaymeTransactions with display, search, and filter options.
    """
    list_display = ['transaction_id', 'state', 'created_at']
    search_fields = ['transaction_id']
    list_filter = ['state']