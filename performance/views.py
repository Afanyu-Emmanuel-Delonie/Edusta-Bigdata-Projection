""" Views for Performance Dashboard System
    Handles teacher, admin, and super admin dashboards
    NO LOGIN REQUIRED - Open access for development
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
import csv
import io

from .models import Performance, Course, Semester, Group, Recommendation
from .forms import CSVUploadForm, DashboardFilterForm, ExportForm
from .csv_processor import process_csv_upload
from .analysis import PerformanceAnalyzer
from .charts import ChartGenerator


def performance_dashboard(request):
    """
    Main dashboard - accessible without login
    Everyone gets full access (super admin view)
    """
    return teacher_dashboard(request)


def teacher_dashboard(request):
    """
    Teacher Dashboard - Open access for everyone
    """
    # Get filters from request
    user = request.user if request.user.is_authenticated else None
    filter_form = DashboardFilterForm(request.GET or None, user=user)
    filters = {}
    
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        # collect possible filters; model instances have an 'id' attribute
        for key in ('course', 'semester', 'group', 'status'):
            if (val := cd.get(key)):
                filters[key] = getattr(val, 'id', val)
    
    # Initialize analyzer with filters
    analyzer = PerformanceAnalyzer(user, filters=filters)

    # Calculate KPIs
    kpis = analyzer.calculate_kpis()
    
    # Get performance distribution
    distribution = analyzer.get_performance_distribution()
    
    # Get top and bottom performers
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    
    # Get course comparison
    course_comparison = analyzer.get_course_comparison()
    
    # Get semester trend
    semester_trend = analyzer.get_semester_trend()
    
    # Generate charts
    chart_generator = ChartGenerator()
    charts = {
        'distribution': chart_generator.generate_score_distribution(distribution),
        'status_pie': chart_generator.generate_status_pie_chart(kpis),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
        'top_bottom': chart_generator.generate_top_bottom_comparison(top_performers, bottom_performers),
        'grade_distribution': chart_generator.generate_grade_distribution(analyzer.get_filtered_queryset()),
    }
    
    # Get student performance table
    performances_queryset = analyzer.get_filtered_queryset()
    
    # Apply search if provided
    search_query = request.GET.get('search', '')
    if search_query:
        performances_queryset = performances_queryset.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(performances_queryset, 25)
    page_number = request.GET.get('page', 1)
    performances_page = paginator.get_page(page_number)
    
    # Get recommendations
    recommendations = analyzer.get_recommendations(unresolved_only=True)[:10]
    
    context = {
        'page_title': 'Teacher Dashboard',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'performances': performances_page,
        'top_performers': top_performers[:5],
        'bottom_performers': bottom_performers[:5],
        'recommendations': recommendations,
        'search_query': search_query,
    }
    
    return render(request, 'performance/teacher_dashboard.html', context)


def admin_dashboard(request):
    """
    Admin Dashboard - Open access for everyone
    """
    # Get filters
    user = request.user if request.user.is_authenticated else None
    filter_form = DashboardFilterForm(request.GET or None)
    filters = {}
    
    if filter_form.is_valid():
        if (sem := filter_form.cleaned_data.get('semester')):
            filters['semester'] = sem.id
    
    # Initialize analyzer (admin sees all data)
    analyzer = PerformanceAnalyzer(user)
    
    # Calculate KPIs
    kpis = analyzer.calculate_kpis()
    
    # Get aggregated data
    distribution = analyzer.get_performance_distribution()
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()
    
    # Generate charts
    chart_generator = ChartGenerator()
    charts = {
        'distribution': chart_generator.generate_score_distribution(distribution),
        'status_pie': chart_generator.generate_status_pie_chart(kpis),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
    }
    
    # Get course-level recommendations (not student-specific)
    recommendations = []
    for course_stat in course_comparison:
        if course_stat['pass_rate'] < 60:
            recommendations.append({
                'priority': 'high',
                'text': f"Course {course_stat['course_code']} has low pass rate ({course_stat['pass_rate']:.1f}%). Consider reviewing curriculum or teaching methods."
            })
        elif course_stat['average_score'] < 70:
            recommendations.append({
                'priority': 'medium',
                'text': f"Course {course_stat['course_code']} has average performance ({course_stat['average_score']:.1f}). Additional support may be needed."
            })
    
    context = {
        'page_title': 'Admin Dashboard',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'course_comparison': course_comparison,
        'recommendations': recommendations,
    }
    
    return render(request, 'performance/admin_dashboard.html', context)


def super_admin_dashboard(request):
    """
    Super Admin Dashboard
    Renders the same dashboard but with super-admin context (full access).
    """
    # Build filters from request
    user = request.user if request.user.is_authenticated else None
    filter_form = DashboardFilterForm(request.GET or None, user=user)
    filters = {}

    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        for key in ('course', 'semester', 'group', 'status'):
            if (val := cd.get(key)):
                filters[key] = getattr(val, 'id', val)

    # Initialize analyzer with filters (super admin sees all data)
    analyzer = PerformanceAnalyzer(user, filters=filters)

    # Calculate KPIs & get charts/data
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()

    chart_generator = ChartGenerator()
    charts = {
        'distribution': chart_generator.generate_score_distribution(distribution),
        'status_pie': chart_generator.generate_status_pie_chart(kpis),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
        'top_bottom': chart_generator.generate_top_bottom_comparison(top_performers, bottom_performers),
        'grade_distribution': chart_generator.generate_grade_distribution(analyzer.get_filtered_queryset()),
    }

    # Student table
    performances_queryset = analyzer.get_filtered_queryset()

    # Apply search if provided
    search_query = request.GET.get('search', '')
    if search_query:
        performances_queryset = performances_queryset.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )

    paginator = Paginator(performances_queryset, 25)
    page_number = request.GET.get('page', 1)
    performances_page = paginator.get_page(page_number)

    recommendations = analyzer.get_recommendations(unresolved_only=True)[:20]

    context = {
        'page_title': 'Super Admin Dashboard',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'performances': performances_page,
        'top_performers': top_performers[:5],
        'bottom_performers': bottom_performers[:5],
        'recommendations': recommendations,
        'search_query': search_query,
        'is_super_admin': True,
    }

    return render(request, 'performance/teacher_dashboard.html', context)

def api_filter_options(request):
    """Return available filter options (courses, semesters, groups)"""
    from .models import Course, Semester, Group
    
    courses = list(Course.objects.values('id', 'code', 'name'))
    semesters = list(Semester.objects.values('id', 'name'))
    groups = list(Group.objects.values('id', 'name'))
    
    return JsonResponse({
        'courses': courses,
        'semesters': semesters,
        'groups': groups
    })
    
    
def upload_csv(request):
    """
    Handle CSV/Excel file upload - Open access
    """
    user = request.user if request.user.is_authenticated else None
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']

            # Process the file
            results = process_csv_upload(file, user)

            # If AJAX request, return JSON instead of redirecting
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

            if results['success']:
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'success_count': results.get('success_count', 0),
                        'error_count': results.get('error_count', 0),
                        'errors': results.get('errors', []),
                    })

                messages.success(
                    request,
                    f"File uploaded successfully! {results['success_count']} records imported."
                )
                if results['error_count'] > 0:
                    messages.warning(
                        request,
                        f"{results['error_count']} records had errors."
                    )
                return redirect('performance:dashboard')
            else:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': results.get('errors', [])
                    }, status=400)

                for error in results['errors']:
                    messages.error(request, error)
    else:
        form = CSVUploadForm()
    
    context = {
        'page_title': 'Upload Student Data',
        'form': form,
    }
    
    return render(request, 'performance/upload_csv.html', context)


def export_data(request):
    """
    Export performance data to CSV - Open access
    """
    user = request.user if request.user.is_authenticated else None
    
    # Get filters
    filters = {}
    if (course := request.GET.get('course')):
        filters['course'] = course
    if (semester := request.GET.get('semester')):
        filters['semester'] = semester
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(user)
    
    # Get DataFrame
    df = analyzer.export_to_dataframe()
    
    if df.empty:
        messages.warning(request, 'No data to export.')
        return redirect('performance:dashboard')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="performance_data.csv"'
    
    # Write DataFrame to CSV
    df.to_csv(response, index=False)
    
    return response


def resolve_recommendation(request, recommendation_id):
    """
    Mark a recommendation as resolved - Open access
    """
    user = request.user if request.user.is_authenticated else None
    recommendation = get_object_or_404(Recommendation, id=recommendation_id)
    
    recommendation.is_resolved = True
    recommendation.resolved_by = user
    from django.utils import timezone
    recommendation.resolved_at = timezone.now()
    recommendation.save()
    
    messages.success(request, 'Recommendation marked as resolved.')
    return redirect('performance:dashboard')


def student_detail(request, student_id):
    """
    View detailed performance for a specific student - Open access
    """
    from .models import Student
    user = request.user if request.user.is_authenticated else None
    student = get_object_or_404(Student, student_id=student_id)
    
    # Everyone sees all performances (no restrictions)
    performances = Performance.objects.filter(student=student)
    
    performances = performances.select_related('course', 'semester', 'group').order_by('-semester__start_date')
    
    # Calculate student stats
    if performances.exists():
        scores = [float(p.score) for p in performances]
        student_stats = {
            'average_score': sum(scores) / len(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'total_courses': performances.values('course').distinct().count(),
        }
    else:
        student_stats = None
    
    context = {
        'page_title': f'Student: {student.get_full_name()}',
        'student': student,
        'performances': performances,
        'student_stats': student_stats,
    }
    
    return render(request, 'performance/student_detail.html', context)


def api_kpis(request):
    """API endpoint returning KPIs as JSON"""
    user = request.user if request.user.is_authenticated else None
    # Build filters from GET params
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search'):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    analyzer = PerformanceAnalyzer(user, filters=filters)

    # Base KPIs
    kpis = analyzer.calculate_kpis()

    # Add status counts directly from queryset for accuracy
    qs = analyzer.get_filtered_queryset()
    kpis.update({
        'excellent_count': qs.filter(score__gte=85).count(),
        'good_count': qs.filter(score__gte=70, score__lt=85).count(),
        'average_count': qs.filter(score__gte=50, score__lt=70).count(),
        'poor_count': qs.filter(score__lt=50).count(),
    })

    return JsonResponse(kpis)


def api_chart(request, chart_name):
    """Return a chart image (base64) for the requested chart name."""
    user = request.user if request.user.is_authenticated else None
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search'):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    analyzer = PerformanceAnalyzer(user, filters=filters)
    chart_generator = ChartGenerator()

    chart = None
    if chart_name == 'distribution':
        distribution = analyzer.get_performance_distribution()
        chart = chart_generator.generate_score_distribution(distribution)
    elif chart_name == 'status_pie':
        # Use KPIs to generate pie chart
        kpis = analyzer.calculate_kpis()
        # ensure status counts are present
        qs = analyzer.get_filtered_queryset()
        kpis.update({
            'excellent_count': qs.filter(score__gte=85).count(),
            'good_count': qs.filter(score__gte=70, score__lt=85).count(),
            'average_count': qs.filter(score__gte=50, score__lt=70).count(),
            'poor_count': qs.filter(score__lt=50).count(),
        })
        chart = chart_generator.generate_status_pie_chart(kpis)
    elif chart_name == 'course_comparison':
        course_comp = analyzer.get_course_comparison()
        chart = chart_generator.generate_course_comparison(course_comp)
    elif chart_name == 'semester_trend':
        sem_trend = analyzer.get_semester_trend()
        chart = chart_generator.generate_semester_trend(sem_trend)
    elif chart_name == 'top_bottom':
        top = analyzer.get_top_performers(10)
        bottom = analyzer.get_bottom_performers(10)
        chart = chart_generator.generate_top_bottom_comparison(top, bottom)
    elif chart_name == 'grade_distribution':
        chart = chart_generator.generate_grade_distribution(analyzer.get_filtered_queryset())

    if not chart:
        return JsonResponse({'error': 'Chart not available'}, status=404)

    return JsonResponse({'chart': chart})


def api_performances(request):
    """Return student performance table data as JSON (supports pagination and search)."""
    user = request.user if request.user.is_authenticated else None
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search'):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    analyzer = PerformanceAnalyzer(user, filters=filters)
    qs = analyzer.get_filtered_queryset()

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        qs = qs.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )

    # Pagination
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 25))
    except ValueError:
        page_size = 25

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    data = []
    for perf in page_obj:
        data.append({
            'student_id': perf.student.student_id,
            'name': perf.student.get_full_name(),
            'course': perf.course.code,
            'semester': perf.semester.name,
            'score': float(perf.score),
            'grade': perf.grade,
            'status': perf.performance_status,
            'ranking': perf.ranking,
        })

    return JsonResponse({
        'results': data,
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'total': paginator.count,
    })