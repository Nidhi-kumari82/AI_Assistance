import os
import numpy as np

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI-compatible client
client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))

EMBED_MODEL = os.getenv("EMBED_MODEL")
KB_FOLDER = os.getenv("KB_FOLDER")


# 1. Convert text into embeddings
def get_embedding(text):

    response = client.embeddings.create(model=EMBED_MODEL, input=text)

    return response.data[0].embedding


# 2. Calculate cosine similarity
def cosine_similarity(A, B):

    dot_prod = np.dot(A, B)

    norm_a = np.linalg.norm(A)
    norm_b = np.linalg.norm(B)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_prod / (norm_a * norm_b)


# 3. Load documents from folder
def load_documents(folder=KB_FOLDER):

    documents = []

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith((".txt", ".text")):
            continue

        path = os.path.join(folder, filename)

        with open(path, "r", encoding="utf-8") as f:
            documents.append({"source": filename, "text": f.read()})

    return documents


# 4. Generate embeddings for all documents
def add_embeddings(documents):

    for document in documents:
        vector = get_embedding(document["text"])

        document["vector"] = vector

    return documents


# 5. Search relevant documents
def search(query, documents, top_k=3):

    query_vector = get_embedding(query)

    results = []

    for document in documents:
        score = cosine_similarity(query_vector, document["vector"])

        results.append(
            {
                "score": float(score),
                "source": document["source"],
                "size": len(document["text"]),
                "text": document["text"],
            }
        )

    results.sort(key=lambda rec: rec["score"], reverse=True)

    return results[:top_k]


# 6. Test retrieval
def test(user_query, documents, top_k=3):

    print(f"\nUser query: {user_query}\n")

    results = search(user_query, documents, top_k)

    for r in results:
        print(f"Score: {r['score']:.4f}")
        print(f"Source: {r['source']}")
        print(f"Size: {r['size']} characters")
        print(f"Content: {r['text'][:300]}")
        print("-" * 50)


# 7. Main execution
documents = load_documents()

documents = add_embeddings(documents)

print(f"We have embedded {len(documents)} documents")

user_query = "How many days of maternity leave will I get?"

test(user_query, documents)
