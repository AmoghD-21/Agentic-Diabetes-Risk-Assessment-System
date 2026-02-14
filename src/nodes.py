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