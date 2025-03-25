from django.contrib import admin
from django import forms
from .models import Section, Test, Question, Option
from django.core.exceptions import ValidationError

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'language', 'level', 'duration')
    search_fields = ('title', 'description')
    list_filter = ('language', 'type', 'level')

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order')
    search_fields = ('title', 'description', 'text', 'options_array', 'constraints')
    list_filter = ('section',)

class OptionInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        """Admin panelda faqat 1 ta `is_correct=True` bo‘lishini tekshiradi"""
        super().clean()
        if not self.instance.has_options:
            return  # Agar variantlar mavjud bo‘lmasa, tekshirishni o‘tkazib yuboramiz
        correct_count = sum(1 for form in self.forms if form.cleaned_data.get('is_correct', False) and not form.cleaned_data.get('DELETE', False))
        if correct_count > 1:
            raise ValidationError("Faqat bitta variant to‘g‘ri bo‘lishi mumkin!")
        if correct_count == 0:
            raise ValidationError("Hech bo‘lmaganda bitta variant to‘g‘ri bo‘lishi kerak!")

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    formset = OptionInlineFormset

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'has_options')
    search_fields = ('text', 'answer')
    list_filter = ('test', 'has_options')
    inlines = [OptionInline]

# Agar Option ni alohida ko‘rish kerak bo‘lsa, izohni oling:
# @admin.register(Option)
# class OptionAdmin(admin.ModelAdmin):
#     list_display = ('text', 'question', 'is_correct')
#     search_fields = ('text',)
#     list_filter = ('question', 'is_correct')