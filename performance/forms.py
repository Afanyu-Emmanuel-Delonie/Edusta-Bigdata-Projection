"""
Forms for Performance Dashboard
Includes CSV upload and DYNAMIC filter forms based on actual dataset
"""

from django import forms
from django.db.models import Q
from .models import Course, Semester, Group, Performance, Dataset, Student


class CSVUploadForm(forms.Form):
    """
    Form for uploading CSV/Excel files with dataset naming
    """
    
    dataset_name = forms.CharField(
        max_length=100,
        required=True,
        label='Dataset Name',
        help_text='Give this upload a name (e.g., "Midterm Exam", "Final Grades", "Quiz 1")',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., Midterm Exam 2024'
        })
    )
    
    dataset_description = forms.CharField(
        required=False,
        label='Description (Optional)',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Brief description of this dataset...',
            'rows': 3
        })
    )
    
    file = forms.FileField(
        label='Upload CSV or Excel File',
        help_text='Accepted formats: .csv, .xlsx, .xls',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label='Auto-detect from file',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        required=True,
        empty_label='Select Semester',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if file:
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                raise forms.ValidationError('Invalid file format. Please upload a CSV or Excel file.')
            
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size exceeds 10MB limit.')
        
        return file


class DashboardFilterForm(forms.Form):
    """
    DYNAMIC Form for filtering dashboard data
    Filters populate based on actual data in the database
    """
    
    # Department Filter
    department = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    # Course Filter
    course = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    # Semester Filter
    semester = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    # Group Filter
    group = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    # Status Filter
    status = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    # Search Field
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search by Student ID or Name...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        current_filters = kwargs.pop('current_filters', {})
        super().__init__(*args, **kwargs)
        
        # Get base queryset for performance records
        qs = Performance.objects.all()
        
        # Apply user restrictions if teacher
        if user and hasattr(user, 'role') and user.role.is_teacher():
            qs = qs.filter(course__teacher=user)
        
        # 1. DEPARTMENT FILTER (from Student model)
        departments = Student.objects.filter(
            performances__in=qs
        ).values_list('department', flat=True).distinct().order_by('department')
        
        dept_choices = [('', 'All Departments')]
        dept_choices.extend([(dept, dept) for dept in departments if dept])
        self.fields['department'].choices = dept_choices
        
        # Apply department filter for cascading
        if current_filters.get('department'):
            qs = qs.filter(student__department=current_filters['department'])
        
        # 2. COURSE FILTER (only courses in dataset)
        courses = qs.values_list('course__id', 'course__code', 'course__name').distinct().order_by('course__code')
        
        course_choices = [('', 'All Courses')]
        for course_id, code, name in courses:
            label = f"{code} - {name}" if name and name != code else code
            course_choices.append((str(course_id), label))
        self.fields['course'].choices = course_choices
        
        # Apply course filter for cascading
        if current_filters.get('course'):
            qs = qs.filter(course__id=current_filters['course'])
        
        # 3. SEMESTER FILTER (Static - 1, 2, Summer with counts)
        # DON'T apply cascading - show all semesters independently
        semester_qs = Performance.objects.all()
        
        # Apply user restrictions if teacher
        if user and hasattr(user, 'role') and user.role.is_teacher():
            semester_qs = semester_qs.filter(course__teacher=user)
        
        from django.db.models import Q, Count
        
        # Count for Semester 1
        sem1_count = semester_qs.filter(
            Q(semester__name__icontains='1') | 
            Q(semester__name__icontains='one') | 
            Q(semester__name__icontains='first')
        ).values('student').distinct().count()
        
        # Count for Semester 2
        sem2_count = semester_qs.filter(
            Q(semester__name__icontains='2') | 
            Q(semester__name__icontains='two') | 
            Q(semester__name__icontains='second')
        ).values('student').distinct().count()
        
        # Count for Summer
        summer_count = semester_qs.filter(
            semester__name__icontains='summer'
        ).values('student').distinct().count()
        
        semester_choices = [('', 'All Semesters')]
        
        # Only add options that have data
        if sem1_count > 0:
            semester_choices.append(('1', f'Semester 1 ({sem1_count})'))
        if sem2_count > 0:
            semester_choices.append(('2', f'Semester 2 ({sem2_count})'))
        if summer_count > 0:
            semester_choices.append(('summer', f'Summer ({summer_count})'))
        
        self.fields['semester'].choices = semester_choices
        
        # Apply semester filter for cascading
        if current_filters.get('semester'):
            qs = qs.filter(semester__id=current_filters['semester'])
        
        # 4. GROUP FILTER (Course Code - Group Name format)
        groups = qs.filter(group__isnull=False).values_list(
            'group__id', 'group__name', 'course__code'
        ).distinct().order_by('course__code', 'group__name')
        
        group_choices = [('', 'All Groups')]
        for group_id, group_name, course_code in groups:
            label = f"{course_code} - {group_name}"
            group_choices.append((str(group_id), label))
        self.fields['group'].choices = group_choices
        
        # 5. STATUS FILTER (only statuses present in data)
        statuses = qs.values_list('performance_status', flat=True).distinct().order_by('performance_status')
        
        status_choices = [('', 'All Status')]
        status_order = ['Excellent', 'Good', 'Average', 'Poor']
        for status in status_order:
            if status in statuses:
                status_choices.append((status, status))
        self.fields['status'].choices = status_choices


class ExportForm(forms.Form):
    """
    Form for exporting data
    """
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel (XLSX)'),
        ('pdf', 'PDF Report'),
    ]
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        })
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        label='Include Charts (PDF only)',
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'
        })
    )