"""
Views for Performance Dashboard System
Handles teacher, admin, and super admin dashboards
WITH DYNAMIC FILTERS based on actual dataset
"""

# Django imports
# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q, Count, Max, Min, F
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required

# Python standard library
import json
from datetime import datetime
from collections import Counter  # ← ADD THIS LINE
from decimal import Decimal

# Your models
from .models import Student, Performance, Semester, Course, Group, Dataset, Recommendation

# Your forms
from .forms import CSVUploadForm, DashboardFilterForm

# Your utilities
from .csv_processor import process_csv_upload
from .analysis import PerformanceAnalyzer
from .charts import ChartGenerator
from .ml_service import get_ml_service
from .recommendation_engine import get_recommendation_engine

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

# ===== DASHBOARDS =====

def performance_dashboard(request):
    """Main dashboard - accessible without login"""
    return teacher_dashboard(request)


# Add this helper function to your views.py (before the dashboard functions)

def add_student_gpa_to_performances(performances_queryset):
    """
    Add student's overall GPA to each performance record
    This calculates GPA for each unique student in the queryset
    
    Args:
        performances_queryset: QuerySet of Performance objects
    
    Returns:
        QuerySet with student_gpa annotation
    """
    from django.db.models import Avg
    from collections import defaultdict
    
    # Get all unique students in the queryset
    student_ids = performances_queryset.values_list('student_id', flat=True).distinct()
    
    # Calculate GPA for each student
    student_gpas = {}
    
    for student_id in student_ids:
        # Get all performances for this student
        student_perfs = Performance.objects.filter(student_id=student_id)
        
        if student_perfs.exists():
            # Calculate GPA using our formula
            total_weighted_score = 0.0
            total_credits = 0
            
            for perf in student_perfs:
                score = float(perf.score) if perf.score else 0.0
                credits = perf.course.credits if hasattr(perf.course, 'credits') and perf.course.credits else 3
                
                total_weighted_score += score * credits
                total_credits += credits
            
            # Calculate average and convert to GPA
            if total_credits > 0:
                average_score = total_weighted_score / total_credits
                gpa = round((average_score / 100) * 4.0, 2)
                student_gpas[student_id] = gpa
    
    # Add GPA to each performance object
    performances_list = list(performances_queryset)
    for perf in performances_list:
        perf.student_gpa = student_gpas.get(perf.student_id, 0.0)
    
    return performances_list


# UPDATE your teacher_dashboard function (around line 40)

def teacher_dashboard(request):
    """Teacher Dashboard with dynamic filters + ML charts"""
    user = request.user if request.user.is_authenticated else None

    # Extract filters
    current_filters = extract_filters(request)
    filter_form = DashboardFilterForm(request.GET or None, user=user, current_filters=current_filters)
    filters = build_filters(filter_form)

    analyzer = PerformanceAnalyzer(user, filters=filters)
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()

    chart_generator = ChartGenerator()
    charts = generate_charts(
        chart_generator,
        analyzer,
        kpis,
        distribution,
        top_performers,
        bottom_performers,
        course_comparison,
        semester_trend
    )

    # Safe ML charts fallback
    try:
        pass_fail_distribution = analyzer.get_pass_fail_distribution()
    except Exception:
        pass_fail_distribution = {"Pass": 1, "Fail": 1}

    try:
        feature_importance = analyzer.get_feature_importance()
    except Exception:
        feature_importance = [{"Feature": "Sample", "Importance": 50}]

    try:
        confusion_matrix_data = analyzer.get_confusion_matrix()
    except Exception:
        confusion_matrix_data = [[1, 0], [0, 1]]

    # Pagination
    performances_queryset = apply_search_filter(request, analyzer.get_filtered_queryset())
    
    # IMPORTANT: Add GPA to performances BEFORE pagination
    performances_with_gpa = add_student_gpa_to_performances(performances_queryset)
    
    # Now paginate the list (not queryset)
    from django.core.paginator import Paginator
    paginator = Paginator(performances_with_gpa, 25)
    page_number = request.GET.get('page', 1)
    performances_page = paginator.get_page(page_number)

    # Recommendations
    recommendations = analyzer.get_recommendations(unresolved_only=True)[:20]

    context = {
        'page_title': 'Teacher Dashboard',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'performances': performances_page,  # Now includes student_gpa
        'top_performers': top_performers[:5],
        'bottom_performers': bottom_performers[:5],
        'recommendations': recommendations,
        'search_query': request.GET.get('search', ''),
        'pass_fail_distribution': pass_fail_distribution,
        'feature_importance': feature_importance,
        'confusion_matrix_data': confusion_matrix_data,
    }

    return render(request, 'performance/teacher_dashboard.html', context)


# ALSO UPDATE super_admin_dashboard the same way

def super_admin_dashboard(request):
    """Super Admin Dashboard with dynamic filters"""
    user = request.user if request.user.is_authenticated else None
    current_filters = extract_filters(request)
    filter_form = DashboardFilterForm(request.GET or None, user=user, current_filters=current_filters)
    filters = build_filters(filter_form)

    analyzer = PerformanceAnalyzer(user, filters=filters)
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()

    chart_generator = ChartGenerator()
    charts = generate_charts(chart_generator, analyzer, kpis, distribution, top_performers, bottom_performers, course_comparison, semester_trend)

    performances_queryset = apply_search_filter(request, analyzer.get_filtered_queryset())
    
    # IMPORTANT: Add GPA before pagination
    performances_with_gpa = add_student_gpa_to_performances(performances_queryset)
    
    from django.core.paginator import Paginator
    paginator = Paginator(performances_with_gpa, 25)
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
        'search_query': request.GET.get('search', ''),
        'is_super_admin': True,
    }

    return render(request, 'performance/teacher_dashboard.html', context)

def admin_dashboard(request):
    """Admin Dashboard with dynamic filters"""
    user = request.user if request.user.is_authenticated else None
    current_filters = extract_filters(request)
    filter_form = DashboardFilterForm(request.GET or None, user=user, current_filters=current_filters)
    filters = build_filters(filter_form)

    analyzer = PerformanceAnalyzer(user, filters=filters)
    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()

    chart_generator = ChartGenerator()
    charts = generate_charts(chart_generator, analyzer, kpis, distribution, None, None, course_comparison, semester_trend)

    recommendations = generate_course_recommendations(course_comparison)

    context = {
        'page_title': 'Admin Dashboard',
        'filter_form': filter_form,
        'kpis': kpis,
        'charts': charts,
        'course_comparison': course_comparison,
        'recommendations': recommendations,
    }

    return render(request, 'performance/admin_dashboard.html', context)



# ===== UTILITY FUNCTIONS =====

def extract_filters(request):
    """Extract filter parameters from GET"""
    current_filters = {}
    for key in ['department', 'course', 'semester', 'group', 'status']:
        val = request.GET.get(key)
        if val:
            try:
                current_filters[key] = int(val) if key not in ['department', 'status'] else val
            except (ValueError, TypeError):
                current_filters[key] = val
    return current_filters


def build_filters(filter_form):
    """Convert filter form into analyzer filters"""
    filters = {}
    if filter_form.is_valid():
        cd = filter_form.cleaned_data
        for key in ('department', 'course', 'semester', 'group', 'status'):
            if cd.get(key):
                filters[key] = cd[key]
    return filters


def apply_search_filter(request, queryset):
    """Apply search filter to queryset"""
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    return queryset


def paginate_queryset(request, queryset, page_size=25):
    """Paginate queryset"""
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)


def generate_charts(chart_generator, analyzer, kpis, distribution, top_performers, bottom_performers, course_comparison, semester_trend):
    """
    Generate all charts for dashboards
    Returns JSON strings that can be safely used in templates with |safe filter
    """
    charts = {
        'distribution': chart_generator.generate_score_distribution(distribution),
        'status_pie': chart_generator.generate_status_pie_chart(kpis),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
    }

    if top_performers is not None and bottom_performers is not None:
        charts['top_bottom'] = chart_generator.generate_top_bottom_comparison(top_performers, bottom_performers)
        charts['grade_distribution'] = chart_generator.generate_grade_distribution(analyzer.get_filtered_queryset())

    # Return as-is - ChartGenerator already returns JSON strings
    return charts

def generate_course_recommendations(course_comparison):
    """Generate recommendations for courses"""
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
    return recommendations


# ===== CSV UPLOAD & EXPORT =====

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

            try:
                results = process_csv_upload(
                    file,
                    user,
                    dataset_name=dataset_name,
                    dataset_description=dataset_description,
                    course=course,
                    semester=semester
                )
                return handle_upload_results(request, results, dataset_name, is_ajax)
            except Exception as e:
                return handle_upload_error(request, str(e), is_ajax)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CSVUploadForm()

    current_records = Performance.objects.count()
    latest_dataset = Dataset.objects.order_by('-created_at').first()

    context = {
        'page_title': 'Upload Student Data',
        'form': form,
        'current_records': current_records,
        'latest_dataset': latest_dataset,
        'warning_message': 'Note: Uploading new data will REPLACE all existing performance records.'
    }

    return render(request, 'performance/upload_csv.html', context)


def handle_upload_results(request, results, dataset_name, is_ajax):
    if results['success']:
        if is_ajax:
            return JsonResponse({
                'success': True,
                'success_count': results.get('success_count', 0),
                'error_count': results.get('error_count', 0),
                'deleted_count': results.get('deleted_count', 0),
                'errors': results.get('errors', []),
            })
        messages.success(request, f" Dataset '{dataset_name}' uploaded successfully!")
        messages.info(request, f"{results['success_count']} new records imported. Previous data ({results.get('deleted_count', 0)} records) replaced.")
        if results.get('error_count', 0) > 0:
            messages.warning(request, f"{results['error_count']} records had errors and were skipped.")
        return redirect('performance:dashboard')
    else:
        if is_ajax:
            return JsonResponse({'success': False, 'errors': results.get('errors', ['Unknown error'])}, status=400)
        messages.error(request, "❌ Upload failed. Check errors below.")
        for error in results.get('errors', []):
            messages.error(request, error)
        return redirect('performance:upload_csv')


def handle_upload_error(request, error_message, is_ajax):
    if is_ajax:
        return JsonResponse({'success': False, 'errors': [error_message]}, status=400)
    messages.error(request, f"❌ Unexpected error: {error_message}")
    return redirect('performance:upload_csv')


def export_data(request):
    user = request.user if request.user.is_authenticated else None
    export_format = request.GET.get('format', 'csv')
    selected_course = request.GET.get('course')
    selected_semester = request.GET.get('semester')
    selected_group = request.GET.get('group')

    analyzer = PerformanceAnalyzer(user, course=selected_course, semester=selected_semester, group=selected_group)

    if export_format == 'pdf':
        return export_pdf_report(request, analyzer, filters=request.GET)
    else:
        df = analyzer.export_to_dataframe()
        if df.empty:
            messages.warning(request, 'No data to export.')
            return redirect('performance:dashboard')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="performance_data.csv"'
        df.to_csv(response, index=False)
        return response


def export_pdf_report(request, analyzer, filters):
    from io import BytesIO
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.utils import timezone

    kpis = analyzer.calculate_kpis()
    distribution = analyzer.get_performance_distribution()
    top_performers = analyzer.get_top_performers(10)
    bottom_performers = analyzer.get_bottom_performers(10)
    course_comparison = analyzer.get_course_comparison()
    semester_trend = analyzer.get_semester_trend()
    performances = analyzer.get_filtered_queryset()[:50]

    qs = analyzer.get_filtered_queryset()
    kpis.update({
        'excellent_count': qs.filter(score__gte=85).count(),
        'good_count': qs.filter(score__gte=70, score__lt=85).count(),
        'average_count': qs.filter(score__gte=50, score__lt=70).count(),
        'poor_count': qs.filter(score__lt=50).count(),
    })

    chart_generator = ChartGenerator()
    charts = generate_charts(chart_generator, analyzer, kpis, distribution, top_performers, bottom_performers, course_comparison, semester_trend)
    charts_json = {key: json.dumps(value, cls=DjangoJSONEncoder) for key, value in charts.items()}

    context = {
        'title': 'Performance Analysis Report',
        'generated_date': timezone.now(),
        'user': request.user,
        'filters': filters,
        'kpis': kpis,
        'distribution': distribution,
        'top_performers': top_performers[:10],
        'bottom_performers': bottom_performers[:10],
        'course_comparison': course_comparison,
        'semester_trend': semester_trend,
        'performances': performances,
        'charts': charts_json,
    }

    template = get_template('performance/pdf_report.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="performance_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        return response

    messages.error(request, 'Error generating PDF report.')
    return redirect('performance:dashboard')


# ===== STUDENT DETAIL & ANALYSIS =====

# ===== HELPER FUNCTIONS FOR STUDENT DETAIL =====
# Add these BEFORE the student_detail function

def calculate_student_stats(student, performances):
    """
    Calculate overall statistics for a student
    Returns dict with all required stats
    """
    if not performances.exists():
        return {
            'overall_average': 0,
            'current_semester_avg': 0,
            'overall_rank': 'N/A',
            'total_students': 0,
            'highest_score': 0,
            'best_course': 'N/A',
            'total_courses': 0
        }
    
    # Calculate overall average
    overall_avg = performances.aggregate(avg=Avg('score'))['avg']
    overall_average = round(overall_avg, 1) if overall_avg else 0
    
    # Get current semester (most recent)
    latest_semester = performances.order_by('-semester__start_date').first().semester
    current_semester_perfs = performances.filter(semester=latest_semester)
    current_sem_avg = current_semester_perfs.aggregate(avg=Avg('score'))['avg']
    current_semester_avg = round(current_sem_avg, 1) if current_sem_avg else 0
    
    # Calculate overall rank
    from .models import Student, Performance
    
    all_student_avgs = []
    # FIXED: Changed 'performance__isnull' to 'performances__isnull'
    all_students = Student.objects.filter(
        performances__isnull=False
    ).distinct()
    
    for s in all_students:
        s_avg = Performance.objects.filter(student=s).aggregate(avg=Avg('score'))['avg']
        if s_avg:
            all_student_avgs.append({
                'student_id': s.student_id,
                'average': s_avg
            })
    
    # Sort by average descending
    all_student_avgs.sort(key=lambda x: x['average'], reverse=True)
    
    # Find current student's rank
    overall_rank = 'N/A'
    for idx, item in enumerate(all_student_avgs, 1):
        if item['student_id'] == student.student_id:
            overall_rank = idx
            break
    
    total_students = len(all_student_avgs)
    
    # Find best performance
    best_perf = performances.order_by('-score').first()
    highest_score = round(best_perf.score, 1) if best_perf else 0
    best_course = f"{best_perf.course.code}" if best_perf else 'N/A'
    
    # Total courses
    total_courses = performances.values('course').distinct().count()
    
    print(f"\n=== Student Stats Debug ===")
    print(f"Student: {student.student_id}")
    print(f"Overall Average: {overall_average}")
    print(f"Current Semester Avg: {current_semester_avg}")
    print(f"Overall Rank: {overall_rank} out of {total_students}")
    print(f"Highest Score: {highest_score} in {best_course}")
    print(f"Total Courses: {total_courses}")
    print("=" * 50)
    
    return {
        'overall_average': overall_average,
        'current_semester_avg': current_semester_avg,
        'overall_rank': overall_rank,
        'total_students': total_students,
        'highest_score': highest_score,
        'best_course': best_course,
        'total_courses': total_courses
    }


def calculate_semester_stats(student, performances):
    """
    Calculate statistics for each semester
    Returns list of dicts with semester stats
    """
    if not performances.exists():
        return []
    
    from .models import Performance
    
    # Group by semester
    semesters = performances.values('semester').distinct()
    semester_stats = []
    
    for sem in semesters:
        semester_id = sem['semester']
        semester = performances.filter(semester_id=semester_id).first().semester
        
        # Get all performances for this semester
        sem_perfs = performances.filter(semester=semester)
        
        # Calculate average
        sem_avg = sem_perfs.aggregate(avg=Avg('score'))['avg']
        average = round(sem_avg, 1) if sem_avg else 0
        
        # Calculate rank for this semester
        # Get all students in this semester with their averages
        semester_student_avgs = []
        students_in_sem = Performance.objects.filter(
            semester=semester
        ).values('student').distinct()
        
        for s in students_in_sem:
            s_id = s['student']
            s_avg = Performance.objects.filter(
                student_id=s_id,
                semester=semester
            ).aggregate(avg=Avg('score'))['avg']
            
            if s_avg:
                semester_student_avgs.append({
                    'student_id': s_id,
                    'average': s_avg
                })
        
        # Sort and find rank
        semester_student_avgs.sort(key=lambda x: x['average'], reverse=True)
        
        rank = 'N/A'
        for idx, item in enumerate(semester_student_avgs, 1):
            if item['student_id'] == student.student_id:
                rank = idx
                break
        
        # Course count
        course_count = sem_perfs.count()
        
        # Determine status based on average
        if average >= 85:
            status = 'Excellent'
        elif average >= 70:
            status = 'Good'
        elif average >= 50:
            status = 'Average'
        else:
            status = 'Needs Improvement'
        
        # Get semester type (1, 2, or 3 for summer)
        semester_type = getattr(semester, 'semester_type', '1')
        
        semester_stats.append({
            'semester_name': semester.name,
            'semester_type': str(semester_type),
            'average': average,
            'rank': rank,
            'course_count': course_count,
            'status': status
        })
    
    # Sort by semester start date (most recent first)
    semester_stats.sort(
        key=lambda x: performances.filter(
            semester__name=x['semester_name']
        ).first().semester.start_date if performances.filter(
            semester__name=x['semester_name']
        ).exists() else '',
        reverse=True
    )
    
    print(f"\n=== Semester Stats Debug ===")
    print(f"Total Semesters: {len(semester_stats)}")
    for stat in semester_stats:
        print(f"  {stat['semester_name']}: Avg={stat['average']}, Rank={stat['rank']}, Status={stat['status']}")
    print("=" * 50)
    
    return semester_stats


def calculate_grade_distribution(performances):
    """
    Calculate distribution of grades
    Returns dict like {'A': 5, 'B': 10, ...}
    """
    if not performances.exists():
        return {}
    
    # Count grades
    grades = [p.grade for p in performances if p.grade]
    grade_counts = Counter(grades)
    
    # Return as dict with counts
    grade_distribution = dict(grade_counts)
    
    print(f"\n=== Grade Distribution Debug ===")
    print(f"Total Grades: {len(grades)}")
    print(f"Distribution: {grade_distribution}")
    print("=" * 50)
    
    return grade_distribution


def generate_student_charts(student, performances):
    """Generate Chart.js configuration for student visualizations"""
    from django.db.models import Avg
    from collections import Counter
    
    # Course Performance Chart
    course_data = list(performances.values(
        'course__code', 'course__name', 'score'
    ).order_by('-score')[:10])  # Top 10 courses
    
    course_performance = {
        'type': 'bar',
        'data': {
            'labels': [item['course__code'] for item in course_data],
            'datasets': [{
                'label': 'Score (%)',
                'data': [float(item['score']) for item in course_data],
                'backgroundColor': 'rgba(54, 162, 235, 0.6)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'max': 100
                }
            },
            'plugins': {
                'legend': {
                    'display': True,
                    'position': 'top'
                },
                'title': {
                    'display': True,
                    'text': 'Top 10 Course Performance'
                }
            }
        }
    }
    
    # Progress Over Time
    semester_progress = list(performances.values(
        'semester__name', 'semester__start_date'
    ).annotate(
        avg_score=Avg('score')
    ).order_by('semester__start_date'))
    
    progress_over_time = {
        'type': 'line',
        'data': {
            'labels': [item['semester__name'] for item in semester_progress],
            'datasets': [{
                'label': 'Average Score',
                'data': [float(item['avg_score']) for item in semester_progress],
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'tension': 0.4,
                'fill': True
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'scales': {
                'y': {
                    'beginAtZero': True,
                    'max': 100
                }
            },
            'plugins': {
                'legend': {
                    'display': True
                },
                'title': {
                    'display': True,
                    'text': 'Performance Trend Over Time'
                }
            }
        }
    }
    
    # Grade Distribution
    grades = [p.grade for p in performances if p.grade]
    grade_counts = Counter(grades)
    
    grade_distribution = {
        'type': 'doughnut',
        'data': {
            'labels': list(grade_counts.keys()),
            'datasets': [{
                'data': list(grade_counts.values()),
                'backgroundColor': [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(153, 102, 255, 0.6)',
                    'rgba(255, 159, 64, 0.6)',
                ]
            }]
        },
        'options': {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'position': 'right'
                },
                'title': {
                    'display': True,
                    'text': 'Grade Distribution'
                }
            }
        }
    }
    
    print(f"\n=== Chart Data Debug ===")
    print(f"Course data points: {len(course_data)}")
    print(f"Semester progress points: {len(semester_progress)}")
    print(f"Grade distribution: {len(grade_counts)} grades")
    print("=" * 50)
    
    return {
        'course_performance': course_performance,
        'progress_over_time': progress_over_time,
        'grade_distribution': grade_distribution
    }

"""
GPA Calculation System - Direct Score to GPA Conversion
Formula: (Average Score / 100) * 4.0
"""

def calculate_gpa(performances):
    """
    Calculate GPA directly from numerical scores
    Formula: GPA = (Average Score / 100) × 4.0
    
    If courses have credits:
    GPA = ((sum of score × credit) / sum of credits) / 100 × 4.0
    
    Args:
        performances: QuerySet of Performance objects
    
    Returns:
        dict with gpa, total_credits, quality_points, grade_breakdown
    """
    if not performances.exists():
        return {
            'gpa': 0.0,
            'total_credits': 0,
            'quality_points': 0.0,
            'average_score': 0.0,
            'grade_breakdown': {}
        }
    
    total_weighted_score = 0.0
    total_credits = 0
    grade_breakdown = {}
    
    print("\n=== GPA Calculation (Score-Based) ===")
    
    for perf in performances:
        score = float(perf.score) if perf.score else 0.0
        
        # Get course credits (default to 3 if not set)
        credits = perf.course.credits if hasattr(perf.course, 'credits') and perf.course.credits else 3
        
        # Weighted score for this course
        weighted_score = score * credits
        total_weighted_score += weighted_score
        total_credits += credits
        
        print(f"Course: {perf.course.code}, Score: {score}, Credits: {credits}, Weighted: {weighted_score}")
        
        # Track grade breakdown
        if perf.grade:
            if perf.grade in grade_breakdown:
                grade_breakdown[perf.grade] += 1
            else:
                grade_breakdown[perf.grade] = 1
    
    # Calculate average score (weighted by credits)
    average_score = (total_weighted_score / total_credits) if total_credits > 0 else 0.0
    
    # Convert to 4.0 scale
    # Formula: (Average Score / 100) × 4.0
    gpa = (average_score / 100) * 4.0
    gpa = round(gpa, 2)
    
    # Quality points = GPA × Credits (total weighted points on 4.0 scale)
    quality_points = gpa * total_credits
    
    print(f"\nTotal Weighted Score: {total_weighted_score}")
    print(f"Total Credits: {total_credits}")
    print(f"Average Score: {average_score:.2f}%")
    print(f"GPA (4.0 scale): {gpa}")
    print(f"Quality Points: {quality_points:.2f}")
    print(f"Grade Distribution: {grade_breakdown}")
    print("=" * 50)
    
    return {
        'gpa': gpa,
        'total_credits': total_credits,
        'quality_points': round(quality_points, 2),
        'average_score': round(average_score, 2),
        'grade_breakdown': grade_breakdown
    }




def calculate_semester_gpa(performances, semester):
    """
    Calculate GPA for a specific semester
    """
    semester_perfs = performances.filter(semester=semester)
    return calculate_gpa(semester_perfs)


def calculate_cumulative_gpa(student):
    """
    Calculate cumulative GPA across all semesters
    """
    all_performances = Performance.objects.filter(student=student)
    return calculate_gpa(all_performances)


def get_gpa_status(gpa):
    """
    Get academic standing based on GPA
    """
    if gpa >= 3.7:
        return {'status': 'Dean\'s List', 'color': 'green', 'icon': '🏆'}
    elif gpa >= 3.5:
        return {'status': 'High Honors', 'color': 'blue', 'icon': '⭐'}
    elif gpa >= 3.0:
        return {'status': 'Good Standing', 'color': 'teal', 'icon': '✓'}
    elif gpa >= 2.5:
        return {'status': 'Satisfactory', 'color': 'yellow', 'icon': '○'}
    elif gpa >= 2.0:
        return {'status': 'Academic Warning', 'color': 'orange', 'icon': '⚠️'}
    else:
        return {'status': 'Academic Probation', 'color': 'red', 'icon': '⚠️'}


# UPDATE your calculate_student_stats function to include GPA
def calculate_student_stats(student, performances):
    """
    Calculate overall statistics for a student including GPA
    """
    if not performances.exists():
        return {
            'overall_average': 0,
            'current_semester_avg': 0,
            'overall_rank': 'N/A',
            'total_students': 0,
            'highest_score': 0,
            'best_course': 'N/A',
            'total_courses': 0,
            'gpa': 0.0,
            'gpa_status': get_gpa_status(0.0),
            'cumulative_gpa': 0.0,
        }
    
    # Calculate overall average
    overall_avg = performances.aggregate(avg=Avg('score'))['avg']
    overall_average = round(overall_avg, 1) if overall_avg else 0
    
    # Get current semester (most recent)
    latest_semester = performances.order_by('-semester__start_date').first().semester
    current_semester_perfs = performances.filter(semester=latest_semester)
    current_sem_avg = current_semester_perfs.aggregate(avg=Avg('score'))['avg']
    current_semester_avg = round(current_sem_avg, 1) if current_sem_avg else 0
    
    # Calculate overall rank
    from .models import Student, Performance
    
    all_student_avgs = []
    all_students = Student.objects.filter(
        performances__isnull=False
    ).distinct()
    
    for s in all_students:
        s_avg = Performance.objects.filter(student=s).aggregate(avg=Avg('score'))['avg']
        if s_avg:
            all_student_avgs.append({
                'student_id': s.student_id,
                'average': s_avg
            })
    
    # Sort by average descending
    all_student_avgs.sort(key=lambda x: x['average'], reverse=True)
    
    # Find current student's rank
    overall_rank = 'N/A'
    for idx, item in enumerate(all_student_avgs, 1):
        if item['student_id'] == student.student_id:
            overall_rank = idx
            break
    
    total_students = len(all_student_avgs)
    
    # Find best performance
    best_perf = performances.order_by('-score').first()
    highest_score = round(best_perf.score, 1) if best_perf else 0
    best_course = f"{best_perf.course.code}" if best_perf else 'N/A'
    
    # Total courses
    total_courses = performances.values('course').distinct().count()
    
    # Calculate GPA
    gpa_info = calculate_gpa(performances)
    cumulative_gpa = gpa_info['gpa']
    gpa_status = get_gpa_status(cumulative_gpa)
    
    # Calculate current semester GPA
    current_semester_gpa_info = calculate_gpa(current_semester_perfs)
    current_semester_gpa = current_semester_gpa_info['gpa']
    
    return {
        'overall_average': overall_average,
        'current_semester_avg': current_semester_avg,
        'overall_rank': overall_rank,
        'total_students': total_students,
        'highest_score': highest_score,
        'best_course': best_course,
        'total_courses': total_courses,
        'gpa': current_semester_gpa,
        'cumulative_gpa': cumulative_gpa,
        'gpa_status': gpa_status,
        'quality_points': gpa_info['quality_points'],
        'total_credits': gpa_info['total_credits'],
    }


# UPDATE calculate_semester_stats to include semester GPA
def calculate_semester_stats(student, performances):
    """
    Calculate statistics for each semester including GPA
    """
    if not performances.exists():
        return []
    
    from .models import Performance
    
    # Group by semester
    semesters = performances.values('semester').distinct()
    semester_stats = []
    
    for sem in semesters:
        semester_id = sem['semester']
        semester = performances.filter(semester_id=semester_id).first().semester
        
        # Get all performances for this semester
        sem_perfs = performances.filter(semester=semester)
        
        # Calculate average
        sem_avg = sem_perfs.aggregate(avg=Avg('score'))['avg']
        average = round(sem_avg, 1) if sem_avg else 0
        
        # Calculate GPA for this semester
        semester_gpa_info = calculate_gpa(sem_perfs)
        semester_gpa = semester_gpa_info['gpa']
        
        # Calculate rank for this semester
        semester_student_avgs = []
        students_in_sem = Performance.objects.filter(
            semester=semester
        ).values('student').distinct()
        
        for s in students_in_sem:
            s_id = s['student']
            s_avg = Performance.objects.filter(
                student_id=s_id,
                semester=semester
            ).aggregate(avg=Avg('score'))['avg']
            
            if s_avg:
                semester_student_avgs.append({
                    'student_id': s_id,
                    'average': s_avg
                })
        
        # Sort and find rank
        semester_student_avgs.sort(key=lambda x: x['average'], reverse=True)
        
        rank = 'N/A'
        for idx, item in enumerate(semester_student_avgs, 1):
            if item['student_id'] == student.student_id:
                rank = idx
                break
        
        # Course count
        course_count = sem_perfs.count()
        
        # Determine status based on GPA
        if semester_gpa >= 3.5:
            status = 'Excellent'
        elif semester_gpa >= 3.0:
            status = 'Good'
        elif semester_gpa >= 2.5:
            status = 'Average'
        else:
            status = 'Needs Improvement'
        
        # Get semester type
        semester_type = getattr(semester, 'semester_type', '1')
        
        semester_stats.append({
            'semester_name': semester.name,
            'semester_type': str(semester_type),
            'average': average,
            'gpa': semester_gpa,  # Add GPA
            'rank': rank,
            'course_count': course_count,
            'status': status
        })
    
    # Sort by semester start date (most recent first)
    semester_stats.sort(
        key=lambda x: performances.filter(
            semester__name=x['semester_name']
        ).first().semester.start_date if performances.filter(
            semester__name=x['semester_name']
        ).exists() else '',
        reverse=True
    )
    
    return semester_stats


# ===== STUDENT DETAIL VIEW =====

def student_detail(request, student_id):
    """
    Detailed view for individual student performance
    Shows comprehensive statistics, semester breakdown, and visualizations
    """
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get all performances for this student
    performances = Performance.objects.filter(
        student=student
    ).select_related(
        'course', 'semester', 'group'
    ).order_by('-semester__start_date', 'course__code')

    # Check if student has any performance data
    if not performances.exists():
        context = {
            'student': student,
            'no_data': True,
            'page_title': f'Student Profile: {student.get_full_name()}',
        }
        return render(request, 'performance/student_detail.html', context)

    # Calculate statistics
    student_stats = calculate_student_stats(student, performances)
    semester_stats = calculate_semester_stats(student, performances)
    grade_distribution = calculate_grade_distribution(performances)
    
    # Generate charts - this returns Python dicts
    charts = generate_student_charts(student, performances)
    
    print("=" * 50)
    print("DEBUG: Chart data being passed to template:")
    print("Chart keys:", charts.keys())
    for key, value in charts.items():
        print(f"\n{key}:")
        print(f"  Type: {type(value)}")
        print(f"  Has 'type': {'type' in value if isinstance(value, dict) else 'N/A'}")
        print(f"  Has 'data': {'data' in value if isinstance(value, dict) else 'N/A'}")
        if isinstance(value, dict) and 'data' in value:
            print(f"  Data keys: {value['data'].keys() if isinstance(value['data'], dict) else 'N/A'}")
    print("=" * 50)

    # Add class average comparison for each performance
    for perf in performances:
        class_avg = Performance.objects.filter(
            course=perf.course,
            semester=perf.semester
        ).aggregate(avg_score=Avg('score'))['avg_score']
        perf.class_average = round(class_avg, 1) if class_avg else None

    # Don't convert to JSON in the view - let the template handle it
    # Just pass the Python dictionaries directly
    context = {
        'student': student,
        'student_stats': student_stats,
        'semester_stats': semester_stats,
        'grade_distribution': grade_distribution,
        'performances': performances,
        'charts': charts,  # Pass Python dicts directly
        'charts_json': json.dumps(charts, cls=DjangoJSONEncoder),  # Also provide as JSON string
        'no_data': False,
        'page_title': f'Student Profile: {student.get_full_name()}',
    }

    return render(request, 'performance/student_detail.html', context)


# ===== API ENDPOINTS =====

def api_filter_options(request):
    courses = list(Course.objects.filter(performances__isnull=False).distinct().values('id', 'code', 'name'))
    semesters = list(Semester.objects.filter(performances__isnull=False).distinct().values('id', 'name'))
    groups = list(Group.objects.filter(performances__isnull=False).distinct().values('id', 'name', 'course__code'))
    departments = list(Student.objects.filter(performances__isnull=False).values_list('department', flat=True).distinct())
    return JsonResponse({'courses': courses, 'semesters': semesters, 'groups': groups, 'departments': departments})


def api_kpis(request):
    user = request.user if request.user.is_authenticated else None
    filters = {key: request.GET.get(key) for key in ('course', 'semester', 'group', 'status', 'search', 'department') if request.GET.get(key)}
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


def api_performances(request):
    user = request.user if request.user.is_authenticated else None
    filters = {key: request.GET.get(key) for key in ('course', 'semester', 'group', 'status', 'search', 'department') if request.GET.get(key)}
    analyzer = PerformanceAnalyzer(user, filters=filters)
    qs = apply_search_filter(request, analyzer.get_filtered_queryset())

    page_obj = paginate_queryset(request, qs, page_size=int(request.GET.get('page_size', 25)))
    data = [{
        'student_id': perf.student.student_id,
        'name': perf.student.get_full_name(),
        'course': perf.course.code,
        'semester': perf.semester.name,
        'score': float(perf.score),
        'grade': perf.grade,
        'status': perf.performance_status,
        'ranking': perf.ranking
    } for perf in page_obj]

    return JsonResponse({'results': data, 'page': page_obj.number, 'num_pages': page_obj.paginator.num_pages, 'total': page_obj.paginator.count})




def ml_dashboard(request):
    """
    ML-Enhanced Dashboard with Predictions and Risk Assessment
    """
    # Get filter parameters
    semester_id = request.GET.get('semester')
    course_id = request.GET.get('course')
    department = request.GET.get('department')
    risk_level = request.GET.get('risk_level')
    
    # Build queryset
    qs = Performance.objects.all().select_related('student', 'course', 'semester')
    
    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    if course_id:
        qs = qs.filter(course_id=course_id)
    if department:
        qs = qs.filter(student__department__iexact=department)
    if risk_level:
        qs = qs.filter(risk_level=risk_level)
    
    # ML-specific KPIs
    total_students = qs.values('student').distinct().count()
    total_predictions = qs.filter(ml_predicted_pass__isnull=False).count()
    
    # Prediction accuracy (if actual results available)
    predicted_pass = qs.filter(ml_predicted_pass=True).count()
    predicted_fail = qs.filter(ml_predicted_pass=False).count()
    actual_pass = qs.filter(score__gte=50).count()
    actual_fail = qs.filter(score__lt=50).count()
    
    # Risk distribution
    risk_distribution = {
        'critical': qs.filter(risk_level='CRITICAL').count(),
        'high': qs.filter(risk_level='HIGH').count(),
        'medium': qs.filter(risk_level='MEDIUM').count(),
        'low': qs.filter(risk_level='LOW').count(),
        'none': qs.filter(risk_level='NONE').count(),
    }
    
    # Intervention statistics
    needs_intervention = qs.filter(needs_intervention=True).count()
    high_priority_interventions = qs.filter(
        needs_intervention=True,
        intervention_priority__lte=3
    ).count()
    
    # ML confidence distribution
    high_confidence = qs.filter(ml_confidence__gte=80).count()
    medium_confidence = qs.filter(ml_confidence__gte=60, ml_confidence__lt=80).count()
    low_confidence = qs.filter(ml_confidence__lt=60).count()
    
    # Trend analysis
    trend_distribution = {
        'improving': qs.filter(performance_trend='IMPROVING').count(),
        'stable': qs.filter(performance_trend='STABLE').count(),
        'declining': qs.filter(performance_trend='DECLINING').count(),
        'unknown': qs.filter(performance_trend='UNKNOWN').count(),
    }
    
    # Top at-risk students
    at_risk_students = qs.filter(
        risk_level__in=['CRITICAL', 'HIGH']
    ).order_by('risk_score').reverse()[:20]
    
    # Students with highest intervention priority
    priority_interventions = qs.filter(
        needs_intervention=True
    ).order_by('intervention_priority')[:15]
    
    # Recommendations summary
    unresolved_recommendations = Recommendation.objects.filter(
        is_resolved=False,
        student__in=qs.values_list('student', flat=True)
    ).count()
    
    high_priority_recs = Recommendation.objects.filter(
        is_resolved=False,
        priority='high',
        student__in=qs.values_list('student', flat=True)
    ).count()
    
    # ML model info
    ml_service = get_ml_service()
    model_info = {
        'loaded': ml_service.model_loaded,
        'version': ml_service.MODEL_VERSION if ml_service.model_loaded else 'N/A',
        'filename': ml_service.MODEL_FILENAME,
    }
    
    # Prediction vs Actual comparison (for model validation)
    prediction_accuracy = None
    if total_predictions > 0:
        # Calculate how many predictions matched actual outcomes
        correct_predictions = 0
        for perf in qs.filter(ml_predicted_pass__isnull=False):
            actual_passed = float(perf.score or 0) >= 50
            if perf.ml_predicted_pass == actual_passed:
                correct_predictions += 1
        
        prediction_accuracy = round((correct_predictions / total_predictions) * 100, 2)
    
    context = {
        # Basic stats
        'total_students': total_students,
        'total_predictions': total_predictions,
        'predicted_pass': predicted_pass,
        'predicted_fail': predicted_fail,
        'actual_pass': actual_pass,
        'actual_fail': actual_fail,
        'prediction_accuracy': prediction_accuracy,
        
        # Risk analysis
        'risk_distribution': risk_distribution,
        'needs_intervention': needs_intervention,
        'high_priority_interventions': high_priority_interventions,
        
        # ML confidence
        'high_confidence': high_confidence,
        'medium_confidence': medium_confidence,
        'low_confidence': low_confidence,
        
        # Trends
        'trend_distribution': trend_distribution,
        
        # Lists
        'at_risk_students': at_risk_students,
        'priority_interventions': priority_interventions,
        
        # Recommendations
        'unresolved_recommendations': unresolved_recommendations,
        'high_priority_recs': high_priority_recs,
        
        # Model info
        'model_info': model_info,
        
        # Filter options
        'semesters': Semester.objects.all(),
        'courses': Course.objects.all(),
        'departments': Student.objects.values_list('department', flat=True).distinct(),
        'selected_semester': semester_id,
        'selected_course': course_id,
        'selected_department': department,
        'selected_risk_level': risk_level,
    }
    
    return render(request, 'performance/ml_dashboard.html', context)


@login_required
def student_ml_profile(request, student_id):
    """
    Detailed ML profile for individual student
    Shows predictions, risk assessment, recommendations
    """
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get active semester (or allow selection)
    semester_id = request.GET.get('semester')
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
    else:
        semester = Semester.objects.filter(is_active=True).first()
    
    if not semester:
        messages.error(request, 'No active semester found.')
        return redirect('performance:dashboard')
    
    # Get student's performances
    performances = Performance.objects.filter(
        student=student,
        semester=semester
    ).select_related('course')
    
    if not performances.exists():
        messages.warning(request, f'No performance data found for {student.get_full_name()}')
        return redirect('performance:dashboard')
    
    # Calculate overall statistics
    total_courses = performances.count()
    avg_score = performances.aggregate(Avg('score'))['score__avg'] or 0
    avg_confidence = performances.aggregate(Avg('ml_confidence'))['ml_confidence__avg'] or 0
    
    courses_at_risk = performances.filter(risk_level__in=['CRITICAL', 'HIGH']).count()
    predicted_passes = performances.filter(ml_predicted_pass=True).count()
    predicted_failures = performances.filter(ml_predicted_pass=False).count()
    
    # Risk summary
    highest_risk = performances.order_by('-risk_score').first()
    
    # Get comprehensive recommendations
    rec_engine = get_recommendation_engine()
    student_summary = rec_engine.get_student_summary(student, semester)
    
    # Get all recommendations from database
    db_recommendations = Recommendation.objects.filter(
        student=student,
        semester=semester,
        is_resolved=False
    ).order_by('-priority', '-created_at')
    
    context = {
        'student': student,
        'semester': semester,
        'performances': performances,
        'total_courses': total_courses,
        'avg_score': round(float(avg_score), 2),
        'avg_confidence': round(float(avg_confidence), 2),
        'courses_at_risk': courses_at_risk,
        'predicted_passes': predicted_passes,
        'predicted_failures': predicted_failures,
        'highest_risk': highest_risk,
        'student_summary': student_summary,
        'db_recommendations': db_recommendations,
        'semesters': Semester.objects.all(),
    }
    
    return render(request, 'performance/student_ml_profile.html', context)


@login_required
def run_predictions_view(request):
    """
    Manually trigger ML predictions for selected data
    """
    if request.method == 'POST':
        semester_id = request.POST.get('semester')
        course_id = request.POST.get('course')
        force = request.POST.get('force') == 'true'
        generate_recs = request.POST.get('generate_recommendations') == 'true'
        
        # Build queryset
        qs = Performance.objects.all()
        
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if course_id:
            qs = qs.filter(course_id=course_id)
        
        # Filter unpredicted unless force
        if not force:
            qs = qs.filter(ml_predicted_pass__isnull=True)
        
        if qs.count() == 0:
            messages.warning(request, 'No records to process.')
            return redirect('performance:ml_dashboard')
        
        # Run predictions
        ml_service = get_ml_service()
        if not ml_service.model_loaded:
            messages.error(request, 'ML model not loaded. Please check server configuration.')
            return redirect('performance:ml_dashboard')
        
        success_count = 0
        error_count = 0
        
        for performance in qs:
            try:
                ml_service.update_performance_with_prediction(performance, save=True)
                success_count += 1
            except Exception as e:
                error_count += 1
        
        messages.success(
            request,
            f'✅ Predictions complete: {success_count} successful, {error_count} errors'
        )
        
        # Generate recommendations if requested
        if generate_recs:
            rec_engine = get_recommendation_engine()
            rec_stats = rec_engine.batch_generate_recommendations(qs, auto_save=True)
            messages.info(
                request,
                f'📋 Generated {rec_stats["total_recommendations"]} recommendations '
                f'({rec_stats["high_priority"]} high priority)'
            )
        
        return redirect('performance:ml_dashboard')
    
    # GET request - show form
    context = {
        'semesters': Semester.objects.all(),
        'courses': Course.objects.all(),
    }
    return render(request, 'performance/run_predictions.html', context)


@login_required
def ml_analytics_api(request):
    """
    JSON API endpoint for ML analytics data
    For charts and visualizations
    """
    semester_id = request.GET.get('semester')
    
    qs = Performance.objects.all()
    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    
    # Risk level distribution
    risk_data = {
        'labels': ['Critical', 'High', 'Medium', 'Low', 'None'],
        'values': [
            qs.filter(risk_level='CRITICAL').count(),
            qs.filter(risk_level='HIGH').count(),
            qs.filter(risk_level='MEDIUM').count(),
            qs.filter(risk_level='LOW').count(),
            qs.filter(risk_level='NONE').count(),
        ]
    }
    
    # Prediction confidence distribution
    confidence_data = {
        'labels': ['High (80-100%)', 'Medium (60-79%)', 'Low (0-59%)'],
        'values': [
            qs.filter(ml_confidence__gte=80).count(),
            qs.filter(ml_confidence__gte=60, ml_confidence__lt=80).count(),
            qs.filter(ml_confidence__lt=60).count(),
        ]
    }
    
    # Score vs ML Prediction scatter
    scatter_data = []
    for perf in qs.filter(ml_predicted_pass__isnull=False)[:100]:  # Limit for performance
        scatter_data.append({
            'score': float(perf.score or 0),
            'confidence': float(perf.ml_confidence or 0),
            'predicted_pass': perf.ml_predicted_pass,
            'student_id': perf.student.student_id,
        })
    
    return JsonResponse({
        'risk_distribution': risk_data,
        'confidence_distribution': confidence_data,
        'scatter_data': scatter_data,
    })


@login_required
def export_ml_report(request):
    """
    Export comprehensive ML report as CSV
    """
    import csv
    from django.utils import timezone
    
    semester_id = request.GET.get('semester')
    
    qs = Performance.objects.all().select_related('student', 'course', 'semester')
    if semester_id:
        qs = qs.filter(semester_id=semester_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ml_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Student Name', 'Department', 'Course', 'Semester',
        'Score', 'Grade', 'Status',
        'ML Prediction', 'ML Confidence (%)', 'Prob Pass (%)', 'Prob Fail (%)',
        'Risk Level', 'Risk Score', 'Needs Intervention', 'Priority',
        'Performance Trend', 'Predicted Final Score',
        'Attendance', 'Mid-Semester', 'Final Exam'
    ])
    
    for perf in qs:
        writer.writerow([
            perf.student.student_id,
            perf.student.get_full_name(),
            perf.student.department,
            perf.course.code,
            perf.semester.name,
            float(perf.score or 0),
            perf.grade,
            perf.status,
            perf.ml_prediction_label or 'N/A',
            float(perf.ml_confidence or 0),
            float(perf.prob_pass or 0),
            float(perf.prob_fail or 0),
            perf.risk_level,
            float(perf.risk_score or 0),
            'Yes' if perf.needs_intervention else 'No',
            perf.intervention_priority or 'N/A',
            perf.performance_trend,
            float(perf.predicted_final_score or 0) if perf.predicted_final_score else 'N/A',
            float(perf.attendance or 0),
            float(perf.mid_semester or 0),
            float(perf.final_exam or 0),
        ])
    
    return response


# Data set cleaning 

@login_required
@require_POST
def reset_all_data(request):
    """
    Reset all performance data in the system
    Only accessible by superusers/admins
    """
    # Security check - only superusers can reset data
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to reset data.")
        return JsonResponse({
            'success': False, 
            'message': 'Permission denied'
        }, status=403)
    
    try:
        with transaction.atomic():
            # Import your models
            from .models import Performance, Recommendation, Student, Course
            
            # Delete all data
            deleted_counts = {
                'performances': Performance.objects.all().delete()[0],
                'recommendations': Recommendation.objects.all().delete()[0],
                'students': Student.objects.all().delete()[0],
                'courses': Course.objects.all().delete()[0],
            }
            
            messages.success(
                request, 
                f"Successfully deleted: {deleted_counts['performances']} performances, "
                f"{deleted_counts['students']} students, "
                f"{deleted_counts['courses']} courses, "
                f"{deleted_counts['recommendations']} recommendations."
            )
            
            return JsonResponse({
                'success': True,
                'message': 'All data has been reset successfully',
                'deleted_counts': deleted_counts
            })
            
    except Exception as e:
        messages.error(request, f"Error resetting data: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)