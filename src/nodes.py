# import os
# from dotenv import load_dotenv
# from src.state import AgentState
# from src.tools import run_diabetes_prediction, search_tool
# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel, Field
# from typing import Optional

# # 1. Load API Keys from .env
# load_dotenv()

# # 2. Define the extraction schema
# class ExtractionSchema(BaseModel):
#     """Extract health metrics from the conversation."""
#     age: Optional[int] = Field(None, description="User's age")
#     glucose: Optional[int] = Field(None, description="Blood glucose level")
#     bmi: Optional[float] = Field(None, description="Body Mass Index")

# # 3. Initialize the LLM
# # Note: Using your specific Azure/GitHub configuration
# llm = ChatOpenAI(
#     model="gpt-4o", 
#     api_key=os.getenv("GITHUB_TOKEN"),
#     base_url="https://models.inference.ai.azure.com",
#     max_tokens=4096,
#     temperature=0 
# )

# def triage_node(state: AgentState):
#     """Processes user input, saves metrics to memory, and asks for missing info."""
#     user_text = state["messages"][-1].content
    
#     # 1. Pull existing metrics from history
#     current_metrics = state.get("metrics", {}) or {}

#     # 2. Extract new data from the current message
#     extractor = llm.with_structured_output(ExtractionSchema)
#     new_data = extractor.invoke(user_text)

#     # 3. Update the persistent dictionary
#     if new_data.age: current_metrics["age"] = new_data.age
#     if new_data.glucose: current_metrics["glucose"] = new_data.glucose
#     if new_data.bmi: current_metrics["bmi"] = new_data.bmi

#     # 4. Identify what is still needed
#     missing = []
#     if not current_metrics.get("age"): missing.append("age")
#     if not current_metrics.get("glucose"): missing.append("glucose level")
#     if not current_metrics.get("bmi"): missing.append("BMI")

#     # 5. Generate Response
#     if missing:
#         # We make the LLM generate a friendly response instead of a rigid list
#         missing_str = ", ".join(missing)
#         response = llm.invoke(
#             f"The user said: '{user_text}'. We still need: {missing_str}. "
#             f"Ask for the missing info politely in simple English."
#         ).content
#     else:
#         response = "I have all your details. Analyzing your health risk now..."

#     return {
#         "messages": [("assistant", response)],
#         "metrics": current_metrics
#     }

# # ✅ CRITICAL: Added the Predictor Node
# def predictor_node(state: AgentState):
#     """Feeds the collected metrics into the Scikit-Learn .pkl model."""
#     # This calls the function in src/tools.py
#     result = run_diabetes_prediction(state["metrics"])
#     return {"prediction_result": result}

# # --- Inside src/nodes.py ---

# def guardrail_node(state: AgentState):
#     """
#     Validates if the extracted health metrics are within physically 
#     possible or medically 'sane' ranges.
#     """
#     metrics = state.get("metrics", {})
#     errors = []

#     # Define common medical sanity ranges
#     ranges = {
#         "age": (1, 120),
#         "glucose": (20, 600),
#         "bmi": (10, 70) 
#     }

#     for key, (min_val, max_val) in ranges.items():
#         val = metrics.get(key)
#         if val is not None:
#             if val < min_val or val > max_val:
#                 errors.append(f"{key.capitalize()} ({val}) is outside the realistic range of {min_val}-{max_val}.")

#     if errors:
#         error_msg = "⚠️ **Safety Warning:** " + " ".join(errors) + " Please double-check your readings and re-enter the data."
#         return {
#             "messages": [("assistant", error_msg)],
#             "guardrail_status": "fail" # Custom flag to stop the graph
#         }
    
#     return {"guardrail_status": "pass"}

# def researcher_node(state: AgentState):
#     """Uses DuckDuckGo to find specific advice based on the risk score."""
#     risk_info = state["prediction_result"]
#     age = state["metrics"].get("age")
    
#     query = f"Top vegetarian diet and lifestyle prevention tips for {age} year old with {risk_info} diabetes"
#     results = search_tool.run(query)
    
#     # Construct final output
#     final_report = f"### 🩺 Assessment Result\n**{risk_info}**\n\n### 🥗 Personalized Recommendations\n{results}"
    
#     return {
#         "search_data": results,
#         "messages": [("assistant", final_report)]
#     }


import os
from dotenv import load_dotenv
from src.state import AgentState
from src.tools import run_diabetes_prediction, search_tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

# 1. Load Keys
load_dotenv()

# 2. Extraction Schema (Invisible to the user)
class ExtractionSchema(BaseModel):
    age: Optional[int] = Field(None)
    glucose: Optional[int] = Field(None)
    bmi: Optional[float] = Field(None)

# 3. LLM Setup
llm = ChatOpenAI(
    model="gpt-4.1", 
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url="https://models.inference.ai.azure.com",
    temperature=0.7 # Increased slightly for more natural/varied speech
)

# --- NODES ---

def triage_node(state: AgentState):
    """The Conversational Brain: Handles chat and data extraction simultaneously."""
    user_text = state["messages"][-1].content
    current_metrics = state.get("metrics", {}) or {}

    # 1. Background Extraction (Silent)
    extractor = llm.with_structured_output(ExtractionSchema)
    extracted = extractor.invoke(user_text)

    # Update stored metrics
    if extracted.age: current_metrics["age"] = extracted.age
    if extracted.glucose: current_metrics["glucose"] = extracted.glucose
    if extracted.bmi: current_metrics["bmi"] = extracted.bmi

    # 2. Natural Language Generation
    # We check what is missing just so the LLM knows, but we don't force a list.
    missing = [k for k in ["age", "glucose", "bmi"] if not current_metrics.get(k)]
    
    system_prompt = f"""
    You are a helpful, empathetic medical assistant. 
    CURRENT DATA: {current_metrics}
    MISSING DATA: {missing}
    
    YOUR GOAL: 
    1. Respond to the user's specific message naturally (chat, answer questions, or empathize).
    2. If the user is just saying 'Hi' or chatting, be warm and explain you can help assess diabetes risk.
    3. If data is missing, subtly ask for ONE missing piece of info at a time in a way that fits the conversation.
    4. If ALL data is present, tell them you're ready to perform the clinical analysis.
    
    IMPORTANT: Do not sound like a computer. Use emojis and vary your tone.
    """
    
    # We pass the whole history so the LLM knows the 'vibe' of the chat
    messages = [("system", system_prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "metrics": current_metrics
    }

def guardrail_node(state: AgentState):
    """Checks if the data provided is medically realistic."""
    m = state.get("metrics", {})
    errors = []
    
    # Validation Logic
    if m.get("age") and (m["age"] < 1 or m["age"] > 120):
        errors.append(f"an age of {m['age']}")
    if m.get("glucose") and (m["glucose"] < 30 or m["glucose"] > 600):
        errors.append(f"a glucose level of {m['glucose']}")
    if m.get("bmi") and (m["bmi"] < 10 or m["bmi"] > 70):
        errors.append(f"a BMI of {m['bmi']}")

    if errors:
        msg = f"Hmm, I noticed something a bit unusual: {', '.join(errors)}. Could you please double-check those numbers for me? Medical accuracy is important for a good assessment! 😊"
        return {"messages": [("assistant", msg)], "guardrail_status": "fail"}
    
    return {"guardrail_status": "pass"}

def predictor_node(state: AgentState):
    """Runs the ML model."""
    result = run_diabetes_prediction(state["metrics"])
    return {"prediction_result": result}

def researcher_node(state: AgentState):
    """Finds lifestyle tips based on the prediction."""
    risk = state["prediction_result"]
    age = state["metrics"].get("age")
    
    query = f"Vegetarian diet and lifestyle tips for a {age} year old with {risk} diabetes"
    results = search_tool.run(query)
    
    report = f"### 🩺 My Analysis\nBased on your metrics, your result is: **{risk}**\n\n### 🥗 Recommendations\n{results}"
    return {"messages": [("assistant", report)]}