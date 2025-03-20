from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from apps.users.models import User

# Group modelini admin paneldan o‘chirish
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("phone", "password")}),  # Username o‘rniga phone
        ("Personal info", {"fields": ("first_name", "last_name", "email", "picture", "gender", "region", "language", "balance")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    list_display = ("id", "phone", "first_name", "last_name", "is_active")
    list_display_links = ("id", "phone", "first_name", "last_name")
    search_fields = ("phone", "first_name", "last_name", "email")
    list_filter = ("is_active",)
    ordering = ("-id",)
