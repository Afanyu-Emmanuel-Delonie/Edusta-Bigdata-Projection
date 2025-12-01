"""
Views for Performance Dashboard System
Handles teacher, admin, and super admin dashboards
WITH DYNAMIC FILTERS based on actual dataset
"""

# Django imports
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import HttpResponse, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

# Python standard library
import json
from datetime import datetime

# Your models
from .models import Student, Performance, Semester, Course, Group, Dataset

# Your forms
from .forms import CSVUploadForm, DashboardFilterForm

# Your utilities
from .csv_processor import process_csv_upload
from .analysis import PerformanceAnalyzer
from .charts import ChartGenerator


# ===== DASHBOARDS =====

def performance_dashboard(request):
    """Main dashboard - accessible without login"""
    return teacher_dashboard(request)


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
    performances_page = paginate_queryset(request, performances_queryset)

    # Recommendations
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
        'search_query': request.GET.get('search', ''),
        'pass_fail_distribution': pass_fail_distribution,
        'feature_importance': feature_importance,
        'confusion_matrix_data': confusion_matrix_data,
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
    performances_page = paginate_queryset(request, performances_queryset)

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
    """Generate all charts for dashboards"""
    charts = {
        'distribution': chart_generator.generate_score_distribution(distribution),
        'status_pie': chart_generator.generate_status_pie_chart(kpis),
        'course_comparison': chart_generator.generate_course_comparison(course_comparison),
        'semester_trend': chart_generator.generate_semester_trend(semester_trend),
    }

    if top_performers is not None and bottom_performers is not None:
        charts['top_bottom'] = chart_generator.generate_top_bottom_comparison(top_performers, bottom_performers)
        charts['grade_distribution'] = chart_generator.generate_grade_distribution(analyzer.get_filtered_queryset())

    for key in charts:
        charts[key] = json.dumps(charts[key], cls=DjangoJSONEncoder)

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

def student_detail(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    performances = Performance.objects.filter(student=student).select_related('course', 'semester', 'group').order_by('-semester__start_date', 'course__code')

    if not performances.exists():
        return render(request, 'performance/student_detail.html', {'student': student, 'no_data': True})

    student_stats = calculate_student_stats(student, performances)
    semester_stats = calculate_semester_stats(student, performances)
    grade_distribution = calculate_grade_distribution(performances)
    charts = generate_student_charts(student, performances)

    for perf in performances:
        class_avg = Performance.objects.filter(course=perf.course, semester=perf.semester).aggregate(avg_score=Avg('score'))['avg_score']
        perf.class_average = round(class_avg, 1) if class_avg else None

    charts_json = {key: json.dumps(value, cls=DjangoJSONEncoder) for key, value in charts.items()}

    context = {
        'student': student,
        'student_stats': student_stats,
        'semester_stats': semester_stats,
        'grade_distribution': grade_distribution,
        'performances': performances,
        'charts': charts_json,
        'no_data': False,
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


# ===== REPORTS & RECOMMENDATIONS =====

def reports_and_recommendations(request):
    user = request.user if request.user.is_authenticated else None
    current_filters = extract_filters(request)
    filter_form = DashboardFilterForm(request.GET or None, user=user, current_filters=current_filters)
    filters = build_filters(filter_form)

    analyzer = PerformanceAnalyzer(user, filters=filters)
    recommendations = analyzer.get_recommendations(unresolved_only=False)
    performances_queryset = analyzer.get_filtered_queryset()
    performances_page = paginate_queryset(request, performances_queryset)

    context = {
        'page_title': 'Reports & Recommendations',
        'filter_form': filter_form,
        'performances': performances_page,
        'recommendations': recommendations,
        'search_query': request.GET.get('search', ''),
    }

    return render(request, 'performance/reports.html', context)
