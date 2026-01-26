from django.urls import path
from . import views

app_name = 'performance'  # Add this line

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('risk-tracker/', views.risk_tracker, name='risk_tracker'),
    path('graduation/', views.graduation_analytics, name='graduation'),
    path('insights/', views.institutional_insights, name='insights'),
    path('management/', views.data_management, name='management'),
    path('bulk-upload/', views.upload_semester_data, name='bulk_upload'),
    path('submit-record/', views.submit_record, name='submit_record'),
]