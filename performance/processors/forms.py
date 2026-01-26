from django import forms
from .models import Department

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Academic CSV")
    year = forms.IntegerField(initial=2026)

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code']