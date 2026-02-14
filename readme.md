# 🩺 Agentic Diabetes Risk Assessment System
This project is a sophisticated Medical AI Agent designed to transition from simple chatbots to autonomous, safe, and stateful AI systems. It leverages a Multi-Node Directed Acyclic Graph (DAG) to guide users through health data collection, provide a machine-learning-based risk score, and perform real-time web research for personalized lifestyle advice.

🚀 Key Technical Features
Stateful Orchestration: Managed by LangGraph, allowing the agent to "remember" user metrics (Age, Glucose, BMI) across multiple chat turns.

Clinical Brain: Integrates a custom-trained Scikit-Learn model to calculate risk probability with high precision.

Human-in-the-Loop (HITL): Implements Breakpoints and Checkpointers to pause the graph for user data verification before triggering analysis—ensuring clinical safety.

Dynamic Research Node: Uses DuckDuckGo Search API to fetch real-time, personalized vegetarian dietary tips based on the user's specific risk profile.

Professional UI: A Streamlit dashboard featuring Streaming Responses and interactive Plotly Risk Gauges.

3. The "How It Works" Section (Architectural Explanation)
This is great for showing recruiters how you think about system design:

Triage Node (LLM): Uses GPT-4o and Pydantic to extract structured health metrics from natural language.

Router (Logic): Evaluates if the collected data is complete. If so, it triggers the HITL Breakpoint.

Predictor Node (ML): Once the user confirms, the agent feeds the data into the .pkl model.

Researcher Node (Tools): The agent identifies the risk level and searches the web for tailored recommendations.


├── app.py             # Streamlit Entry Point
├── src/
│   ├── agent.py       # LangGraph Definition
│   ├── nodes.py       # Logic for each node
│   ├── tools.py       # ML Model & Search Tools
│   └── state.py       # Pydantic State Schema
├── data/
│   └── model.pkl      # Trained ML Model
├── .env               # API Keys (Ignore in Git!)
└── requirements.txt   # Dependencies