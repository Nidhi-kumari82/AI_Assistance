# Standard library imports
import os

# Third-party imports
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY", "ollama"),
)

stream = client.chat.completions.create(
    model=os.getenv("MODEL"),
    messages=[
        {
            "role": "user",
            "content": "What is the llm. explain in 100 words. no need to mention number of words",
        }
    ],
    stream=True,
)

full_response = ""

for chunk in stream:
    piece = chunk.choices[0].delta.content
    if not chunk.choices:
        continue
    if piece:
        print(piece, end="", flush=True)
        full_response += piece

print("\n\nFull response:")
print(full_response)
