from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from apps.users.models import User, VerificationCode, Country, Region

# Group modelini admin paneldan o'chirish
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("phone", "password")}),  # Username o'rniga phone
        ("Personal info", {"fields": ("first_name", "last_name", "email", "picture", "gender", "region", "language")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    list_display = ("id", "phone", "first_name", "last_name", "is_active", "reviewer_status")
    list_display_links = ("id", "phone", "first_name", "last_name")
    search_fields = ("phone", "first_name", "last_name", "email")
    list_filter = ("is_active", "groups")
    ordering = ("-id",)
    
    def reviewer_status(self, obj):
        """Show if user is a reviewer"""
        from django.utils.html import format_html
        if obj.groups.filter(name='Reviewer').exists():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Tekshiruvchi</span>'
            )
        return '-'
    reviewer_status.short_description = 'Reviewer'

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('user__phone', 'user__email', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    list_display_links = ('id', 'name')
    list_filter = ('country',)
    search_fields = ('name', 'country__name')
    ordering = ('country__name', 'name')
