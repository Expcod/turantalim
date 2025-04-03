from django.contrib import admin

from django.urls import reverse
from django.utils.html import format_html
from .models import ExamPayment
from payme.models import PaymeTransactions
# admin.site.unregister(PaymeTransactions)

@admin.register(ExamPayment)
class PaymentAdmin(admin.ModelAdmin):
   list_display = (
        "id",
        "exam",
        "user",
        "amount",
        "is_paid",
        "payment_method",
   )
list_filter = ("is_paid", "payment_method")
search_fields = ("exam__title", "user__username")


class PaymeTransactionsAdmin(admin.ModelAdmin):
    """
    Admin for PaymeTransactions with display, search, and filter options.
    """
    list_display = ['transaction_id', 'state', 'created_at']
    search_fields = ['transaction_id']
    list_filter = ['state']