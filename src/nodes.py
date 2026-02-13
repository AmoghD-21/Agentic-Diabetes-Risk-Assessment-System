import os
from dotenv import load_dotenv
from src.state import AgentState
from src.tools import run_diabetes_prediction, search_tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

# 1. Load API Keys from .env
load_dotenv()

# 2. Define the extraction schema
class ExtractionSchema(BaseModel):
    """Extract health metrics from the conversation."""
    age: Optional[int] = Field(None, description="User's age")
    glucose: Optional[int] = Field(None, description="Blood glucose level")
    bmi: Optional[float] = Field(None, description="Body Mass Index")

# 3. Initialize the LLM
# Note: Using your specific Azure/GitHub configuration
llm = ChatOpenAI(
    model="gpt-4o", 
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url="https://models.inference.ai.azure.com",
    max_tokens=4096,
    temperature=0 
)

def triage_node(state: AgentState):
    """Processes user input, saves metrics to memory, and asks for missing info."""
    user_text = state["messages"][-1].content
    
    # 1. Pull existing metrics from history
    current_metrics = state.get("metrics", {}) or {}

    # 2. Extract new data from the current message
    extractor = llm.with_structured_output(ExtractionSchema)
    new_data = extractor.invoke(user_text)

    # 3. Update the persistent dictionary
    if new_data.age: current_metrics["age"] = new_data.age
    if new_data.glucose: current_metrics["glucose"] = new_data.glucose
    if new_data.bmi: current_metrics["bmi"] = new_data.bmi

    # 4. Identify what is still needed
    missing = []
    if not current_metrics.get("age"): missing.append("age")
    if not current_metrics.get("glucose"): missing.append("glucose level")
    if not current_metrics.get("bmi"): missing.append("BMI")

    # 5. Generate Response
    if missing:
        # We make the LLM generate a friendly response instead of a rigid list
        missing_str = ", ".join(missing)
        response = llm.invoke(
            f"The user said: '{user_text}'. We still need: {missing_str}. "
            f"Ask for the missing info politely in simple English."
        ).content
    else:
        response = "I have all your details. Analyzing your health risk now..."

    return {
        "messages": [("assistant", response)],
        "metrics": current_metrics
    }

# ✅ CRITICAL: Added the Predictor Node
def predictor_node(state: AgentState):
    """Feeds the collected metrics into the Scikit-Learn .pkl model."""
    # This calls the function in src/tools.py
    result = run_diabetes_prediction(state["metrics"])
    return {"prediction_result": result}

def researcher_node(state: AgentState):
    """Uses DuckDuckGo to find specific advice based on the risk score."""
    risk_info = state["prediction_result"]
    age = state["metrics"].get("age")
    
    query = f"Top vegetarian diet and lifestyle prevention tips for {age} year old with {risk_info} diabetes"
    results = search_tool.run(query)
    
    # Construct final output
    final_report = f"### 🩺 Assessment Result\n**{risk_info}**\n\n### 🥗 Personalized Recommendations\n{results}"
    
    return {
        "search_data": results,
        "messages": [("assistant", final_report)]
    }