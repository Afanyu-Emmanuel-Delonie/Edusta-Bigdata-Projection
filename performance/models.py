"""
Models for Student Performance Management System
Handles courses, students, performance records, and user roles
UPDATED: Added score components and proper calculation support
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


# User Role Choices
class UserRole(models.Model):
    """
    Extends Django User model with role-based permissions
    Roles: Super Admin, Admin, Teacher
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')
    department = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'


class Course(models.Model):
    """
    Represents a course offered at AUCA
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses')
    credits = models.IntegerField(default=3)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(models.Model):
    """
    Represents a student at AUCA
    """
    student_id = models.CharField(max_length=10, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100, blank=True, default='General')
    enrollment_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['student_id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_semester_courses_count(self, semester):
        """Get count of active courses for this student in a semester"""
        return Performance.objects.filter(
            student=self,
            semester=semester,
            dataset__is_active=True
        ).values('course').distinct().count()
    
    def can_enroll_in_course(self, semester):
        """Check if student can enroll in another course (8-course limit)"""
        return self.get_semester_courses_count(semester) < 8


class Semester(models.Model):
    """
    Represents an academic semester
    """
    SEMESTER_CHOICES = [
        ('Fall', 'Fall'),
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
    ]
    
    name = models.CharField(max_length=50)  # e.g., "Fall 2024"
    semester_type = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-year', '-start_date']
        unique_together = ['semester_type', 'year']
        verbose_name = 'Semester'
        verbose_name_plural = 'Semesters'
    
    def __str__(self):
        return self.name


class Group(models.Model):
    """
    Represents a student group within a course
    """
    name = models.CharField(max_length=50)  # e.g., "Group A", "Section 1"
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='groups')
    max_students = models.IntegerField(default=30)
    
    class Meta:
        ordering = ['course', 'name']
        unique_together = ['name', 'course', 'semester']
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.semester})"


class Dataset(models.Model):
    """
    Represents a named dataset (e.g., Midterm, Final, Quiz)
    Teachers can create multiple datasets per semester
    Admins see merged data across all datasets for a semester
    """
    name = models.CharField(max_length=100)  # e.g., "Midterm Exam 2024"
    description = models.TextField(blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='datasets')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='datasets', null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='datasets')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'semester', 'course']
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
    
    def __str__(self):
        course_code = self.course.code if self.course else "All Courses"
        return f"{self.name} - {course_code} - {self.semester.name}"


class Performance(models.Model):
    """
    Stores student performance data for a specific course/semester/dataset
    UPDATED: Added all score components and calculation fields
    """
    GRADE_CHOICES = [
        ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
        ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
        ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
        ('D', 'D'), ('F', 'F'),
    ]
    
    STATUS_CHOICES = [
        ('PASS', 'Pass'),
        ('PROBATION', 'Probation'),
        ('FAIL', 'Fail'),
    ]
    
    PERFORMANCE_STATUS_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('Poor', 'Poor'),
    ]
    
    # Core relationships
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='performances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='performances')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='performances')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='performances')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='performances', null=True, blank=True)
    
    # Score components - FIXED: Added default=0 and null=True, blank=True
    quiz1 = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Quiz 1 score (0-100)"
    )
    quiz2 = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Quiz 2 score (0-100)"
    )
    assignment = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Assignment score (0-100)"
    )
    attendance = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Attendance score (0-100)"
    )
    mid_semester = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Mid-semester exam score (0-100)"
    )
    final_exam = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Final exam score (0-100)"
    )
    
    # Calculated fields
    other_total = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(400)],
        help_text="Sum of quiz1 + quiz2 + assignment + attendance"
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Final weighted score (30% mid + 40% final + 30% other)"
    )
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, blank=True,
        help_text="PASS (≥50), PROBATION (40-49), FAIL (<40)"
    )
    performance_status = models.CharField(
        max_length=20, choices=PERFORMANCE_STATUS_CHOICES, blank=True,
        help_text="Excellent (≥85), Good (70-84), Average (50-69), Poor (<50)"
    )
    ranking = models.IntegerField(null=True, blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-semester', 'course', '-score']
        unique_together = ['student', 'course', 'semester', 'dataset']
        verbose_name = 'Performance Record'
        verbose_name_plural = 'Performance Records'
        indexes = [
            models.Index(fields=['course', 'semester']),
            models.Index(fields=['student', 'semester']),
            models.Index(fields=['status']),
            models.Index(fields=['performance_status']),
            models.Index(fields=['dataset']),
        ]
    
    def __str__(self):
        dataset_name = f" [{self.dataset.name}]" if self.dataset else ""
        return f"{self.student.student_id} - {self.course.code}{dataset_name} - {self.score}"
    
    def clean(self):
        """Validate 8-course limit per student per semester"""
        super().clean()
        
        # Check if this is a new record (not an update)
        if not self.pk:
            # Count existing courses for this student in this semester
            existing_courses = Performance.objects.filter(
                student=self.student,
                semester=self.semester,
                dataset__is_active=True
            ).exclude(
                course=self.course  # Don't count if updating same course
            ).values('course').distinct().count()
            
            if existing_courses >= 8:
                raise ValidationError(
                    f'Student {self.student.student_id} already has 8 courses in {self.semester}. '
                    'AUCA policy limits students to 8 courses per semester.'
                )
    
    def save(self, *args, **kwargs):
        """Auto-calculate grade, status, and performance_status based on score"""
        # Ensure score is set, default to 0 if None
        if self.score is None:
            self.score = 0
        
        # Calculate grade if not provided
        if not self.grade:
            self.grade = self.calculate_grade()
        
        # Calculate status if not provided
        if not self.status:
            self.status = self.calculate_status()
        
        # Calculate performance status if not provided
        if not self.performance_status:
            self.performance_status = self.calculate_performance_status()
        
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def calculate_grade(self):
        """Calculate letter grade based on score - AUCA Grading Scale"""
        score = float(self.score) if self.score else 0
        
        if score >= 95: return 'A+'
        elif score >= 90: return 'A'
        elif score >= 85: return 'A-'
        elif score >= 80: return 'B+'
        elif score >= 75: return 'B'
        elif score >= 70: return 'B-'
        elif score >= 65: return 'C+'
        elif score >= 60: return 'C'
        elif score >= 55: return 'C-'
        elif score >= 50: return 'D'
        else: return 'F'
    
    def calculate_status(self):
        """Calculate academic status based on score - AUCA Academic Status Rules"""
        score = float(self.score) if self.score else 0
        
        if score >= 50: return 'PASS'
        elif score >= 40: return 'PROBATION'
        else: return 'FAIL'
    
    def calculate_performance_status(self):
        """Calculate performance status for additional classification"""
        score = float(self.score) if self.score else 0
        
        if score >= 85: return 'Excellent'
        elif score >= 70: return 'Good'
        elif score >= 50: return 'Average'
        else: return 'Poor'
    
    @staticmethod
    def calculate_weighted_score(mid_semester, final_exam, other_total_normalized):
        """
        Calculate final weighted score
        Formula: 30% mid-semester + 40% final exam + 30% other activities
        
        Args:
            mid_semester: Mid-semester exam score (0-100)
            final_exam: Final exam score (0-100)
            other_total_normalized: Normalized other activities score (0-100)
        
        Returns:
            Weighted final score (0-100)
        """
        weighted = (
            float(mid_semester or 0) * 0.30 +
            float(final_exam or 0) * 0.40 +
            float(other_total_normalized or 0) * 0.30
        )
        return min(max(weighted, 0), 100)  # Clamp to 0-100


class UploadHistory(models.Model):
    """
    Tracks CSV/Excel file uploads
    UPDATED: Added more detailed tracking
    """
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_history')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='uploads/%Y/%m/')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Upload statistics
    records_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    skipped_duplicates = models.IntegerField(default=0)
    skipped_8_course_limit = models.IntegerField(default=0)
    
    # Error logging
    errors_log = models.TextField(blank=True)
    
    # Grade distribution (JSON or text)
    grade_distribution = models.JSONField(null=True, blank=True)
    status_distribution = models.JSONField(null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Upload History'
        verbose_name_plural = 'Upload Histories'
    
    def __str__(self):
        dataset_info = f" [{self.dataset.name}]" if self.dataset else ""
        return f"{self.file_name}{dataset_info} - {self.uploaded_by.username} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def success_rate(self):
        """Calculate upload success rate"""
        if self.records_count == 0:
            return 0
        return (self.success_count / self.records_count) * 100


class Recommendation(models.Model):
    """
    Stores automated recommendations for students
    """
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='recommendations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='recommendations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_text = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_recommendations')
    
    class Meta:
        ordering = ['-created_at', '-priority']
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} - {self.priority}"


class AcademicYear(models.Model):
    """
    Represents an academic year (optional, for better organization)
    """
    name = models.CharField(max_length=20, unique=True)  # e.g., "2024-2025"
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_year']
        verbose_name = 'Academic Year'
        verbose_name_plural = 'Academic Years'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Ensure end_year > start_year"""
        if self.end_year <= self.start_year:
            raise ValidationError('End year must be greater than start year.')


class Teacher(models.Model):
    """
    Extended teacher information (optional enhancement)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200, blank=True)
    office_location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.teacher_id})"