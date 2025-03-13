from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'amount', 'status', 'transaction_id', 'payment_url', 'created_at']
    list_filter = ['status']
    search_fields = ['user__email', 'test__title', 'transaction_id']
    list_editable = ['status']
    list_display_links = ['user', 'test']
    readonly_fields = ['transaction_id', 'payment_url', 'created_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'test', 'amount', 'status')
        }),
        ('Payment Info', {
            'fields': ('transaction_id', 'payment_url', 'created_at')
        })
    )
    ordering = ['-created_at']
    actions = ['make_completed', 'make_failed']

    def make_completed(self, request, queryset):
        queryset.update(status='completed')
    make_completed.short_description = 'Mark selected payments as completed'

    def make_failed(self, request, queryset):
        queryset.update(status='failed')
    make_failed.short_description = 'Mark selected payments as failed'