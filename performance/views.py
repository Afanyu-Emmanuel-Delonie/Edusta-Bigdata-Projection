""" Views for Performance Dashboard System
    Handles teacher, admin, and super admin dashboards
    WITH DYNAMIC FILTERS based on actual dataset
"""
# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.http import HttpResponse, JsonResponse

# Your models
from .models import (
    Student, 
    Performance, 
    Semester, 
    Course, 
    Group, 
    Dataset,
    Recommendation
)

# Your forms
from .forms import CSVUploadForm, DashboardFilterForm, ExportForm

# Your utilities
from .csv_processor import process_csv_upload
from .analysis import PerformanceAnalyzer
from .charts import ChartGenerator

# Python standard library
import json
from decimal import Decimal
import csv
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder

# For file handling
import pandas as pd
import openpyxl


def performance_dashboard(request):
    """Main dashboard - accessible without login"""
    return teacher_dashboard(request)


def teacher_dashboard(request):
    """Teacher Dashboard with DYNAMIC filters"""
    user = request.user if request.user.is_authenticated else None
    
    # Extract current filter values
    current_filters = {}
    for key in ['department', 'course', 'semester', 'group', 'status']:
        val = request.GET.get(key)
        if val:
            try:
                current_filters[key] = int(val) if key != 'department' and key != 'status' else val
            except (ValueError, TypeError):
                current_filters[key] = val
    
    # Initialize form with current filters for cascading
    filter_form = DashboardFilterForm(
        request.GET or None,
        user=user,
        current_filters=current_filters
    )
    
    # Build filters for analyzer
    filters = {}
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        
        # Department filter (new)
        if cd.get('department'):
            filters['department'] = cd['department']
        
        # Other filters
        for key in ('course', 'semester', 'group', 'status'):
            if cd.get(key):
                filters[key] = cd[key]
    
    # Initialize analyzer with filters
    analyzer = PerformanceAnalyzer(user, filters=filters)
    
    # Calculate KPIs & get charts/data
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    
    # Get top and bottom performers
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    
    # Get comparison data
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
    """Admin Dashboard with DYNAMIC filters"""
    user = request.user if request.user.is_authenticated else None
    
    # Extract current filter values
    current_filters = {}
    for key in ['department', 'course', 'semester', 'group', 'status']:
        val = request.GET.get(key)
        if val:
            try:
                current_filters[key] = int(val) if key != 'department' and key != 'status' else val
            except (ValueError, TypeError):
                current_filters[key] = val
    
    filter_form = DashboardFilterForm(
        request.GET or None,
        user=user,
        current_filters=current_filters
    )
    
    filters = {}
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        if cd.get('department'):
            filters['department'] = cd['department']
        if cd.get('semester'):
            filters['semester'] = cd['semester']
        if cd.get('course'):
            filters['course'] = cd['course']
    
    # Initialize analyzer (admin sees all data)
    analyzer = PerformanceAnalyzer(user, filters=filters)
    
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
    
    # Get course-level recommendations
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
    """Super Admin Dashboard with DYNAMIC filters"""
    user = request.user if request.user.is_authenticated else None
    
    # Extract current filter values
    current_filters = {}
    for key in ['department', 'course', 'semester', 'group', 'status']:
        val = request.GET.get(key)
        if val:
            try:
                current_filters[key] = int(val) if key != 'department' and key != 'status' else val
            except (ValueError, TypeError):
                current_filters[key] = val
    
    filter_form = DashboardFilterForm(
        request.GET or None,
        user=user,
        current_filters=current_filters
    )
    
    filters = {}
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        if cd.get('department'):
            filters['department'] = cd['department']
        for key in ('course', 'semester', 'group', 'status'):
            if cd.get(key):
                filters[key] = cd[key]

    # Initialize analyzer with filters
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
    """Return available filter options based on current dataset"""
    # Get dynamic data
    courses = list(Course.objects.filter(
        performances__isnull=False
    ).distinct().values('id', 'code', 'name'))
    
    semesters = list(Semester.objects.filter(
        performances__isnull=False
    ).distinct().values('id', 'name'))
    
    groups = list(Group.objects.filter(
        performances__isnull=False
    ).distinct().values('id', 'name', 'course__code'))
    
    departments = list(Student.objects.filter(
        performances__isnull=False
    ).values_list('department', flat=True).distinct())
    
    return JsonResponse({
        'courses': courses,
        'semesters': semesters,
        'groups': groups,
        'departments': departments
    })



def upload_csv(request):
    """Handle CSV/Excel file upload with dataset override"""
    user = request.user if request.user.is_authenticated else None
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            dataset_name = form.cleaned_data['dataset_name']
            dataset_description = form.cleaned_data.get('dataset_description', '')
            course = form.cleaned_data.get('course')
            semester = form.cleaned_data.get('semester')

            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

            # Call process_csv_upload - it handles its own transaction
            try:
                results = process_csv_upload(
                    file, 
                    user,
                    dataset_name=dataset_name,
                    dataset_description=dataset_description,
                    course=course,
                    semester=semester
                )

                if results['success']:
                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'success_count': results.get('success_count', 0),
                            'error_count': results.get('error_count', 0),
                            'deleted_count': results.get('deleted_count', 0),
                            'errors': results.get('errors', []),
                        })

                    messages.success(
                        request,
                        f"✅ Dataset '{dataset_name}' uploaded successfully!"
                    )
                    messages.info(
                        request,
                        f"📊 {results['success_count']} new records imported. "
                        f"Previous data ({results.get('deleted_count', 0)} records) has been replaced."
                    )
                    
                    if results.get('error_count', 0) > 0:
                        messages.warning(
                            request,
                            f"⚠️ {results['error_count']} records had errors and were skipped."
                        )
                    
                    return redirect('performance:dashboard')
                else:
                    # Upload failed
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'errors': results.get('errors', ['Unknown error occurred'])
                        }, status=400)

                    messages.error(
                        request,
                        "❌ Upload failed. Please check the errors below."
                    )
                    for error in results.get('errors', []):
                        messages.error(request, error)

            except Exception as e:
                # Handle unexpected errors
                error_message = f"Unexpected error during upload: {str(e)}"
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'errors': [error_message]
                    }, status=400)

                messages.error(request, f"❌ {error_message}")
                
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CSVUploadForm()
    
    # Get statistics for the upload page (with error handling)
    try:
        current_records = Performance.objects.count()
    except Exception:
        current_records = 0
        
    try:
        latest_dataset = Dataset.objects.order_by('-created_at').first()
    except Exception:
        latest_dataset = None
    
    context = {
        'page_title': 'Upload Student Data',
        'form': form,
        'current_records': current_records,
        'latest_dataset': latest_dataset,
        'warning_message': 'Note: Uploading new data will REPLACE all existing performance records.'
    }
    
    return render(request, 'performance/upload_csv.html', context)
def export_data(request):
    """Export performance data to CSV or PDF"""
    user = request.user if request.user.is_authenticated else None
    
    filters = {}
    if (course := request.GET.get('course')):
        filters['course'] = course
    if (semester := request.GET.get('semester')):
        filters['semester'] = semester
    if (department := request.GET.get('department')):
        filters['department'] = department
    
    # Get export format (default to CSV)
    export_format = request.GET.get('format', 'csv')
    
    analyzer = PerformanceAnalyzer(user, filters=filters)
    
    if export_format == 'pdf':
        return export_pdf_report(request, analyzer, filters)
    else:
        # CSV Export
        df = analyzer.export_to_dataframe()
        
        if df.empty:
            messages.warning(request, 'No data to export.')
            return redirect('performance:dashboard')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="performance_data.csv"'
        df.to_csv(response, index=False)
        
        return response


def export_pdf_report(request, analyzer, filters):
    """Generate comprehensive PDF report"""
    from io import BytesIO
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.utils import timezone
    
    # Calculate all necessary data
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()
    performances = analyzer.get_filtered_queryset()[:50]  # Limit to 50 records
    
    # Additional stats
    qs = analyzer.get_filtered_queryset()
    kpis.update({
        'excellent_count': qs.filter(score__gte=85).count(),
        'good_count': qs.filter(score__gte=70, score__lt=85).count(),
        'average_count': qs.filter(score__gte=50, score__lt=70).count(),
        'poor_count': qs.filter(score__lt=50).count(),
    })
    
    # Prepare context
    context = {
        'title': 'Performance Analysis Report',
        'generated_date': timezone.now(),
        'user': request.user if request.user.is_authenticated else None,
        'filters': filters,
        'kpis': kpis,
        'distribution': distribution,
        'top_performers': top_performers[:10],
        'bottom_performers': bottom_performers[:10],
        'course_comparison': course_comparison,
        'semester_trend': semester_trend,
        'performances': performances,
    }
    
    # Render template
    template = get_template('performance/pdf_report.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="performance_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response
    
    messages.error(request, 'Error generating PDF report.')
    return redirect('performance:dashboard')


def resolve_recommendation(request, recommendation_id):
    """Mark a recommendation as resolved"""
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
    Detailed view for a specific student with complete analysis
    """
    # Get student
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all performances for this student
    performances = Performance.objects.filter(
        student=student
    ).select_related('course', 'semester', 'group').order_by('-semester__start_date', 'course__code')
    
    # Check if student has any data
    if not performances.exists():
        context = {
            'student': student,
            'no_data': True
        }
        return render(request, 'performance/student_detail.html', context)
    
    # ===== CALCULATE STUDENT STATISTICS =====
    student_stats = calculate_student_stats(student, performances)
    
    # ===== CALCULATE SEMESTER STATISTICS =====
    semester_stats = calculate_semester_stats(student, performances)
    
    # ===== CALCULATE GRADE DISTRIBUTION =====
    grade_distribution = calculate_grade_distribution(performances)
    
    # ===== GENERATE CHARTS =====
    charts = generate_student_charts(student, performances)
    
    # ===== ADD CLASS AVERAGE TO PERFORMANCES =====
    performances_with_avg = []
    for perf in performances:
        # Calculate class average for this course
        class_avg = Performance.objects.filter(
            course=perf.course,
            semester=perf.semester
        ).aggregate(avg_score=Avg('score'))['avg_score']
        
        perf.class_average = round(class_avg, 1) if class_avg else None
        performances_with_avg.append(perf)
    
    context = {
        'student': student,
        'student_stats': student_stats,
        'semester_stats': semester_stats,
        'grade_distribution': grade_distribution,
        'performances': performances_with_avg,
        'charts': charts,
        'no_data': False
    }
    
    return render(request, 'performance/student_detail.html', context)


def calculate_student_stats(student, performances):
    """
    Calculate overall student statistics
    """
    from decimal import Decimal
    
    # Overall average
    overall_avg = performances.aggregate(avg=Avg('score'))['avg'] or 0
    overall_avg = float(overall_avg) if isinstance(overall_avg, Decimal) else overall_avg
    
    # Total courses
    total_courses = performances.count()
    
    # Highest score and best course
    best_performance = performances.order_by('-score').first()
    highest_score = float(best_performance.score) if best_performance else 0
    best_course = best_performance.course.code if best_performance else 'N/A'
    
    # Current semester average (most recent semester)
    latest_semester = performances.order_by('-semester__start_date').first()
    if latest_semester:
        current_semester_avg = performances.filter(
            semester=latest_semester.semester
        ).aggregate(avg=Avg('score'))['avg'] or 0
        current_semester_avg = float(current_semester_avg) if isinstance(current_semester_avg, Decimal) else current_semester_avg
    else:
        current_semester_avg = 0
    
    # Overall rank (across all students based on average)
    all_students = Student.objects.filter(
        performances__isnull=False
    ).annotate(
        avg_score=Avg('performances__score')
    ).order_by('-avg_score')
    
    overall_rank = 1
    total_students = all_students.count()
    
    for idx, std in enumerate(all_students, 1):
        if std.student_id == student.student_id:
            overall_rank = idx
            break
    
    return {
        'overall_average': round(overall_avg, 1),
        'total_courses': total_courses,
        'highest_score': round(highest_score, 1),
        'best_course': best_course,
        'current_semester_avg': round(current_semester_avg, 1),
        'overall_rank': overall_rank,
        'total_students': total_students
    }


def calculate_semester_stats(student, performances):
    """
    Calculate statistics for each semester
    """
    from decimal import Decimal
    
    semester_stats = []
    
    # Get unique semesters for this student
    semesters = performances.values_list('semester', flat=True).distinct()
    
    for semester_id in semesters:
        semester = Semester.objects.get(id=semester_id)
        semester_perfs = performances.filter(semester=semester)
        
        # Calculate average for this semester
        sem_avg = semester_perfs.aggregate(avg=Avg('score'))['avg'] or 0
        sem_avg = float(sem_avg) if isinstance(sem_avg, Decimal) else sem_avg
        
        # Count courses in this semester
        course_count = semester_perfs.count()
        
        # Determine status
        if sem_avg >= 85:
            status = 'Excellent'
        elif sem_avg >= 70:
            status = 'Good'
        elif sem_avg >= 50:
            status = 'Average'
        else:
            status = 'Poor'
        
        # Calculate rank in this semester
        semester_rankings = Student.objects.filter(
            performances__semester=semester
        ).annotate(
            avg_score=Avg('performances__score')
        ).order_by('-avg_score')
        
        rank = 1
        for idx, std in enumerate(semester_rankings, 1):
            if std.student_id == student.student_id:
                rank = idx
                break
        
        # Determine semester type
        sem_name_lower = semester.name.lower()
        if '1' in sem_name_lower or 'one' in sem_name_lower or 'first' in sem_name_lower:
            semester_type = '1'
        elif '2' in sem_name_lower or 'two' in sem_name_lower or 'second' in sem_name_lower:
            semester_type = '2'
        elif 'summer' in sem_name_lower:
            semester_type = 'summer'
        else:
            semester_type = 'other'
        
        semester_stats.append({
            'semester_name': semester.name,
            'semester_type': semester_type,
            'average': round(sem_avg, 1),
            'rank': rank,
            'course_count': course_count,
            'status': status
        })
    
    # Sort by semester type (1, 2, summer)
    order = {'1': 1, '2': 2, 'summer': 3, 'other': 4}
    semester_stats.sort(key=lambda x: order.get(x['semester_type'], 4))
    
    return semester_stats


def calculate_grade_distribution(performances):
    """
    Calculate distribution of grades
    """
    grade_counts = performances.values('grade').annotate(
        count=Count('grade')
    ).order_by('grade')
    
    # Initialize all grades
    distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    
    for item in grade_counts:
        grade = item['grade']
        count = item['count']
        if grade in distribution:
            distribution[grade] = count
    
    return distribution


def generate_student_charts(student, performances):
    """
    Generate Chart.js configurations for all student charts
    """
    from decimal import Decimal
    
    charts = {}
    
    # ===== CHART 1: Course Performance Bar Chart =====
    course_labels = []
    course_scores = []
    course_colors = []
    
    for perf in performances.order_by('semester__start_date', 'course__code'):
        course_labels.append(f"{perf.course.code}")
        # Ensure score is converted to float
        score_value = float(perf.score) if isinstance(perf.score, Decimal) else perf.score
        course_scores.append(score_value)
        
        # Color based on score
        if score_value >= 85:
            course_colors.append('rgba(34, 197, 94, 0.8)')  # Green
        elif score_value >= 70:
            course_colors.append('rgba(59, 130, 246, 0.8)')  # Blue
        elif score_value >= 50:
            course_colors.append('rgba(234, 179, 8, 0.8)')  # Yellow
        else:
            course_colors.append('rgba(239, 68, 68, 0.8)')  # Red
    
    charts['course_performance'] = {
        'type': 'bar',
        'data': {
            'labels': course_labels,
            'datasets': [{
                'label': 'Score (%)',
                'data': course_scores,
                'backgroundColor': course_colors,
                'borderColor': course_colors,
                'borderWidth': 2
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'display': False},
                'title': {
                    'display': False
                }
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'max': 100,
                    'ticks': {
                        'callback': "function(value) { return value + '%'; }"
                    }
                }
            }
        }
    }
    
    # ===== CHART 2: Progress Over Time Line Chart =====
    time_labels = []
    time_scores = []
    
    # Group by semester and calculate average
    semesters_ordered = performances.values(
        'semester__name', 'semester__start_date'
    ).distinct().order_by('semester__start_date')
    
    for sem in semesters_ordered:
        sem_perfs = performances.filter(semester__name=sem['semester__name'])
        avg_score = sem_perfs.aggregate(avg=Avg('score'))['avg'] or 0
        
        # Convert Decimal to float
        avg_value = float(avg_score) if isinstance(avg_score, Decimal) else avg_score
        
        time_labels.append(sem['semester__name'])
        time_scores.append(round(avg_value, 1))
    
    charts['progress_over_time'] = {
        'type': 'line',
        'data': {
            'labels': time_labels,
            'datasets': [{
                'label': 'Average Score',
                'data': time_scores,
                'borderColor': 'rgba(59, 130, 246, 1)',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'borderWidth': 3,
                'fill': True,
                'tension': 0.4,
                'pointRadius': 6,
                'pointHoverRadius': 8,
                'pointBackgroundColor': 'rgba(59, 130, 246, 1)',
                'pointBorderColor': '#fff',
                'pointBorderWidth': 2
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {'display': True},
                'title': {'display': False}
            },
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'max': 100,
                    'ticks': {
                        'callback': "function(value) { return value + '%'; }"
                    }
                }
            }
        }
    }
    
    # ===== CHART 3: Grade Distribution Pie Chart =====
    grade_dist = calculate_grade_distribution(performances)
    
    grade_labels = []
    grade_data = []
    grade_colors = [
        'rgba(34, 197, 94, 0.8)',   # A - Green
        'rgba(59, 130, 246, 0.8)',  # B - Blue
        'rgba(234, 179, 8, 0.8)',   # C - Yellow
        'rgba(249, 115, 22, 0.8)',  # D - Orange
        'rgba(239, 68, 68, 0.8)'    # F - Red
    ]
    
    for idx, (grade, count) in enumerate(grade_dist.items()):
        if count > 0:  # Only include grades that exist
            grade_labels.append(f'Grade {grade}')
            grade_data.append(count)
    
    # Filter colors to match data
    filtered_colors = [grade_colors[i] for i, (_, count) in enumerate(grade_dist.items()) if count > 0]
    
    charts['grade_distribution'] = {
        'type': 'doughnut',
        'data': {
            'labels': grade_labels,
            'datasets': [{
                'data': grade_data,
                'backgroundColor': filtered_colors,
                'borderColor': '#fff',
                'borderWidth': 2
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'display': True,
                    'position': 'bottom'
                },
                'title': {'display': False}
            }
        }
    }
    
    # Convert to JSON-safe format using DjangoJSONEncoder
    for key in charts:
        charts[key] = json.dumps(charts[key], cls=DjangoJSONEncoder)
    
    return charts


def api_kpis(request):
    """API endpoint returning KPIs as JSON"""
    user = request.user if request.user.is_authenticated else None
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search', 'department'):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    analyzer = PerformanceAnalyzer(user, filters=filters)
    kpis = analyzer.calculate_kpis()

    qs = analyzer.get_filtered_queryset()
    kpis.update({
        'excellent_count': qs.filter(score__gte=85).count(),
        'good_count': qs.filter(score__gte=70, score__lt=85).count(),
        'average_count': qs.filter(score__gte=50, score__lt=70).count(),
        'poor_count': qs.filter(score__lt=50).count(),
    })

    return JsonResponse(kpis)


def api_chart(request, chart_name):
    """Return chart data for the requested chart name"""
    user = request.user if request.user.is_authenticated else None
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search', 'department'):
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
        kpis = analyzer.calculate_kpis()
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
    """Return student performance table data as JSON"""
    user = request.user if request.user.is_authenticated else None
    filters = {}
    for key in ('course', 'semester', 'group', 'status', 'search', 'department'):
        val = request.GET.get(key)
        if val:
            filters[key] = val

    analyzer = PerformanceAnalyzer(user, filters=filters)
    qs = analyzer.get_filtered_queryset()

    search_query = request.GET.get('search', '')
    if search_query:
        qs = qs.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )

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
    
    
"""
Add these functions to your existing views.py file
Place them after your existing view functions (after api_performances)
"""

def reports_and_recommendations(request):
    """
    Comprehensive Reports and Recommendations Page
    Shows detailed analysis, insights, and actionable recommendations
    """
    user = request.user if request.user.is_authenticated else None
    
    # Extract current filter values
    current_filters = {}
    for key in ['department', 'course', 'semester', 'group', 'status']:
        val = request.GET.get(key)
        if val:
            try:
                current_filters[key] = int(val) if key != 'department' and key != 'status' else val
            except (ValueError, TypeError):
                current_filters[key] = val
    
    # Initialize form with current filters
    filter_form = DashboardFilterForm(
        request.GET or None,
        user=user,
        current_filters=current_filters
    )
    
    # Build filters for analyzer
    filters = {}
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        if cd.get('department'):
            filters['department'] = cd['department']
        for key in ('course', 'semester', 'group', 'status'):
            if cd.get(key):
                filters[key] = cd[key]
    
    # Initialize analyzer with filters
    analyzer = PerformanceAnalyzer(user, filters=filters)
    
    # Calculate comprehensive KPIs
    kpis = analyzer.calculate_kpis()
    qs = analyzer.get_filtered_queryset()
    
    # Extended KPIs
    kpis.update({
        'excellent_count': qs.filter(score__gte=85).count(),
        'good_count': qs.filter(score__gte=70, score__lt=85).count(),
        'average_count': qs.filter(score__gte=50, score__lt=70).count(),
        'poor_count': qs.filter(score__lt=50).count(),
        'total_records': qs.count(),
    })
    
    # Get performance data
    top_performers = analyzer.get_top_performers(15)
    bottom_performers = analyzer.get_bottom_performers(15)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()
    
    # ===== GENERATE RECOMMENDATIONS =====
    recommendations = generate_comprehensive_recommendations(
        kpis, course_comparison, semester_trend, qs
    )
    
    # ===== ANALYZE TRENDS =====
    trends = analyze_performance_trends(semester_trend, course_comparison)
    
    # ===== IDENTIFY AT-RISK STUDENTS =====
    at_risk_students = identify_at_risk_students(qs)
    
    # ===== DEPARTMENT ANALYSIS =====
    department_analysis = analyze_by_department(qs)
    
    # ===== GENERATE CHARTS FOR REPORTS =====
    chart_generator = ChartGenerator()
    charts = {
        'distribution': chart_generator.generate_score_distribution(
            analyzer.get_performance_distribution()
        ),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
        'grade_distribution': chart_generator.generate_grade_distribution(qs),
    }
    
    context = {
        'page_title': 'Reports & Recommendations',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'top_performers': top_performers,
        'bottom_performers': bottom_performers,
        'course_comparison': course_comparison,
        'semester_trend': semester_trend,
        'recommendations': recommendations,
        'trends': trends,
        'at_risk_students': at_risk_students,
        'department_analysis': department_analysis,
        'filters_applied': bool(filters),
    }
    
    return render(request, 'performance/reports_recommendations.html', context)


def generate_comprehensive_recommendations(kpis, course_comparison, semester_trend, qs):
    """
    Generate comprehensive recommendations based on data analysis
    """
    recommendations = []
    
    # 1. Overall Performance Recommendations
    if kpis['average_score'] < 60:
        recommendations.append({
            'category': 'Overall Performance',
            'priority': 'high',
            'title': 'Critical: Low Overall Performance',
            'description': f"The overall average score is {kpis['average_score']:.1f}%, which is below acceptable standards.",
            'action': 'Immediate intervention required. Consider curriculum review, additional tutoring sessions, and teacher training.',
            'icon': 'exclamation-circle'
        })
    elif kpis['average_score'] < 70:
        recommendations.append({
            'category': 'Overall Performance',
            'priority': 'medium',
            'title': 'Moderate Performance Concerns',
            'description': f"The overall average score is {kpis['average_score']:.1f}%, which could be improved.",
            'action': 'Implement targeted support programs and review teaching methodologies.',
            'icon': 'exclamation-triangle'
        })
    else:
        recommendations.append({
            'category': 'Overall Performance',
            'priority': 'low',
            'title': 'Good Overall Performance',
            'description': f"The overall average score is {kpis['average_score']:.1f}%, which is satisfactory.",
            'action': 'Maintain current standards and focus on excellence programs for top performers.',
            'icon': 'check-circle'
        })
    
    # 2. Pass Rate Recommendations
    if kpis['pass_rate'] < 70:
        recommendations.append({
            'category': 'Pass Rate',
            'priority': 'high',
            'title': 'Low Pass Rate Alert',
            'description': f"Only {kpis['pass_rate']:.1f}% of students are passing (score ≥ 50).",
            'action': 'Urgent: Implement remedial programs, identify struggling students, and provide additional support.',
            'icon': 'user-times'
        })
    elif kpis['pass_rate'] < 85:
        recommendations.append({
            'category': 'Pass Rate',
            'priority': 'medium',
            'title': 'Pass Rate Improvement Needed',
            'description': f"Pass rate is {kpis['pass_rate']:.1f}%, which leaves room for improvement.",
            'action': 'Focus on students at risk of failing and provide targeted interventions.',
            'icon': 'user-check'
        })
    
    # 3. Course-Specific Recommendations
    for course in course_comparison:
        if course['pass_rate'] < 60:
            recommendations.append({
                'category': 'Course Analysis',
                'priority': 'high',
                'title': f"Critical Issues in {course['course_code']}",
                'description': f"Pass rate of {course['pass_rate']:.1f}% with average score {course['average_score']:.1f}%.",
                'action': f"Review {course['course_code']} curriculum, teaching methods, and assessment criteria. Consider course redesign.",
                'icon': 'book'
            })
        elif course['average_score'] < 65:
            recommendations.append({
                'category': 'Course Analysis',
                'priority': 'medium',
                'title': f"Performance Issues in {course['course_code']}",
                'description': f"Average score is {course['average_score']:.1f}%, below target.",
                'action': f"Provide additional resources and support for {course['course_code']} students.",
                'icon': 'book-open'
            })
    
    # 4. Excellence Rate Recommendations
    excellent_percentage = (kpis['excellent_count'] / kpis['total_students'] * 100) if kpis['total_students'] > 0 else 0
    
    if excellent_percentage < 15:
        recommendations.append({
            'category': 'Excellence Programs',
            'priority': 'medium',
            'title': 'Low Excellence Rate',
            'description': f"Only {excellent_percentage:.1f}% of students achieve excellent performance (score ≥ 85).",
            'action': 'Develop gifted student programs, advanced courses, and enrichment activities to challenge high performers.',
            'icon': 'star'
        })
    elif excellent_percentage > 30:
        recommendations.append({
            'category': 'Excellence Programs',
            'priority': 'low',
            'title': 'Strong Excellence Rate',
            'description': f"{excellent_percentage:.1f}% of students achieve excellent performance.",
            'action': 'Continue excellence programs and consider expanding advanced placement opportunities.',
            'icon': 'trophy'
        })
    
    # 5. Poor Performance Recommendations
    poor_percentage = (kpis['poor_count'] / kpis['total_students'] * 100) if kpis['total_students'] > 0 else 0
    
    if poor_percentage > 20:
        recommendations.append({
            'category': 'At-Risk Students',
            'priority': 'high',
            'title': 'High Number of Struggling Students',
            'description': f"{kpis['poor_count']} students ({poor_percentage:.1f}%) are performing poorly (score < 50).",
            'action': 'Immediate intervention required. Implement intensive remedial programs, one-on-one tutoring, and parental involvement.',
            'icon': 'user-shield'
        })
    elif poor_percentage > 10:
        recommendations.append({
            'category': 'At-Risk Students',
            'priority': 'medium',
            'title': 'Students Needing Support',
            'description': f"{kpis['poor_count']} students need additional support.",
            'action': 'Provide targeted interventions and closely monitor progress.',
            'icon': 'hands-helping'
        })
    
    # 6. Semester Trend Analysis
    if len(semester_trend) >= 2:
        latest = semester_trend[-1]
        previous = semester_trend[-2]
        
        if latest['average_score'] < previous['average_score'] - 5:
            recommendations.append({
                'category': 'Trend Analysis',
                'priority': 'high',
                'title': 'Declining Performance Trend',
                'description': f"Performance dropped from {previous['average_score']:.1f}% to {latest['average_score']:.1f}% between semesters.",
                'action': 'Investigate causes of decline and implement corrective measures immediately.',
                'icon': 'chart-line'
            })
        elif latest['average_score'] > previous['average_score'] + 5:
            recommendations.append({
                'category': 'Trend Analysis',
                'priority': 'low',
                'title': 'Improving Performance Trend',
                'description': f"Performance improved from {previous['average_score']:.1f}% to {latest['average_score']:.1f}%.",
                'action': 'Continue current strategies and document successful practices for replication.',
                'icon': 'arrow-up'
            })
    
    return recommendations


def analyze_performance_trends(semester_trend, course_comparison):
    """
    Analyze trends in performance data
    """
    trends = {
        'semester_progression': 'stable',
        'semester_message': '',
        'best_performing_courses': [],
        'worst_performing_courses': [],
        'improvement_areas': []
    }
    
    # Analyze semester progression
    if len(semester_trend) >= 2:
        latest = semester_trend[-1]['average_score']
        previous = semester_trend[-2]['average_score']
        
        if latest > previous + 3:
            trends['semester_progression'] = 'improving'
            trends['semester_message'] = 'Performance is improving over time. Keep up the good work!'
        elif latest < previous - 3:
            trends['semester_progression'] = 'declining'
            trends['semester_message'] = 'Performance is declining. Immediate action needed.'
        else:
            trends['semester_progression'] = 'stable'
            trends['semester_message'] = 'Performance is stable across semesters.'
    
    # Identify best and worst courses
    sorted_courses = sorted(course_comparison, key=lambda x: x['average_score'], reverse=True)
    
    trends['best_performing_courses'] = sorted_courses[:3]
    trends['worst_performing_courses'] = sorted_courses[-3:]
    
    # Identify improvement areas
    for course in course_comparison:
        if course['pass_rate'] < 70:
            trends['improvement_areas'].append({
                'area': f"{course['course_code']} - Pass Rate",
                'current': f"{course['pass_rate']:.1f}%",
                'target': '80%',
                'gap': 80 - course['pass_rate']
            })
        
        if course['average_score'] < 65:
            trends['improvement_areas'].append({
                'area': f"{course['course_code']} - Average Score",
                'current': f"{course['average_score']:.1f}%",
                'target': '70%',
                'gap': 70 - course['average_score']
            })
    
    return trends


def identify_at_risk_students(qs):
    """
    Identify students who are at risk and need immediate attention
    """
    at_risk = []
    
    # Students with average score < 50
    poor_students = Student.objects.filter(
        performances__in=qs
    ).annotate(
        avg_score=Avg('performances__score'),
        total_courses=Count('performances')
    ).filter(
        avg_score__lt=50
    ).order_by('avg_score')[:20]
    
    for student in poor_students:
        recent_performances = qs.filter(student=student).order_by('-semester__start_date')[:3]
        
        at_risk.append({
            'student': student,
            'avg_score': round(student.avg_score, 1),
            'total_courses': student.total_courses,
            'recent_performances': list(recent_performances),
            'risk_level': 'High' if student.avg_score < 40 else 'Medium'
        })
    
    return at_risk


def analyze_by_department(qs):
    """
    Analyze performance by department
    """
    departments = qs.values('student__department').annotate(
        student_count=Count('student', distinct=True),
        avg_score=Avg('score'),
        pass_count=Count('id', filter=Q(score__gte=50)),
        excellent_count=Count('id', filter=Q(score__gte=85))
    ).order_by('-avg_score')
    
    dept_analysis = []
    for dept in departments:
        dept_name = dept['student__department'] or 'Not Specified'
        total_records = qs.filter(student__department=dept['student__department']).count()
        
        pass_rate = (dept['pass_count'] / total_records * 100) if total_records > 0 else 0
        
        dept_analysis.append({
            'department': dept_name,
            'student_count': dept['student_count'],
            'avg_score': round(dept['avg_score'], 1),
            'pass_rate': round(pass_rate, 1),
            'excellent_count': dept['excellent_count'],
            'status': 'Excellent' if dept['avg_score'] >= 80 else 'Good' if dept['avg_score'] >= 70 else 'Needs Improvement'
        })
    
    return dept_analysis