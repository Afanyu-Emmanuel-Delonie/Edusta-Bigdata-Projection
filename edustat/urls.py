"""
Main URL Configuration for AUCA Clone Project
This file routes URLs to the appropriate apps.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin panel - accessible at /admin/
    path('admin/', admin.site.urls),
    
    # Accounts app - handles login, logout, registration
    path('accounts/', include('accounts.urls')),
    
    # Redirect root to performance dashboard
    path('', RedirectView.as_view(url='/performance/', permanent=False)),
    
    # Performance app - handles performance metrics and reports
    path('performance/', include('performance.urls', namespace='performance')),
]

# Serve media files in development
# In production, use a web server like Nginx to serve these
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)