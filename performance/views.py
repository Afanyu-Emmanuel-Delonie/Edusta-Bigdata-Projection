from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView

from .models import AcademicRecord, Student, Course
from .services.analytics import (
    get_available_years,
    get_selected_year,
    get_dashboard_context,
    get_risk_tracker_context,
    get_graduation_context,
    get_insights_context,
    TARGET_YEAR,
)
from .services.data_import import import_records_from_file


@login_required
def analytics_dashboard(request):
    years = get_available_years()
    selected_year = get_selected_year(request)
    context = {
        'available_years': years,
        'selected_year': selected_year,
        **get_dashboard_context(selected_year),
    }
    return render(request, 'performance/overview.html', context)


@login_required
def risk_tracker(request):
    years = get_available_years()
    selected_year = get_selected_year(request)
    context = {
        'available_years': years,
        'selected_year': selected_year,
        **get_risk_tracker_context(request, selected_year),
    }
    return render(request, 'performance/risk_tracker.html', context)


@login_required
def graduation_analytics(request):
    years = get_available_years()
    selected_year = get_selected_year(request)
    context = {
        'available_years': years,
        'selected_year': selected_year,
        **get_graduation_context(selected_year),
    }
    return render(request, 'performance/graduation.html', context)


@login_required
def institutional_insights(request):
    years = get_available_years()
    selected_year = get_selected_year(request)
    context = {
        'available_years': years,
        'selected_year': selected_year,
        **get_insights_context(selected_year),
    }
    return render(request, 'performance/insights.html', context)


@login_required
def data_management(request):
    records = AcademicRecord.objects.filter(academic_year=TARGET_YEAR)
    total_samples = records.count()

    accuracy = 0
    if total_samples > 0:
        correct = sum(
            1 for r in records
            if ((r.ca_total or 0) >= 20 and (r.attendance_rate or 0) >= 0.7)
            == (((r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0)) >= 50)
        )
        accuracy = round((correct / total_samples) * 100, 1)

    context = {
        'total_samples': total_samples,
        'accuracy': accuracy,
        'ca_importance': 65,
        'attendance_importance': 35,
        'courses': Course.objects.all(),
    }
    return render(request, 'performance/ai_diagnostics.html', context)


@login_required
def upload_semester_data(request):
    if request.method == 'POST' and request.FILES.get('file'):
        success, message, _ = import_records_from_file(request.FILES['file'])
        if success:
            messages.success(request, message)
        else:
            messages.error(request, f'Error uploading data: {message}')
    return redirect('performance:management')


@login_required
def submit_record(request):
    if request.method == 'POST':
        try:
            student = Student.objects.get(student_id=request.POST.get('student_id'))
            AcademicRecord.objects.create(
                student=student,
                course_code=request.POST.get('course_code'),
                academic_year=TARGET_YEAR,
                ca_total=float(request.POST.get('ca_score', 0)),
                mid_term=0,
                final_exam=0,
                attendance_rate=float(request.POST.get('attendance', 0)),
                teacher_id='T001',
            )
            messages.success(request, f'Record added for {student.first_name} {student.last_name}')
        except Student.DoesNotExist:
            messages.error(request, f"Student ID {request.POST.get('student_id')} not found")
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('performance:management')


class RecordCreateView(CreateView):
    model = AcademicRecord
    fields = ['student', 'course_code', 'academic_year', 'ca_total', 'mid_term', 'final_exam', 'attendance_rate', 'teacher_id']
    template_name = 'performance/record_form.html'
    success_url = '/performance/'
