"""
Complete Performance Management Models with ML Prediction Fields
Simplified - Single User Type (Django's built-in User)
"""
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class Course(models.Model):
    """Course/Subject information"""
    code = models.CharField(max_length=20, unique=True, help_text="Course code (e.g., CS101)")
    name = models.CharField(max_length=200, help_text="Full course name")
    department = models.CharField(max_length=100, blank=True)
    credits = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(10)])
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_teaching')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(models.Model):
    """Student information"""
    student_id = models.CharField(max_length=20, unique=True, help_text="Student ID number")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    
    class Meta:
        ordering = ['student_id']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Semester(models.Model):
    """Academic semester/term"""
    SEMESTER_TYPE_CHOICES = [
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
    ]
    
    name = models.CharField(max_length=50, unique=True, help_text="e.g., Fall 2024")
    semester_type = models.CharField(max_length=10, choices=SEMESTER_TYPE_CHOICES)
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)])
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-year', '-start_date']
        verbose_name = 'Semester'
        verbose_name_plural = 'Semesters'
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")


class Group(models.Model):
    """Course group/section"""
    name = models.CharField(max_length=50, help_text="Group name (e.g., Group A)")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='groups')
    max_students = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    
    class Meta:
        ordering = ['course', 'name']
        unique_together = ['course', 'semester', 'name']
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.semester.name})"


class Dataset(models.Model):
    """Dataset for organizing uploaded performance data"""
    name = models.CharField(max_length=200, help_text="Dataset name")
    description = models.TextField(blank=True)
    
    # ✅ FIX: Make course nullable since CSV can contain multiple courses
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='datasets',
        null=True,  # ✅ Added
        blank=True  # ✅ Added
    )
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='datasets')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='datasets_uploaded')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        # ✅ FIX: Removed course from unique_together since it can be NULL
        # unique_together = ['name', 'course', 'semester']
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
    
    def __str__(self):
        course_str = f" - {self.course.code}" if self.course else ""
        return f"{self.name}{course_str} ({self.semester.name})"

class Performance(models.Model):
    """
    Stores student performance data with ML predictions
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
    
    RISK_LEVEL_CHOICES = [
        ('CRITICAL', 'Critical Risk'),
        ('HIGH', 'High Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('LOW', 'Low Risk'),
        ('NONE', 'No Risk'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    TREND_CHOICES = [
        ('IMPROVING', 'Improving'),
        ('STABLE', 'Stable'),
        ('DECLINING', 'Declining'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    # Core relationships
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='performances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='performances')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='performances')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='performances')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='performances', null=True, blank=True)
    
    # Score components (normalized 0-100)
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
        help_text="Attendance percentage (0-100)"
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
    
    # ML PREDICTION FIELDS
    ml_predicted_pass = models.BooleanField(
        null=True, blank=True,
        help_text="ML prediction: True=Pass, False=Fail"
    )
    ml_confidence = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="ML prediction confidence (0-100%)"
    )
    ml_prediction_label = models.CharField(
        max_length=10, blank=True,
        help_text="Pass or Fail label from ML model"
    )
    
    # Risk assessment
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        default='UNKNOWN',
        help_text="Automated risk assessment based on ML + rules"
    )
    risk_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Composite risk score (0=no risk, 100=critical risk)"
    )
    
    # Performance trend prediction
    performance_trend = models.CharField(
        max_length=20,
        choices=TREND_CHOICES,
        default='UNKNOWN',
        help_text="Predicted trend based on historical data"
    )
    
    # Predicted final score
    predicted_final_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="ML-predicted final score based on current performance"
    )
    
    # Intervention recommendations
    needs_intervention = models.BooleanField(
        default=False,
        help_text="Flagged for immediate intervention"
    )
    intervention_priority = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Intervention priority (1=highest, 10=lowest)"
    )
    
    # Probability scores (from Random Forest)
    prob_fail = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Probability of failure (0-100%)"
    )
    prob_pass = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Probability of passing (0-100%)"
    )
    
    # ML metadata
    ml_model_version = models.CharField(
        max_length=50, blank=True,
        help_text="Version of ML model used for prediction"
    )
    ml_predicted_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp when ML prediction was made"
    )
    ml_features_json = models.JSONField(
        null=True, blank=True,
        help_text="JSON dump of features used for prediction"
    )
    
    class Performance(models.Model):
    # ... all your existing fields ...
    
    # ... existing methods like calculate_grade(), calculate_status(), etc. ...
    
     @property
     def gpa(self):
            """
            Calculate GPA for this single course (4.0 scale)
            Formula: (Score / 100) × 4.0
            
            This represents what this course contributes to overall GPA
            """
            if not self.score:
                return 0.0
            
            score = float(self.score)
            # Convert score (0-100) to GPA (0-4.0)
            gpa = (score / 100) * 4.0
            
            return round(gpa, 2)
        
    def calculate_ranking(self):
            """
            Calculate student's ranking in their course/semester
            Returns ranking number (1 = top performer)
            """
            # Get all performances in same course and semester
            same_course_semester = Performance.objects.filter(
                course=self.course,
                semester=self.semester
            ).order_by('-score')
            
            # Find this student's position
            rank = 1
            for perf in same_course_semester:
                if perf.id == self.id:
                    return rank
                rank += 1
            
            return None
        
    def save(self, *args, **kwargs):
            """Auto-calculate derived fields"""
            if self.score is None:
                self.score = 0
            
            if not self.grade:
                self.grade = self.calculate_grade()
            if not self.status:
                self.status = self.calculate_status()
            if not self.performance_status:
                self.performance_status = self.calculate_performance_status()
            
            if self.ml_predicted_pass is not None and not self.risk_level:
                self.risk_level = self.calculate_risk_level()
            
            # Calculate ranking if not set
            is_new = self.pk is None
            
            self.full_clean()
            super().save(*args, **kwargs)
            
            # Update ranking after save (need ID first)
            if is_new or not self.ranking:
                self.ranking = self.calculate_ranking()
                # Save again with ranking (use update to avoid recursion)
                Performance.objects.filter(pk=self.pk).update(ranking=self.ranking)
    
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
            models.Index(fields=['risk_level']),
            models.Index(fields=['ml_predicted_pass']),
            models.Index(fields=['needs_intervention']),
        ]
    
    def __str__(self):
        dataset_name = f" [{self.dataset.name}]" if self.dataset else ""
        return f"{self.student.student_id} - {self.course.code}{dataset_name} - {self.score}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate derived fields"""
        if self.score is None:
            self.score = 0
        
        if not self.grade:
            self.grade = self.calculate_grade()
        if not self.status:
            self.status = self.calculate_status()
        if not self.performance_status:
            self.performance_status = self.calculate_performance_status()
        
        if self.ml_predicted_pass is not None and not self.risk_level:
            self.risk_level = self.calculate_risk_level()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calculate_grade(self):
        """Calculate letter grade based on score"""
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
        """Calculate academic status"""
        score = float(self.score) if self.score else 0
        
        if score >= 50: return 'PASS'
        elif score >= 40: return 'PROBATION'
        else: return 'FAIL'
    
    def calculate_performance_status(self):
        """Calculate performance classification"""
        score = float(self.score) if self.score else 0
        
        if score >= 85: return 'Excellent'
        elif score >= 70: return 'Good'
        elif score >= 50: return 'Average'
        else: return 'Poor'
    
    def calculate_risk_level(self):
        """Calculate risk level based on ML prediction + actual score"""
        score = float(self.score) if self.score else 0
        ml_conf = float(self.ml_confidence) if self.ml_confidence else 50
        
        if score < 40 and not self.ml_predicted_pass and ml_conf > 70:
            return 'CRITICAL'
        
        if score < 50 and not self.ml_predicted_pass:
            return 'HIGH'
        
        if 40 <= score < 55 or ml_conf < 60:
            return 'MEDIUM'
        
        if 55 <= score < 85:
            return 'LOW'
        
        return 'NONE'
    
    def get_ml_summary(self):
        """Get human-readable ML prediction summary"""
        if self.ml_predicted_pass is None:
            return "No prediction available"
        
        prediction = "PASS" if self.ml_predicted_pass else "FAIL"
        confidence = f"{self.ml_confidence:.1f}%" if self.ml_confidence else "N/A"
        
        return f"{prediction} (Confidence: {confidence})"
    
    def get_risk_color(self):
        """Get color code for risk level (for UI)"""
        colors = {
            'CRITICAL': '#DC2626',
            'HIGH': '#F59E0B',
            'MEDIUM': '#FCD34D',
            'LOW': '#10B981',
            'NONE': '#3B82F6',
        }
        return colors.get(self.risk_level, '#6B7280')
    
    def get_intervention_message(self):
        """Get recommended intervention message"""
        if not self.needs_intervention:
            return None
        
        messages = {
            'CRITICAL': "URGENT: Immediate academic intervention required",
            'HIGH': "HIGH PRIORITY: Schedule counseling session",
            'MEDIUM': "MODERATE: Monitor progress closely",
            'LOW': "✓ LOW: Encourage continued effort",
        }
        return messages.get(self.risk_level, "Review student progress")


class UploadHistory(models.Model):
    """Track file upload history"""
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='upload_history')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True, blank=True)
    records_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Upload History'
        verbose_name_plural = 'Upload Histories'
    
    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


class Recommendation(models.Model):
    """Academic recommendations and interventions"""
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
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_recommendations')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at', '-priority']
        verbose_name = 'Recommendation'
        verbose_name_plural = 'Recommendations'
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} - {self.priority}"
    
    
@property
def gpa(self):
    """
    Calculate GPA based on grade
    Standard 4.0 scale
    """
    grade_to_gpa = {
        'A+': 4.0,
        'A': 4.0,
        'A-': 3.7,
        'B+': 3.3,
        'B': 3.0,
        'B-': 2.7,
        'C+': 2.3,
        'C': 2.0,
        'C-': 1.7,
        'D': 1.0,
        'F': 0.0,
    }
    return grade_to_gpa.get(self.grade, 0.0)


# Also, if you don't have this method, add it:
def calculate_ranking(self):
    """
    Calculate student's ranking in their course/semester
    Returns ranking number (1 = top performer)
    """
    from django.db.models import Count
    
    # Get all performances in same course and semester
    same_course_semester = Performance.objects.filter(
        course=self.course,
        semester=self.semester
    ).order_by('-score')
    
    # Find this student's position
    rank = 1
    for perf in same_course_semester:
        if perf.id == self.id:
            return rank
        rank += 1
    
    return None


# Override save method to auto-calculate ranking
def save(self, *args, **kwargs):
    """Auto-calculate ranking and other derived fields before saving"""
    
    # Calculate ranking if not set
    if not self.ranking:
        super().save(*args, **kwargs)  # Save first to get ID
        self.ranking = self.calculate_ranking()
    
    super().save(*args, **kwargs)