"""
ml_visualize.py

Visualizes the ML predictions for the AUCA dataset:
- Confusion matrix
- Feature importance
- Pass/Fail distribution
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# Step 1: Load normalized dataset and predictions
df = pd.read_csv('../data/clean_data_normalized.csv')
pred_df = pd.read_csv('../data/predictions.csv')

# Features and target
feature_cols = ['assignment_score', 'midterm_score', 'final_score', 'attendance_percent', 'total_score']
X = df[feature_cols]
y = df['pass_fail_encoded']

# Step 2: Train Random Forest again for feature importance
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)
importances = clf.feature_importances_

# Feature importance plot
plt.figure(figsize=(8,5))
sns.barplot(x=feature_cols, y=importances)
plt.title("Feature Importance (Random Forest)")
plt.ylabel("Importance")
plt.xlabel("Features")
plt.tight_layout()
plt.savefig('../data/feature_importance.png')
plt.show()

# Step 3: Confusion matrix for predictions
cm = confusion_matrix(pred_df['true_label'], pred_df['predicted_label'])
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fail', 'Pass'])
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig('../data/confusion_matrix.png')
plt.show()

# Step 4: Pass/Fail distribution in dataset
plt.figure(figsize=(6,4))
sns.countplot(x='pass_fail', data=df)
plt.title("Pass/Fail Distribution")
plt.ylabel("Count")
plt.xlabel("Outcome")
plt.tight_layout()
plt.savefig('../data/pass_fail_distribution.png')
plt.show()
