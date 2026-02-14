from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes import triage_node, guardrail_node, predictor_node, researcher_node
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

def route_after_triage(state: AgentState):
    metrics = state.get("metrics", {})
    # If we have the big three, go to Guardrail first
    if metrics.get("glucose") and metrics.get("bmi") and metrics.get("age"):
        return "guardrail"
    return "triage"

def route_after_guardrail(state: AgentState):
    # If guardrail failed, go back to Triage to ask for correct data
    if state.get("guardrail_status") == "fail":
        return "triage"
    return "predict"

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("triage", triage_node)
workflow.add_node("guardrail", guardrail_node)
workflow.add_node("predict", predictor_node)
workflow.add_node("research", researcher_node)

workflow.add_edge(START, "triage")

# Conditional: Triage -> Guardrail (if data complete)
workflow.add_conditional_edges("triage", route_after_triage, {
    "guardrail": "guardrail",
    "triage": END
})

# Conditional: Guardrail -> Predict (if passed) OR Triage (if failed)
workflow.add_conditional_edges("guardrail", route_after_guardrail, {
    "predict": "predict",
    "triage": "triage"
})

workflow.add_edge("predict", "research")
workflow.add_edge("research", END)

# Compile with HITL on 'predict'
diabetes_agent = workflow.compile(
    checkpointer=memory,
    interrupt_before=["predict"]
)
