# train_now.py
from performance.ml_models.trainer import train_and_save_models
import os

# =========================================================
# PATH TO YOUR DATASET
# Example: 'data/university_history.csv'
# =========================================================
MY_DATASET_PATH = 'historical_data.csv' 
# =========================================================

if __name__ == "__main__":
    if os.path.exists(MY_DATASET_PATH):
        print(f"--- Training Models for Performance App using: {MY_DATASET_PATH} ---")
        try:
            train_and_save_models(MY_DATASET_PATH)
            print("--- Success! Models saved in performance/ml_models/saved_models/ ---")
        except KeyError as e:
            print(f"ERROR: Column name {e} not found in your CSV.")
            print("Ensure your CSV has columns: 'ca_score', 'year', and 'final_score'")
    else:
        print(f"ERROR: File not found at {MY_DATASET_PATH}")