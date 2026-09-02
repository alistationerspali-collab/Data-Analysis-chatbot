"""Streamlit chat UI hitting the FastAPI backend, with chart rendering."""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Data Analysis Chatbot", page_icon="📊", layout="wide")

# --- Minimal custom styling ---
st.markdown("""
    <style>
        .main .block-container { padding-top: 2rem; max-width: 900px; }
        [data-testid="stChatMessage"] { border-radius: 12px; }
        h1 { font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 📊 Data Analysis Chatbot")
    st.caption("Ask questions about Sales, Purchase, Stock, Inventory, and Account data from Busy.")
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    st.divider()
    st.markdown("**Example questions**")
    st.caption("• Top 5 items by sales amount")
    st.caption("• Sales trend by month")
    st.caption("• Outstanding change for [party name]")
    st.caption("• Sales for group [group name]")

st.title("📊 Data Analysis Chatbot")

# --- Chat input ---
question = st.chat_input("Ask about your Busy sales/purchase/stock/account data...")

if question:
    with st.spinner("Analyzing your question..."):
        try:
            response = requests.post(
                API_URL, json={"message": question, "session_id": "streamlit"}, timeout=60
            )
            st.session_state.history.append((question, response.json()))
        except requests.exceptions.RequestException as e:
            st.session_state.history.append((question, {"error": f"Request failed: {e}"}))


def render_chart(data: list[dict], chart_spec: dict):
    chart_type = chart_spec.get("chart_type")
    x_axis = chart_spec.get("x_axis")
    y_axis = chart_spec.get("y_axis")

    if not data or chart_type in (None, "none", "table"):
        return False

    df = pd.DataFrame(data)
    if x_axis not in df.columns or y_axis not in df.columns:
        return False

    if chart_type == "bar":
        fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis)
    elif chart_type == "line":
        fig = px.line(df, x=x_axis, y=y_axis, markers=True)
    elif chart_type == "pie":
        fig = px.pie(df, names=x_axis, values=y_axis)
    elif chart_type == "scatter":
        fig = px.scatter(df, x=x_axis, y=y_axis)
    else:
        return False

    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
    return True


# --- Empty state ---
if not st.session_state.history:
    st.info("👋 Ask me anything about your Sales, Purchase, Stock, Inventory, or Account data.")

# --- Chat history ---
for q, a in st.session_state.history:
    st.chat_message("user", avatar="🧑").write(q)
    with st.chat_message("assistant", avatar="📊"):
        if a.get("declined"):
            st.info(a["reason"])
        elif "error" in a:
            st.error(a["error"])
        else:
            render_chart(a["data"], a.get("chart_spec", {}))
            st.dataframe(a["data"], use_container_width=True)
            with st.expander("View generated SQL"):
                st.code(a["sql"], language="sql")