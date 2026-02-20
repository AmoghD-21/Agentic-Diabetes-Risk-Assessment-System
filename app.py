# import streamlit as st
# import uuid
# import plotly.graph_objects as go
# from datetime import datetime
# from src.agent import diabetes_agent
# from src.reports import generate_pdf_report

# # 1. Page Configuration
# st.set_page_config(
#     page_title="Diabetes AI Assistant", 
#     page_icon="🩺", 
#     layout="wide"
# )

# # 2. Function to Create the Risk Meter (Gauge Chart)
# def create_risk_meter(probability_pct):
#     color = "green" if probability_pct <= 30 else "orange" if probability_pct <= 70 else "red"
#     fig = go.Figure(go.Indicator(
#         mode = "gauge+number",
#         value = probability_pct,
#         title = {'text': "Diabetes Risk Probability (%)", 'font': {'size': 18}},
#         gauge = {
#             'axis': {'range': [0, 100], 'tickwidth': 1},
#             'bar': {'color': color},
#             'bgcolor': "white",
#             'borderwidth': 2,
#             'bordercolor': "gray",
#             'steps': [
#                 {'range': [0, 30], 'color': 'rgba(0, 255, 0, 0.1)'},
#                 {'range': [30, 70], 'color': 'rgba(255, 165, 0, 0.1)'},
#                 {'range': [70, 100], 'color': 'rgba(255, 0, 0, 0.1)'}
#             ],
#             'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': probability_pct}
#         }
#     ))
#     fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
#     return fig

# # 3. Session State Initialization
# if "messages" not in st.session_state:
#     st.session_state.messages = [{
#         "role": "assistant", 
#         "content": "Hello! I am your AI health assistant. Let's look into your diabetes risk together. Could you tell me a bit about your **Age**, **Glucose level**, or **BMI**? 😊"
#     }]
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = str(uuid.uuid4())

# # 4. Agent State Retrieval
# config = {"configurable": {"thread_id": st.session_state.thread_id}}
# state_snapshot = diabetes_agent.get_state(config)
# current_metrics = state_snapshot.values.get("metrics", {}) if state_snapshot.values else {}

# # 5. Sidebar: Data Tracker & PDF Export
# with st.sidebar:
#     st.title("🛡️ Agent Control")
#     if st.button("🔄 Reset Conversation"):
#         st.session_state.clear()
#         st.rerun()
    
#     st.markdown("---")
#     st.subheader("📋 Recorded Metrics")
#     st.write(f"{'✅' if current_metrics.get('age') else '❌'} **Age:** {current_metrics.get('age', '—')}")
#     st.write(f"{'✅' if current_metrics.get('glucose') else '❌'} **Glucose:** {current_metrics.get('glucose', '—')}")
#     st.write(f"{'✅' if current_metrics.get('bmi') else '❌'} **BMI:** {current_metrics.get('bmi', '—')}")
    
#     # PDF Export Section (Appears after analysis)
#     if "final_report_data" in st.session_state:
#         st.markdown("---")
#         st.subheader("📄 Export Results")
#         data = st.session_state.final_report_data
        
#         # Ensure data is returned as bytes from reports.py
#         pdf_bytes = generate_pdf_report(data["metrics"], data["result"], data["advice"])
        
#         st.download_button(
#             label="📥 Download Medical Report (PDF)",
#             data=pdf_bytes,
#             file_name=f"Diabetes_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
#             mime="application/pdf"
#         )

#     st.markdown("---")
#     st.markdown("### Risk Legend")
#     st.success("0-30%: Low Risk")
#     st.warning("31-70%: Moderate Risk")
#     st.error("71-100%: High Risk")

# # 6. Display Chat History
# for i, message in enumerate(st.session_state.messages):
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#         if "metadata" in message and "PROB_VAL:" in message["metadata"]:
#             prob = float(message["metadata"].split(":")[1])
#             st.plotly_chart(create_risk_meter(prob), use_container_width=True, key=f"hist_chart_{i}")

# # 7. Handle User Input
# if prompt := st.chat_input("Ask me anything or share your stats..."):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         response_placeholder = st.empty()
#         full_response = ""
        
#         # Initial stream (Triage/Conversation -> Guardrail)
#         for chunk in diabetes_agent.stream({"messages": [("user", prompt)]}, config=config, stream_mode="values"):
#             if "messages" in chunk:
#                 last_msg = chunk["messages"][-1]
#                 if hasattr(last_msg, "content") and last_msg.type == "ai":
#                     full_response = last_msg.content
#                     response_placeholder.markdown(full_response + "▌")
        
#         response_placeholder.markdown(full_response)
#         st.session_state.messages.append({"role": "assistant", "content": full_response})
#         st.rerun()

# # 8. HITL Logic: Confirmation & Analysis execution
# if state_snapshot.next and "predict" in state_snapshot.next:
#     with st.chat_message("assistant"):
#         st.warning("⚠️ **Data Confirmation Required**")
#         st.write("I have collected your health data and it has passed safety checks. Please confirm:")
#         st.info(f"**Age:** {current_metrics.get('age')} | **Glucose:** {current_metrics.get('glucose')} | **BMI:** {current_metrics.get('bmi')}")
        
#         col1, col2 = st.columns(2)
        
#         if col1.button("✅ Confirm & Run Analysis"):
#             with st.spinner("Executing Prediction & Web Research..."):
#                 current_prob = None
#                 final_res_str = ""
                
#                 # Resume graph execution from the breakpoint
#                 for chunk in diabetes_agent.stream(None, config=config, stream_mode="values"):
#                     if "messages" in chunk:
#                         full_response = chunk["messages"][-1].content
                    
#                     if "prediction_result" in chunk and chunk["prediction_result"]:
#                         final_res_str = chunk["prediction_result"]
#                         try:
#                             # Parsing probability from "Status (XX.XX% probability)"
#                             current_prob = float(final_res_str.split("(")[1].split("%")[0])
#                         except: pass

#                 # Final UI update for results
#                 st.markdown(full_response)
#                 metadata = f"PROB_VAL:{current_prob}" if current_prob is not None else ""
#                 if current_prob is not None:
#                     st.plotly_chart(create_risk_meter(current_prob), use_container_width=True, key="live_prediction_chart")
                
#                 # Save data for PDF and persistence
#                 st.session_state.final_report_data = {
#                     "metrics": current_metrics,
#                     "result": final_res_str,
#                     "advice": full_response
#                 }
#                 st.session_state.messages.append({"role": "assistant", "content": full_response, "metadata": metadata})
#                 st.rerun()

#         if col2.button("❌ Edit Data"):
#             st.info("No problem! Just let me know which values to change.")


import streamlit as st
import uuid
import plotly.graph_objects as go
from datetime import datetime
from src.agent import diabetes_agent
from src.reports import generate_pdf_report
from src.utils import extract_text_from_pdf

# 1. Page Configuration
st.set_page_config(
    page_title="Diabetes AI Architect", 
    page_icon="🩺", 
    layout="wide"
)

# 2. Risk Meter UI Component
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
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! I can analyze your health metrics via chat or by **uploading a Lab Report (PDF)**. How would you like to start? 😊"
    }]
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Refresh current agent state to display updated metrics in sidebar
state_snapshot = diabetes_agent.get_state(config)
m = state_snapshot.values.get("metrics", {}) if state_snapshot.values else {}

# 4. Sidebar: Tools and Dashboard
with st.sidebar:
    st.title("🛡️ Agent Control Center")
    if st.button("🔄 Reset Conversation"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.subheader("📄 Upload Lab Report")
    uploaded_file = st.file_uploader("Upload PDF Report", type=['pdf'], key="pdf_uploader")
    
    # PDF Processing Pipeline
    if uploaded_file and "file_processed" not in st.session_state:
        with st.spinner("Analyzing Document (Running Multi-Engine Extraction)..."):
            try:
                file_bytes = uploaded_file.read()
                raw_text = extract_text_from_pdf(file_bytes)
                
                # Check for empty/scanned PDF that failed all engines
                if not raw_text or len(raw_text.strip()) == 0:
                    st.error("⚠️ This PDF appears to be a scanned image or an unsupported format.")
                    st.info("Please **type your metrics** (Age, Glucose, BMI) directly into the chat below!")
                    st.session_state.file_processed = True
                else:
                    # 1. Update Graph State with extracted text
                    diabetes_agent.update_state(config, {"report_text": raw_text})
                    
                    # 2. Run the graph to trigger the parser_node
                    inputs = {"messages": [("user", "I've uploaded a report. Please extract my data.")]}
                    final_chunk = None
                    for chunk in diabetes_agent.stream(inputs, config=config, stream_mode="values"):
                        final_chunk = chunk
                    
                    # 3. Add Parser's response to chat
                    if final_chunk and final_chunk.get("messages"):
                        st.session_state.messages.append({"role": "assistant", "content": final_chunk["messages"][-1].content})
                    
                    st.session_state.file_processed = True
                    st.rerun()
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
                st.session_state.file_processed = True

    st.markdown("---")
    st.subheader("📋 Recorded Metrics")
    st.write(f"{'✅' if m.get('age') else '❌'} **Age:** {m.get('age', '—')}")
    st.write(f"{'✅' if m.get('glucose') else '❌'} **Glucose:** {m.get('glucose', '—')}")
    st.write(f"{'✅' if m.get('bmi') else '❌'} **BMI:** {m.get('bmi', '—')}")
    
    # Download Section
    if "final_report_data" in st.session_state:
        st.markdown("---")
        st.subheader("📄 Export Results")
        data = st.session_state.final_report_data
        pdf_bytes = generate_pdf_report(data["metrics"], data["result"], data["advice"], data.get("diet_plan"))
        st.download_button(
            label="📥 Download Full Report",
            data=pdf_bytes,
            file_name=f"Diabetes_Assessment_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# 5. Main Chat Interface
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "metadata" in message and "PROB_VAL:" in message["metadata"]:
            prob = float(message["metadata"].split(":")[1])
            st.plotly_chart(create_risk_meter(prob), use_container_width=True, key=f"hist_chart_{i}")

# 6. Chat Input Handler
if prompt := st.chat_input("Type your metrics or ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        for chunk in diabetes_agent.stream({"messages": [("user", prompt)]}, config=config, stream_mode="values"):
            if "messages" in chunk:
                last_msg = chunk["messages"][-1]
                if hasattr(last_msg, "content") and last_msg.type == "ai":
                    full_response = last_msg.content
                    response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

# 7. HITL Logic: The Breakpoint before Prediction
if state_snapshot.next and "predict" in state_snapshot.next:
    with st.chat_message("assistant"):
        st.warning("⚠️ **Review Extracted Data**")
        st.write("The system has identified the following metrics. Please confirm to generate your ML prediction and **7-day Indian Vegetarian plan**:")
        st.info(f"**Age:** {m.get('age')} | **Glucose:** {m.get('glucose')} | **BMI:** {m.get('bmi')}")
        
        if st.button("✅ Confirm & Run Analysis"):
            with st.spinner("Generating clinical assessment and vegetarian diet plan..."):
                current_prob, final_res, diet_plan, final_msg = None, "", "", ""
                # Resume execution from the interrupt
                for chunk in diabetes_agent.stream(None, config=config, stream_mode="values"):
                    if "messages" in chunk:
                        final_msg = chunk["messages"][-1].content
                    if "prediction_result" in chunk:
                        final_res = chunk["prediction_result"]
                        try:
                            # Parse probability from the result string
                            current_prob = float(final_res.split("(")[1].split("%")[0])
                        except: pass
                    if "diet_plan" in chunk:
                        diet_plan = chunk["diet_plan"]

                # Save all final state to session for the Export button and UI
                st.session_state.final_report_data = {
                    "metrics": m, "result": final_res, "advice": final_msg, "diet_plan": diet_plan
                }
                metadata = f"PROB_VAL:{current_prob}" if current_prob is not None else ""
                st.session_state.messages.append({"role": "assistant", "content": final_msg, "metadata": metadata})
                st.rerun()