from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes import (
    report_parser_node, 
    triage_node, 
    guardrail_node, 
    predictor_node, 
    diet_planner_node
)
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

# --- ROUTING LOGIC ---

def route_start(state: AgentState):
    """Decide whether to parse a PDF or start a conversation."""
    report_text = state.get("report_text")
    # Debug logging
    if report_text:
        print(f"[DEBUG route_start] report_text found, length: {len(report_text)}")
        return "parser"
    print("[DEBUG route_start] No report_text, routing to triage")
    return "triage"

def route_after_triage(state: AgentState):
    """Route to guardrail only when all three metrics are captured."""
    metrics = state.get("metrics", {})
    if metrics.get("glucose") and metrics.get("bmi") and metrics.get("age"):
        return "guardrail"
    return "triage"

def route_after_guardrail(state: AgentState):
    """If data is unrealistic, loop back to Triage for correction."""
    if state.get("guardrail_status") == "fail":
        return "triage"
    return "predict"

# --- GRAPH DEFINITION ---



workflow = StateGraph(AgentState)

# 1. Add All Nodes
workflow.add_node("parser", report_parser_node)
workflow.add_node("triage", triage_node)
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("predict", predictor_node)
workflow.add_node("planner", diet_planner_node)

# 2. Entry Logic (PDF vs Chat)
workflow.add_conditional_edges(START, route_start, {
    "parser": "parser",
    "triage": "triage"
})

# 3. Define Main Flow Edges
workflow.add_edge("parser", "guardrail") # From PDF directly to validation

workflow.add_conditional_edges("triage", route_after_triage, {
    "guardrail": "guardrail",
    "triage": END
})

workflow.add_conditional_edges("guardrail", route_after_guardrail, {
    "predict": "predict",
    "triage": "triage"
})

# 4. Final Path: Predict -> Generate 7-Day Vegetarian Plan -> End
workflow.add_edge("predict", "planner")
workflow.add_edge("planner", END)

# --- COMPILATION ---

# We keep the HITL (Human-in-the-Loop) on 'predict'.
# This allows the user to see the extracted metrics (from PDF or Chat) 
# and click "Confirm" before the ML Model and Diet Planner run.
diabetes_agent = workflow.compile(
    checkpointer=memory,
    interrupt_before=["predict"]
)