def start_tool_flow(state: dict) -> str:
    state["tool_state"] = {
        "active": True,
        "step": "collect_name",
        "collected": {
            "name": None,
            "ssn_last4": None,
            "dob": None
        }
    }
    
    return "To check your order status, please provide your full name."

def valid_ssn(value: str) -> bool:
    return value.isdigit() and len(value) == 4

def valid_dob(value: str) -> bool:
    # simple check
    return len(value) == 10  # YYYY-MM-DD

from app.tools.order_status import check_order_status

def handle_tool_flow(user_input: str, state: dict) -> str:
    
    tool_state = state["tool_state"]
    step = tool_state["step"]
    
    if step == "collect_name":
        tool_state["collected"]["name"] = user_input
        tool_state["step"] = "collect_ssn"
        return "Please provide the last 4 digits of your SSN."
    
    elif step == "collect_ssn":
        if not valid_ssn(user_input):
            return "Invalid SSN. Please enter exactly 4 digits."
        
        tool_state["collected"]["ssn_last4"] = user_input
        tool_state["step"] = "collect_dob"
        return "Please provide your date of birth (YYYY-MM-DD)."
    
    elif step == "collect_dob":
        if not valid_dob(user_input):
            return "Invalid DOB format. Use YYYY-MM-DD."
        
        tool_state["collected"]["dob"] = user_input
        
        return execute_tool(state)


def execute_tool(state: dict) -> str:
    """Run the mock order status tool and reset workflow state."""
    tool_state = state["tool_state"]
    collected = tool_state["collected"]

    result = check_order_status(
        name=collected["name"],
        ssn=collected["ssn_last4"],
        dob=collected["dob"]
    )

    state["tool_state"] = {
        "active": False,
        "step": None,
        "collected": {
            "name": None,
            "ssn_last4": None,
            "dob": None
        }
    }

    return result