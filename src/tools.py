import os
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.tools import tool

# --- Configuration & Environment ---
os.environ["HF_HOME"] = "D:/huggingface_cache"
DB_DIR = "./chroma_db"

# 1. Initialize the Search Tool (for general web research)
search_tool = DuckDuckGoSearchRun()

# 2. Load ML Model + Scaler
_model_path = Path(__file__).resolve().parent.parent / "data" / "diabetes_model.pkl"
if not _model_path.exists():
    _model_path = Path("data/diabetes_model.pkl")

try:
    with open(_model_path, "rb") as f:
        model_data = pickle.load(f)
    scaler = model_data["scaler"]
    diabetes_model = model_data["model"]
except (FileNotFoundError, OSError):
    scaler = None
    diabetes_model = None


# --- Tool 1: ML Prediction Tool ---
def run_diabetes_prediction(metrics: dict):
    """
    Processes extracted metrics, scales them, and returns ML prediction probability.
    """
    if not diabetes_model or not scaler:
        return "Model not loaded. Please check data/diabetes_model.pkl"

    # Mapping extracted names to clinical dataset features
    raw_features = [
        float(metrics.get("pregnancies", 0)),
        float(metrics.get("glucose", 0)),
        float(metrics.get("blood_pressure", 72)), 
        float(metrics.get("skin_thickness", 23)), 
        float(metrics.get("insulin", 30)),        
        float(metrics.get("bmi", 0)),
        float(metrics.get("pedigree", 0.47)),     
        float(metrics.get("age", 0))
    ]

    feature_names = [
        "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", 
        "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
    ]
    
    input_df = pd.DataFrame([raw_features], columns=feature_names)

    # Scale and Predict
    input_scaled = scaler.transform(input_df)
    pred = diabetes_model.predict(input_scaled)[0]
    prob = diabetes_model.predict_proba(input_scaled)[0][1]

    status = "High Risk" if pred == 1 else "Low Risk"
    return f"{status} ({round(prob * 100, 2)}% probability)"


# --- Tool 2: Agentic RAG Tool (Vector DB Search) ---
@tool
def lookup_medical_guidelines(query: str) -> str:
    """
    Searches the local knowledge base for Glycemic Index (GI) charts, 
    Indian food database, and clinical diabetes guidelines.
    """
    try:
        # Initialize embeddings using your custom cache path
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        if not os.path.exists(DB_DIR):
            return "Knowledge base not initialized. Run ingest.py first."

        # Load the existing Vector DB
        vector_db = Chroma(
            persist_directory=DB_DIR,
            embedding_function=embeddings
        )
        
        # Retrieve top 3 relevant chunks
        docs = vector_db.similarity_search(query, k=3)
        
        if not docs:
            return "No specific medical guidelines found for this query."

        context = "\n\n".join([f"Guideline: {d.page_content}" for d in docs])
        return context
    except Exception as e:
        return f"Error retrieving medical data: {str(e)}"