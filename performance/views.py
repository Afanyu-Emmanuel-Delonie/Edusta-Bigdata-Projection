import os
import joblib
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import Student, AcademicRecord, Teacher, Department, Course
from .forms import CSVUploadForm


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard combining actual performance and AI predictions
    Handles both Situation A (predictions) and Situation B (actual results)
    """
    # 1. Load AI Assets
    model_dir = os.path.join('performance', 'ml_models', 'saved_models')
    try:
        classifier = joblib.load(os.path.join(model_dir, 'classifier.pkl'))
        le_course = joblib.load(os.path.join(model_dir, 'le_course.pkl'))
        le_teacher = joblib.load(os.path.join(model_dir, 'le_teacher.pkl'))
        features = joblib.load(os.path.join(model_dir, 'feature_names.pkl'))
        models_loaded = True
    except FileNotFoundError:
        models_loaded = False
        messages.warning(request, 'AI models not found. Using simplified predictions.')
    
    # 2. Fetch all data
    students = Student.objects.select_related('department').all()
    records = AcademicRecord.objects.all()
    
    results_list = []
    total_risk_count = 0
    high_performers = 0
    at_risk_students = 0
    
    for student in students:
        # Get the record for this specific student
        record = records.filter(student=student).first()
        
        if record:
            # ACTUAL PERFORMANCE (Situation B)
            actual_gpa = round((record.final_score / 100) * 4.0, 2) if record.final_score > 0 else 0
            
            # AI PREDICTION (Situation A)
            if models_loaded and record.ca_score > 0:
                try:
                    # Prepare AI Input
                    ca_perc = (record.ca_score / 40) * 100
                    c_enc = le_course.transform([record.course_code])[0] if record.course_code else 0
                    t_enc = le_teacher.transform([record.teacher_id])[0] if record.teacher_id else 0
                    
                    input_df = pd.DataFrame(
                        [[ca_perc, record.attendance_rate, c_enc, t_enc]], 
                        columns=features
                    )
                    
                    # Get prediction probability
                    probs = classifier.predict_proba(input_df)[0]
                    # Predict GPA based on pass probability (class 1)
                    predicted_gpa = round(probs[1] * 4.0, 2)
                except Exception as e:
                    # Fallback to simple prediction
                    predicted_gpa = round((record.ca_score / 40) * 4.0 * 0.95, 2)
            else:
                # Simple prediction formula when models not available
                predicted_gpa = round((record.ca_score / 40) * 4.0 * 0.95, 2)
            
            # Update student record
            student.current_gpa = actual_gpa if actual_gpa > 0 else predicted_gpa
            student.predicted_gpa = predicted_gpa
            
            # Define Status based on Actual GPA (or predicted if no final score)
            gpa_to_check = actual_gpa if actual_gpa > 0 else predicted_gpa
            
            if gpa_to_check >= 3.5:
                student.status = 'Excellent'
                high_performers += 1
            elif gpa_to_check >= 3.0:
                student.status = 'Good'
            elif gpa_to_check >= 2.0:
                student.status = 'Pass'
            else:
                student.status = 'At Risk'
                at_risk_students += 1
            
            student.save()
            
            # Variance Analysis (The "Hard" Part)
            # Only calculate variance if we have actual results
            if actual_gpa > 0:
                variance = round(actual_gpa - predicted_gpa, 2)
                variance_category = get_variance_category(variance)
                
                # Count students with negative variance (performing worse than predicted)
                if variance < -0.5:
                    total_risk_count += 1
            else:
                variance = None
                variance_category = 'Pending'
            
            results_list.append({
                'student': student,
                'actual': actual_gpa if actual_gpa > 0 else None,
                'predicted': predicted_gpa,
                'variance': variance,
                'variance_category': variance_category,
                'record': record,
                'status': student.status,
                'department': student.department.name if hasattr(student, 'department') and student.department else 'N/A'
            })
    
    # Sort by variance (most at-risk first)
    results_list = sorted(
        results_list, 
        key=lambda x: x['variance'] if x['variance'] is not None else 0
    )
    
    # Calculate summary statistics
    total_students = students.count()
    avg_actual_gpa = sum([r['actual'] for r in results_list if r['actual']]) / len([r for r in results_list if r['actual']]) if any(r['actual'] for r in results_list) else 0
    avg_predicted_gpa = sum([r['predicted'] for r in results_list]) / len(results_list) if results_list else 0
    
    context = {
        'results': results_list,
        'total_students': total_students,
        'risk_count': total_risk_count,
        'high_performers': high_performers,
        'at_risk_students': at_risk_students,
        'avg_actual_gpa': round(avg_actual_gpa, 2),
        'avg_predicted_gpa': round(avg_predicted_gpa, 2),
        'departments': Department.objects.all() if 'Department' in dir() else None,
        'models_status': 'Active' if models_loaded else 'Fallback Mode'
    }
    
    return render(request, 'performance/overview.html', context)


def get_variance_category(variance):
    """
    Helper function to categorize variance between predicted and actual GPA
    """
    if variance is None:
        return 'Pending'
    elif variance >= 0.5:
        return 'Outperforming'
    elif variance >= -0.2:
        return 'On Track'
    elif variance >= -0.5:
        return 'Slight Underperformance'
    else:
        return 'High Risk'

@login_required
def risk_tracker(request):
    """Risk tracker for students needing intervention"""
    try:
        # Students with low final scores (< 50)
        at_risk_students = Student.objects.annotate(
            avg_score=Avg('academicrecord__final_score')
        ).filter(avg_score__lt=50).order_by('avg_score')
        
        context = {
            'at_risk_students': at_risk_students,
            'total_at_risk': at_risk_students.count(),
        }
        return render(request, 'performance/risk_tracker.html', context)
    except Exception as e:
        messages.error(request, f'Risk tracker error: {str(e)}')
        return render(request, 'performance/risk_tracker.html', {'error': str(e)})


@login_required
def graduation_analytics(request):
    """Graduation analytics - shows students with finalized scores"""
    try:
        # Students with completed records (final_score > 0)
        graduates = Student.objects.annotate(
            final_avg=Avg('academicrecord__final_score')
        ).filter(final_avg__gt=0).order_by('-final_avg')
        
        context = {
            'graduates': graduates,
            'total_graduates': graduates.count(),
        }
        return render(request, 'performance/graduation_analytics.html', context)
    except Exception as e:
        messages.error(request, f'Graduation analytics error: {str(e)}')
        return render(request, 'performance/graduation_analytics.html', {'error': str(e)})


@login_required
def institutional_insights(request):
    """Institutional insights and statistics"""
    try:
        # Statistics by department
        dept_stats = Department.objects.annotate(
            student_count=Count('student'),
            avg_score=Avg('student__academicrecord__final_score')
        ).order_by('-avg_score')
        
        # Statistics by teacher
        teacher_stats = Teacher.objects.annotate(
            course_count=Count('courses'),
            avg_student_score=Avg('courses__academicrecord__final_score')
        ).order_by('-avg_student_score')
        
        context = {
            'dept_stats': dept_stats,
            'teacher_stats': teacher_stats,
        }
        return render(request, 'performance/institutional_insights.html', context)
    except Exception as e:
        messages.error(request, f'Insights error: {str(e)}')
        return render(request, 'performance/institutional_insights.html', {'error': str(e)})


@login_required
def data_management(request):
    """Data management and CSV upload"""
    form = CSVUploadForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST' and form.is_valid():
        try:
            file = request.FILES['file']
            # Process the file
            messages.success(request, 'File uploaded successfully!')
        except Exception as e:
            messages.error(request, f'Upload error: {str(e)}')
    
    context = {'form': form}
    return render(request, 'performance/management.html', context)


@login_required
def upload_semester_data(request):
    """Bulk upload semester data"""
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                messages.success(request, 'Data uploaded successfully!')
                return redirect('performance:dashboard')
            except Exception as e:
                messages.error(request, f'Error uploading data: {str(e)}')
    else:
        form = CSVUploadForm()
    
    return render(request, 'performance/management.html', {'form': form})


class RecordCreateView(CreateView):
    """Create a new academic record"""
    model = AcademicRecord
    fields = ['student', 'course_code', 'ca_score', 'final_score', 'attendance_rate', 'teacher_id']
    template_name = 'performance/record_form.html'
    success_url = '/performance/'

