from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('', views.performance_dashboard, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('student/<str:student_id>/', views.student_detail, name='student_detail'),
    path('export/', views.export_data, name='export_data'),
    path('api/filters/', views.api_filter_options, name='api_filter_options'),
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/performances/', views.api_performances, name='api_performances'),

    # Updated this line: name should match your template
    path('reports/', views.reports_and_recommendations, name='reports_recommendations'),
]
