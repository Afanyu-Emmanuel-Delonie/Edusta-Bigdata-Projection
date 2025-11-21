"""
Views for the Accounts app
Handles user authentication (login/logout)
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm

def user_login(request):
    """
    Handle user login
    
    GET: Display login form
    POST: Process login credentials
    
    Security features:
    - CSRF protection (automatic with Django)
    - Password hashing (automatic with Django auth)
    - Session-based authentication
    - Failed login messages
    """
    
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        
        if form.is_valid():
            # Get username and password from form
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            # Authenticate user (checks username and password)
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Log the user in (creates session)
                login(request, user)
                
                # Handle "Remember Me" functionality
                if not remember_me:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                else:
                    # Session lasts for 2 weeks
                    request.session.set_expiry(1209600)
                
                # Success message
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Redirect to dashboard or next page
                next_url = request.GET.get('next', 'dashboard:dashboard')
                return redirect(next_url)
            else:
                # Invalid credentials
                messages.error(request, 'Invalid email/ID or password.')
        else:
            # Form validation failed
            messages.error(request, 'Please correct the errors below.')
    else:
        # GET request - show empty form
        form = CustomLoginForm()
    
    context = {
        'form': form,
        'page_title': 'Login - AUCA'
    }
    
    return render(request, 'accounts/login.html', context)


@login_required  # This decorator ensures only logged-in users can access this view
def user_logout(request):
    """
    Handle user logout
    
    Logs out the user and redirects to homepage
    The @login_required decorator ensures only logged-in users can logout
    """
    
    # Log the user out (destroys session)
    logout(request)
    
    # Success message
    messages.success(request, 'You have been logged out successfully.')
    
    # Redirect to homepage
    return redirect('home:home')