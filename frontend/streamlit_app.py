#!/usr/bin/env python3
"""
Streamlit Web UI for AI Agent System (Level 200 - Frontend Layer)

Run this to launch the interactive web interface:
    streamlit run frontend/streamlit_app.py

Features:
    • Multi-turn chat with streaming responses
    • Order status verification workflow
    • Session management
    • Metrics & system statistics dashboard
    • Conversation history
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
from requests.exceptions import ConnectionError

# Configure Streamlit
st.set_page_config(
    page_title="AI Agent System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_CHECK_INTERVAL = 30  # seconds

# Custom CSS
st.markdown("""
<style>
    .stChat {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 12px;
        border-radius: 4px;
        border-left: 4px solid #28a745;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 12px;
        border-radius: 4px;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def get_session_state():
    """Initialize session state."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "api_available" not in st.session_state:
        st.session_state.api_available = False
    if "last_health_check" not in st.session_state:
        st.session_state.last_health_check = 0
    return st.session_state


def check_api_health() -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except (ConnectionError, requests.Timeout):
        return False


def get_system_metrics() -> dict | None:
    """Get system metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def send_chat_message(message: str) -> str:
    """Send message to API and get response."""
    state = get_session_state()

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"session_id": state.session_id, "message": message},
            timeout=30,
            stream=True
        )

        if response.status_code == 200:
            # Handle streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "token" in data:
                            full_response += data["token"]
                        elif "error" in data:
                            return f"Error: {data['error']}"
                    except json.JSONDecodeError:
                        pass
            return full_response if full_response else "No response received"
        else:
            return f"Error: {response.status_code}"
    except requests.Timeout:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"


@st.cache_resource
def get_db_explorer_data():
    """Load recent session and message records from the SQLite database."""
    db_file = Path("data/sqlite/conversations.db")
    if not db_file.exists():
        return {
            "sessions": [],
            "messages": [],
            "docs": [],
            "logs": []
        }

    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    sessions = cursor.execute(
        "SELECT id, user_id, created_at, updated_at, "
        "context_type, messages_count FROM conversation_sessions "
        "ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    messages = cursor.execute(
        "SELECT id, session_id, role, substr(content, 1, 140) "
        "AS preview, created_at, intent, rag_query FROM messages "
        "ORDER BY created_at DESC LIMIT 50"
    ).fetchall()

    docs = []
    docs_dir = Path("data/docs")
    if docs_dir.exists():
        for item in docs_dir.iterdir():
            if item.is_file():
                docs.append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "path": str(item),
                })

    log_file = Path("logs/app.log")
    logs = []
    if log_file.exists():
        with log_file.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            logs = [line.strip() for line in lines[-100:]]

    connection.close()
    return {
        "sessions": [dict(row) for row in sessions],
        "messages": [dict(row) for row in messages],
        "docs": docs,
        "logs": logs,
    }


# ============================================================================
# MAIN UI
# ============================================================================

def main():
    """Main Streamlit app."""
    state = get_session_state()

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write("")
    with col2:
        st.markdown("# 🧠 AI Agent System")
        st.markdown("*Conversational AI with RAG & Order Workflow*")
    with col3:
        # Health indicator
        current_time = time.time()
        if current_time - state.last_health_check > HEALTH_CHECK_INTERVAL:
            state.api_available = check_api_health()
            state.last_health_check = current_time

        if state.api_available:
            st.markdown("### 🟢 API Online")
        else:
            st.markdown("### 🔴 API Offline")

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        st.write(f"**Session ID**: `{state.session_id}`")

        st.divider()

        st.subheader("📊 System Status")

        if state.api_available:
            metrics = get_system_metrics()
            if metrics:
                st.write("**Active Metrics:**")
                for metric_name, metric_data in metrics.items():
                    if isinstance(metric_data, dict):
                        st.write(f"- {metric_name}: {metric_data}")
                    else:
                        st.write(f"- {metric_name}: {metric_data}")
            else:
                st.info("No metrics available")
        else:
            st.error("Start the API server: `uvicorn app.main:app --reload`")

        st.divider()

        st.subheader("ℹ️ Help")

        with st.expander("**Order Status Workflow**"):
            st.write("""
            To check your order status, simply say:
            - "Where is my order?"
            - "Check my order status"
            - "I want to verify my order"

            The system will then ask for:
            1. Your full name
            2. Last 4 digits of SSN
            3. Your date of birth (YYYY-MM-DD)
            """)

        with st.expander("**Ask about Documents**"):
            st.write("""
            Ask questions about the company's 10-K filing:
            - "What are the business risks?"
            - "Tell me about seasonality"
            - "What's the revenue breakdown?"

            The system will retrieve relevant documents and answer your questions.
            """)

        with st.divider():

            if st.button("🔄 Clear Conversation", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Main content
    if not state.api_available:
        st.error(
            "⚠️ **API Server is not running!**\n\n"
            "Start it with:\n"
            "```bash\n"
            "uvicorn app.main:app --reload\n"
            "```"
        )
        return

    # Chat interface
    st.subheader("💬 Conversation")

    # Display chat history
    for msg in state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(msg["content"])

    # Input field
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to history
        state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Get response from API
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Thinking..."):
                response = send_chat_message(prompt)

            st.markdown(response)

            # Add to history
            state.messages.append({"role": "assistant", "content": response})

    # Data explorer for stored conversations, RAG docs, and logs
    st.subheader("📊 Data Explorer")
    explorer_data = get_db_explorer_data()
    explorer_tabs = st.tabs(["Sessions", "Messages", "RAG Docs", "Logs"])

    with explorer_tabs[0]:
        if explorer_data["sessions"]:
            for session in explorer_data["sessions"]:
                st.write(f"**Session:** {session['id']}")
                st.write(
                    f"- user_id: {session['user_id']} | "
                    f"context_type: {session['context_type']} | "
                    f"messages: {session['messages_count']} | "
                    f"created_at: {session['created_at']}"
                )
                st.divider()
        else:
            st.info("No session records available yet.")

    with explorer_tabs[1]:
        if explorer_data["messages"]:
            for message in explorer_data["messages"]:
                st.write(f"**{message['role'].title()}** ({message['created_at']})")
                st.write(
                    f"- session: {message['session_id']} | "
                    f"intent: {message['intent']} | "
                    f"rag_query: {message['rag_query']}"
                )
                st.write(message['preview'])
                st.divider()
        else:
            st.info("No message records available yet.")

    with explorer_tabs[2]:
        if explorer_data["docs"]:
            for doc in explorer_data["docs"]:
                st.write(f"- {doc['name']} ({doc['size']} bytes)")
        else:
            st.info("No RAG documents found in data/docs.")

    with explorer_tabs[3]:
        if explorer_data["logs"]:
            st.write("Last 100 log lines from logs/app.log")
            st.code("\n".join(explorer_data["logs"][-20:]), language="json")
        else:
            st.info("No application logs found yet. Ensure the backend is running and logs/app.log exists.")

    # Footer
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("📊 **Endpoints**: /chat, /health, /metrics")
    with col2:
        st.caption("📦 **Database**: SQLite (data/sqlite/conversations.db)")
    with col3:
        st.caption(f"⏰ **Session**: {state.session_id}")


if __name__ == "__main__":
    main()
