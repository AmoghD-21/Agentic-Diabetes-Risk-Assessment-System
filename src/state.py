# from typing import TypedDict, Annotated, List, Optional
# from langgraph.graph.message import add_messages

# class AgentState(TypedDict):
#     # Annotate with add_messages so new messages are appended, not overwritten
#     messages: Annotated[List, add_messages]
#     # Dictionary to store clinical values extracted from chat
#     metrics: dict 
#     # Store the risk result from the .pkl model
#     prediction_result: Optional[str]
#     # Store the result from the web search API
#     search_data: Optional[str]


from typing import TypedDict, Annotated, List, Optional, Dict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 1. Conversation History
    # add_messages allows the graph to append new chat turns automatically
    messages: Annotated[List, add_messages]
    
    # 2. Extracted Clinical Metrics
    # Stores { "age": int, "glucose": int, "bmi": float, etc. }
    metrics: Dict[str, Optional[float]] 
    
    # 3. Multimodal Data
    # Stores the raw text extracted from an uploaded PDF report
    report_text: Optional[str]
    
    # 4. Analysis Results
    # guardrail_status tracks if metrics are medically realistic ('pass'/'fail')
    guardrail_status: Optional[str]
    # Prediction result from the Random Forest .pkl model
    prediction_result: Optional[str]
    
    # 5. Personalized Outputs
    # Stores the generated 7-Day Indian Vegetarian Diet Plan
    diet_plan: Optional[str]
    # Stores fallback research data if needed
    search_data: Optional[str]