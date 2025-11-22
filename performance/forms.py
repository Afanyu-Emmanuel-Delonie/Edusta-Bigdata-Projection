"""
Forms for Performance Dashboard
Includes CSV upload and filter forms
"""

from django import forms
from .models import Course, Semester, Group, Performance

class CSVUploadForm(forms.Form):
    """
    Form for uploading CSV/Excel files
    """
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
        required=False,
        empty_label='Auto-detect from file',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    def clean_file(self):
        """
        Validate uploaded file
        """
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file extension
            file_name = file.name.lower()
            if not (file_name.endswith('.csv') or file_name.endswith('.xlsx') or file_name.endswith('.xls')):
                raise forms.ValidationError('Invalid file format. Please upload a CSV or Excel file.')
            
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size exceeds 10MB limit.')
        
        return file


class DashboardFilterForm(forms.Form):
    """
    Form for filtering dashboard data
    """
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label='All Courses',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('-year', '-start_date'),
        required=False,
        empty_label='All Semesters',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label='All Groups',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Performance.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white',
            'onchange': 'this.form.submit()'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search by Student ID or Name...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter courses by user if teacher
        if user and hasattr(user, 'role') and user.role.is_teacher():
            self.fields['course'].queryset = Course.objects.filter(teacher=user)


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