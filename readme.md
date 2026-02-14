# 🩺 Agentic Diabetes Risk Assessment System

An end-to-end **Agentic AI** application that transitions from simple health-chat to a production-ready clinical assessment tool. Built with **LangGraph** for stateful orchestration, **Scikit-Learn** for machine learning, and **Streamlit** for a professional dashboard.



## 🚀 Key Technical Features

### 1. Multi-Node Agentic Architecture
Unlike linear chatbots, this system uses a **Directed Acyclic Graph (DAG)** to manage conversation flow.
* **Triage Node:** Employs LLM-based structured extraction to capture health metrics (Age, Glucose, BMI) from natural dialogue.
* **Guardrail Node:** A clinical safety layer that validates inputs against realistic medical ranges to prevent model hallucinations.
* **Researcher Node:** Uses **DuckDuckGo Search API** to fetch real-time, personalized lifestyle advice based on the user's risk profile.

### 2. Human-in-the-Loop (HITL) 
Implemented **LangGraph Checkpointers** to pause execution. The agent verifies extracted data with the user before triggering the ML prediction node, ensuring 100% data integrity.



### 3. Machine Learning Integration
Integrates a **Random Forest Classifier** trained on clinical data to provide real-time risk probabilities, visualized through interactive **Plotly** gauges.

### 4. Professional PDF Reporting
A modular reporting system built with **FPDF2** that sanitizes Unicode/emojis and generates a downloadable medical summary for the user.



---

## 🛠️ Tech Stack

* **Orchestration:** LangGraph
* **LLM:** OpenAI GPT-4o
* **ML Model:** Scikit-Learn (Random Forest)
* **UI/UX:** Streamlit & Plotly
* **Tools:** DuckDuckGo Search API, FPDF2
* **State Management:** LangGraph MemorySaver

---

## 📂 Project Structure

```text
├── app.py              # Streamlit Frontend & HITL UI
├── src/
│   ├── agent.py        # LangGraph Workflow Definition
│   ├── nodes.py        # Conversational & Safety Logic
│   ├── tools.py        # ML Prediction & Search Tools
│   ├── reports.py      # PDF Generation & Sanitization
│   └── state.py        # Pydantic State Schema
├── requirements.txt    # Project Dependencies
└── .env                # API Keys (Github Token / OpenAI)