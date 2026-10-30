"""
URL configuration for parkease project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import welcome_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', welcome_view, name='home'),
    path('', include('accounts.urls')),
    path('', include('parking.urls')),
    path('', include('bookings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
