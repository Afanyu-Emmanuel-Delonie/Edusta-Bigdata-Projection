"""
Analytics Service
All business logic for dashboard, risk tracker, graduation, and insights views.
Views should call these functions and only handle HTTP request/response.
"""

import json
from django.db.models import Avg
from scipy.stats import pearsonr
from ..models import AcademicRecord, Department, Teacher, Course

TARGET_YEAR = "2025/2026"


def get_available_years():
    return AcademicRecord.objects.values_list(
        'academic_year', flat=True
    ).distinct().order_by('-academic_year')


def get_selected_year(request):
    years = get_available_years()
    return request.GET.get('academic_year') or (years[0] if years else TARGET_YEAR)


def get_dashboard_context(selected_year):
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department')

    total_scores = [
        (r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0)
        for r in records
    ]
    avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

    chart_data = [
        sum(1 for s in total_scores if s >= 80),
        sum(1 for s in total_scores if 70 <= s < 80),
        sum(1 for s in total_scores if 50 <= s < 70),
        sum(1 for s in total_scores if s < 50),
    ]

    alerts = records.filter(ca_total__lt=20).select_related(
        'student', 'student__department'
    )[:10]
    for alert in alerts:
        alert.ca_score = alert.ca_total
        total = (alert.ca_total or 0) + (alert.mid_term or 0) + (alert.final_exam or 0)
        alert.student_gpa = (total / 100) * 4.0

    dept_stats = []
    for dept in Department.objects.all():
        dept_records = records.filter(student__department=dept)
        if dept_records.exists():
            dept_scores = [
                (r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0)
                for r in dept_records
            ]
            avg_dept = sum(dept_scores) / len(dept_scores)
            dept_stats.append({
                'code': dept.code,
                'name': dept.name,
                'avg_gpa': round((avg_dept / 100) * 4.0, 2),
                'student_count': dept_records.count(),
            })
    dept_stats.sort(key=lambda x: x['avg_gpa'], reverse=True)

    return {
        'total_count': records.count(),
        'alert_count': records.filter(ca_total__lt=15).count(),
        'avg_gpa': round((avg_score / 100) * 4.0, 2),
        'grad_ready_count': sum(1 for s in total_scores if s >= 50),
        'pass_count': sum(1 for s in total_scores if s >= 50),
        'first_class_count': chart_data[0],
        'chart_data': chart_data,
        'dept_stats': dept_stats,
        'alerts': alerts,
    }


def get_risk_tracker_context(request, selected_year):
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
        record.total_score = (
            (record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)
        )
        if not record.final_exam or record.final_exam == 0:
            pre_exam = (record.ca_total or 0) + (record.mid_term or 0)
            record.status_label = "High Risk" if pre_exam < 30 else "On Track"
        else:
            record.status_label = "Cleared" if record.total_score >= 50 else "Failed"
        record.is_above_avg = record.ca_total > historical_avg

    return {
        'departments': Department.objects.all(),
        'alerts': records,
        'historical_baseline': round(historical_avg, 1),
        'stats': {
            'total': records.count(),
            'critical': records.filter(ca_total__lt=15).count(),
        },
    }


def get_graduation_context(selected_year):
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department')

    graduation_ready = [
        r for r in records
        if (r.ca_total or 0) + (r.mid_term or 0) + (r.final_exam or 0) >= 50
    ]
    total = records.count()

    return {
        'total_students': total,
        'graduation_ready': len(graduation_ready),
        'graduation_rate': round(len(graduation_ready) / total * 100, 1) if total else 0,
        'records': graduation_ready,
    }


def get_insights_context(selected_year):
    records = AcademicRecord.objects.filter(
        academic_year=selected_year
    ).select_related('student', 'student__department')

    # Department consistency matrix
    consistency_matrix = []
    for dept in Department.objects.all():
        dept_records = records.filter(student__department=dept)
        if not dept_records.exists():
            continue
        ca_scores = list(dept_records.values_list('ca_total', flat=True))
        final_scores = list(dept_records.values_list('final_exam', flat=True))
        try:
            correlation = round(pearsonr(ca_scores, final_scores)[0], 2) if len(ca_scores) > 1 else 0
        except Exception:
            correlation = 0
        avg_ca = sum(ca_scores) / len(ca_scores)
        avg_final = sum(final_scores) / len(final_scores)
        bias = "Lenient" if avg_ca > 25 and avg_final > 60 else ("Strict" if avg_ca < 20 and avg_final < 50 else "Balanced")
        consistency_matrix.append({
            'name': dept.name,
            'avg_ca': avg_ca,
            'avg_final': avg_final,
            'correlation': correlation,
            'bias': bias,
        })

    # Teacher recovery rates
    recovery_data = []
    for teacher in Teacher.objects.all()[:5]:
        teacher_records = records.filter(teacher_id=teacher.employee_id)
        low_ca = teacher_records.filter(ca_total__lt=20)
        if low_ca.exists():
            recovered = sum(
                1 for r in low_ca
                if (r.ca_total + r.mid_term + r.final_exam) >= 50
            )
            rate = round((recovered / low_ca.count()) * 100, 1)
        else:
            rate = 0
        recovery_data.append({'name': teacher.name, 'rate': rate})

    # Course performance chart
    course_data = {}
    for record in records:
        if record.course_code not in course_data:
            course_data[record.course_code] = {'scores': [], 'passed': 0, 'total': 0}
        total_score = (record.ca_total or 0) + (record.mid_term or 0) + (record.final_exam or 0)
        course_data[record.course_code]['scores'].append(total_score)
        course_data[record.course_code]['total'] += 1
        if total_score >= 50:
            course_data[record.course_code]['passed'] += 1

    chart_labels, chart_scores, chart_pass_rates = [], [], []
    for code, data in sorted(course_data.items())[:8]:
        chart_labels.append(code)
        chart_scores.append(round(sum(data['scores']) / len(data['scores']), 1))
        chart_pass_rates.append(round(data['passed'] / data['total'] * 100, 1) if data['total'] else 0)

    return {
        'consistency_matrix': consistency_matrix,
        'recovery_data': recovery_data,
        'chart_labels': json.dumps(chart_labels),
        'chart_scores': json.dumps(chart_scores),
        'chart_pass_rates': json.dumps(chart_pass_rates),
    }
