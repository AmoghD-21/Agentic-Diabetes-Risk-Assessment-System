import pickle
import numpy as np
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the DuckDuckGo Search Tool
search_tool = DuckDuckGoSearchRun()

# Load model + scaler
with open('data/diabetes_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

scaler = model_data["scaler"]
diabetes_model = model_data["model"]


def run_diabetes_prediction(metrics: dict):
    # Ensure clinical order:
    # [Preg, Glucose, BP, Skin, Insulin, BMI, Pedigree, Age]
    input_array = np.array([[
        metrics.get("pregnancies", 0),
        metrics.get("glucose", 0),
        metrics.get("blood_pressure", 70),
        metrics.get("skin_thickness", 20),
        metrics.get("insulin", 79),
        metrics.get("bmi", 0),
        metrics.get("pedigree", 0.47),
        metrics.get("age", 0)
    ]])

    # 🔥 Scale input before prediction
    input_scaled = scaler.transform(input_array)

    pred = diabetes_model.predict(input_scaled)[0]
    prob = diabetes_model.predict_proba(input_scaled)[0][1]

    status = "High Risk" if pred == 1 else "Low Risk"
    return f"{status} ({round(prob * 100, 2)}% probability)"
