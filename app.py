import streamlit as st
import uuid
import plotly.graph_objects as go
from src.agent import diabetes_agent

# 1. Page Configuration
st.set_page_config(page_title="Diabetes AI Assistant", page_icon="🩺", layout="wide")

# 2. Function to Create the Risk Meter
def create_risk_meter(probability_pct):
    color = "green" if probability_pct <= 30 else "orange" if probability_pct <= 70 else "red"
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = probability_pct,
        title = {'text': "Diabetes Risk Probability (%)", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.1)'},
                {'range': [30, 70], 'color': 'rgba(255, 165, 0, 0.1)'},
                {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.1)'}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': probability_pct}
        }
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your AI health assistant. Let's look into your diabetes risk together. Could you tell me a bit about your **Age**, **Glucose level**, or **BMI**? 😊"}]
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# 4. Sidebar with Live Data Tracker
config = {"configurable": {"thread_id": st.session_state.thread_id}}
state_snapshot = diabetes_agent.get_state(config)
current_metrics = state_snapshot.values.get("metrics", {}) if state_snapshot.values else {}

with st.sidebar:
    st.title("🛡️ Agent Control")
    if st.button("🔄 Reset Conversation"):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    st.subheader("📋 Recorded Metrics")
    # Real-time dashboard showing the agent's extraction progress
    st.write(f"{'✅' if current_metrics.get('age') else '❌'} **Age:** {current_metrics.get('age', '—')}")
    st.write(f"{'✅' if current_metrics.get('glucose') else '❌'} **Glucose:** {current_metrics.get('glucose', '—')}")
    st.write(f"{'✅' if current_metrics.get('bmi') else '❌'} **BMI:** {current_metrics.get('bmi', '—')}")
    
    st.markdown("---")
    st.markdown("### Risk Legend")
    st.success("0-30%: Low Risk")
    st.warning("31-70%: Moderate Risk")
    st.error("71-100%: High Risk")

# 5. Display Chat History
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # FIX: Unique key for charts in history using the loop index
        if "metadata" in message and "PROB_VAL:" in message["metadata"]:
            prob = float(message["metadata"].split(":")[1])
            st.plotly_chart(create_risk_meter(prob), use_container_width=True, key=f"hist_chart_{i}")

# 6. Handle User Input
if prompt := st.chat_input("Ask me anything or share your stats..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Initial stream (Triage -> Guardrail)
        for chunk in diabetes_agent.stream({"messages": [("user", prompt)]}, config=config, stream_mode="values"):
            if "messages" in chunk:
                last_msg = chunk["messages"][-1]
                if hasattr(last_msg, "content") and last_msg.type == "ai":
                    full_response = last_msg.content
                    response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

# 7. HITL Logic: Checking for Interruptions (Post-Guardrail)
state_snapshot = diabetes_agent.get_state(config)

if state_snapshot.next and "predict" in state_snapshot.next:
    m = state_snapshot.values.get("metrics", {})
    
    with st.chat_message("assistant"):
        st.warning("⚠️ **Human-in-the-Loop: Confirmation Required**")
        st.write("I have collected your data and passed the safety checks. Please confirm these details are correct before I perform the clinical analysis:")
        st.info(f"**Age:** {m.get('age')} | **Glucose:** {m.get('glucose')} | **BMI:** {m.get('bmi')}")
        
        col1, col2 = st.columns(2)
        
        if col1.button("✅ Confirm & Analyze"):
            with st.spinner("Running ML Prediction and Research..."):
                current_prob = None
                # Resume the stream by passing None to continue from the checkpoint
                for chunk in diabetes_agent.stream(None, config=config, stream_mode="values"):
                    if "messages" in chunk:
                        full_response = chunk["messages"][-1].content
                    
                    if "prediction_result" in chunk and chunk["prediction_result"]:
                        try:
                            # Parse probability from result string "Status (XX.XX% probability)"
                            res_str = chunk["prediction_result"]
                            current_prob = float(res_str.split("(")[1].split("%")[0])
                        except: pass

                # Display the final report
                st.markdown(full_response)
                metadata = f"PROB_VAL:{current_prob}" if current_prob is not None else ""
                if current_prob is not None:
                    # FIX: Unique key for the live prediction chart
                    st.plotly_chart(create_risk_meter(current_prob), use_container_width=True, key="live_prediction_chart")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response, "metadata": metadata})
                st.rerun()

        if col2.button("❌ Edit Data"):
            st.info("No problem! Please tell me the corrected values in the chat.")