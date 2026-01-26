from django import forms
from .models import Student, AcademicRecord


class CSVUploadForm(forms.Form):
    """Form for uploading CSV files with performance data"""
    file = forms.FileField(
        label='Upload CSV File',
        help_text='Upload CSV with columns: student_id, course_code, ca_total, mid_term, final_exam, attendance_rate, teacher_id',
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50',
            'accept': '.csv'
        })
    )
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        
        if file:
            if not file.name.lower().endswith('.csv'):
                raise forms.ValidationError('Please upload a CSV file.')
            
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size exceeds 10MB limit.')
        
        return file


class AcademicRecordForm(forms.ModelForm):
    class Meta:
        model = AcademicRecord
        fields = ['student', 'course_code', 'ca_total', 'mid_term', 'final_exam', 'attendance_rate', 'teacher_id']
        
    def clean_ca_total(self):  # Changed from clean_ca_score
        ca = self.cleaned_data.get('ca_total')
        if ca < 0 or ca > 30:  # CA is out of 30 based on your 30/30/40 system
            raise forms.ValidationError("CA Total must be between 0 and 30.")
        return ca

    def clean_mid_term(self):  # Added validation for mid_term
        mid = self.cleaned_data.get('mid_term')
        if mid is not None and (mid < 0 or mid > 30):  # Mid-term is out of 30
            raise forms.ValidationError("Mid-term must be between 0 and 30.")
        return mid

    def clean_attendance_rate(self):
        att = self.cleaned_data.get('attendance_rate')
        if att is not None and (att < 0 or att > 1):
            raise forms.ValidationError("Attendance must be between 0.0 and 1.0 (e.g., 0.85 for 85%).")
        return att

    def clean_final_exam(self):  # Changed from clean_final_score
        final = self.cleaned_data.get('final_exam')
        # Allow 0 for 'Situation A' (not yet uploaded)
        if final is not None and (final < 0 or final > 40):  # Final exam is out of 40
            raise forms.ValidationError("Final Exam must be between 0 and 40.")
        return final