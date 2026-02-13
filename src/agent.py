# from langgraph.graph import StateGraph, START, END
# from src.state import AgentState
# from src.nodes import triage_node, predictor_node, researcher_node
# from langgraph.checkpoint.memory import MemorySaver


# memory = MemorySaver()
# def route_after_triage(state: AgentState):
#     """
#     The Gatekeeper: Determines if we should do medical work 
#     or just stay in the conversation loop.
#     """
#     metrics = state.get("metrics", {})
    
#     # We only move to prediction if the critical numbers are present and valid
#     glucose = metrics.get("glucose")
#     bmi = metrics.get("bmi")
    
#     if glucose and bmi and glucose > 0 and bmi > 0:
#         return "predict"
    
#     # If data is missing or it's just a greeting, we end this turn.
#     # The next message from the user will start the 'triage' node again.
#     return "end_conversation"

# # 1. Initialize Graph
# workflow = StateGraph(AgentState)

# # 2. Add Nodes
# workflow.add_node("triage", triage_node)
# workflow.add_node("predict", predictor_node)
# workflow.add_node("research", researcher_node)

# # 3. Set entry point
# workflow.add_edge(START, "triage")

# # 4. Add the Conditional Logic
# # This maps the return string of 'route_after_triage' to a specific destination
# workflow.add_conditional_edges(
#     "triage", 
#     route_after_triage, 
#     {
#         "predict": "predict",        # Path to work
#         "end_conversation": END      # Path to just chat and stop
#     }
# )

# # 5. Connect the 'Work' path
# workflow.add_edge("predict", "research")
# workflow.add_edge("research", END)

# # 6. Compile
# # We keep the 'diabetes_agent' name so your app.py doesn't need to change.
# diabetes_agent = workflow.compile(checkpointer=memory)




from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes import triage_node, predictor_node, researcher_node
from langgraph.checkpoint.memory import MemorySaver

# Initialize Memory to store the state during the "Pause"
memory = MemorySaver()

def route_after_triage(state: AgentState):
    """
    Determines if we should move to the HITL confirmation step 
    or stay in the conversation loop.
    """
    metrics = state.get("metrics", {})
    
    glucose = metrics.get("glucose")
    bmi = metrics.get("bmi")
    age = metrics.get("age")
    
    # We move to 'predict' only if all clinical values are present.
    # Because of the interrupt, it will stop BEFORE actually running 'predict'.
    if glucose and bmi and age and glucose > 0 and bmi > 0:
        return "predict"
    
    return "end_conversation"

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("triage", triage_node)
workflow.add_node("predict", predictor_node)
workflow.add_node("research", researcher_node)

# 3. Set entry point
workflow.add_edge(START, "triage")

# 4. Add the Conditional Logic
workflow.add_conditional_edges(
    "triage", 
    route_after_triage, 
    {
        "predict": "predict",        
        "end_conversation": END      
    }
)

# 5. Connect the 'Work' path
workflow.add_edge("predict", "research")
workflow.add_edge("research", END)

# 6. Compile with Checkpointer and Breakpoint
# ✅ This is the HITL magic line
diabetes_agent = workflow.compile(
    checkpointer=memory,
    interrupt_before=["predict"] 
)