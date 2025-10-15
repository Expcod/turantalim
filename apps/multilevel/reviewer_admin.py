"""
Comprehensive Reviewer Admin Interface
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .reviewer_models import ReviewerProxy
from .reviewer_forms import ReviewerCreationForm, ReviewerChangeForm
from .models import ManualReview

User = get_user_model()


class ReviewerReviewInline(admin.TabularInline):
    """
    Inline to show all reviews done by a reviewer
    """
    model = ManualReview
    extra = 0
    can_delete = False
    
    fields = ('review_link', 'user_name', 'section', 'exam_name', 'total_score', 'reviewed_at', 'status')
    readonly_fields = ('review_link', 'user_name', 'section', 'exam_name', 'total_score', 'reviewed_at', 'status')
    
    def review_link(self, obj):
        """Link to the manual review detail page"""
        if obj.id:
            url = reverse('admin:multilevel_manualreview_change', args=[obj.id])
            return format_html('<a href="{}" target="_blank">Tekshiruv #{}</a>', url, obj.id)
        return '-'
    review_link.short_description = 'Tekshiruv ID'
    
    def user_name(self, obj):
        """Get student name"""
        return obj.test_result.user_test.user.get_full_name()
    user_name.short_description = 'Talaba'
    
    def exam_name(self, obj):
        """Get exam name"""
        return f"{obj.test_result.user_test.exam.title} ({obj.test_result.user_test.exam.level})"
    exam_name.short_description = 'Imtihon'
    
    def get_queryset(self, request):
        """Only show checked reviews"""
        qs = super().get_queryset(request)
        return qs.filter(status='checked').select_related(
            'test_result__user_test__user',
            'test_result__user_test__exam'
        ).order_by('-reviewed_at')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ReviewerProxy)
class ReviewerAdmin(admin.ModelAdmin):
    """
    Custom admin for managing Reviewers with statistics
    """
    form = ReviewerChangeForm
    # add_form = ReviewerCreationForm  # Not used with ModelAdmin
    
    list_display = [
        'phone',
        'first_name',
        'last_name',
        'email',
        'admin_status_display',
        'is_active',
        'date_joined'
    ]
    
    list_filter = ['is_active', 'date_joined', 'groups__name']
    search_fields = ['phone', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    list_per_page = 100  # Show 100 items per page
    list_max_show_all = 200  # Allow showing all if less than 200
    
    fieldsets = (
        ('Asosiy Ma\'lumotlar', {
            'fields': ('phone', 'first_name', 'last_name', 'email')
        }),
        ('Statistika', {
            'fields': ('stats_display',),
            'classes': ('wide',),
            'description': 'Tekshiruvchi statistikasi'
        }),
        ('Holati', {
            'fields': ('is_active',),
            'description': 'Tekshiruvchi faolmi?'
        }),
        ('Muhim Sanalar', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'last_name', 'email', 'password1', 'password2'),
            'description': format_html(
                '<div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">'
                '<strong>Yangi Tekshiruvchi Yaratish</strong><br>'
                'Tekshiruvchi avtomatik ravishda "Reviewer" guruhiga qo\'shiladi.<br>'
                '<ul style="margin-top: 10px;">'
                '<li>Telefon raqami login sifatida ishlatiladi</li>'
                '<li>Istalgan parolni kiriting (validatsiya yo\'q)</li>'
                '<li>Tekshiruvchi admin-dashboard ga kira oladi</li>'
                '<li>Django admin panelga kirish huquqi bo\'lmaydi</li>'
                '</ul>'
                '</div>'
            )
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'stats_display']
    inlines = [ReviewerReviewInline]
    
    def get_queryset(self, request):
        """Show only users in Reviewer group (including staff/superuser reviewers)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get ALL users in Reviewer group - NO FILTERING by staff status
        qs = User.objects.filter(groups__name='Reviewer').distinct()
        
        # Add review statistics annotations
        return qs.annotate(
            total_reviews=Count('reviews', filter=Q(reviews__status='checked')),
            writing_count=Count('reviews', filter=Q(reviews__status='checked', reviews__section='writing')),
            speaking_count=Count('reviews', filter=Q(reviews__status='checked', reviews__section='speaking')),
            avg_score=Avg('reviews__total_score', filter=Q(reviews__status='checked'))
        )
    
    def admin_status_display(self, obj):
        """Show if reviewer is also staff/superuser"""
        if obj.is_superuser:
            return format_html('<span style="color: red; font-weight: bold;">👑 Superuser</span>')
        elif obj.is_staff:
            return format_html('<span style="color: orange; font-weight: bold;">⚡ Xodim</span>')
        return format_html('<span style="color: gray;">-</span>')
    admin_status_display.short_description = 'Admin Holati'
    
    def total_reviews_display(self, obj):
        """Display total reviews with icon"""
        count = obj.total_reviews if hasattr(obj, 'total_reviews') else obj.get_total_reviews()
        color = 'green' if count > 10 else 'orange' if count > 0 else 'gray'
        return format_html(
            '<span style="color: {}; font-weight: bold;">📊 {}</span>',
            color, count
        )
    total_reviews_display.short_description = 'Jami Tekshiruvlar'
    total_reviews_display.admin_order_field = 'total_reviews'
    
    def writing_reviews_display(self, obj):
        """Display writing reviews"""
        count = obj.writing_count if hasattr(obj, 'writing_count') else obj.get_writing_reviews()
        return format_html('<span style="color: #1976d2;">✍️ {}</span>', count)
    writing_reviews_display.short_description = 'Yozish'
    writing_reviews_display.admin_order_field = 'writing_count'
    
    def speaking_reviews_display(self, obj):
        """Display speaking reviews"""
        count = obj.speaking_count if hasattr(obj, 'speaking_count') else obj.get_speaking_reviews()
        return format_html('<span style="color: #d32f2f;">🎤 {}</span>', count)
    speaking_reviews_display.short_description = 'Gapirish'
    speaking_reviews_display.admin_order_field = 'speaking_count'
    
    def average_score_display(self, obj):
        """Display average score"""
        avg = obj.avg_score if hasattr(obj, 'avg_score') else obj.get_average_score()
        avg = round(avg, 2) if avg else 0
        color = 'green' if avg >= 70 else 'orange' if avg >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, avg
        )
    average_score_display.short_description = 'O\'rtacha Ball'
    average_score_display.admin_order_field = 'avg_score'
    
    def last_review_date(self, obj):
        """Display last review date"""
        date = obj.get_latest_review_date()
        if date:
            # Calculate time difference
            now = timezone.now()
            diff = now - date
            
            if diff.days == 0:
                time_str = 'Bugun'
            elif diff.days == 1:
                time_str = 'Kecha'
            elif diff.days < 7:
                time_str = f'{diff.days} kun oldin'
            else:
                time_str = date.strftime('%d.%m.%Y')
            
            return format_html(
                '<span title="{}">{}</span>',
                date.strftime('%d.%m.%Y %H:%M'),
                time_str
            )
        return format_html('<span style="color: gray;">-</span>')
    last_review_date.short_description = 'Oxirgi Tekshiruv'
    
    def stats_display(self, obj):
        """Display comprehensive statistics"""
        if not obj or not obj.pk:
            return '<span style="color: gray;">Ma\'lumot yo\'q</span>'
        
        # Calculate statistics directly from ManualReview model
        from apps.multilevel.models import ManualReview
        from django.db.models import Avg
        
        total = ManualReview.objects.filter(reviewer=obj, status='checked').count()
        writing = ManualReview.objects.filter(reviewer=obj, status='checked', section='writing').count()
        speaking = ManualReview.objects.filter(reviewer=obj, status='checked', section='speaking').count()
        
        avg_result = ManualReview.objects.filter(reviewer=obj, status='checked').aggregate(Avg('total_score'))
        avg = round(avg_result['total_score__avg'], 2) if avg_result['total_score__avg'] else 0
        
        last_review = ManualReview.objects.filter(reviewer=obj, status='checked').order_by('-reviewed_at').first()
        last_date = last_review.reviewed_at if last_review else None
        
        html = f'''
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px;">
            <h3 style="margin-top: 0;">Tekshiruvchi Statistikasi</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Jami Tekshiruvlar:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <span style="font-size: 18px; color: #1976d2; font-weight: bold;">{total}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Yozish Bo'limi:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <span style="color: #1976d2;">✍️ {writing}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <strong>Gapirish Bo'limi:</strong>
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <span style="color: #d32f2f;">🎤 {speaking}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;">
                        <strong>Oxirgi Tekshiruv:</strong>
                    </td>
                    <td style="padding: 10px;">
                        {last_date.strftime('%d.%m.%Y %H:%M') if last_date else '-'}
                    </td>
                </tr>
            </table>
        </div>
        '''
        return format_html(html)
    stats_display.short_description = 'Statistika'
    
    def save_model(self, request, obj, form, change):
        """Ensure user is properly set up as reviewer"""
        # Only set is_staff/is_superuser to False for NEW reviewers
        # Allow existing staff/superuser to remain as reviewer
        if not change:  # New object being created
            obj.is_staff = False
            obj.is_superuser = False
        
        super().save_model(request, obj, form, change)
        
        # Ensure user is in Reviewer group
        from django.contrib.auth.models import Group
        try:
            reviewer_group = Group.objects.get(name='Reviewer')
            if not obj.groups.filter(name='Reviewer').exists():
                obj.groups.add(reviewer_group)
        except Group.DoesNotExist:
            self.message_user(
                request,
                'Ogohlantirish: Reviewer guruhi topilmadi. python manage.py setup_reviewers commandni ishga tushiring.',
                level='warning'
            )
    
    def delete_model(self, request, obj):
        """Custom delete with confirmation"""
        self.message_user(
            request,
            f'Tekshiruvchi {obj.get_full_name()} o\'chirildi. Uning barcha tekshiruvlari saqlanib qoladi.',
            level='warning'
        )
        super().delete_model(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete reviewers"""
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """Allow viewing all reviewers"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Allow changing all reviewers"""
        return request.user.has_perm('users.change_user')
    
    def get_readonly_fields(self, request, obj=None):
        """Make phone readonly for existing users"""
        if obj:  # Editing existing user
            return self.readonly_fields + ['phone']
        return self.readonly_fields
    