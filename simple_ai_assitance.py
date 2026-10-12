from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),  # Ollama doesn't require a real API key
)

messages = []

while True:
    user_input = input("\nNidhi: ")

    if user_input.lower() in ["exit", "bye", "quit", "goodbye", "by"]:
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=os.getenv("MODEL"), messages=messages
    )

    assistant_reply = response.choices[0].message.content

    messages.append({"role": "assistant", "content": assistant_reply})

    print("\nAssistant:", assistant_reply)
