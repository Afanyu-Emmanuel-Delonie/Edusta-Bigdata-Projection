import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier

class EduStatEngine:
    def __init__(self, historical_data_path):
        # Load the 4-year historical dataset
        self.df = pd.read_csv(historical_data_path)
        self.regressor = LinearRegression()
        self.classifier = RandomForestClassifier(n_estimators=100)

    def train_models(self):
        # --- 1. Train Regression (Predicting the Score) ---
        # Features: CA Score, Year, Department_Encoded
        # Target: Final_Score
        X = self.df[['ca_score', 'year']] 
        y = self.df['final_score']
        self.regressor.fit(X, y)

        # --- 2. Train Classifier (Predicting the Status) ---
        # We create a 'status' column: 0=Fail, 1=Probation, 2=Pass
        def label_status(score):
            if score < 10: return 0      # Fail
            if 10 <= score < 12: return 1 # Probation
            return 2                     # Pass

        self.df['status'] = self.df['final_score'].apply(label_status)
        y_class = self.df['status']
        self.classifier.fit(X, y_class)
        
        print("Models trained successfully using 4-year trend data.")

    def predict_performance(self, current_ca, current_year):
        """Input: Current CA score and Year. Output: (Predicted Score, Status Tag)"""
        input_data = np.array([[current_ca, current_year]])
        
        pred_score = self.regressor.predict(input_data)[0]
        pred_class = self.classifier.predict(input_data)[0]
        
        status_map = {0: "Fail", 1: "Probation", 2: "Pass"}
        return round(pred_score, 2), status_map[pred_class]