from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    # ===== DASHBOARDS =====
    path('', views.performance_dashboard, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    
    # ===== ML DASHBOARD =====
    path('ml/', views.ml_dashboard, name='ml_dashboard'),
    path('ml/run-predictions/', views.run_predictions_view, name='run_predictions'),
    path('ml/analytics-api/', views.ml_analytics_api, name='ml_analytics_api'),
    path('ml/export/', views.export_ml_report, name='export_ml_report'),
    
    # ===== DATA MANAGEMENT =====
    path('upload/', views.upload_csv, name='upload_csv'),
    path('export/', views.export_data, name='export_data'),
    
    # ===== STUDENT VIEWS =====
    path('student/<str:student_id>/', views.student_detail, name='student_detail'),
    path('student/<str:student_id>/ml-profile/', views.student_ml_profile, name='student_ml_profile'),
    
    
    # ===== API ENDPOINTS =====
    path('api/filters/', views.api_filter_options, name='api_filter_options'),
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/performances/', views.api_performances, name='api_performances'),
    path('reset-data/', views.reset_all_data, name='reset_data'),
]