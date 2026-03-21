"""
Standalone script to train ML models.
Run from project root: python scripts/train_now.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance.ml_models.trainer import train_and_save_models

DATASET_PATH = 'historical_data.csv'

if __name__ == "__main__":
    if os.path.exists(DATASET_PATH):
        print(f"Training models using: {DATASET_PATH}")
        try:
            train_and_save_models(DATASET_PATH)
            print("Models saved to performance/ml_models/saved_models/")
        except KeyError as e:
            print(f"ERROR: Column {e} not found. CSV needs: ca_score, year, final_score")
    else:
        print(f"ERROR: {DATASET_PATH} not found")
