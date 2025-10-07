from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class AdminDashboardView(UserPassesTestMixin, TemplateView):
    """View for serving admin dashboard HTML files"""
    
    def test_func(self):
        # Allow access only for staff/admin users
        # For now, allow all to test, but you should enable this in production
        return True  # Change to: return self.request.user.is_staff
    
    def get_template_names(self):
        # Get the requested path
        path = self.kwargs.get('path', 'index.html')
        
        # If no extension, assume it's a page and add .html
        if '.' not in path:
            path = f"{path}.html"
        
        return [f"admin_dashboard/{path}"]
    
    def handle_no_permission(self):
        return redirect('admin:login')
