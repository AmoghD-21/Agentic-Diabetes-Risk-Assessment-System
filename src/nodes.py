import os
from dotenv import load_dotenv
from src.state import AgentState
from src.tools import run_diabetes_prediction, search_tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

# 1. Load Keys
load_dotenv()

# 2. Extraction Schema (Now used for both Chat and PDF parsing)
class ExtractionSchema(BaseModel):
    age: Optional[int] = Field(None, description="The age of the patient")
    glucose: Optional[int] = Field(None, description="Blood glucose/sugar level")
    bmi: Optional[float] = Field(None, description="Body Mass Index")

# 3. LLM Setup (GPT-4o is excellent for structured extraction)
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://models.inference.ai.azure.com"),
    temperature=0.2,  # Lower temperature for accurate data extraction
)

# --- NODES ---

def report_parser_node(state: AgentState):
    """Processes raw text from a PDF and extracts metrics using structured output."""
    raw_text = state.get("report_text", "")
    
    # Debug logging
    print(f"[DEBUG report_parser_node] Raw text length: {len(raw_text)} characters")
    print(f"[DEBUG report_parser_node] Raw text preview (first 500 chars): {raw_text[:500]}")
    
    if not raw_text or len(raw_text.strip()) == 0:
        print("[WARNING report_parser_node] Empty report_text received!")
        return {
            "messages": [("assistant", "⚠️ I couldn't extract any text from the PDF. Please ensure the PDF contains readable text.")],
            "report_text": None,
        }
    
    # Enhanced prompt for messy OCR text - more robust extraction
    extraction_prompt = f"""You are a medical data extraction specialist. Extract clinical metrics from this lab report text.

The text may be messy due to OCR or PDF extraction. Look for:
- Age: Patient's age (usually a number between 1-120)
- Glucose: Blood glucose/sugar level (look for values like "Glucose", "FBS", "Fasting Blood Sugar", "HbA1c", "Blood Sugar" - typically 70-600 mg/dL)
- BMI: Body Mass Index (usually a decimal number between 10-70, may be written as "BMI" or "Body Mass Index")

Extract ONLY the numeric values. If a value is not found, leave it as None.

Lab Report Text:
{raw_text}

Extract the age, glucose level, and BMI from the above text."""
    
    # Use structured output to extract metrics
    extractor = llm.with_structured_output(ExtractionSchema)
    try:
        extracted = extractor.invoke(extraction_prompt)
        print(f"[DEBUG report_parser_node] Extracted values - Age: {extracted.age}, Glucose: {extracted.glucose}, BMI: {extracted.bmi}")
    except Exception as e:
        print(f"[ERROR report_parser_node] Extraction failed: {e}")
        return {
            "messages": [("assistant", f"⚠️ Error extracting data from PDF: {str(e)}")],
            "report_text": None,
        }

    # Merge with existing metrics (preserve any previously extracted values)
    current_metrics = state.get("metrics", {}) or {}
    if extracted.age is not None: 
        current_metrics["age"] = int(extracted.age)
    if extracted.glucose is not None: 
        current_metrics["glucose"] = int(extracted.glucose)
    if extracted.bmi is not None: 
        current_metrics["bmi"] = float(extracted.bmi)
    
    print(f"[DEBUG report_parser_node] Final metrics dict: {current_metrics}")

    # Generate user-friendly message
    extracted_count = sum([1 for k in ["age", "glucose", "bmi"] if current_metrics.get(k)])
    if extracted_count == 0:
        msg = "⚠️ I couldn't find Age, Glucose, or BMI in your report. Please check the sidebar or provide these values manually."
    elif extracted_count < 3:
        missing = [k for k in ["age", "glucose", "bmi"] if not current_metrics.get(k)]
        msg = f"✅ I extracted some metrics from your report. Missing: {', '.join(missing)}. Please check the sidebar and provide any missing values."
    else:
        msg = "✅ I've successfully analyzed your report and extracted all metrics! Please check the sidebar to verify them."

    return {
        "metrics": current_metrics,
        "messages": [("assistant", msg)],
        "report_text": None,  # Clear so next turn routes to triage, not parser
    }

def triage_node(state: AgentState):
    """The Conversational Brain: Handles chat and data extraction simultaneously."""
    messages = state.get("messages") or []
    user_text = messages[-1].content if messages else ""
    current_metrics = state.get("metrics", {}) or {}

    # Background Extraction from chat history
    extractor = llm.with_structured_output(ExtractionSchema)
    extracted = extractor.invoke(user_text)

    if extracted.age: current_metrics["age"] = extracted.age
    if extracted.glucose: current_metrics["glucose"] = extracted.glucose
    if extracted.bmi: current_metrics["bmi"] = extracted.bmi

    missing = [k for k in ["age", "glucose", "bmi"] if not current_metrics.get(k)]
    
    system_prompt = f"""
    You are a medical assistant. 
    CURRENT DATA: {current_metrics}
    MISSING DATA: {missing}
    
    If data is missing, ask for ONE piece subtly. 
    If all data is present, tell them you're ready for the analysis.
    """
    
    messages = [("system", system_prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response], "metrics": current_metrics}

def guardrail_node(state: AgentState):
    """Checks if the data provided is medically realistic."""
    m = state.get("metrics", {})
    errors = []
    
    if m.get("age") and (m["age"] < 1 or m["age"] > 120): errors.append(f"age {m['age']}")
    if m.get("glucose") and (m["glucose"] < 30 or m["glucose"] > 600): errors.append(f"glucose {m['glucose']}")
    if m.get("bmi") and (m["bmi"] < 10 or m["bmi"] > 70): errors.append(f"BMI {m['bmi']}")

    if errors:
        msg = f"I noticed some unusual values: {', '.join(errors)}. Please check them for accuracy! 😊"
        return {"messages": [("assistant", msg)], "guardrail_status": "fail"}
    
    return {"guardrail_status": "pass"}

def predictor_node(state: AgentState):
    """Runs the Scikit-Learn Random Forest model."""
    result = run_diabetes_prediction(state["metrics"])
    return {"prediction_result": result}

def diet_planner_node(state: AgentState):
    """NEW: Generates a 7-day Indian Vegetarian plan based on ML result."""
    risk = state["prediction_result"]
    m = state.get("metrics", {})
    
    # Using the LLM to generate a structured, culturally relevant diet (Markdown table)
    prompt = f"""
    You are a Senior Indian Dietician. Create a 7-day Indian Vegetarian Diabetes Plan for:
    Risk: {risk}
    Stats: {m}
    
    Requirements:
    1. Output MUST be a single Markdown table with columns: Day | Breakfast | Lunch | Dinner | Snacks
    2. Include Indian vegetarian meals: Poha, Dals, Ragi, Paneer, Sprouts, Roti, Sabzi, Curd, etc.
    3. Focus on Low Glycemic Index foods suitable for diabetes management.
    4. One row per day (Day 1 through Day 7). Use proper Markdown table syntax with | and -.
    """
    
    response = llm.invoke(prompt)
    
    full_report = f"### 🩺 Assessment Result: {risk}\n\n{response.content}"
    
    return {
        "messages": [("assistant", full_report)],
        "diet_plan": response.content # Saved for PDF generation
    }