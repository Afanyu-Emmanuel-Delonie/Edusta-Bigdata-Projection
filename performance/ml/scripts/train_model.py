import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import joblib

# ---------------------------------------
# 1. LOAD THE CLEAN DATA
# ---------------------------------------
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "features.csv")
df = pd.read_csv(DATA_PATH)

# Features (X) and Target (y)
X = df.drop("pass_fail", axis=1)
y = df["pass_fail"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------------------------------
# 2. RANDOM FOREST MODEL
# ---------------------------------------
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42
)
rf_model.fit(X_train, y_train)

rf_preds = rf_model.predict(X_test)

print("\n🌲 RANDOM FOREST RESULTS")
print("Accuracy:", accuracy_score(y_test, rf_preds))
print(classification_report(y_test, rf_preds))

# ---------------------------------------
# 3. LOGISTIC REGRESSION BASELINE
# ---------------------------------------
log_model = LogisticRegression(max_iter=500)
log_model.fit(X_train, y_train)

log_preds = log_model.predict(X_test)

print("\n📌 LOGISTIC REGRESSION BASELINE")
print("Accuracy:", accuracy_score(y_test, log_preds))
print(classification_report(y_test, log_preds))

# ---------------------------------------
# 4. SAVE THE RANDOM FOREST MODEL
# ---------------------------------------

# The path of THIS script
SCRIPT_DIR = os.path.dirname(__file__)

# Correct path: performance/ml/models/
MODELS_DIR = os.path.join(SCRIPT_DIR, "..", "models")

# Create directory if it doesn't exist
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_passfail.pkl")

joblib.dump(rf_model, MODEL_PATH)

print(f"\n✅ Model saved successfully at: {MODEL_PATH}")

    