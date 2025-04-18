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

        active_forms = [
            form for form in self.forms
            if not form.cleaned_data.get('DELETE', False)
        ]

        if len(active_forms) < 2:
            raise ValidationError("Variantli savolda kamida 2 ta variant bo‘lishi kerak!")

        correct_count = sum(
            1 for form in active_forms
            if form.cleaned_data.get('is_correct', False)
        )

        if correct_count > 1:
            raise ValidationError("Faqat bitta variant to‘g‘ri bo‘lishi mumkin!")
        if correct_count == 0:
            raise ValidationError("Hech bo‘lmaganda bitta variant to‘g‘ri bo‘lishi kerak!")

# Option Inline
class OptionInline(admin.TabularInline):
    model = Option
    extra = 2  
    formset = OptionInlineFormset
    fields = ('text', 'is_correct')

# Question uchun maxsus ModelForm
class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        has_options = cleaned_data.get('has_options')
        answer = cleaned_data.get('answer')
        test = cleaned_data.get('test')

        section_type = None
        if test and test.section:
            section_type = test.section.type

        if section_type in ['writing', 'speaking']:
            return cleaned_data

        if not has_options and not answer:
            raise ValidationError("Variantlarsiz savolda javob majburiy!")

        if has_options:
            option_forms = self.data.get('option_set-TOTAL_FORMS')
            if not option_forms:
                raise ValidationError("Variantli savolda kamida 2 ta variant bo‘lishi kerak!")

            total_forms = int(option_forms)
            active_forms = 0
            correct_count = 0

            for i in range(total_forms):
                if f'option_set-{i}-DELETE' not in self.data:
                    active_forms += 1
                    if f'option_set-{i}-is_correct' in self.data and self.data[f'option_set-{i}-is_correct'] == 'on':
                        correct_count += 1
                    text_field = f'option_set-{i}-text'
                    if text_field not in self.data or not self.data[text_field]:
                        raise ValidationError(f"Variant {i+1} matni bo‘sh bo‘lmasligi kerak!")

            if active_forms < 2:
                raise ValidationError("Variantli savolda kamida 2 ta variant bo‘lishi kerak!")

            if correct_count == 0:
                raise ValidationError("Hech bo‘lmaganda bitta variant to‘g‘ri bo‘lishi kerak!")
            if correct_count > 1:
                raise ValidationError("Faqat bitta variant to‘g‘ri bo‘lishi mumkin!")

        return cleaned_data

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
    form = QuestionAdminForm

    def text_short(self, obj):
        return obj.text[:50]
    text_short.short_description = "Savol matni"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

# TestResult Admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user_test', 'section', 'status', 'score', 'start_time')
    search_fields = ('user_test__user__username', 'section__title')
    list_filter = ('status', 'section__type', 'user_test__exam')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_test__user', 'section__exam')