"""
ML Prediction Service - Comprehensive Student Performance Prediction
FIXED VERSION with proper feature engineering
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.utils import timezone


class MLPredictionService:
    """
    Comprehensive ML prediction service with innovative features
    """
    
    MODEL_FILENAME = "random_forest_passfail.pkl"
    MODEL_VERSION = "v1.0_RF200"
    
    def __init__(self):
        """Initialize ML service and load model"""
        self.model = self._load_model()
        self.model_loaded = self.model is not None
    
    def _load_model(self):
        """Load trained Random Forest model"""
        try:
            possible_paths = [
                Path(__file__).resolve().parent.parent / "ml" / "models" / self.MODEL_FILENAME,
                Path(__file__).resolve().parent / "models" / self.MODEL_FILENAME,
                Path("performance/ml/models") / self.MODEL_FILENAME,
            ]
            
            for model_path in possible_paths:
                if model_path.exists():
                    print(f"✅ Loading ML model from: {model_path}")
                    return joblib.load(model_path)
            
            print(f"⚠️ WARNING: ML model not found. Predictions will use fallback rules.")
            return None
            
        except Exception as e:
            print(f"❌ ERROR loading ML model: {str(e)}")
            return None
    
    def prepare_features(self, performance_record) -> Dict[str, float]:
        """
        UPDATED: Prepare features that match the trained model
        Creates ALL features the model expects from available data
        """
        # Get raw scores (0-100)
        quiz1 = float(performance_record.quiz1 or 0)
        quiz2 = float(performance_record.quiz2 or 0)
        assignment = float(performance_record.assignment or 0)
        attendance = float(performance_record.attendance or 0)
        mid_semester = float(performance_record.mid_semester or 0)
        final_exam = float(performance_record.final_exam or 0)
        
        # Calculate averages for assignment_score
        assignment_score = (quiz1 + quiz2 + assignment) / 3 if (quiz1 or quiz2 or assignment) else 0
        
        # Normalize to 0-1 scale
        assignment_norm = assignment_score / 100.0
        midterm_norm = mid_semester / 100.0
        final_norm = final_exam / 100.0
        attendance_norm = attendance / 100.0
        
        # Calculate derived features the model expects
        features = {
            # Basic scores (normalized)
            'assignment_score': assignment_norm,
            'midterm_score': midterm_norm,
            'final_score': final_norm,
            'attendance_percent': attendance_norm,
            
            # Derived features
            'exam_avg': (midterm_norm + final_norm) / 2,
            'early_performance': (assignment_norm + midterm_norm) / 2,
            'consistency_score': 1.0 - abs(midterm_norm - final_norm),
            'improvement_score': max(0, final_norm - midterm_norm),
            'attendance_risk': 1.0 - attendance_norm,
            
            # Risk indicators
            'low_attendance': 1 if attendance_norm < 0.7 else 0,
            'failing_midterm': 1 if midterm_norm < 0.5 else 0,
            'failing_final': 1 if final_norm < 0.5 else 0,
            'weak_early_performance': 1 if (assignment_norm + midterm_norm) / 2 < 0.5 else 0,
            
            # Interaction features
            'attendance_exam_interaction': attendance_norm * ((midterm_norm + final_norm) / 2),
            'assignment_exam_gap': abs(assignment_norm - ((midterm_norm + final_norm) / 2)),
        }
        
        return features
    
    def predict_pass_fail(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        UPDATED: Predict pass/fail using ML model with proper feature handling
        """
        if not self.model_loaded:
            return self._fallback_prediction(features)
        
        try:
            # Prepare input DataFrame
            input_df = pd.DataFrame([features])
            
            # Handle feature alignment with model
            if hasattr(self.model, 'feature_names_in_'):
                expected_features = list(self.model.feature_names_in_)
                
                # Add any missing features with 0
                for feat in expected_features:
                    if feat not in input_df.columns:
                        input_df[feat] = 0
                        print(f"⚠️ Added missing feature '{feat}' with default value 0")
                
                # Reorder to match model's expected order
                input_df = input_df[expected_features]
            
            # Get prediction and probabilities
            prediction = self.model.predict(input_df)[0]
            probabilities = self.model.predict_proba(input_df)[0]
            
            # Extract probabilities for each class
            classes = list(getattr(self.model, 'classes_', [0, 1]))
            fail_idx = classes.index(0) if 0 in classes else 0
            pass_idx = classes.index(1) if 1 in classes else 1
            
            prob_fail = float(probabilities[fail_idx]) * 100
            prob_pass = float(probabilities[pass_idx]) * 100
            
            print(f"✅ ML Model prediction successful: {self.MODEL_VERSION}")
            
            return {
                'prediction': int(prediction),
                'label': 'Pass' if prediction == 1 else 'Fail',
                'predicted_pass': bool(prediction == 1),
                'confidence': prob_pass if prediction == 1 else prob_fail,
                'prob_pass': prob_pass,
                'prob_fail': prob_fail,
                'model_version': self.MODEL_VERSION,
                'prediction_method': 'ML_Model',
            }
            
        except Exception as e:
            print(f"❌ ML prediction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._fallback_prediction(features)
    
    def _fallback_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Rule-based prediction when ML model unavailable
        Uses multiple features for better accuracy
        """
        # Get normalized scores
        assignment = features.get('assignment_score', 0)
        midterm = features.get('midterm_score', 0)
        final = features.get('final_score', 0)
        attendance = features.get('attendance_percent', 0)
        
        # Calculate weighted total (0-1 scale)
        # 30% midterm + 40% final + 20% assignment + 10% attendance
        total_score = (midterm * 0.30) + (final * 0.40) + (assignment * 0.20) + (attendance * 0.10)
        total_score_percent = total_score * 100  # Convert to 0-100
        
        # Predict pass if >= 50%
        predicted_pass = total_score_percent >= 50
        
        # Calculate confidence based on distance from threshold
        distance_from_threshold = abs(total_score_percent - 50)
        confidence = min(50 + distance_from_threshold, 100)
        
        prob_pass = total_score_percent if predicted_pass else 100 - total_score_percent
        prob_fail = 100 - prob_pass
        
        print(f"⚠️ Using fallback rules (score: {total_score_percent:.1f}%)")
        
        return {
            'prediction': 1 if predicted_pass else 0,
            'label': 'Pass' if predicted_pass else 'Fail',
            'predicted_pass': predicted_pass,
            'confidence': confidence,
            'prob_pass': prob_pass,
            'prob_fail': prob_fail,
            'model_version': 'Fallback_Rules',
            'prediction_method': 'Rule_Based',
        }
    
    def calculate_risk_score(self, performance_record, ml_prediction: Dict) -> float:
        """Calculate composite risk score (0-100)"""
        score = float(performance_record.score or 0)
        attendance = float(performance_record.attendance or 0)
        ml_conf = ml_prediction['confidence']
        predicted_pass = ml_prediction['predicted_pass']
        
        risk = 0
        
        # Factor 1: Low score increases risk
        if score < 40:
            risk += 40
        elif score < 50:
            risk += 25
        elif score < 60:
            risk += 15
        
        # Factor 2: ML predicts failure
        if not predicted_pass:
            risk += 30
        
        # Factor 3: Low ML confidence
        if ml_conf < 60:
            risk += 15
        
        # Factor 4: Low attendance
        if attendance < 50:
            risk += 15
        elif attendance < 70:
            risk += 10
        
        return min(risk, 100)
    
    def determine_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into risk level"""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'NONE'
    
    def calculate_intervention_priority(self, risk_score: float, performance_record) -> int:
        """Calculate intervention priority (1-10, where 1 is highest)"""
        if risk_score >= 80:
            priority = 1
        elif risk_score >= 60:
            priority = 3
        elif risk_score >= 40:
            priority = 5
        elif risk_score >= 20:
            priority = 7
        else:
            priority = 10
        
        score = float(performance_record.score or 0)
        if score < 30:
            priority = max(1, priority - 2)
        elif score < 40:
            priority = max(1, priority - 1)
        
        return max(1, min(priority, 10))
    
    def predict_final_score(self, performance_record) -> Optional[float]:
        """Predict final score if only mid-semester data is available"""
        mid_score = float(performance_record.mid_semester or 0)
        final_score = float(performance_record.final_exam or 0)
        attendance = float(performance_record.attendance or 0)
        
        # If we have final score, use weighted calculation
        if final_score > 0:
            other_total = float(performance_record.quiz1 or 0) + float(performance_record.quiz2 or 0) + \
                         float(performance_record.assignment or 0) + attendance
            other_normalized = (other_total / 400) * 100
            predicted = (mid_score * 0.30) + (final_score * 0.40) + (other_normalized * 0.30)
            return max(0, min(predicted, 100))
        
        # If only mid-semester, extrapolate
        if mid_score == 0:
            return None
        
        attendance_factor = (attendance - 70) / 100
        predicted = mid_score + (mid_score * attendance_factor * 0.2)
        return max(0, min(predicted, 100))
    
    def analyze_performance_trend(self, student, semester) -> str:
        """Analyze student's performance trend"""
        try:
            from .models import Performance
            
            performances = Performance.objects.filter(
                student=student,
                semester=semester
            ).order_by('uploaded_at')
            
            if performances.count() < 2:
                return 'UNKNOWN'
            
            scores = [float(p.score) for p in performances if p.score]
            
            if len(scores) >= 3:
                recent_avg = sum(scores[-2:]) / 2
                older_avg = sum(scores[:-2]) / len(scores[:-2])
                diff = recent_avg - older_avg
                
                if diff > 5:
                    return 'IMPROVING'
                elif diff < -5:
                    return 'DECLINING'
            
            return 'STABLE'
            
        except Exception:
            return 'UNKNOWN'
    
    def run_complete_prediction(self, performance_record) -> Dict[str, Any]:
        """Run complete ML prediction pipeline"""
        # 1. Prepare features
        features = self.prepare_features(performance_record)
        
        # 2. Run ML prediction
        ml_prediction = self.predict_pass_fail(features)
        
        # 3. Calculate risk score
        risk_score = self.calculate_risk_score(performance_record, ml_prediction)
        risk_level = self.determine_risk_level(risk_score)
        
        # 4. Determine intervention needs
        needs_intervention = risk_level in ['CRITICAL', 'HIGH']
        intervention_priority = self.calculate_intervention_priority(
            risk_score, performance_record
        ) if needs_intervention else None
        
        # 5. Predict final score
        predicted_final = self.predict_final_score(performance_record)
        
        # 6. Analyze trend
        trend = self.analyze_performance_trend(
            performance_record.student,
            performance_record.semester
        )
        
        return {
            'ml_predicted_pass': ml_prediction['predicted_pass'],
            'ml_confidence': Decimal(str(round(ml_prediction['confidence'], 2))),
            'ml_prediction_label': ml_prediction['label'],
            'prob_pass': Decimal(str(round(ml_prediction['prob_pass'], 2))),
            'prob_fail': Decimal(str(round(ml_prediction['prob_fail'], 2))),
            'risk_score': Decimal(str(round(risk_score, 2))),
            'risk_level': risk_level,
            'needs_intervention': needs_intervention,
            'intervention_priority': intervention_priority,
            'predicted_final_score': Decimal(str(round(predicted_final, 2))) if predicted_final else None,
            'performance_trend': trend,
            'ml_model_version': ml_prediction['model_version'],
            'ml_predicted_at': timezone.now(),
            'ml_features_json': features,
        }
    
    def update_performance_with_prediction(self, performance_record, save=True):
        """Update Performance record with ML prediction results"""
        prediction_results = self.run_complete_prediction(performance_record)
        
        # Update fields
        for field, value in prediction_results.items():
            if hasattr(performance_record, field):
                setattr(performance_record, field, value)
        
        if save:
            performance_record.save()
        
        return prediction_results
    
    def batch_predict(self, performance_records) -> List[Dict[str, Any]]:
        """Run predictions on multiple performance records"""
        results = []
        
        for record in performance_records:
            try:
                prediction = self.run_complete_prediction(record)
                prediction['record_id'] = record.id
                prediction['student_id'] = record.student.student_id
                results.append(prediction)
            except Exception as e:
                print(f"❌ Batch prediction error for {record.student.student_id}: {str(e)}")
                results.append({
                    'record_id': record.id,
                    'student_id': record.student.student_id,
                    'error': str(e)
                })
        
        return results


# Singleton instance
_ml_service = None

def get_ml_service() -> MLPredictionService:
    """Get or create ML prediction service singleton"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLPredictionService()
    return _ml_service