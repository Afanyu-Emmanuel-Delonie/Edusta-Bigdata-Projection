# urls.py - Add this path to your urlpatterns

from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    # Dashboard views
    path('', views.performance_dashboard, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    
    # Reports and Recommendations (NEW)
    path('reports-recommendations/', views.reports_and_recommendations, name='reports_recommendations'),
    
    # Existing report page
    path('reports-recommendations/', views.reports_and_recommendations, name='reports_recommendations'),
    
    # Data management
    path('upload/', views.upload_csv, name='upload_csv'),
    path('export/', views.export_data, name='export_data'),
    
    # Student details
    path('student/<str:student_id>/', views.student_detail, name='student_detail'),
    
    # Recommendations
    path('resolve/<int:recommendation_id>/', views.resolve_recommendation, name='resolve_recommendation'),
    
    # API endpoints
    path('api/filter-options/', views.api_filter_options, name='api_filter_options'),
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/chart/<str:chart_name>/', views.api_chart, name='api_chart'),
    path('api/performances/', views.api_performances, name='api_performances'),
]