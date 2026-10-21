# Standard library imports
from datetime import datetime
import json
import os
from urllib.parse import quote

# Third-party imports
import requests

# Local imports
from Utilities.utilities import log


# -------------------- TOOL FUNCTIONS --------------------


def get_current_time():
    """Return the current local date and time."""
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def get_city_weather(city: str):
    """Return the current weather for a city."""
    if not city or not city.strip():
        raise ValueError("City name cannot be empty.")

    city = city.strip()
    url = f"https://wttr.in/{quote(city)}?format=3"

    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "LocalAIAssistant/1.0"},
    )
    response.raise_for_status()

    return response.text.strip()


def get_user_city():
    """Return the configured city of the user."""
    city = os.getenv("USER_CITY", "").strip()

    if not city:
        return "User city is not configured. Set USER_CITY in your .env file."

    return city


# -------------------- TOOL DEFINITIONS --------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_city_weather",
            "description": "Get current weather information for a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city whose current weather is requested.",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_city",
            "description": (
                "Get the user's configured city when they ask about "
                "their city or the place where they live."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# -------------------- FUNCTION MAPPING --------------------

FUNCTION_NAME_TO_FUNCTION_MAP = {
    "get_current_time": get_current_time,
    "get_city_weather": get_city_weather,
    "get_user_city": get_user_city,
}


# -------------------- TOOL EXECUTION --------------------


def run_tools(tool_call):
    """Execute a requested tool and return its result."""

    func_name = getattr(
        getattr(tool_call, "function", None),
        "name",
        None,
    )

    if not func_name:
        return "Error: Tool call does not contain a function name."

    fn = FUNCTION_NAME_TO_FUNCTION_MAP.get(func_name)

    if fn is None:
        return f"Error: Unknown tool '{func_name}'."

    try:
        raw_args = tool_call.function.arguments or "{}"

        # Some clients provide a dictionary; others provide JSON text.
        if isinstance(raw_args, str):
            func_args = json.loads(raw_args)
        elif isinstance(raw_args, dict):
            func_args = raw_args
        else:
            return "Error: Tool arguments must be a JSON object."

        if not isinstance(func_args, dict):
            return "Error: Tool arguments must be a JSON object."

        log(f"Running tool: {func_name}")

        result = fn(**func_args)

        log(f"Tool completed: {func_name}")
        return str(result)

    except json.JSONDecodeError:
        return f"Error: Invalid JSON arguments for '{func_name}'."

    except TypeError:
        return f"Error: Invalid arguments supplied to '{func_name}'."

    except requests.RequestException as e:
        log(f"Network error in {func_name}: {e}")
        return "Error: Weather service is unavailable. Please try again."

    except Exception as e:
        log(f"Error in {func_name}: {e}")
        return f"Error while running '{func_name}'."
