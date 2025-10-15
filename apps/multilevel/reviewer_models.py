"""
Reviewer Proxy Model for better admin organization
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q

User = get_user_model()


class ReviewerProxyManager(models.Manager):
    """Custom manager for ReviewerProxy that returns all reviewers"""
    def get_queryset(self):
        """Return all users without filtering by staff status"""
        return super().get_queryset().filter(groups__name='Reviewer')


class ReviewerProxy(User):
    """
    Proxy model for User to create a separate Reviewers section in admin
    This allows us to manage reviewers separately from regular users
    """
    
    objects = ReviewerProxyManager()  # Custom manager
    
    class Meta:
        proxy = True
        verbose_name = "Tekshiruvchi"
        verbose_name_plural = "Tekshiruvchilar"
    
    def get_total_reviews(self):
        """Get total number of reviews completed by this reviewer"""
        return self.reviews.filter(status='checked').count()
    
    def get_writing_reviews(self):
        """Get number of writing reviews"""
        return self.reviews.filter(status='checked', section='writing').count()
    
    def get_speaking_reviews(self):
        """Get number of speaking reviews"""
        return self.reviews.filter(status='checked', section='speaking').count()
    
    def get_average_score(self):
        """Get average score given by this reviewer"""
        from django.db.models import Avg
        avg = self.reviews.filter(status='checked').aggregate(Avg('total_score'))['total_score__avg']
        return round(avg, 2) if avg else 0
    
    def get_latest_review_date(self):
        """Get date of last review"""
        latest = self.reviews.filter(status='checked').order_by('-reviewed_at').first()
        return latest.reviewed_at if latest else None

