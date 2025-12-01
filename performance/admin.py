"""
Django Admin Configuration for Performance Management
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Student, Course, Semester, Group, 
    Performance, Recommendation, Dataset
)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'semester_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['year', 'semester_type', 'is_active']
    search_fields = ['name', 'year']
    ordering = ['-year', '-semester_type']
    
    actions = ['make_active']
    
    def make_active(self, request, queryset):
        Semester.objects.all().update(is_active=False)
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} semester(s) set as active.")
    make_active.short_description = "Set as active semester"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'department', 'email']
    list_filter = ['department']
    search_fields = ['student_id', 'first_name', 'last_name', 'email']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'department']
    list_filter = ['department']
    search_fields = ['code', 'name']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'semester']
    list_filter = ['course', 'semester']
    search_fields = ['name']


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'student_display', 'course_display', 'semester_display', 
        'dataset_display', 'score_display', 'grade', 
        'performance_status_badge', 'ml_prediction_badge',
        'risk_level_badge', 'ranking'
    ]
    list_filter = [
        'semester', 'course', 'dataset', 'performance_status', 
        'grade', 'status', 'risk_level', 'ml_predicted_pass',
        'needs_intervention'
    ]
    search_fields = [
        'student__student_id', 'student__first_name', 
        'student__last_name', 'course__code', 'course__name'
    ]
    raw_id_fields = ['student', 'course', 'semester', 'group', 'dataset', 'uploaded_by']
    ordering = ['-semester', 'course', '-score']
    date_hierarchy = 'uploaded_at'
    
    readonly_fields = [
        'uploaded_at', 'updated_at', 'ml_predicted_at',
        'grade', 'status', 'performance_status', 'other_total'
    ]
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'course', 'semester', 'group', 'dataset')
        }),
        ('Score Components', {
            'fields': (
                'quiz1', 'quiz2', 'assignment', 'attendance',
                'mid_semester', 'final_exam', 'other_total'
            )
        }),
        ('Calculated Results', {
            'fields': ('score', 'grade', 'status', 'performance_status', 'ranking')
        }),
        ('ML Predictions', {
            'fields': (
                'ml_predicted_pass', 'ml_confidence', 'ml_prediction_label',
                'predicted_final_score', 'prob_pass', 'prob_fail'
            ),
            'classes': ('collapse',)
        }),
        ('Risk Assessment', {
            'fields': (
                'risk_level', 'risk_score', 'performance_trend',
                'needs_intervention', 'intervention_priority'
            ),
            'classes': ('collapse',)
        }),
        ('ML Metadata', {
            'fields': (
                'ml_model_version', 'ml_predicted_at', 'ml_features_json'
            ),
            'classes': ('collapse',)
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_display(self, obj):
        """Display student ID and name"""
        return f"{obj.student.student_id}"
    student_display.short_description = 'Student'
    student_display.admin_order_field = 'student__student_id'
    
    def course_display(self, obj):
        """Display course code"""
        return obj.course.code
    course_display.short_description = 'Course'
    course_display.admin_order_field = 'course__code'
    
    def semester_display(self, obj):
        """Display semester name"""
        return obj.semester.name
    semester_display.short_description = 'Semester'
    semester_display.admin_order_field = 'semester__name'
    
    def dataset_display(self, obj):
        """Display dataset name"""
        if obj.dataset:
            return obj.dataset.name
        return '-'
    dataset_display.short_description = 'Dataset'
    
    def score_display(self, obj):
        """Display score with color coding"""
        score = float(obj.score) if obj.score else 0
        if score >= 85:
            color = '#10B981'
        elif score >= 70:
            color = '#3B82F6'
        elif score >= 50:
            color = '#F59E0B'
        else:
            color = '#DC2626'
        score_formatted = f'{score:.2f}'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, score_formatted
        )
    score_display.short_description = 'Score'
    score_display.admin_order_field = 'score'

    def performance_status_badge(self, obj):
        """Display performance status as colored badge"""
        colors = {
            'Excellent': '#10B981',
            'Good': '#3B82F6',
            'Average': '#F59E0B',
            'Poor': '#DC2626',
        }
        color = colors.get(obj.performance_status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, str(obj.performance_status) if obj.performance_status else 'N/A'
        )
    performance_status_badge.short_description = 'Performance'
    performance_status_badge.admin_order_field = 'performance_status'
    
    def ml_prediction_badge(self, obj):
        """Display ML prediction as badge"""
        if obj.ml_predicted_pass is None:
            return format_html(
                '<span style="background-color: #6B7280; color: white; padding: 3px 10px; border-radius: 10px; font-size: 11px;">No Prediction</span>'
            )
        
        if obj.ml_predicted_pass:
            color = '#10B981'
            text = 'PASS'
        else:
            color = '#DC2626'
            text = 'FAIL'
        
        confidence = f"{obj.ml_confidence:.1f}%" if obj.ml_confidence else "N/A"
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 11px;">{} ({})</span>',
            color, text, confidence
        )
    ml_prediction_badge.short_description = 'ML Prediction'
    ml_prediction_badge.admin_order_field = 'ml_predicted_pass'
    
    def risk_level_badge(self, obj):
        """Display risk level as colored badge"""
        colors = {
            'CRITICAL': '#DC2626',
            'HIGH': '#F59E0B',
            'MEDIUM': '#FCD34D',
            'LOW': '#10B981',
            'NONE': '#3B82F6',
            'UNKNOWN': '#6B7280',
        }
        color = colors.get(obj.risk_level, '#6B7280')
        text_color = 'white' if obj.risk_level != 'MEDIUM' else '#1F2937'
        display_text = obj.get_risk_level_display() if hasattr(obj, 'get_risk_level_display') else obj.risk_level
        
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 10px; font-size: 11px; font-weight: bold;">{}</span>',
            color, text_color, display_text
        )
    risk_level_badge.short_description = 'Risk Level'
    risk_level_badge.admin_order_field = 'risk_level'
    
    actions = ['recalculate_scores', 'mark_for_intervention', 'clear_ml_predictions']
    
    def recalculate_scores(self, request, queryset):
        """Recalculate grades and statuses for selected records"""
        updated = 0
        for performance in queryset:
            performance.grade = performance.calculate_grade()
            performance.status = performance.calculate_status()
            performance.performance_status = performance.calculate_performance_status()
            performance.save()
            updated += 1
        
        self.message_user(request, f'{updated} performance records recalculated successfully.')
    recalculate_scores.short_description = 'Recalculate grades and status'
    
    def mark_for_intervention(self, request, queryset):
        """Mark selected students for intervention"""
        updated = queryset.update(needs_intervention=True)
        self.message_user(request, f'{updated} students marked for intervention.')
    mark_for_intervention.short_description = 'Mark for intervention'
    
    def clear_ml_predictions(self, request, queryset):
        """Clear ML predictions for selected records"""
        updated = queryset.update(
            ml_predicted_pass=None,
            ml_confidence=None,
            ml_prediction_label='',
            predicted_final_score=None,
            prob_pass=None,
            prob_fail=None,
            ml_predicted_at=None
        )
        self.message_user(request, f'{updated} ML predictions cleared.')
    clear_ml_predictions.short_description = 'Clear ML predictions'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('student', 'course', 'semester', 'dataset', 'uploaded_by', 'group')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'priority', 
        'is_resolved', 'created_at'
    ]
    list_filter = ['priority', 'is_resolved', 'created_at']
    search_fields = ['student__student_id', 'recommendation_text']


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']