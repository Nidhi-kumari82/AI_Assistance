# ==============================
# 1. Standard Library Imports
# ==============================
import os
from types import SimpleNamespace

# ==============================
# 2. Third-Party Imports
# ==============================
from dotenv import load_dotenv
from openai import OpenAI

# ==============================
# 3. Local Imports
# ==============================
from tools import TOOLS, run_tools
from Utilities.utilities import log


# ==============================
# 4. Environment Configuration
# ==============================

# Load variables from the .env file into the environment.
load_dotenv()

# Initialize the OpenAI-compatible client.
# This can connect to Ollama or another compatible API.
client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY", "ollama"),
)

# Name of the LLM configured in the .env file.
MODEL = os.getenv("MODEL")

# Maximum number of consecutive tool-execution rounds.
MAX_TOOL_ROUNDS = 5


# ==============================
# 5. Conversation History
# ==============================

# Store messages so the assistant can use previous conversation context.
messages = [
    {
        "role": "system",
        "content": (
            "You are a humble, helpful, general-purpose AI assistant. "
            "Answer general knowledge, programming, coding, and "
            "educational questions directly using your own knowledge. "
            "You can explain Python, C++, Java, DSA, DBMS, and "
            "other technical topics without calling tools. "
            "Use available tools only when a task requires external "
            "information, such as current weather, time, or location. "
            "Never claim that you cannot answer a question merely "
            "because no tool exists for it. "
            "Never invent tool results. "
            "Keep responses clear and concise."
        ),
    }
]


# ==============================
# 6. Stream the Model Response
# ==============================


def stream_chat(history):
    """
    Request a streamed response from the LLM.

    Returns:
        full_response: Complete assistant text.
        calls_list: Collected tool calls, if any.
    """

    # stream=True lets us receive the response in chunks.
    stream = client.chat.completions.create(
        model=MODEL,
        messages=history,
        tools=TOOLS,
        stream=True,
    )

    full_response = ""

    # Tool calls arrive in fragments.
    # Use the tool-call index to combine fragments correctly.
    calls = {}

    # Print the assistant label only when text arrives.
    label_printed = False

    try:
        # Process each chunk as it arrives.
        for chunk in stream:
            # Skip chunks without response choices.
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # ------------------------------
            # A. Stream Assistant Text
            # ------------------------------
            if delta.content:
                if not label_printed:
                    print("🤖 Assistant: ", end="", flush=True)
                    label_printed = True

                # Print immediately instead of waiting for completion.
                print(delta.content, end="", flush=True)

                # Accumulate text for conversation history.
                full_response += delta.content

            # ------------------------------
            # B. Collect Tool Call Fragments
            # ------------------------------
            for tc in delta.tool_calls or []:
                # Create a container for a new tool-call index.
                obj = calls.setdefault(
                    tc.index,
                    SimpleNamespace(
                        id=None,
                        function=SimpleNamespace(
                            name="",
                            arguments="",
                        ),
                    ),
                )

                # The tool-call ID may arrive in an initial chunk.
                if tc.id:
                    obj.id = tc.id

                # Function names and arguments may arrive in pieces.
                if tc.function:
                    if tc.function.name:
                        obj.function.name += tc.function.name

                    if tc.function.arguments:
                        obj.function.arguments += tc.function.arguments

    except KeyboardInterrupt:
        # Handle interruption while the stream is active.
        print("\n[Stopped by you]")

    if label_printed:
        print()

    # Restore the original order of tool calls.
    calls_list = [calls[key] for key in sorted(calls)]

    return full_response, calls_list


# ==============================
# 7. Build Tool Call Payload
# ==============================


def build_tool_calls_payload(tool_calls):
    """
    Convert collected tool calls into the dictionary format
    expected in an assistant message by the API.
    """

    payload = []

    for tool_call in tool_calls:
        tool_call_dict = {
            "id": tool_call.id,
            "type": "function",
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments,
            },
        }

        payload.append(tool_call_dict)

    return payload


# ==============================
# 8. Main Assistant Loop
# ==============================


def get_assistant_response():
    """
    Continuously accept user input, stream model responses,
    execute requested tools, and handle chained tool calls.
    """

    while True:
        try:
            # Read user input and remove surrounding whitespace.
            user_input = input("\n👤 Nidhi: ").strip()

            # Exit commands terminate the assistant loop.
            if user_input.lower() in {"exit", "bye", "quit", "goodbye"}:
                print("🤖 Assistant: Goodbye!")
                break

            # Ignore empty input.
            if not user_input:
                continue

            # Add the user's message to conversation history.
            messages.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

            # Allow tool rounds followed by a final response attempt.
            for step in range(MAX_TOOL_ROUNDS + 1):
                # Stream the model response and collect tool calls.
                full_response, tool_calls = stream_chat(messages)

                # If no tools were requested, the model has answered.
                if not tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": full_response,
                        }
                    )
                    break

                # Stop if the tool-round limit has been reached.
                if step == MAX_TOOL_ROUNDS:
                    fallback = (
                        "Sorry, I could not finish this within the tool-step limit."
                    )

                    print(f"\n🤖 Assistant: {fallback}")

                    messages.append(
                        {
                            "role": "assistant",
                            "content": fallback,
                        }
                    )
                    break

                # Log the current tool-execution round.
                log(f"Step {step + 1}: model requested {len(tool_calls)} tool(s)")

                # Save the assistant's tool-call request.
                # The API needs this before receiving tool results.
                messages.append(
                    {
                        "role": "assistant",
                        "content": full_response or None,
                        "tool_calls": build_tool_calls_payload(tool_calls),
                    }
                )

                # Execute each requested tool.
                for tool_call in tool_calls:
                    result = run_tools(tool_call)

                    # Display the tool name and its result.
                    print(f"\n🔧 Tool: {tool_call.function.name}")
                    print(f"📄 Result: {result}")

                    # Return the result to the model.
                    # The model can use it in its next response.
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )

        except KeyboardInterrupt:
            # Allow Ctrl+C to exit cleanly.
            print("\n🤖 Assistant: Goodbye!")
            break

        except Exception as error:
            # Log unexpected errors and keep the assistant running.
            log(f"Error: {error}")
            print("\n🤖 Assistant: Something went wrong. Please try again.")


# ==============================
# 9. Program Entry Point
# ==============================

# Run the assistant only when this file is executed directly.
if __name__ == "__main__":
    get_assistant_response()
