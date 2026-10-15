from datetime import datetime


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# TOOLS=[{},{}....]


TOOLS = [
    {
        "type": "Function",
        "function": {
            "name": "get_current_time",
            "description": "Return the current data and time as a formatted string",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]

FUNCTION_NAME_TO_FUNCTION_MAP = {
    "get_current_time": get_current_time,
}
