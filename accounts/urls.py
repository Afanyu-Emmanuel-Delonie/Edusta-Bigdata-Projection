"""
URL patterns for the Accounts app
Maps authentication URLs to views
"""

from django.urls import path
from . import views

# App namespace
app_name = 'accounts'

urlpatterns = [
    # Login page - accessible at /accounts/login/
    path('login/', views.user_login, name='login'),
    
    # Logout - accessible at /accounts/logout/
    path('logout/', views.user_logout, name='logout'),
]