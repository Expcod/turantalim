from django.contrib import admin
from django import forms
from .models import Exam, Section, Test, Question, Option, UserTest, TestResult
from django.core.exceptions import ValidationError

# Option Inline Formset
class OptionInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if not self.instance.pk or not self.instance.has_options:
            return  
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
    fields = ('text', 'is_correct')



# Exam Admin
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'level', 'price')
    search_fields = ('title', 'description')
    list_filter = ('language', 'level')


    def get_queryset(self, request):
        return super().get_queryset(request).select_related('language')

# Section Admin
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'exam', 'duration')
    search_fields = ('title', 'description')
    list_filter = ('type', 'exam')


    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exam')

# Test Admin
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order')
    search_fields = ('title', 'description', 'text', 'options_array', 'constraints')
    list_filter = ('section__exam', 'section__type')


    def get_queryset(self, request):
        return super().get_queryset(request).select_related('section__exam')

# Question Admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'test', 'has_options')
    search_fields = ('text', 'answer')
    list_filter = ('test__section__exam', 'has_options')
    inlines = [OptionInline]

    def text_short(self, obj):
        return obj.text[:50]
    text_short.short_description = "Savol matni"

    def save_model(self, request, obj, form, change):

        if not obj.has_options and not obj.answer:
            self.message_user(request, "Variantlarsiz savolda javob majburiy", level='ERROR')
            return
        super().save_model(request, obj, form, change)



# TestResult Admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user_test', 'section', 'status', 'score', 'start_time')
    search_fields = ('user_test__user__username', 'section__title')
    list_filter = ('status', 'section__type', 'user_test__exam')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_test__user', 'section__exam')

