"""
Performance Analysis Module
Analyzes student performance data and generates insights
"""

import pandas as pd
from django.db.models import Avg, Count, Q, Max, Min
from decimal import Decimal
from .models import Performance, Course, Semester, Student, Recommendation


class PerformanceAnalyzer:
    """
    Analyzes performance data and generates KPIs, charts, and recommendations
    """
    
    def __init__(self, user, filters=None):
        """
        Initialize analyzer
        
        Args:
            user: Django User object (can be None for anonymous access)
        """
        self.user = user
        # Filters is a dict that can include keys: course, semester, group, status, search
        self.filters = filters or {}
    
    def get_filtered_queryset(self):
        """
        Get filtered queryset of all performances
        For now, returns all performances (no user filtering)
        
        Returns:
            QuerySet of Performance objects
        """
        qs = Performance.objects.all().select_related(
            'student', 'course', 'semester', 'group'
        )

        # Apply basic filters if provided
        f = self.filters or {}

        # Filter by course (accept id or code)
        course = f.get('course')
        if course:
            try:
                course_id = int(course)
                qs = qs.filter(course__id=course_id)
            except Exception:
                qs = qs.filter(course__code__iexact=str(course))

        # Filter by semester (id or name)
        semester = f.get('semester')
        if semester:
            try:
                sem_id = int(semester)
                qs = qs.filter(semester__id=sem_id)
            except Exception:
                qs = qs.filter(semester__name__iexact=str(semester))

        # Filter by group (id or name)
        group = f.get('group')
        if group:
            try:
                group_id = int(group)
                qs = qs.filter(group__id=group_id)
            except Exception:
                qs = qs.filter(group__name__iexact=str(group))

        # Filter by performance status
        status = f.get('status')
        if status:
            qs = qs.filter(performance_status__iexact=str(status))

        # Search across student id and names
        search = f.get('search')
        if search:
            qs = qs.filter(
                Q(student__student_id__icontains=search) |
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )

        # If the user appears to be a teacher, optionally restrict to their courses
        try:
            if self.user and hasattr(self.user, 'role') and getattr(self.user, 'role') and getattr(self.user.role, 'is_teacher', lambda: False)():
                qs = qs.filter(course__teacher=self.user)
        except Exception:
            # ignore role checks if role API isn't present
            pass

        return qs.order_by('-semester__start_date', '-score')
    
    def calculate_kpis(self):
        """
        Calculate Key Performance Indicators
        
        Returns:
            dict with KPI metrics
        """
        performances = self.get_filtered_queryset()
        
        if not performances.exists():
            return {
                'total_students': 0,
                'average_score': 0,
                'pass_rate': 0,
                'fail_rate': 0,
                'total_courses': 0,
                'highest_score': 0,
                'lowest_score': 0,
            }
        
        total = performances.count()
        passing = performances.filter(score__gte=50).count()
        failing = performances.filter(score__lt=50).count()
        
        scores = performances.values_list('score', flat=True)
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_students': performances.values('student').distinct().count(),
            'average_score': round(avg_score, 2),
            'pass_rate': round((passing / total * 100), 2) if total > 0 else 0,
            'fail_rate': round((failing / total * 100), 2) if total > 0 else 0,
            'total_courses': performances.values('course').distinct().count(),
            'highest_score': performances.aggregate(Max('score'))['score__max'] or 0,
            'lowest_score': performances.aggregate(Min('score'))['score__min'] or 0,
        }
    
    def get_performance_distribution(self):
        """
        Get distribution of scores in ranges
        
        Returns:
            dict with score ranges and counts
        """
        performances = self.get_filtered_queryset()
        
        ranges = {
            '90-100': performances.filter(score__gte=90, score__lte=100).count(),
            '80-89': performances.filter(score__gte=80, score__lt=90).count(),
            '70-79': performances.filter(score__gte=70, score__lt=80).count(),
            '60-69': performances.filter(score__gte=60, score__lt=70).count(),
            '50-59': performances.filter(score__gte=50, score__lt=60).count(),
            '0-49': performances.filter(score__gte=0, score__lt=50).count(),
        }
        
        return ranges
    
    def get_top_performers(self, limit=10):
        """
        Get top performing students
        
        Args:
            limit: number of top performers to return
        
        Returns:
            list of dicts with student info and scores
        """
        performances = self.get_filtered_queryset()[:limit]
        
        result = []
        for perf in performances:
            result.append({
                'student_id': perf.student.student_id,
                'student_name': perf.student.get_full_name(),
                'course': perf.course.code,
                'score': float(perf.score),
                'semester': perf.semester.name,
            })
        
        return result
    
    def get_bottom_performers(self, limit=10):
        """
        Get bottom performing students
        
        Args:
            limit: number of bottom performers to return
        
        Returns:
            list of dicts with student info and scores
        """
        performances = self.get_filtered_queryset().order_by('score')[:limit]
        
        result = []
        for perf in performances:
            result.append({
                'student_id': perf.student.student_id,
                'student_name': perf.student.get_full_name(),
                'course': perf.course.code,
                'score': float(perf.score),
                'semester': perf.semester.name,
            })
        
        return result
    
    def get_course_comparison(self):
        """
        Compare performance across courses
        
        Returns:
            list of dicts with course statistics
        """
        performances = self.get_filtered_queryset()
        
        courses = performances.values('course__code', 'course__name').annotate(
            total_students=Count('student', distinct=True),
            average_score=Avg('score'),
        ).order_by('-average_score')
        
        result = []
        for course in courses:
            course_perfs = performances.filter(course__code=course['course__code'])
            total = course_perfs.count()
            passing = course_perfs.filter(score__gte=50).count()
            
            result.append({
                'course_code': course['course__code'],
                'course_name': course['course__name'],
                'total_students': course['total_students'],
                'average_score': round(float(course['average_score']), 2),
                'pass_rate': round((passing / total * 100), 2) if total > 0 else 0,
            })
        
        return result
    
    def get_semester_trend(self):
        """
        Get performance trends across semesters
        
        Returns:
            list of dicts with semester statistics
        """
        performances = self.get_filtered_queryset()
        
        semesters = performances.values('semester__name', 'semester__year').annotate(
            total_students=Count('student', distinct=True),
            average_score=Avg('score'),
        ).order_by('semester__year', 'semester__name')
        
        result = []
        for sem in semesters:
            sem_perfs = performances.filter(semester__name=sem['semester__name'])
            total = sem_perfs.count()
            passing = sem_perfs.filter(score__gte=50).count()
            
            result.append({
                'semester': sem['semester__name'],
                'year': sem['semester__year'],
                'total_students': sem['total_students'],
                'average_score': round(float(sem['average_score']), 2),
                'pass_rate': round((passing / total * 100), 2) if total > 0 else 0,
            })
        
        return result
    
    def get_recommendations(self, unresolved_only=True):
        """
        Get recommendations for improvement
        
        Args:
            unresolved_only: if True, only return unresolved recommendations
        
        Returns:
            QuerySet of Recommendation objects
        """
        recommendations = Recommendation.objects.all().select_related(
            'student', 'course'
        ).order_by('-priority', '-created_at')
        
        if unresolved_only:
            recommendations = recommendations.filter(is_resolved=False)
        
        return recommendations
    
    def export_to_dataframe(self):
        """
        Export performance data to Pandas DataFrame
        
        Returns:
            pandas DataFrame with performance data
        """
        performances = self.get_filtered_queryset()
        
        data = []
        for perf in performances:
            data.append({
                'Student_ID': perf.student.student_id,
                'First_Name': perf.student.first_name,
                'Last_Name': perf.student.last_name,
                'Department': perf.student.department,
                'Course': perf.course.code,
                'Course_Name': perf.course.name,
                'Semester': perf.semester.name,
                'Group': perf.group.name if perf.group else '',
                'Score': float(perf.score),
                'Grade': perf.grade,
                'Status': perf.performance_status,
            })
        
        return pd.DataFrame(data)
    
    def calculate_rankings(self):
        """
        Calculate rankings for all students in each course/semester
        """
        performances = self.get_filtered_queryset()
        
        # Group by course and semester
        for course in Course.objects.all():
            for semester in Semester.objects.all():
                course_perfs = performances.filter(
                    course=course,
                    semester=semester
                ).order_by('-score')
                
                # Update rankings
                for rank, perf in enumerate(course_perfs, start=1):
                    perf.ranking = rank
                    perf.save(update_fields=['ranking'])
    
    def generate_recommendations(self):
        """
        Generate recommendations for students with low performance
        """
        performances = self.get_filtered_queryset().filter(score__lt=50)
        
        for perf in performances:
            # Check if recommendation already exists
            exists = Recommendation.objects.filter(
                student=perf.student,
                course=perf.course,
                semester=perf.semester,
                is_resolved=False
            ).exists()
            
            if not exists:
                Recommendation.objects.create(
                    student=perf.student,
                    course=perf.course,
                    semester=perf.semester,
                    recommendation_text=f"Student scoring {perf.score}% needs additional support in {perf.course.code}",
                    priority='high' if perf.score < 40 else 'medium',
                )