from django.urls import path
from . import views

urlpatterns = [
    # Page 1: Overview
    path('', views.analytics_dashboard, name='dashboard'),
    
    # Page 2: Risk Tracker (Situation A)
    path('risk-tracker/', views.risk_tracker, name='risk_tracker'),
    
    # Page 3: Graduation (Situation B)
    path('graduation/', views.graduation_analytics, name='graduation'),
    
    # Page 4: Statistics (Insights)
    path('insights/', views.institutional_insights, name='insights'),
    
    # Page 5: Management (Engine)
    path('management/', views.data_management, name='management'),

    # Action URLs
    path('bulk-upload/', views.upload_semester_data, name='bulk_upload'),
    path('submit-record/', views.RecordCreateView.as_view(), name='submit_record'),
]