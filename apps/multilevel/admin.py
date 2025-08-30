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
    preparation_time = forms.IntegerField(
        label="Preparation Time (seconds)",
        min_value=0,
        required=False,
        help_text="Enter preparation time in seconds for speaking questions only."
    )
    response_time = forms.IntegerField(
        label="Response Time (seconds)",
        min_value=0,
        required=False,
        help_text="Enter response time in seconds for speaking questions only."
    )

    class Meta:
        model = Question
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        has_options = cleaned_data.get('has_options')
        answer = cleaned_data.get('answer')
        test = cleaned_data.get('test')
        preparation_time = cleaned_data.get('preparation_time')
        response_time = cleaned_data.get('response_time')

        section_type = None
        if test and test.section:
            section_type = test.section.type

        if section_type in ['writing', 'speaking']:
            if section_type == 'speaking':
                if preparation_time is not None and preparation_time < 0:
                    raise ValidationError("Preparation time cannot be negative!")
                if response_time is not None and response_time < 0:
                    raise ValidationError("Response time cannot be negative!")
            else:
                if preparation_time is not None or response_time is not None:
                    raise ValidationError("Preparation and response times are only applicable to speaking tests!")
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

        if preparation_time is not None or response_time is not None:
            raise ValidationError("Preparation and response times are only applicable to speaking tests!")

        return cleaned_data

# Exam Admin
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'language', 'level', 'price','status')
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
    list_display = ('id', 'title', 'section', 'order')
    search_fields = ('title', 'description', 'text', 'options_array', 'constraints')
    list_filter = ('section__exam', 'section__type')
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('section', 'title', 'description', 'order')
        }),
        ('Kontent', {
            'fields': ('picture', 'audio', 'text_title', 'text', 'options_array', 'sample', 'constraints')
        }),
        ('Writing test vaqtlari', {
            'fields': ('response_time', 'upload_time'),
            'description': 'Faqat writing section uchun javob berish va rasm yuklash vaqtini belgilang (sekundlarda)',
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('section__exam')

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.section and obj.section.type != 'writing':
            # Writing bo'lmagan sectionlar uchun vaqt maydonlarini yashirish
            fieldsets = list(fieldsets)
            fieldsets = [fieldset for fieldset in fieldsets if fieldset[0] != 'Writing test vaqtlari']
        return fieldsets

    def save_model(self, request, obj, form, change):
        # Writing bo'lmagan sectionlar uchun vaqt maydonlarini tozalash
        if obj.section and obj.section.type != 'writing':
            obj.response_time = None
            obj.upload_time = None
        super().save_model(request, obj, form, change)

    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        # Writing section uchun vaqt maydonlarini ko'rsatish
        if 'response_time' not in list_display:
            list_display.append('response_time')
        if 'upload_time' not in list_display:
            list_display.append('upload_time')
        return list_display

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.section and obj.section.type != 'writing':
            # Writing bo'lmagan sectionlar uchun vaqt maydonlarini yashirish
            fieldsets = list(fieldsets)
            fieldsets = [fieldset for fieldset in fieldsets if fieldset[0] != 'Writing test vaqtlari']
        return fieldsets

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
        if form.cleaned_data.get('test') and form.cleaned_data.get('test').section.type == 'speaking':
            obj.preparation_time = form.cleaned_data.get('preparation_time')
            obj.response_time = form.cleaned_data.get('response_time')
        super().save_model(request, obj, form, change)

# TestResult Admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user_test', 'section', 'status', 'score', 'start_time')
    search_fields = ('user_test__user__username', 'section__title')
    list_filter = ('status', 'section__type', 'user_test__exam')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_test__user', 'section__exam')
