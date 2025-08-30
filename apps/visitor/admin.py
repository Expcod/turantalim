from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Visitor


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name_display', 'phone_number', 'status_display', 
        'created_at_tashkent', 'admin_link'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        (_('Holat'), {
            'fields': ('status', 'notes')
        }),
        (_('Vaqt'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name_display(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name_display.short_description = _('To\'liq ism')
    full_name_display.admin_order_field = 'first_name'
    
    def status_display(self, obj):
        status_colors = {
            'new': '#ffc107',      # Yellow
            'in_review': '#17a2b8', # Blue
            'approved': '#28a745',  # Green
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 4px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Holat')
    
    def created_at_tashkent(self, obj):
        """Tashkent vaqti bilan ko'rsatish"""
        if obj.created_at:
            tashkent_time = timezone.localtime(obj.created_at, timezone=timezone.get_fixed_timezone(300))
            return tashkent_time.strftime('%d.%m.%Y %H:%M')
        return '-'
    created_at_tashkent.short_description = _('Yaratilgan vaqti')
    created_at_tashkent.admin_order_field = 'created_at'
    
    def admin_link(self, obj):
        url = reverse('admin:visitor_visitor_change', args=[obj.id])
        return format_html('<a href="{}">Tahrirlash</a>', url)
    admin_link.short_description = _('Amallar')
    
    actions = ['mark_as_new', 'mark_as_in_review', 'mark_as_approved']
    
    def mark_as_new(self, request, queryset):
        updated = queryset.update(status=Visitor.StatusChoices.NEW)
        self.message_user(request, f"{updated} ta ariza yangi holatga o'tkazildi")
    mark_as_new.short_description = _("Tanlangan arizalarni 'Yangi' holatiga o'tkazish")
    
    def mark_as_in_review(self, request, queryset):
        updated = queryset.update(status=Visitor.StatusChoices.IN_REVIEW)
        self.message_user(request, f"{updated} ta ariza 'Ko'rib chiqilmoqda' holatiga o'tkazildi")
    mark_as_in_review.short_description = _("Tanlangan arizalarni 'Ko'rib chiqilmoqda' holatiga o'tkazish")
    
    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status=Visitor.StatusChoices.APPROVED)
        self.message_user(request, f"{updated} ta ariza 'Qabul qilindi' holatiga o'tkazildi")
    mark_as_approved.short_description = _("Tanlangan arizalarni 'Qabul qilindi' holatiga o'tkazish")
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
