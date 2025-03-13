from django.contrib import admin

from django import forms
from django.contrib import admin
from .models import Section, Test, Question, Option
from django.core.exceptions import ValidationError

@admin.register(Section)
class ListeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'language', 'submitters')
    search_fields = ('title', 'description')
    list_filter = ('language',)

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order')
    search_fields = ('title', 'description', 'text', 'options', 'constraints')
    list_filter = ('section',)


class OptionInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        """Admin panelda faqat 1 ta `is_correct=True` bo‘lishini tekshiradi"""
        super().clean()
        # correct_count = sum(1 for form in self.forms if form.cleaned_data.get('is_correct', False))

        # if correct_count > 1:
        #     raise ValidationError("Faqat bitta variant to‘g‘ri bo‘lishi mumkin!")
        # if correct_count == 0:
        #     raise ValidationError("Hech bo‘lmaganda bitta variant to‘g‘ri bo‘lishi kerak!")
        
class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    formset = OptionInlineFormset  # Custom formset qo‘shildi

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'has_options')
    search_fields = ('text', 'answer')
    list_filter = ('test', 'has_options')
    inlines = [OptionInline]

# @admin.register(Option)
# class OptionAdmin(admin.ModelAdmin):
#     list_display = ('text', 'question', 'is_correct')
#     search_fields = ('text',)
#     list_filter = ('question', 'is_correct')
