from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
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
    search_fields = ("exam__title", "user__username")

@admin.register(UserBalance)
class UserBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "balance")
    search_fields = ("user__username",)

@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "transaction_type", "description", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__username", "description")

class PaymeTransactionsAdmin(admin.ModelAdmin):
    """
    Admin for PaymeTransactions with display, search, and filter options.
    """
    list_display = ['transaction_id', 'state', 'created_at']
    search_fields = ['transaction_id']
    list_filter = ['state']