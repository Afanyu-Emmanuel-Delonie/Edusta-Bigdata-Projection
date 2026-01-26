from django.db.models import Avg, Max, StdDev, Count
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
import pandas as pd
import json
from scipy.stats import pearsonr
from .models import Student, AcademicRecord, Teacher, Department, Course

TARGET_YEAR = "2025/2026"

def get_academic_context(request):
    """Helper to get years and the selected year dynamically"""
    years = AcademicRecord.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    selected_year = request.GET.get('academic_year') or (years[0] if years else TARGET_YEAR)
    return years, selected_year

@login_required
def analytics_dashboard(request):
    years, selected_year = get_academic_context(request)
    
    records = AcademicRecord.objects.filter(academic_year=selected_year).select_related('student', 'student__department')
    
    stats = records.aggregate(
        avg_ca=Avg('ca_total'),
        avg_mid=Avg('mid_term'),
        avg_final=Avg('final_exam')
    )
    
    total_scores = [(r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0) for r in records]
    avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
    
    chart_data = [
        sum(1 for s in total_scores if s >= 80),
        sum(1 for s in total_scores if 70 <= s < 80),
        sum(1 for s in total_scores if 50 <= s < 70),
        sum(1 for s in total_scores if s < 50)
    ]
    
    # Get priority/at-risk students (CA < 20)
    alerts = records.filter(ca_total__lt=20).select_related('student', 'student__department')[:10]
    
    # Add calculated fields to each alert
    for alert in alerts:
        alert.ca_score = alert.ca_total
        total = (alert.ca_total or 0) + (alert.mid_term or 0) + (alert.final_exam or 0)
        alert.student_gpa = (total / 100) * 4.0
    
    # Department stats with proper aggregation
    dept_stats = []
    for dept in Department.objects.all():
        dept_records = records.filter(student__department=dept)
        if dept_records.exists():
            dept_total_scores = [(r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0) for r in dept_records]
            avg_dept_score = sum(dept_total_scores) / len(dept_total_scores) if dept_total_scores else 0
            
            dept_stats.append({
                'code': dept.code,
                'name': dept.name,
                'avg_gpa': (avg_dept_score / 100) * 4.0,
                'student_count': dept_records.count()
            })
    
    # Sort by avg_gpa descending
    dept_stats.sort(key=lambda x: x['avg_gpa'], reverse=True)

    context = {
        'total_count': records.count(),
        'alert_count': records.filter(ca_total__lt=15).count(),
        'avg_gpa': round((avg_score / 100) * 4.0, 2),
        'grad_ready_count': sum(1 for s in total_scores if s >= 50),
        'pass_count': sum(1 for s in total_scores if s >= 50),
        'first_class_count': chart_data[0],
        'chart_data': chart_data,
        'available_years': years,
        'selected_year': selected_year,
        'dept_stats': dept_stats,
        'alerts': alerts
    }
    return render(request, 'performance/overview.html', context)

@login_required
def risk_tracker(request):
    years, selected_year = get_academic_context(request)
    
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department')

    historical_avg = AcademicRecord.objects.exclude(
        academic_year=selected_year
    ).aggregate(Avg('ca_total'))['ca_total__avg'] or 0

    selected_dept = request.GET.get('department')
    if selected_dept:
        records = records.filter(student__department_id=selected_dept)

    for record in records:
        record.total_score = (record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)
        
        if not record.final_exam or record.final_exam == 0:
            pre_exam = (record.ca_total or 0) + (record.mid_term or 0)
            record.status_label = "High Risk" if pre_exam < 30 else "On Track"
        else:
            record.status_label = "Cleared" if record.total_score >= 50 else "Failed"
            
        record.is_above_avg = record.ca_total > historical_avg

    context = {
        'available_years': years,
        'selected_year': selected_year,
        'departments': Department.objects.all(),
        'alerts': records,
        'historical_baseline': round(historical_avg, 1),
        'stats': {
            'total': records.count(),
            'critical': records.filter(ca_total__lt=15).count()
        }
    }
    return render(request, 'performance/risk_tracker.html', context)

@login_required
def graduation_analytics(request):
    years, selected_year = get_academic_context(request)
    
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department')
    
    graduation_ready = []
    for record in records:
        total_score = (record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)
        if total_score >= 50:
            graduation_ready.append(record)
    
    context = {
        'available_years': years,
        'selected_year': selected_year,
        'total_students': records.count(),
        'graduation_ready': len(graduation_ready),
        'graduation_rate': round((len(graduation_ready) / records.count() * 100), 1) if records.count() > 0 else 0,
        'records': graduation_ready
    }
    return render(request, 'performance/graduation.html', context)

@login_required
def institutional_insights(request):
    years, selected_year = get_academic_context(request)
    
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department', 'student__department')
    
    # Department Consistency Matrix
    consistency_matrix = []
    for dept in Department.objects.all():
        dept_records = records.filter(student__department=dept)
        if dept_records.exists():
            ca_scores = list(dept_records.values_list('ca_total', flat=True))
            final_scores = list(dept_records.values_list('final_exam', flat=True))
            
            # Calculate correlation
            if len(ca_scores) > 1 and len(final_scores) > 1:
                try:
                    correlation, _ = pearsonr(ca_scores, final_scores)
                    correlation = round(correlation, 2)
                except:
                    correlation = 0
            else:
                correlation = 0
            
            avg_ca = sum(ca_scores) / len(ca_scores) if ca_scores else 0
            avg_final = sum(final_scores) / len(final_scores) if final_scores else 0
            
            # Determine bias
            if avg_ca > 25 and avg_final > 60:
                bias = "Lenient"
            elif avg_ca < 20 and avg_final < 50:
                bias = "Strict"
            else:
                bias = "Balanced"
            
            consistency_matrix.append({
                'name': dept.name,
                'avg_ca': avg_ca,
                'avg_final': avg_final,
                'correlation': correlation,
                'bias': bias
            })
    
    # Recovery Data (Teachers)
    recovery_data = []
    for teacher in Teacher.objects.all()[:5]:
        teacher_records = records.filter(teacher_id=teacher.employee_id)
        low_ca_students = teacher_records.filter(ca_total__lt=20)
        
        if low_ca_students.exists():
            recovered = sum(1 for r in low_ca_students if (r.ca_total + r.mid_term + r.final_exam) >= 50)
            rate = round((recovered / low_ca_students.count()) * 100, 1)
        else:
            rate = 0
        
        recovery_data.append({
            'name': teacher.name,
            'rate': rate
        })
    
    # Course Performance Chart Data
    course_data = {}
    for record in records:
        if record.course_code not in course_data:
            course_data[record.course_code] = {'scores': [], 'passed': 0, 'total': 0}
        
        total_score = (record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)
        course_data[record.course_code]['scores'].append(total_score)
        course_data[record.course_code]['total'] += 1
        if total_score >= 50:
            course_data[record.course_code]['passed'] += 1
    
    chart_labels = []
    chart_scores = []
    chart_pass_rates = []
    
    for course_code, data in sorted(course_data.items())[:8]:
        chart_labels.append(course_code)
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        chart_scores.append(round(avg_score, 1))
        pass_rate = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        chart_pass_rates.append(round(pass_rate, 1))
    
    context = {
        'available_years': years,
        'selected_year': selected_year,
        'consistency_matrix': consistency_matrix,
        'recovery_data': recovery_data,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores),
        'chart_pass_rates': json.dumps(chart_pass_rates),
    }
    return render(request, 'performance/insights.html', context)

@login_required
def data_management(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        academic_year = request.POST.get('academic_year', TARGET_YEAR)
        
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            from django.db import transaction
            with transaction.atomic():
                for _, row in df.iterrows():
                    dept, _ = Department.objects.get_or_create(
                        code=row['department_code'],
                        defaults={'name': row.get('department_name', row['department_code'])}
                    )
                    
                    student, _ = Student.objects.get_or_create(
                        student_id=row['student_id'],
                        defaults={
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'department': dept,
                            'current_gpa': row.get('ca_total', 0) / 10
                        }
                    )

                    AcademicRecord.objects.create(
                        student=student,
                        course_code=row['course_code'],
                        academic_year=academic_year,
                        ca_total=row.get('ca_total', 0),
                        mid_term=row.get('mid_term', 0),
                        final_exam=row.get('final_exam', 0),
                        attendance_rate=row.get('attendance', 0),
                        teacher_id=row.get('teacher_id', 'T001'),
                    )
            messages.success(request, f"Imported data for session {academic_year}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    # Calculate model metrics
    records = AcademicRecord.objects.filter(academic_year=TARGET_YEAR)
    total_samples = records.count()
    
    # Simple accuracy calculation based on prediction vs actual
    if total_samples > 0:
        correct_predictions = 0
        for record in records:
            predicted_pass = (record.ca_total or 0) >= 20 and (record.attendance_rate or 0) >= 0.7
            actual_pass = ((record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)) >= 50
            if predicted_pass == actual_pass:
                correct_predictions += 1
        accuracy = round((correct_predictions / total_samples) * 100, 1)
    else:
        accuracy = 0
    
    # Feature importance (simplified)
    ca_importance = 65
    attendance_importance = 35
            
    context = {
        'total_samples': total_samples,
        'accuracy': accuracy,
        'ca_importance': ca_importance,
        'attendance_importance': attendance_importance,
        'courses': Course.objects.all()
    }
    return render(request, 'performance/ai_diagnostics.html', context)

@login_required
def upload_semester_data(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            from django.db import transaction
            with transaction.atomic():
                for _, row in df.iterrows():
                    # Handle both 'student_id' and 'registration_number' column names
                    student_id = row.get('student_id') or row.get('registration_number')
                    
                    dept, _ = Department.objects.get_or_create(
                        code=row['department_code'],
                        defaults={'name': row.get('department_name', row['department_code'])}
                    )
                    
                    student, _ = Student.objects.get_or_create(
                        student_id=student_id,
                        defaults={
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'department': dept,
                            'current_gpa': row.get('ca_total', 0) / 10
                        }
                    )

                    AcademicRecord.objects.create(
                        student=student,
                        course_code=row.get('course_code', 'GEN101'),
                        academic_year=row.get('academic_year', TARGET_YEAR),
                        ca_total=row.get('ca_total', 0),
                        mid_term=row.get('mid_term', 0),
                        final_exam=row.get('final_exam', 0),
                        attendance_rate=row.get('attendance_rate', row.get('attendance', 0)),
                        teacher_id=row.get('teacher_id', 'T001'),
                    )
            messages.success(request, f'Successfully imported {len(df)} records for {TARGET_YEAR}')
            return redirect('performance:management')
        except Exception as e:
            messages.error(request, f'Error uploading data: {str(e)}')
    
    return redirect('performance:management')

@login_required
def submit_record(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            course_code = request.POST.get('course_code')
            ca_score = float(request.POST.get('ca_score', 0))
            attendance = float(request.POST.get('attendance', 0))
            
            student = Student.objects.get(student_id=student_id)
            
            AcademicRecord.objects.create(
                student=student,
                course_code=course_code,
                academic_year=TARGET_YEAR,
                ca_total=ca_score,
                mid_term=0,
                final_exam=0,
                attendance_rate=attendance,
                teacher_id='T001'
            )
            messages.success(request, f'Record added successfully for {student.first_name} {student.last_name}')
        except Student.DoesNotExist:
            messages.error(request, f'Student ID {student_id} not found in database')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('performance:management')


class RecordCreateView(CreateView):
    model = AcademicRecord
    fields = ['student', 'course_code', 'academic_year', 'ca_total', 'mid_term', 'final_exam', 'attendance_rate', 'teacher_id']
    template_name = 'performance/record_form.html'
    success_url = '/performance/'


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
>>>>>>> 8f8b8a7ee1e2a51d5f675e24d430d18d897fd0f0
