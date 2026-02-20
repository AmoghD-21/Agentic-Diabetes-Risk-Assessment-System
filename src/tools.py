import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Initialize the Search Tool (for fallback research)
search_tool = DuckDuckGoSearchRun()

# 2. Load model + scaler (path works from project root or when run from src/)
_model_path = Path(__file__).resolve().parent.parent / "data" / "diabetes_model.pkl"
if not _model_path.exists():
    _model_path = Path("data/diabetes_model.pkl")  # fallback when cwd is project root
try:
    with open(_model_path, "rb") as f:
        model_data = pickle.load(f)
    scaler = model_data["scaler"]
    diabetes_model = model_data["model"]
except (FileNotFoundError, OSError):
    # This ensures your app doesn't crash during setup if paths differ
    scaler = None
    diabetes_model = None

def run_diabetes_prediction(metrics: dict):
    """
    Processes extracted metrics, scales them, and returns ML prediction.
    """
    if not diabetes_model or not scaler:
        return "Model not loaded. Please check model files."

    # Mapping extracted names to the original clinical dataset features
    # Order: [Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age]
    
    # We use .get(key, default) to ensure we have a valid array for the scaler
    raw_features = [
        float(metrics.get("pregnancies", 0)),
        float(metrics.get("glucose", 0)),
        float(metrics.get("blood_pressure", 72)), # Average BP
        float(metrics.get("skin_thickness", 23)), # Average thickness
        float(metrics.get("insulin", 30)),        # Baseline insulin
        float(metrics.get("bmi", 0)),
        float(metrics.get("pedigree", 0.47)),     # Average pedigree score
        float(metrics.get("age", 0))
    ]

    # Convert to 2D array for the scaler
    input_array = np.array([raw_features])

    # 3. Handle Feature Names Warning
    # Modern Scikit-Learn expects a DataFrame if the scaler was trained on one
    feature_names = [
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", 
        "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
    ]
    input_df = pd.DataFrame(input_array, columns=feature_names)

    # 4. 🔥 Scale input and Predict
    input_scaled = scaler.transform(input_df)
    
    pred = diabetes_model.predict(input_scaled)[0]
    prob = diabetes_model.predict_proba(input_scaled)[0][1]

    status = "High Risk" if pred == 1 else "Low Risk"
    return f"{status} ({round(prob * 100, 2)}% probability)"