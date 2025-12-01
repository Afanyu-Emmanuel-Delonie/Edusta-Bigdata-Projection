"""
Dashboard Views for Student Performance Management
Handles role-based dashboards with KPIs, charts, tables, and recommendations
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Max, Min
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal

from performance.models import (
    Performance, Student, Course, Semester, Group, 
    Recommendation
)
from performance.charts import ChartGenerator


@login_required
def dashboard_home(request):
    """
    Main dashboard - redirects to appropriate role-based dashboard
    """
    try:
        user_role = request.user.role
        
        if user_role.is_super_admin():
            return redirect('dashboard:super_admin_dashboard')
        elif user_role.is_admin():
            return redirect('dashboard:admin_dashboard')
        elif user_role.is_teacher():
            return redirect('dashboard:teacher_dashboard')
        else:
            messages.error(request, 'Invalid user role')
            return redirect('accounts:login')
    
    except UserRole.DoesNotExist:
        messages.error(request, 'User role not assigned. Please contact administrator.')
        return redirect('accounts:login')


@login_required
def teacher_dashboard(request):
    """
    Teacher Dashboard - Shows performance data for teacher's courses
    Features: KPIs, Charts, Student Table, Filters, Recommendations
    """
    try:
        user_role = request.user.role
        
        if not user_role.is_teacher():
            messages.error(request, 'Access denied. Teacher role required.')
            return redirect('dashboard:dashboard_home')
    
    except UserRole.DoesNotExist:
        messages.error(request, 'User role not assigned.')
        return redirect('accounts:login')
    
    # Get filter parameters
    selected_course = request.GET.get('course', '')
    selected_group = request.GET.get('group', '')
    selected_semester = request.GET.get('semester', '')
    selected_status = request.GET.get('status', '')
    
    # Base queryset - teacher's courses only
    performances = Performance.objects.filter(
        course__teacher=request.user
    ).select_related('student', 'course', 'semester', 'group')
    
    # Apply filters
    if selected_course:
        performances = performances.filter(course_id=selected_course)
    
    if selected_group:
        performances = performances.filter(group_id=selected_group)
    
    if selected_semester:
        performances = performances.filter(semester_id=selected_semester)
    
    if selected_status:
        performances = performances.filter(performance_status=selected_status)
    
    # Get filter options
    teacher_courses = Course.objects.filter(teacher=request.user)
    
    if selected_course:
        groups = Group.objects.filter(course_id=selected_course)
    else:
        groups = Group.objects.filter(course__teacher=request.user)
    
    semesters = Semester.objects.all().order_by('-year', '-start_date')
    
    # Calculate KPIs
    kpis = calculate_kpis(performances)
    
    # Generate Charts
    charts = generate_dashboard_charts(performances, kpis)
    
    # Get student performance table data
    student_data = get_student_table_data(performances)
    
    # Get recommendations
    recommendations = get_recommendations(request.user, selected_course, selected_semester)
    
    # Score distribution data
    distribution_data = get_score_distribution(performances)
    
    # Course comparison data
    course_comparison = get_course_comparison(request.user)
    
    context = {
        'page_title': 'Teacher Dashboard',
        'user_role': user_role,
        'kpis': kpis,
        'charts': charts,
        'student_data': student_data,
        'recommendations': recommendations,
        'distribution_data': distribution_data,
        'course_comparison': course_comparison,
        
        # Filters
        'courses': teacher_courses,
        'groups': groups,
        'semesters': semesters,
        'status_choices': Performance.STATUS_CHOICES,
        
        # Selected filters
        'selected_course': selected_course,
        'selected_group': selected_group,
        'selected_semester': selected_semester,
        'selected_status': selected_status,
    }
    
    return render(request, 'dashboard/teacher_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """
    Admin Dashboard - Aggregated view across all courses
    No individual student details
    """
    try:
        user_role = request.user.role
        
        if not user_role.is_admin():
            messages.error(request, 'Access denied. Admin role required.')
            return redirect('dashboard:dashboard_home')
    
    except UserRole.DoesNotExist:
        messages.error(request, 'User role not assigned.')
        return redirect('accounts:login')
    
    # Get all performances
    performances = Performance.objects.all().select_related(
        'student', 'course', 'semester', 'group'
    )
    
    # Apply filters
    selected_semester = request.GET.get('semester', '')
    selected_department = request.GET.get('department', '')
    
    if selected_semester:
        performances = performances.filter(semester_id=selected_semester)
    
    if selected_department:
        performances = performances.filter(course__department=selected_department)
    
    # Calculate aggregated KPIs
    kpis = calculate_kpis(performances)
    
    # Generate aggregated charts
    charts = generate_dashboard_charts(performances, kpis)
    
    # Get aggregated course data (no student details)
    course_stats = get_aggregated_course_stats(performances)
    
    # Get department comparison
    department_comparison = get_department_comparison(performances)
    
    # Get semester trends
    semester_trends = get_semester_trends()
    
    # Get filter options
    semesters = Semester.objects.all().order_by('-year', '-start_date')
    departments = Course.objects.values_list('department', flat=True).distinct()
    
    context = {
        'page_title': 'Admin Dashboard',
        'user_role': user_role,
        'kpis': kpis,
        'charts': charts,
        'course_stats': course_stats,
        'department_comparison': department_comparison,
        'semester_trends': semester_trends,
        
        # Filters
        'semesters': semesters,
        'departments': departments,
        'selected_semester': selected_semester,
        'selected_department': selected_department,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def super_admin_dashboard(request):
    """
    Super Admin Dashboard - Complete system overview
    Full access to all data, students, courses, analytics
    """
    try:
        user_role = request.user.role
        
        if not user_role.is_super_admin():
            messages.error(request, 'Access denied. Super Admin role required.')
            return redirect('dashboard:dashboard_home')
    
    except UserRole.DoesNotExist:
        messages.error(request, 'User role not assigned.')
        return redirect('accounts:login')
    
    # Get all performances with filters
    performances = Performance.objects.all().select_related(
        'student', 'course', 'semester', 'group'
    )
    
    selected_course = request.GET.get('course', '')
    selected_semester = request.GET.get('semester', '')
    selected_department = request.GET.get('department', '')
    selected_status = request.GET.get('status', '')
    
    if selected_course:
        performances = performances.filter(course_id=selected_course)
    
    if selected_semester:
        performances = performances.filter(semester_id=selected_semester)
    
    if selected_department:
        performances = performances.filter(course__department=selected_department)
    
    if selected_status:
        performances = performances.filter(performance_status=selected_status)
    
    # System-wide KPIs
    kpis = calculate_kpis(performances)
    
    # Add system-wide metrics
    kpis['total_students'] = Student.objects.filter(is_active=True).count()
    kpis['total_courses'] = Course.objects.count()
    kpis['total_teachers'] = UserRole.objects.filter(role='teacher').count()
    kpis['active_semesters'] = Semester.objects.filter(is_active=True).count()
    
    # Generate comprehensive charts
    charts = generate_dashboard_charts(performances, kpis)
    
    # Get detailed student data
    student_data = get_student_table_data(performances)
    
    # Get all recommendations
    recommendations = Recommendation.objects.filter(
        is_resolved=False
    ).select_related('student', 'course', 'semester').order_by('-priority', '-created_at')[:20]
    
    # Course performance analysis
    course_comparison = get_all_courses_comparison()
    
    # Department analysis
    department_stats = get_department_comparison(performances)
    
    # Semester trends
    semester_trends = get_semester_trends()
    
    # Get filter options
    courses = Course.objects.all()
    semesters = Semester.objects.all().order_by('-year', '-start_date')
    departments = Course.objects.values_list('department', flat=True).distinct()
    
    context = {
        'page_title': 'Super Admin Dashboard',
        'user_role': user_role,
        'kpis': kpis,
        'charts': charts,
        'student_data': student_data,
        'recommendations': recommendations,
        'course_comparison': course_comparison,
        'department_stats': department_stats,
        'semester_trends': semester_trends,
        
        # Filters
        'courses': courses,
        'semesters': semesters,
        'departments': departments,
        'status_choices': Performance.STATUS_CHOICES,
        
        # Selected filters
        'selected_course': selected_course,
        'selected_semester': selected_semester,
        'selected_department': selected_department,
        'selected_status': selected_status,
    }
    
    return render(request, 'dashboard/super_admin_dashboard.html', context)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_kpis(performances_queryset):
    """
    Calculate Key Performance Indicators
    """
    if not performances_queryset.exists():
        return {
            'total_records': 0,
            'average_score': 0,
            'pass_rate': 0,
            'excellent_count': 0,
            'good_count': 0,
            'average_count': 0,
            'poor_count': 0,
            'highest_score': 0,
            'lowest_score': 0,
        }
    
    # Aggregate calculations
    stats = performances_queryset.aggregate(
        avg_score=Avg('score'),
        max_score=Max('score'),
        min_score=Min('score'),
        total=Count('id'),
    )
    
    # Count by performance status
    status_counts = performances_queryset.values('performance_status').annotate(
        count=Count('id')
    )
    
    status_dict = {item['performance_status']: item['count'] for item in status_counts}
    
    # Calculate pass rate (score >= 50)
    passing = performances_queryset.filter(score__gte=50).count()
    pass_rate = (passing / stats['total'] * 100) if stats['total'] > 0 else 0
    
    return {
        'total_records': stats['total'],
        'average_score': round(float(stats['avg_score'] or 0), 2),
        'pass_rate': round(pass_rate, 2),
        'excellent_count': status_dict.get('Excellent', 0),
        'good_count': status_dict.get('Good', 0),
        'average_count': status_dict.get('Average', 0),
        'poor_count': status_dict.get('Poor', 0),
        'highest_score': round(float(stats['max_score'] or 0), 2),
        'lowest_score': round(float(stats['min_score'] or 0), 2),
    }


def generate_dashboard_charts(performances_queryset, kpis):
    """
    Generate all dashboard charts
    """
    charts = {}
    
    # Score distribution chart
    distribution_data = get_score_distribution(performances_queryset)
    charts['score_distribution'] = ChartGenerator.generate_score_distribution(distribution_data)
    
    # Performance status pie chart
    charts['status_pie'] = ChartGenerator.generate_status_pie_chart(kpis)
    
    # Grade distribution
    charts['grade_distribution'] = ChartGenerator.generate_grade_distribution(performances_queryset)
    
    # Top vs Bottom performers
    top_performers = list(performances_queryset.order_by('-score')[:5].values(
        'student__student_id', 'student__first_name', 'student__last_name', 'score', 'course__code'
    ))
    bottom_performers = list(performances_queryset.order_by('score')[:5].values(
        'student__student_id', 'student__first_name', 'student__last_name', 'score', 'course__code'
    ))
    
    # Format for chart
    top_formatted = [{'student_id': p['student__student_id'], 'score': float(p['score'])} for p in top_performers]
    bottom_formatted = [{'student_id': p['student__student_id'], 'score': float(p['score'])} for p in bottom_performers]
    
    charts['top_bottom'] = ChartGenerator.generate_top_bottom_comparison(top_formatted, bottom_formatted)
    
    return charts


def get_score_distribution(performances_queryset):
    """
    Calculate score distribution for histogram
    """
    if not performances_queryset.exists():
        return {'bins': [], 'frequencies': []}
    
    bins = ['0-49', '50-59', '60-69', '70-79', '80-89', '90-100']
    frequencies = [
        performances_queryset.filter(score__lt=50).count(),
        performances_queryset.filter(score__gte=50, score__lt=60).count(),
        performances_queryset.filter(score__gte=60, score__lt=70).count(),
        performances_queryset.filter(score__gte=70, score__lt=80).count(),
        performances_queryset.filter(score__gte=80, score__lt=90).count(),
        performances_queryset.filter(score__gte=90).count(),
    ]
    
    return {'bins': bins, 'frequencies': frequencies}


def get_student_table_data(performances_queryset):
    """
    Get formatted student performance data for table
    """
    return performances_queryset.values(
        'student__student_id',
        'student__first_name',
        'student__last_name',
        'course__code',
        'course__name',
        'semester__name',
        'group__name',
        'score',
        'grade',
        'performance_status',
        'ranking',
    ).order_by('-score')[:100]  # Limit to 100 for performance


def get_recommendations(user, course_id=None, semester_id=None):
    """
    Get recommendations for teacher's courses
    """
    recommendations = Recommendation.objects.filter(
        course__teacher=user,
        is_resolved=False
    ).select_related('student', 'course', 'semester')
    
    if course_id:
        recommendations = recommendations.filter(course_id=course_id)
    
    if semester_id:
        recommendations = recommendations.filter(semester_id=semester_id)
    
    return recommendations.order_by('-priority', '-created_at')[:15]


def get_course_comparison(user):
    """
    Get average scores by course for teacher
    """
    courses = Course.objects.filter(teacher=user)
    
    course_data = []
    for course in courses:
        avg_score = Performance.objects.filter(course=course).aggregate(
            avg=Avg('score')
        )['avg']
        
        if avg_score:
            course_data.append({
                'course_code': course.code,
                'course_name': course.name,
                'average_score': round(float(avg_score), 2)
            })
    
    return course_data


def get_all_courses_comparison():
    """
    Get average scores for all courses
    """
    courses = Course.objects.all()
    
    course_data = []
    for course in courses:
        stats = Performance.objects.filter(course=course).aggregate(
            avg=Avg('score'),
            count=Count('id')
        )
        
        if stats['avg']:
            course_data.append({
                'course_code': course.code,
                'course_name': course.name,
                'average_score': round(float(stats['avg']), 2),
                'student_count': stats['count']
            })
    
    return sorted(course_data, key=lambda x: x['average_score'], reverse=True)


def get_aggregated_course_stats(performances_queryset):
    """
    Get aggregated statistics by course (no student details)
    """
    course_stats = performances_queryset.values('course__code', 'course__name').annotate(
        avg_score=Avg('score'),
        student_count=Count('student', distinct=True),
        pass_count=Count('id', filter=Q(score__gte=50)),
        excellent_count=Count('id', filter=Q(performance_status='Excellent')),
    ).order_by('-avg_score')
    
    # Calculate pass rate for each course
    result = []
    for stat in course_stats:
        pass_rate = (stat['pass_count'] / stat['student_count'] * 100) if stat['student_count'] > 0 else 0
        result.append({
            'course_code': stat['course__code'],
            'course_name': stat['course__name'],
            'avg_score': round(float(stat['avg_score']), 2),
            'student_count': stat['student_count'],
            'pass_rate': round(pass_rate, 2),
            'excellent_count': stat['excellent_count'],
        })
    
    return result


def get_department_comparison(performances_queryset):
    """
    Compare performance across departments
    """
    dept_stats = performances_queryset.values('course__department').annotate(
        avg_score=Avg('score'),
        student_count=Count('student', distinct=True),
        course_count=Count('course', distinct=True),
    ).order_by('-avg_score')
    
    result = []
    for stat in dept_stats:
        result.append({
            'department': stat['course__department'],
            'avg_score': round(float(stat['avg_score']), 2),
            'student_count': stat['student_count'],
            'course_count': stat['course_count'],
        })
    
    return result


def get_semester_trends():
    """
    Get performance trends across semesters
    """
    semesters = Semester.objects.all().order_by('year', 'start_date')
    
    trend_data = []
    for semester in semesters:
        avg_score = Performance.objects.filter(semester=semester).aggregate(
            avg=Avg('score')
        )['avg']
        
        if avg_score:
            trend_data.append({
                'semester': semester.name,
                'average_score': round(float(avg_score), 2)
            })
    
    return trend_data