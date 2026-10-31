from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))

response = client.embeddings.create(
    model=os.getenv("EMBED_MODEL"),
    input=["I am good girl", "Python is a good programming language."],
)
for i, emb in enumerate(response.data):
    print(f"Embeeding {i},length: {len(emb.embedding)}")
    print(emb.embedding[0:5])
