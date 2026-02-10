
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static

# URLs that should not be translated
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('health/', include('health_check.urls')),
    path('api/memory/', include('project_memory.urls')), # Added Memory API
]

# URLs that should be translated
urlpatterns += i18n_patterns(
    path('', include('coredata.urls')),
    # Add other app URLs here if they need to be translated
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)