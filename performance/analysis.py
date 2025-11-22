"""
Performance Analysis Module - Simplified for Single Dataset
Analyzes student performance data and generates insights
"""

import pandas as pd
from django.db.models import Avg, Count, Q
from .models import Performance, Recommendation


class PerformanceAnalyzer:
    """
    Analyzes performance data - Simplified for single dataset usage
    Since uploads replace all data, we don't need complex dataset filtering
    """
    
    def __init__(self, user=None, filters=None):
        """
        Initialize analyzer
        
        Args:
            user: Django User object (can be None)
            filters: Dictionary of filters (course, semester, group, status, search)
        """
        self.user = user
        self.filters = filters or {}
    
    def get_filtered_queryset(self):
        """
        Get filtered queryset of performances
        Simplified - no complex dataset merging needed
        
        Returns:
            QuerySet of Performance objects
        """
        qs = Performance.objects.all().select_related(
            'student', 'course', 'semester', 'group'
        )

        # Apply basic filters
        f = self.filters

        # Filter by course
        course = f.get('course')
        if course:
            try:
                qs = qs.filter(course__id=int(course))
            except (ValueError, TypeError):
                qs = qs.filter(course__code__iexact=str(course))

        # Filter by semester
        semester = f.get('semester')
        if semester:
            try:
                qs = qs.filter(semester__id=int(semester))
            except (ValueError, TypeError):
                qs = qs.filter(semester__name__iexact=str(semester))

        # Filter by group
        group = f.get('group')
        if group:
            try:
                qs = qs.filter(group__id=int(group))
            except (ValueError, TypeError):
                qs = qs.filter(group__name__iexact=str(group))

        # Filter by status
        status = f.get('status')
        if status:
            qs = qs.filter(performance_status__iexact=str(status))

        # Search across student fields
        search = f.get('search')
        if search:
            qs = qs.filter(
                Q(student__student_id__icontains=search) |
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )

        return qs.order_by('-score')

    def calculate_kpis(self):
        """Calculate Key Performance Indicators"""
        qs = self.get_filtered_queryset()
        
        if not qs.exists():
            return {
                'total_students': 0,
                'average_score': 0,
                'pass_rate': 0,
                'excellent_count': 0,
                'good_count': 0,
                'average_count': 0,
                'poor_count': 0,
            }
        
        total = qs.count()
        avg_score = qs.aggregate(Avg('score'))['score__avg'] or 0
        
        # Count by performance levels
        excellent = qs.filter(score__gte=85).count()
        good = qs.filter(score__gte=70, score__lt=85).count()
        average = qs.filter(score__gte=50, score__lt=70).count()
        poor = qs.filter(score__lt=50).count()
        
        # Calculate pass rate
        passed = qs.filter(score__gte=50).count()
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            'total_students': total,
            'average_score': round(float(avg_score), 2),
            'pass_rate': round(pass_rate, 2),
            'excellent_count': excellent,
            'good_count': good,
            'average_count': average,
            'poor_count': poor,
        }

    def get_performance_distribution(self):
        """Get score distribution by ranges"""
        qs = self.get_filtered_queryset()
        
        return {
            '0-49': qs.filter(score__lt=50).count(),
            '50-69': qs.filter(score__gte=50, score__lt=70).count(),
            '70-84': qs.filter(score__gte=70, score__lt=85).count(),
            '85-100': qs.filter(score__gte=85).count(),
        }

    def get_top_performers(self, limit=10):
        """
        Get top performing students as dictionaries
        
        Returns:
            List of dictionaries with student data
        """
        qs = self.get_filtered_queryset().order_by('-score')[:limit]
        
        result = []
        for perf in qs:
            result.append({
                'student_name': perf.student.get_full_name(),
                'student_id': perf.student.student_id,
                'course': perf.course.code,
                'score': float(perf.score),
                'grade': perf.grade,
                'semester': perf.semester.name,
            })
        
        return result

    def get_bottom_performers(self, limit=10):
        """
        Get bottom performing students as dictionaries
        
        Returns:
            List of dictionaries with student data
        """
        qs = self.get_filtered_queryset().order_by('score')[:limit]
        
        result = []
        for perf in qs:
            result.append({
                'student_name': perf.student.get_full_name(),
                'student_id': perf.student.student_id,
                'course': perf.course.code,
                'score': float(perf.score),
                'grade': perf.grade,
                'semester': perf.semester.name,
            })
        
        return result

    def get_course_comparison(self):
        """Compare performance across courses"""
        qs = self.get_filtered_queryset()
        
        courses = qs.values('course__code', 'course__name').annotate(
            average_score=Avg('score'),
            total_students=Count('id'),
            passed=Count('id', filter=Q(score__gte=50))
        ).order_by('-average_score')
        
        result = []
        for course in courses:
            total = course['total_students']
            pass_rate = (course['passed'] / total * 100) if total > 0 else 0
            result.append({
                'course_code': course['course__code'],
                'course_name': course['course__name'],
                'average_score': round(float(course['average_score'] or 0), 2),
                'total_students': total,
                'pass_rate': round(pass_rate, 2),
            })
        
        return result

    def get_semester_trend(self):
        """Get performance trends across semesters"""
        qs = self.get_filtered_queryset()
        
        semesters = qs.values('semester__name', 'semester__start_date').annotate(
            average_score=Avg('score'),
            total_students=Count('id'),
            passed=Count('id', filter=Q(score__gte=50))
        ).order_by('semester__start_date')
        
        result = []
        for sem in semesters:
            total = sem['total_students']
            pass_rate = (sem['passed'] / total * 100) if total > 0 else 0
            result.append({
                'semester': sem['semester__name'],
                'average_score': round(float(sem['average_score'] or 0), 2),
                'total_students': total,
                'pass_rate': round(pass_rate, 2),
            })
        
        return result

    def get_recommendations(self, unresolved_only=False):
        """Get recommendations for students in current dataset"""
        qs = self.get_filtered_queryset()
        student_ids = qs.values_list('student_id', flat=True).distinct()
        
        recommendations = Recommendation.objects.filter(
            student_id__in=student_ids
        ).select_related('student')
        
        if unresolved_only:
            recommendations = recommendations.filter(is_resolved=False)
        
        return recommendations.order_by('-priority', '-created_at')

    def export_to_dataframe(self):
        """Export filtered data to pandas DataFrame"""
        qs = self.get_filtered_queryset()
        
        data = []
        for perf in qs:
            data.append({
                'Student ID': perf.student.student_id,
                'First Name': perf.student.first_name,
                'Last Name': perf.student.last_name,
                'Course Code': perf.course.code,
                'Course Name': perf.course.name,
                'Semester': perf.semester.name,
                'Group': perf.group.name if perf.group else 'N/A',
                'Score': float(perf.score),
                'Grade': perf.grade,
                'Status': perf.performance_status,
                'Ranking': perf.ranking,
            })
        
        return pd.DataFrame(data)