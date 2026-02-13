from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Annotate with add_messages so new messages are appended, not overwritten
    messages: Annotated[List, add_messages]
    # Dictionary to store clinical values extracted from chat
    metrics: dict 
    # Store the risk result from the .pkl model
    prediction_result: Optional[str]
    # Store the result from the web search API
    search_data: Optional[str]