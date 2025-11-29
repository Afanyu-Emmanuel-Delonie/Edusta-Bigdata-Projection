# Feature Documentation

## Dataset Overview
This feature set is designed for predicting student pass/fail outcomes based on academic performance and attendance data.

## Feature Descriptions

### Basic Features
- **assignment_score**: Normalized assignment score (0-1)
- **midterm_score**: Normalized midterm exam score (0-1)  
- **final_score**: Normalized final exam score (0-1)
- **attendance_percent**: Normalized attendance percentage (0-1)

### Performance Trend Features
- **early_performance**: Average of assignment and midterm scores
- **improvement_score**: Difference between final and midterm scores (positive = improvement)
- **consistency_score**: 1 minus standard deviation of all scores (higher = more consistent performance)

### Composite Metrics
- **exam_avg**: Average of midterm and final exam scores
- **overall_avg**: Average of all three assessment scores
- **weighted_total**: Weighted sum using AUCA rules (30% assignment, 30% midterm, 40% final)

### Risk Indicators
- **attendance_risk**: Binary flag (1 = attendance < 25%, 0 otherwise)
- **weak_subject_count**: Count of subjects with scores below 50% (0-3)
- **performance_gap**: Difference between highest and lowest subject scores
- **low_assignment**: Binary flag for assignment score < 50%
- **low_midterm**: Binary flag for midterm score < 50%  
- **low_final**: Binary flag for final score < 50%

### Target Variable
- **pass_fail**: Binary classification target (1 = Pass, 0 = Fail)

## Intended Use
This feature set is suitable for:
- Binary classification models predicting student success
- Identifying at-risk students early
- Understanding patterns in student performance
- Educational data mining and learning analytics

## Data Source
Original data was normalized to 0-1 range. All features maintain this normalization for consistency.

## Notes
- Missing values: None in the original dataset
- All scores are normalized (0-1 scale)
- Attendance risk follows AUCA policy (<25% attendance = automatic fail)