"""
data_processing.py

This script loads the cleaned AUCA dataset, normalizes numeric features,
encodes the pass/fail label, and saves a normalized CSV for ML models.

"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Step 1: Load the cleaned dataset

df = pd.read_csv('../data/clean_data.csv')  # relative path from scripts folder
print("Dataset loaded. First 5 rows:")
print(df.head())

# Step 2: Normalize numeric features
numeric_cols = ['assignment_score', 'midterm_score', 'final_score', 'attendance_percent', 'total_score']
scaler = MinMaxScaler()
df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
print("\nNumeric features normalized.")

# Step 3: Encode pass/fail
df['pass_fail_encoded'] = df['pass_fail'].map({'Fail': 0, 'Pass': 1})
print("Pass/fail column encoded.")

# Step 4: Save normalized dataset
df.to_csv('../data/clean_data_normalized.csv', index=False)
print("\nNormalized dataset saved to ../data/clean_data_normalized.csv")
