"""
URL patterns for the Dashboard app
All routes here are protected (require login)
"""

from django.urls import path
from . import views

# App namespace
app_name = 'dashboard'

urlpatterns = [
    # Dashboard homepage - accessible at /dashboard/
    path('', views.dashboard, name='dashboard'),
]