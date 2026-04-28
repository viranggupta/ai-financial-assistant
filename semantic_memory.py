from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import numpy as np
import os

# ✅ Secure connection (use Render ENV variable)
client = MongoClient(os.environ["MONGO_URI"])
db = client["financial_db"]
collection = db["memory"]

# 🧠 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# ✅ Store conversation
def store_memory(text):
    embedding = model.encode(text).tolist()

    collection.insert_one({
        "content": text,
        "embedding": embedding
    })


# ✅ Retrieve relevant memory
def retrieve_memory(query, top_k=3):
    query_embedding = model.encode(query)

    docs = list(collection.find())

    if not docs:
        return ""

    scores = []

    for doc in docs:
        if "embedding" in doc:
            doc_embedding = np.array(doc["embedding"])
            score = np.dot(query_embedding, doc_embedding)
            scores.append((score, doc["content"]))

    scores.sort(reverse=True, key=lambda x: x[0])

    # 🔥 Return as TEXT (important)
    return "\n".join([text for _, text in scores[:top_k]])