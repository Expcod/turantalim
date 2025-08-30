from django.contrib import admin
from .models import Language

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'show_picture', 'flag')
    search_fields = ('name', 'flag')
    list_filter = ('name',)

    def show_picture(self, obj):
        if obj.picture:
            return format_html(
                '<img src="{}" width="100" style="max-height:50px; object-fit: cover;" />',
                obj.picture.url
            )
        return "(No Image)"
    show_picture.short_description = "Picture"
