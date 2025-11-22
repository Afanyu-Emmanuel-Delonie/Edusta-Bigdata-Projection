"""
URL Configuration for Dashboard App
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard - redirects based on role
    path('', views.dashboard_home, name='dashboard_home'),
    
    # Role-based dashboards
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
]