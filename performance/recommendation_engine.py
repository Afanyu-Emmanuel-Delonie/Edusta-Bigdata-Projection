"""
Intelligent Recommendation Engine
Generates personalized recommendations based on ML predictions and performance
"""

from typing import List, Dict, Any
from decimal import Decimal
from django.utils import timezone
from .models import Performance, Recommendation, Student, Course, Semester


class RecommendationEngine:
    """
    Generates intelligent, actionable recommendations for students
    Based on ML predictions, risk levels, and performance patterns
    """
    
    RECOMMENDATION_TEMPLATES = {
        # Critical interventions
        'CRITICAL_FAIL_PREDICTION': {
            'priority': 'high',
            'template': "🚨 CRITICAL: ML model predicts high risk of failure ({confidence}% confidence). "
                       "Immediate intervention required. Current score: {score}. "
                       "Recommended actions: Schedule urgent counseling, assign peer tutor, create recovery plan.",
        },
        
        # High priority
        'HIGH_RISK_LOW_ATTENDANCE': {
            'priority': 'high',
            'template': "⚠️ HIGH RISK: Low attendance ({attendance}%) combined with failing scores ({score}). "
                       "Recommended: Contact student immediately, investigate absence reasons, provide makeup opportunities.",
        },
        
        'PROBATION_WARNING': {
            'priority': 'high',
            'template': "⚠️ PROBATION ALERT: Current score ({score}) in probation range (40-49). "
                       "Student at risk of academic probation. "
                       "Recommended: Weekly check-ins, supplemental materials, study skills workshop.",
        },
        
        # Medium priority
        'DECLINING_TREND': {
            'priority': 'medium',
            'template': "📉 DECLINING TREND: Performance showing downward trajectory. "
                       "ML confidence: {confidence}%. "
                       "Recommended: Identify struggling topics, provide targeted support, monitor weekly.",
        },
        
        'LOW_MIDTERM_CONCERN': {
            'priority': 'medium',
            'template': "📊 MIDTERM CONCERN: Mid-semester score ({mid_score}) indicates risk. "
                       "Predicted final score: {predicted_final}. "
                       "Recommended: Intensive review sessions, practice exams, office hours.",
        },
        
        'BORDERLINE_PASS': {
            'priority': 'medium',
            'template': "⚖️ BORDERLINE: Score ({score}) near pass/fail threshold. "
                       "ML prediction: {ml_label} ({confidence}% confidence). "
                       "Recommended: Focus on final exam preparation, review weak areas.",
        },
        
        # Low priority - encouragement
        'GOOD_PROGRESS': {
            'priority': 'low',
            'template': "✅ GOOD PROGRESS: Student performing well (score: {score}). "
                       "ML predicts {ml_label} with {confidence}% confidence. "
                       "Recommended: Maintain current study habits, consider peer tutoring role.",
        },
        
        'IMPROVING_TREND': {
            'priority': 'low',
            'template': "📈 IMPROVING: Performance trending upward. "
                       "Current score: {score}. Keep up the excellent work! "
                       "Recommended: Continue current strategies, set higher goals.",
        },
        
        # Specific interventions
        'ATTENDANCE_IMPROVEMENT_NEEDED': {
            'priority': 'medium',
            'template': "📅 ATTENDANCE: Attendance rate ({attendance}%) below acceptable threshold. "
                       "Recommended: Attendance contract, flexible scheduling if needed.",
        },
        
        'ASSIGNMENT_CATCH_UP': {
            'priority': 'medium',
            'template': "📝 ASSIGNMENTS: Assignment score ({assignment}) significantly lower than exams. "
                       "Recommended: Assignment extensions, time management workshop.",
        },
        
        'EXAM_PREP_NEEDED': {
            'priority': 'medium',
            'template': "📖 EXAM PREPARATION: Exam scores ({mid_score} mid, {final_score} final) need improvement. "
                       "Recommended: Test-taking strategies workshop, practice exams, study groups.",
        },
    }
    
    def __init__(self):
        """Initialize recommendation engine"""
        pass
    
    def generate_recommendations_for_performance(self, performance: Performance) -> List[Dict[str, Any]]:
        """
        Generate all applicable recommendations for a performance record
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        score = float(performance.score or 0)
        attendance = float(performance.attendance or 0)
        mid_score = float(performance.mid_semester or 0)
        final_score = float(performance.final_exam or 0)
        assignment = float(performance.assignment or 0)
        
        ml_predicted = performance.ml_predicted_pass
        ml_conf = float(performance.ml_confidence or 50)
        ml_label = performance.ml_prediction_label or 'Unknown'
        risk_level = performance.risk_level
        trend = performance.performance_trend
        predicted_final = float(performance.predicted_final_score or 0)
        
        # Rule 1: Critical failure prediction
        if ml_predicted is False and ml_conf > 70 and score < 50:
            recommendations.append({
                'type': 'CRITICAL_FAIL_PREDICTION',
                'priority': 'high',
                'message': self._format_message('CRITICAL_FAIL_PREDICTION', {
                    'confidence': ml_conf,
                    'score': score,
                })
            })
        
        # Rule 2: High risk + low attendance
        if risk_level in ['CRITICAL', 'HIGH'] and attendance < 70:
            recommendations.append({
                'type': 'HIGH_RISK_LOW_ATTENDANCE',
                'priority': 'high',
                'message': self._format_message('HIGH_RISK_LOW_ATTENDANCE', {
                    'attendance': attendance,
                    'score': score,
                })
            })
        
        # Rule 3: Probation warning
        if 40 <= score < 50:
            recommendations.append({
                'type': 'PROBATION_WARNING',
                'priority': 'high',
                'message': self._format_message('PROBATION_WARNING', {
                    'score': score,
                })
            })
        
        # Rule 4: Declining trend
        if trend == 'DECLINING':
            recommendations.append({
                'type': 'DECLINING_TREND',
                'priority': 'medium',
                'message': self._format_message('DECLINING_TREND', {
                    'confidence': ml_conf,
                })
            })
        
        # Rule 5: Low midterm concern
        if mid_score > 0 and mid_score < 50 and predicted_final > 0:
            recommendations.append({
                'type': 'LOW_MIDTERM_CONCERN',
                'priority': 'medium',
                'message': self._format_message('LOW_MIDTERM_CONCERN', {
                    'mid_score': mid_score,
                    'predicted_final': predicted_final,
                })
            })
        
        # Rule 6: Borderline pass
        if 48 <= score <= 52:
            recommendations.append({
                'type': 'BORDERLINE_PASS',
                'priority': 'medium',
                'message': self._format_message('BORDERLINE_PASS', {
                    'score': score,
                    'ml_label': ml_label,
                    'confidence': ml_conf,
                })
            })
        
        # Rule 7: Good progress (encouragement)
        if score >= 70 and ml_predicted is True:
            recommendations.append({
                'type': 'GOOD_PROGRESS',
                'priority': 'low',
                'message': self._format_message('GOOD_PROGRESS', {
                    'score': score,
                    'ml_label': ml_label,
                    'confidence': ml_conf,
                })
            })
        
        # Rule 8: Improving trend
        if trend == 'IMPROVING':
            recommendations.append({
                'type': 'IMPROVING_TREND',
                'priority': 'low',
                'message': self._format_message('IMPROVING_TREND', {
                    'score': score,
                })
            })
        
        # Rule 9: Attendance improvement
        if attendance < 75 and score < 60:
            recommendations.append({
                'type': 'ATTENDANCE_IMPROVEMENT_NEEDED',
                'priority': 'medium',
                'message': self._format_message('ATTENDANCE_IMPROVEMENT_NEEDED', {
                    'attendance': attendance,
                })
            })
        
        # Rule 10: Assignment catch-up
        if assignment > 0 and assignment < 50 and (mid_score > 60 or final_score > 60):
            recommendations.append({
                'type': 'ASSIGNMENT_CATCH_UP',
                'priority': 'medium',
                'message': self._format_message('ASSIGNMENT_CATCH_UP', {
                    'assignment': assignment,
                })
            })
        
        # Rule 11: Exam prep needed
        if (mid_score > 0 and mid_score < 50) or (final_score > 0 and final_score < 50):
            recommendations.append({
                'type': 'EXAM_PREP_NEEDED',
                'priority': 'medium',
                'message': self._format_message('EXAM_PREP_NEEDED', {
                    'mid_score': mid_score,
                    'final_score': final_score,
                })
            })
        
        return recommendations
    
    def _format_message(self, template_key: str, context: Dict[str, Any]) -> str:
        """Format recommendation message with context"""
        template = self.RECOMMENDATION_TEMPLATES[template_key]['template']
        
        # Format numbers nicely
        formatted_context = {}
        for key, value in context.items():
            if isinstance(value, (int, float, Decimal)):
                formatted_context[key] = f"{float(value):.1f}"
            else:
                formatted_context[key] = str(value)
        
        return template.format(**formatted_context)
    
    def create_recommendation_records(self, performance: Performance, auto_save=True) -> List[Recommendation]:
        """
        Create Recommendation model instances for a performance record
        
        Args:
            performance: Performance record
            auto_save: Whether to save to database
        
        Returns:
            List of Recommendation objects
        """
        recommendations_data = self.generate_recommendations_for_performance(performance)
        recommendation_objects = []
        
        for rec_data in recommendations_data:
            rec = Recommendation(
                student=performance.student,
                course=performance.course,
                semester=performance.semester,
                recommendation_text=rec_data['message'],
                priority=rec_data['priority'],
                is_resolved=False,
            )
            
            if auto_save:
                rec.save()
            
            recommendation_objects.append(rec)
        
        return recommendation_objects
    
    def batch_generate_recommendations(self, performance_queryset, auto_save=True):
        """
        Generate recommendations for multiple performance records
        
        Args:
            performance_queryset: QuerySet of Performance objects
            auto_save: Whether to save to database
        
        Returns:
            Dictionary with statistics
        """
        total_created = 0
        high_priority_count = 0
        
        for performance in performance_queryset:
            recs = self.create_recommendation_records(performance, auto_save=auto_save)
            total_created += len(recs)
            high_priority_count += sum(1 for r in recs if r.priority == 'high')
        
        return {
            'total_recommendations': total_created,
            'high_priority': high_priority_count,
            'students_processed': performance_queryset.count(),
        }
    
    def get_student_summary(self, student: Student, semester: Semester) -> Dict[str, Any]:
        """
        Get comprehensive summary for a student including all recommendations
        """
        performances = Performance.objects.filter(
            student=student,
            semester=semester
        ).select_related('course')
        
        if not performances.exists():
            return None
        
        # Aggregate statistics
        total_courses = performances.count()
        avg_score = sum(float(p.score or 0) for p in performances) / total_courses
        at_risk_courses = sum(1 for p in performances if p.risk_level in ['CRITICAL', 'HIGH'])
        predicted_failures = sum(1 for p in performances if not p.ml_predicted_pass)
        
        # Get all recommendations
        all_recommendations = []
        for perf in performances:
            recs = self.generate_recommendations_for_performance(perf)
            for rec in recs:
                rec['course'] = perf.course.code
                all_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))
        
        return {
            'student': student,
            'semester': semester,
            'total_courses': total_courses,
            'average_score': round(avg_score, 2),
            'at_risk_courses': at_risk_courses,
            'predicted_failures': predicted_failures,
            'recommendations': all_recommendations,
            'high_priority_count': sum(1 for r in all_recommendations if r['priority'] == 'high'),
        }


# Singleton instance
_recommendation_engine = None

def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine singleton"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine