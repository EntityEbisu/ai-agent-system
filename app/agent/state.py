from typing import Dict, Any

def init_state() -> Dict[str, Any]:
    return {
        "intent": None,
        "tool_state": {
            "active": False,
            "step": None,
            "collected": {
                "name": None,
                "ssn_last4": None,
                "dob": None
            }
        },
        "history": []
    }