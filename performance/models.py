from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True) # e.g., CS, ENG, BIZ

    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    employee_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.name} ({self.department.code})"

class Student(models.Model):
    STATUS_CHOICES = [
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
        ('Probation', 'Probation'),
    ]

    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    # AI Driven Fields
    current_gpa = models.FloatField(help_text="This is the CA score used as input")
    predicted_gpa = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pass')
    
    # Audit info
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class AcademicRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_code = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=20, default='2025/2026')  # Add this field
    ca_total = models.FloatField()
    mid_term = models.FloatField(default=0.0)
    final_exam = models.FloatField(default=0.0)
    attendance_rate = models.FloatField(null=True, blank=True)
    teacher_id = models.CharField(max_length=20)
    is_finalized = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.student_id} - {self.course_code}"
    
     
class Course(models.Model):
   code = models.CharField(max_length=10, unique=True)
   name = models.CharField(max_length=100)
   department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
   credits = models.IntegerField(default=3)


   def __str__(self):
    return self.name