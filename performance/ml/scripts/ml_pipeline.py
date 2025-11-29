"""
ml_pipeline.py

This script:
- Loads the normalized AUCA dataset
- Splits into train/test sets
- Trains a simple ML model to predict Pass/Fail
- Evaluates model accuracy
- Saves predictions to CSV

"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Step 1: Load normalized dataset
df = pd.read_csv('../data/clean_data_normalized.csv')
print("Normalized dataset loaded. First 5 rows:")
print(df.head())

# Step 2: Define features and target
X = df[['assignment_score', 'midterm_score', 'final_score', 'attendance_percent', 'total_score']]
y = df['pass_fail_encoded']

# Step 3: Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTraining samples: {len(X_train)}, Test samples: {len(X_test)}")

# Step 4: Train Random Forest model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
print("\nModel trained successfully.")

# Step 5: Make predictions
y_pred = clf.predict(X_test)

# Step 6: Evaluate model
acc = accuracy_score(y_test, y_pred)
print(f"\nAccuracy on test set: {acc:.2f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))


# Step 7: Save predictions (optional)
pred_df = X_test.copy()
pred_df['true_label'] = y_test
pred_df['predicted_label'] = y_pred
pred_df.to_csv('../data/predictions.csv', index=False)
print("\nPredictions saved to ../data/predictions.csv")
