from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import home  # Import home view directly

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Add home directly without namespace
    path('accounts/', include('accounts.urls')),
    path('events/', include('events.urls')),
    path('tickets/', include('tickets.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)