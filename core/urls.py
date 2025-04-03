from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.main.views import redirect_to_docs
from core.swagger.schema import swagger_urlpatterns


urlpatterns = [
    path('', redirect_to_docs),
    path('admin/', admin.site.urls),
    path('user/', include("apps.users.urls")),
    path('multilevel/', include("apps.multilevel.urls")),
    path('main/', include("apps.main.urls")),
    path('payment/', include("apps.payment.urls")),
]

urlpatterns += swagger_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

