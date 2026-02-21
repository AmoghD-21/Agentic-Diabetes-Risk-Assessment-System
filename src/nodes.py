import os
from dotenv import load_dotenv
from src.state import AgentState
# Added lookup_medical_guidelines to imports
from src.tools import run_diabetes_prediction, search_tool, lookup_medical_guidelines
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

# 1. Load Keys
load_dotenv()

# 2. Extraction Schema
class ExtractionSchema(BaseModel):
    age: Optional[int] = Field(None, description="The age of the patient")
    glucose: Optional[int] = Field(None, description="Blood glucose/sugar level")
    bmi: Optional[float] = Field(None, description="Body Mass Index")

# 3. LLM Setup
llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://models.inference.ai.azure.com"),
    temperature=0.2, 
)

# --- NODES ---

def report_parser_node(state: AgentState):
    """Processes raw text from a PDF and extracts metrics using structured output."""
    raw_text = state.get("report_text", "")
    
    if not raw_text or len(raw_text.strip()) == 0:
        return {
            "messages": [("assistant", "⚠️ I couldn't extract any text from the PDF. Please ensure the PDF contains readable text.")],
            "report_text": None,
        }
    
    extraction_prompt = f"""You are a medical data extraction specialist. Extract clinical metrics from this lab report text.
    Lab Report Text:
    {raw_text}
    Extract the age, glucose level, and BMI."""
    
    extractor = llm.with_structured_output(ExtractionSchema)
    try:
        extracted = extractor.invoke(extraction_prompt)
    except Exception as e:
        return {
            "messages": [("assistant", f"⚠️ Error extracting data from PDF: {str(e)}")],
            "report_text": None,
        }

    current_metrics = state.get("metrics", {}) or {}
    if extracted.age is not None: current_metrics["age"] = int(extracted.age)
    if extracted.glucose is not None: current_metrics["glucose"] = int(extracted.glucose)
    if extracted.bmi is not None: current_metrics["bmi"] = float(extracted.bmi)
    
    extracted_count = sum([1 for k in ["age", "glucose", "bmi"] if current_metrics.get(k)])
    if extracted_count == 0:
        msg = "⚠️ I couldn't find metrics in your report. Please check the sidebar or provide them manually."
    elif extracted_count < 3:
        missing = [k for k in ["age", "glucose", "bmi"] if not current_metrics.get(k)]
        msg = f"✅ Extracted partial metrics. Missing: {', '.join(missing)}."
    else:
        msg = "✅ All metrics successfully extracted! Check the sidebar to verify."

    return {
        "metrics": current_metrics,
        "messages": [("assistant", msg)],
        "report_text": None,
    }

def triage_node(state: AgentState):
    """Handles chat and data extraction simultaneously."""
    messages = state.get("messages") or []
    user_text = messages[-1].content if messages else ""
    current_metrics = state.get("metrics", {}) or {}

    extractor = llm.with_structured_output(ExtractionSchema)
    extracted = extractor.invoke(user_text)

    if extracted.age: current_metrics["age"] = extracted.age
    if extracted.glucose: current_metrics["glucose"] = extracted.glucose
    if extracted.bmi: current_metrics["bmi"] = extracted.bmi

    missing = [k for k in ["age", "glucose", "bmi"] if not current_metrics.get(k)]
    
    system_prompt = f"""You are a medical assistant. 
    CURRENT DATA: {current_metrics} | MISSING DATA: {missing}
    If data is missing, ask for it subtly. If complete, say you're ready."""
    
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
        msg = f"I noticed some unusual values: {', '.join(errors)}. Please check them! 😊"
        return {"messages": [("assistant", msg)], "guardrail_status": "fail"}
    return {"guardrail_status": "pass"}

def predictor_node(state: AgentState):
    """Runs the Scikit-Learn Random Forest model."""
    result = run_diabetes_prediction(state["metrics"])
    return {"prediction_result": result}

def diet_planner_node(state: AgentState):
    """
    ADVANCED RAG: Generates a plan grounded in local medical guidelines (PDF data).
    """
    risk = state["prediction_result"]
    m = state.get("metrics", {})
    glucose_val = m.get("glucose", "High")
    
    # 1. RETRIEVAL STEP: Fetch facts from your Vector DB (GI Chart, ICMR guidelines)
    # This search query triggers the lookup tool we built in tools.py
    search_query = f"Indian vegetarian diet guidelines and Glycemic Index for glucose level {glucose_val}"
    clinical_guidelines = lookup_medical_guidelines.invoke(search_query)
    
    # 2. GENERATION STEP: Ground the LLM with the retrieved facts
    prompt = f"""
    You are a Senior Indian Dietician. Create a 7-day Indian Vegetarian Diabetes Plan.
    
    CLINICAL GUIDELINES (Retrieved from knowledge base):
    {clinical_guidelines}
    
    USER PROFILE:
    - Risk Assessment: {risk}
    - Age: {m.get('age')} | Glucose: {m.get('glucose')} | BMI: {m.get('bmi')}
    
    Requirements:
    1. Output a Markdown table (Day | Breakfast | Lunch | Dinner | Snacks).
    2. Use Indian meals (Ragi, Poha, Paneer, Dals, Sabzi).
    3. You MUST justify at least 2 meal choices using the CLINICAL GUIDELINES provided above (e.g., mentioning specific Glycemic Index values).
    4. Focus on low-GI items mentioned in the guidelines.
    """
    
    response = llm.invoke(prompt)
    full_report = f"### 🩺 Assessment Result: {risk}\n\n{response.content}"
    
    return {
        "messages": [("assistant", full_report)],
        "diet_plan": response.content 
    }