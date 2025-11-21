"""
Views for the Dashboard app
Protected area - requires authentication
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required  # Only logged-in users can access this view
def dashboard(request):
    """
    Main dashboard view
    
    This view is protected by @login_required decorator:
    - If user is not logged in, they are redirected to login page
    - After login, they are redirected back here
    
    Future features to add here:
    - Student grades
    - Course enrollment
    - ML prediction results
    - Personal information
    - Academic calendar
    """
    
    # Get the current logged-in user
    user = request.user
    
    context = {
        'page_title': 'Dashboard - AUCA',
        'user': user,
        'full_name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
    }
    
    return render(request, 'dashboard/dashboard.html', context)