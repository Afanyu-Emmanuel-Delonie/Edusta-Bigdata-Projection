"""
Django Admin Configuration for Performance Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserRole, Course, Student, Semester, Group, 
    Performance, UploadHistory, Recommendation
)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__email', 'department']
    raw_id_fields = ['user']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'teacher', 'credits']
    list_filter = ['department', 'teacher']
    search_fields = ['code', 'name', 'department']
    raw_id_fields = ['teacher']
    ordering = ['code']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'department', 'is_active']
    list_filter = ['department', 'is_active', 'enrollment_date']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']
    ordering = ['student_id']
    date_hierarchy = 'enrollment_date'


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'semester_type', 'year', 'start_date', 'end_date', 'is_active']
    list_filter = ['semester_type', 'year', 'is_active']
    search_fields = ['name']
    ordering = ['-year', '-start_date']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'semester', 'max_students']
    list_filter = ['course', 'semester']
    search_fields = ['name', 'course__code']
    raw_id_fields = ['course', 'semester']


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'semester', 'score_display', 
        'grade', 'performance_status_badge', 'ranking'
    ]
    list_filter = [
        'semester', 'course', 'performance_status', 'grade'
    ]
    search_fields = [
        'student__student_id', 'student__first_name', 
        'student__last_name', 'course__code'
    ]
    raw_id_fields = ['student', 'course', 'semester', 'group']
    ordering = ['-semester', 'course', '-score']
    date_hierarchy = 'uploaded_at'
    
    def score_display(self, obj):
        """Display score with color coding"""
        score = float(obj.score)
        if score >= 85:
            color = 'green'
        elif score >= 70:
            color = 'blue'
        elif score >= 50:
            color = 'orange'
        else:
            color = 'red'
        # FIXED: Format the score BEFORE passing to format_html
        score_formatted = f'{score:.2f}'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, score_formatted
        )
    score_display.short_description = 'Score'

    def performance_status_badge(self, obj):
        """Display performance status as colored badge"""
        colors = {
            'Excellent': 'green',
            'Good': 'blue',
            'Average': 'orange',
            'Poor': 'red',
        }
        color = colors.get(obj.performance_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px;">{}</span>',
            color, str(obj.performance_status)
        )
    performance_status_badge.short_description = 'Status'


@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'file_name', 'uploaded_by', 'course', 'semester',
        'records_count', 'success_count', 'error_count', 'uploaded_at'
    ]
    list_filter = ['uploaded_at', 'course', 'semester']
    search_fields = ['file_name', 'uploaded_by__username']
    raw_id_fields = ['uploaded_by', 'course', 'semester']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    
    def has_add_permission(self, request):
        """Prevent manual addition of upload history"""
        return False


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'semester', 'priority_badge',
        'is_resolved', 'created_at'
    ]
    list_filter = [
        'priority', 'is_resolved', 'semester', 'course', 'created_at'
    ]
    search_fields = [
        'student__student_id', 'student__first_name',
        'student__last_name', 'course__code', 'recommendation_text'
    ]
    raw_id_fields = ['student', 'course', 'semester', 'resolved_by']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at', '-priority']
    date_hierarchy = 'created_at'
    
    def priority_badge(self, obj):
        """Display priority as colored badge"""
        colors = {
            'high': 'red',
            'medium': 'orange',
            'low': 'blue',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; text-transform: uppercase;">{}</span>',
            color, str(obj.priority)
        )
    priority_badge.short_description = 'Priority'
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """Bulk action to mark recommendations as resolved"""
        from django.utils import timezone
        updated = queryset.update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} recommendations marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected recommendations as resolved'