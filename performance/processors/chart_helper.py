from ..models import Student

def get_dashboard_charts():
    # Example: Count students by Status
    pass_count = Student.objects.filter(status='Pass').count()
    fail_count = Student.objects.filter(status='Fail').count()
    prob_count = Student.objects.filter(status='Probation').count()

    return {
        'status_labels': ['Pass', 'Fail', 'Probation'],
        'status_data': [pass_count, fail_count, prob_count],
    }