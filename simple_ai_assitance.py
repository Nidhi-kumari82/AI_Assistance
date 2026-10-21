# Standard library imports
import os

# Third-party imports
from dotenv import load_dotenv
from openai import OpenAI

# Local imports
from tools import TOOLS, run_tools
from Utilities.utilities import log


# Load environment variables
load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY", "ollama"),
)

MODEL = os.getenv("MODEL")
MAX_TOOL_ROUNDS = 5

messages = [
    {
        "role": "system",
        "content": (
            "Act like a humble, helpful assistant. "
            "Keep responses brief and concise. "
            "Use available tools when needed. "
            "Never invent tool results."
        ),
    }
]


def get_assistant_response():
    """Handle user input, chained tool calls, and final responses."""

    while True:
        try:
            user_input = input("\n👤 Nidhi: ").strip()

            if user_input.lower() in {"exit", "bye", "quit", "goodbye"}:
                print("🤖 Assistant: Goodbye!")
                break

            if not user_input:
                continue

            messages.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

            for step in range(MAX_TOOL_ROUNDS + 1):
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                )

                msg = response.choices[0].message

                # No more tool calls: final answer is ready.
                if not msg.tool_calls:
                    answer = msg.content or "I couldn't generate a response."

                    messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                    print("\n🤖 Assistant:", answer)
                    break

                # Allow at most five rounds of tool execution.
                if step == MAX_TOOL_ROUNDS:
                    fallback = (
                        "Sorry, I couldn't finish within the "
                        "tool-call limit. Please try a simpler request."
                    )

                    messages.append(
                        {
                            "role": "assistant",
                            "content": fallback,
                        }
                    )

                    print("\n🤖 Assistant:", fallback)
                    break

                log(f"Step {step + 1}: model requested {len(msg.tool_calls)} tool(s)")

                # Preserve the assistant's tool-call message.
                messages.append(msg.model_dump(exclude_none=True))

                # Execute every tool requested in this round.
                for tool_call in msg.tool_calls:
                    result = run_tools(tool_call)

                    print(f"\n🔧 Tool: {tool_call.function.name}")
                    print(f"📄 Result: {result}")

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )

        except KeyboardInterrupt:
            print("\n🤖 Assistant: Goodbye!")
            break

        except Exception as e:
            log(f"Assistant error: {e}")
            print("\n🤖 Assistant: Something went wrong. Please try again.")


if __name__ == "__main__":
    get_assistant_response()
