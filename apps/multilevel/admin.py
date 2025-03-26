from django.contrib import admin
from django import forms
from .models import Exam, Section, Test, Question, Option
from django.core.exceptions import ValidationError

# Exam Admin
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'level')  # Exam uchun asosiy maydonlar
    search_fields = ('title', 'description')
    list_filter = ('language', 'level')

# Section Admin
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'exam', 'duration')  # 'language' va 'level' o‘rniga 'exam'
    search_fields = ('title', 'description')
    list_filter = ('type', 'exam')  # 'language' va 'level' o‘chirildi

    def get_queryset(self, request):
        # Optimallashtirish uchun exam bilan birga yuklash
        return super().get_queryset(request).select_related('exam')

# Test Admin
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order')  
    search_fields = ('title', 'description', 'text', 'options_array', 'constraints')
    list_filter = ('section',)  

    def get_queryset(self, request):

        return super().get_queryset(request).select_related('section')

# Option Inline Formset
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

# Option Inline
class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    formset = OptionInlineFormset

# Question Admin
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