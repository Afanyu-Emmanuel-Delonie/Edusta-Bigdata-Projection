"""
Dashboard Views - Minimal Implementation
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from performance.models import Student, Course, Department, Teacher


@login_required
def dashboard_home(request):
    """Main dashboard"""
    try:
        context = {
            "total_students": Student.objects.count(),
            "total_departments": Department.objects.count(),
            "total_teachers": Teacher.objects.count(),
        }
        return render(request, "dashboard/dashboard.html", context)
    except Exception as e:
        messages.error(request, str(e))
        return redirect("home:home")


@login_required
def teacher_dashboard(request):
    """Teacher Dashboard"""
    return dashboard_home(request)


@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    return dashboard_home(request)


@login_required
def super_admin_dashboard(request):
    """Super Admin Dashboard"""
    return dashboard_home(request)
