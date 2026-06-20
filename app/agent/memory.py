
from .state import init_state

# In-memory store
sessions: dict[str, dict] = {}

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = init_state()
    return sessions[session_id]

def update_session(session_id: str, state: dict):
    sessions[session_id] = state
