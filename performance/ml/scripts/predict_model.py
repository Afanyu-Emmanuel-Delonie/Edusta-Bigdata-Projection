"""
predict_model.py

Uses the trained Random Forest model to predict whether a student will
PASS (1) or FAIL (0) based on their assessment features.

Documentation
------------
Required input fields (numeric, same scale as used during training):
- assignment_score
- midterm_score
- final_score
- attendance_percent
- total_score

Model path:
- performance/ml/models/student_pass_fail_rf.pkl
  (resolved at runtime relative to this script)

Output meaning:
- prediction: integer 0 or 1
    0 = fail
    1 = pass
- label: string "Fail" or "Pass" corresponding to prediction
- probability: model confidence for class 1 (Pass), in [0.0, 1.0]

Django integration (Member 6):
- Import and call the function from your Django code, for example

    from performance.ml.scripts.predict_model import predict_pass_fail

  In a Django view or service you can:
  - Collect or compute the five required feature values for a student
  - Call predict_pass_fail(...) with those values
  - Use the returned dictionary to display the prediction and
    confidence score, or to trigger recommendations/alerts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd


# Name and location of the trained Random Forest model file.
# Expected to be saved by the training pipeline as a joblib file.
MODEL_FILENAME = "student_pass_fail_rf.pkl"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / MODEL_FILENAME


def _load_model():
    """Load and return the trained Random Forest model.

    Raises:
        FileNotFoundError: If the model file is missing.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at '{MODEL_PATH}'. "
            "Make sure the trained Random Forest model is saved there, "
            "for example using joblib.dump(clf, MODEL_PATH)."
        )

    return joblib.load(MODEL_PATH)


def predict_pass_fail(
    assignment_score: float,
    midterm_score: float,
    final_score: float,
    attendance_percent: float,
    total_score: float,
) -> Dict[str, Any]:
    """Predict whether a student will pass or fail.

    Args:
        assignment_score: Assignment score feature.
        midterm_score: Midterm exam score feature.
        final_score: Final exam score feature.
        attendance_percent: Attendance percentage feature.
        total_score: Combined/total score feature.

    Returns:
        dict with keys:
            - prediction: 0 (fail) or 1 (pass)
            - label: "Fail" or "Pass"
            - probability: confidence for class 1 (Pass), as float in [0, 1]
    """

    # Load the trained Random Forest model
    model = _load_model()

    # Convert inputs into a single-row DataFrame with the correct column names
    input_df = pd.DataFrame(
        [
            {
                "assignment_score": assignment_score,
                "midterm_score": midterm_score,
                "final_score": final_score,
                "attendance_percent": attendance_percent,
                "total_score": total_score,
            }
        ]
    )

    # Run prediction and probability
    pred_array = model.predict(input_df)
    proba_array = model.predict_proba(input_df)

    # Extract scalar values
    pred_class = int(pred_array[0])

    # Ensure we take the probability corresponding to class 1 (Pass)
    classes = list(getattr(model, "classes_", [0, 1]))
    try:
        pass_index = classes.index(1)
    except ValueError:
        # Fallback: assume second column is for positive class
        pass_index = 1 if proba_array.shape[1] > 1 else 0

    pass_probability = float(proba_array[0][pass_index])

    label = "Pass" if pred_class == 1 else "Fail"

    return {
        "prediction": pred_class,
        "label": label,
        "probability": pass_probability,
    }


if __name__ == "__main__":
    # Example usage / simple test of the prediction function.
    # NOTE: These example values should be provided in the same scale
    # that was used during model training (e.g., normalized 0-1 scores
    # if you trained on the normalized dataset).

    example_student = {
        "assignment_score": 0.8,
        "midterm_score": 0.75,
        "final_score": 0.7,
        "attendance_percent": 0.9,
        "total_score": 0.78,
    }

    try:
        result = predict_pass_fail(**example_student)
    except FileNotFoundError as exc:
        print(exc)
    else:
        print("Input features:")
        for k, v in example_student.items():
            print(f"  {k}: {v}")

        print("\nPrediction result:")
        print(f"  prediction (0=fail, 1=pass): {result['prediction']}")
        print(f"  label: {result['label']}")
        print(f"  probability of pass: {result['probability']:.3f}")
