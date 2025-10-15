from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.static import serve
import os

from apps.main.views import redirect_to_docs
from apps.multilevel.auth_views import AdminLoginView, AdminLogoutView
from core.swagger.schema import swagger_urlpatterns


def serve_admin_dashboard(request, path='index.html'):
    """Serve admin dashboard static files"""
    import mimetypes
    from django.http import FileResponse, Http404
    
    # Base directory for admin dashboard
    dashboard_dir = os.path.join(settings.BASE_DIR, 'admin_dashboard')
    
    # If path is empty or just '/', serve index.html
    if not path or path == '/':
        path = 'index.html'
    
    # Build full file path
    file_path = os.path.join(dashboard_dir, path)
    
    # Security check: make sure the file is within dashboard_dir
    if not os.path.abspath(file_path).startswith(os.path.abspath(dashboard_dir)):
        raise Http404("Invalid path")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise Http404(f"File not found: {path}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    
    # Serve the file
    return FileResponse(open(file_path, 'rb'), content_type=content_type)


urlpatterns = [
    path('', redirect_to_docs),
    path('admin/', admin.site.urls),
    path('user/', include("apps.users.urls")),
    path('multilevel/', include("apps.multilevel.urls")),
    path('main/', include("apps.main.urls")),
    path('payment/', include("apps.payment.urls")),
    path('visitor/', include("apps.visitor.urls")),
    path('utils/', include("apps.utils.urls")),
    
    # Admin Dashboard Authentication
    path('api/token/', AdminLoginView.as_view(), name='admin_login'),
    path('api/logout/', AdminLogoutView.as_view(), name='admin_logout'),
    
    # Admin Dashboard
    path('admin-dashboard/', serve_admin_dashboard, {'path': 'index.html'}),
    path('admin-dashboard/<path:path>', serve_admin_dashboard),
]

urlpatterns += swagger_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)