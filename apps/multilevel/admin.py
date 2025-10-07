from django.contrib import admin
from django import forms
from django.db import models
from django.core.exceptions import ValidationError

# Import all models from models.py
from apps.multilevel.models import (
    Exam, Section, Test, Question, Option, UserTest, TestResult, TestImage, QuestionImage,
    SubmissionMedia, ManualReview, QuestionScore, ReviewLog, REVIEW_STATUS_CHOICES
)

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
            raise ValidationError("Variantli savolda kamida 2 ta variant bo'lishi kerak!")

        correct_count = sum(
            1 for form in active_forms
            if form.cleaned_data.get('is_correct', False)
        )

        if correct_count == 0:
            raise ValidationError("Kamida bitta to'g'ri javob bo'lishi kerak!")

# Option Inline
class OptionInline(admin.TabularInline):
    model = Option
    formset = OptionInlineFormset
    extra = 4

# TestImage Inline
class TestImageInline(admin.TabularInline):
    model = TestImage
    extra = 1

# QuestionImage Inline
class QuestionImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 1

# Question Admin
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'text', 'test', 'has_options']
    list_filter = ['test__section__type', 'test__section__exam__level']
    search_fields = ['text', 'test__title']
    inlines = [OptionInline, QuestionImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('test', 'text', 'picture', 'answer', 'has_options')
        }),
        ('Speaking Parameters', {
            'fields': ('preparation_time', 'response_time'),
            'classes': ('collapse',),
            'description': 'Speaking settings for preparation and response time'
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('test__section__exam')

# Test Admin
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'section_info', 'level_info']
    list_filter = ['section__type', 'section__exam__level']
    search_fields = ['title', 'section__title', 'text']
    inlines = [TestImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('section', 'title', 'description', 'picture', 'audio', 'text_title', 'text', 'sample', 'constraints', 'order')
        }),
        ('Writing Parameters', {
            'fields': ('response_time', 'upload_time'),
            'classes': ('collapse',),
            'description': 'Writing settings for response and upload time'
        }),
    )
    
    def section_info(self, obj):
        return f"{obj.section.title} ({obj.section.get_type_display()})"
    section_info.short_description = 'Section'
    
    def level_info(self, obj):
        return obj.section.exam.get_level_display()
    level_info.short_description = 'Level'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('section__exam')

# Section Admin
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'exam_info', 'duration']
    list_filter = ['type', 'exam__level']
    search_fields = ['title', 'exam__title']
    
    def exam_info(self, obj):
        return f"{obj.exam.title} ({obj.exam.get_level_display()})"
    exam_info.short_description = 'Exam'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exam')

# Exam Admin
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'level', 'language', 'price', 'order_id', 'status']
    list_filter = ['level', 'language', 'status']
    search_fields = ['title']
    list_editable = ['order_id', 'status']

# TestResult Admin
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'section_info', 'exam_info', 'score', 'status', 'created_at']
    list_filter = ['status', 'section__type', 'user_test__exam__level']
    search_fields = ['user_test__user__first_name', 'user_test__user__last_name', 'user_test__user__username']
    readonly_fields = ['start_time', 'end_time', 'created_at']
    
    def user_name(self, obj):
        return obj.user_test.user.get_full_name()
    user_name.short_description = 'User'
    
    def section_info(self, obj):
        return f"{obj.section.title} ({obj.section.get_type_display()})"
    section_info.short_description = 'Section'
    
    def exam_info(self, obj):
        return f"{obj.user_test.exam.title} ({obj.user_test.exam.get_level_display()})"
    exam_info.short_description = 'Exam'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user_test__user', 'user_test__exam', 'section'
        )

# UserTest Admin
@admin.register(UserTest)
class UserTestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'exam_info', 'score', 'status', 'created_at']
    list_filter = ['status', 'exam__level', 'payment_status']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'exam__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    
    def exam_info(self, obj):
        return f"{obj.exam.title} ({obj.exam.get_level_display()})"
    exam_info.short_description = 'Exam'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'exam')

# QuestionScore Inline
class QuestionScoreInline(admin.TabularInline):
    model = QuestionScore
    extra = 0

# ReviewLog Inline
class ReviewLogInline(admin.TabularInline):
    model = ReviewLog
    extra = 0
    readonly_fields = ['reviewer', 'action', 'question_number', 'old_score', 'new_score', 'comment', 'created_at']

# ManualReview Admin
@admin.register(ManualReview)
class ManualReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'section', 'exam_info', 'status', 'total_score', 'reviewer_name', 'created_at']
    list_filter = ['status', 'section', 'test_result__user_test__exam__level']
    search_fields = ['test_result__user_test__user__first_name', 'test_result__user_test__user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuestionScoreInline, ReviewLogInline]
    
    def user_name(self, obj):
        return obj.test_result.user_test.user.get_full_name()
    user_name.short_description = 'User'
    
    def exam_info(self, obj):
        return f"{obj.test_result.user_test.exam.title} ({obj.test_result.user_test.exam.get_level_display()})"
    exam_info.short_description = 'Exam'
    
    def reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name()
        return "-"
    reviewer_name.short_description = 'Reviewer'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'test_result__user_test__user', 'test_result__user_test__exam', 'reviewer'
        )

# SubmissionMedia Admin
@admin.register(SubmissionMedia)
class SubmissionMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'section', 'question_number', 'file_type', 'uploaded_at']
    list_filter = ['section', 'file_type', 'test_result__user_test__exam__level']
    search_fields = ['test_result__user_test__user__first_name', 'test_result__user_test__user__last_name']
    
    def user_name(self, obj):
        return obj.test_result.user_test.user.get_full_name()
    user_name.short_description = 'User'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'test_result__user_test__user', 'test_result__user_test__exam'
        )

# ReviewLog Admin
@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'section', 'action', 'reviewer_name', 'created_at']
    list_filter = ['action', 'manual_review__section', 'manual_review__test_result__user_test__exam__level']
    search_fields = ['manual_review__test_result__user_test__user__first_name', 'manual_review__test_result__user_test__user__last_name']
    readonly_fields = ['manual_review', 'reviewer', 'action', 'question_number', 'old_score', 'new_score', 'comment', 'created_at']
    
    def user_name(self, obj):
        return obj.manual_review.test_result.user_test.user.get_full_name()
    user_name.short_description = 'User'
    
    def section(self, obj):
        return obj.manual_review.section
    
    def reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name()
        return "-"
    reviewer_name.short_description = 'Reviewer'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'manual_review__test_result__user_test__user', 'reviewer'
        )