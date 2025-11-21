"""
URL patterns for the Home app
Maps URLs to views
"""

from django.urls import path
from . import views

# App namespace for better organization
app_name = 'home'

urlpatterns = [
    # Homepage route - accessible at /
    path('', views.home, name='home'),
]