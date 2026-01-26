import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_and_save_models(csv_path):
    # Load Data
    df = pd.read_csv(csv_path)

    # 1. Feature Engineering
    # Normalize CA to 0-100 scale
    df['ca_perc'] = (df['ca_score'] / 40) * 100
    
    # Encode categorical text data into numbers
    le_course = LabelEncoder()
    le_teacher = LabelEncoder()
    df['course_enc'] = le_course.fit_transform(df['course_code'])
    df['teacher_enc'] = le_teacher.fit_transform(df['teacher_id'])

    # 2. Select Features (The 'Clues')
    features = ['ca_perc', 'attendance_rate', 'course_enc', 'teacher_enc']
    X = df[features]
    y_reg = df['final_score']
    
    # Target: 0=Fail (<50), 1=Probation (50-60), 2=Pass (>60)
    y_clf = y_reg.apply(lambda x: 0 if x < 50 else (1 if x < 60 else 2))

    # 3. Split data for testing
    X_train, X_test, y_train, y_test = train_test_split(X, y_clf, test_size=0.15, random_state=42)

    # 4. Train High-Performance Classifier
    # Gradient Boosting builds trees sequentially to minimize error
    classifier = GradientBoostingClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=4,
        random_state=42
    )
    classifier.fit(X_train, y_train)

    # 5. Train Regressor (for predicting the exact score)
    predictor = GradientBoostingRegressor(n_estimators=500, random_state=42)
    predictor.fit(X, y_reg)

    # 6. Performance Report
    acc = accuracy_score(y_test, classifier.predict(X_test))
    print(f"\n" + "="*30)
    print(f" FINAL MODEL ACCURACY: {round(acc * 100, 2)}%")
    print("="*30)
    
    # Show which features matter most
    importances = dict(zip(features, classifier.feature_importances_))
    print("Feature Importance:")
    for feat, imp in importances.items():
        print(f" - {feat}: {round(imp*100, 2)}%")

    # 7. Save Models and Encoders
    model_dir = os.path.join('performance', 'ml_models', 'saved_models')
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(classifier, os.path.join(model_dir, 'classifier.pkl'))
    joblib.dump(predictor, os.path.join(model_dir, 'predictor.pkl'))
    joblib.dump(features, os.path.join(model_dir, 'feature_names.pkl'))
    joblib.dump(le_course, os.path.join(model_dir, 'le_course.pkl'))
    joblib.dump(le_teacher, os.path.join(model_dir, 'le_teacher.pkl'))
    print("\nAll components saved successfully! ✅")

if __name__ == "__main__":
    train_and_save_models('historical_data.csv')