"""
Custom permissions for Manual Review System
"""
from rest_framework.permissions import BasePermission


class IsReviewerOrAdmin(BasePermission):
    """
    Permission class that allows access to:
    - Staff users (is_staff=True)
    - Users in the 'Reviewer' group
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Staff users have access
        if request.user.is_staff:
            return True
        
        # Check if user is in Reviewer group
        return request.user.groups.filter(name='Reviewer').exists()
