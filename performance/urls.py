"""
URL patterns for Performance Dashboard
"""

from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    # Main dashboard (routes based on role)
    path('', views.performance_dashboard, name='dashboard'),
    
    # Role-specific dashboards
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    
    # CSV Upload
    path('upload/', views.upload_csv, name='upload_csv'),
    
    # Export
    path('export/', views.export_data, name='export_data'),
    
    # Recommendations
    path('recommendation/<int:recommendation_id>/resolve/', 
         views.resolve_recommendation, 
         name='resolve_recommendation'),
    
    # Student detail
    path('student/<str:student_id>/', views.student_detail, name='student_detail'),
    # API endpoints for dynamic dashboard updates
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/chart/<str:chart_name>/', views.api_chart, name='api_chart'),
    path('api/performances/', views.api_performances, name='api_performances'),
    path('api/filter-options/', views.api_filter_options, name='api_filter_options'),
]