from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import numpy as np

# 🔗 MongoDB connection
from pymongo import MongoClient

client = MongoClient("mongodb+srv://viranggupta:j4pWpQBRV82djarF@gmp-21-19-virang.srl59.mongodb.net/?retryWrites=true&w=majority")
db = client["financial_db"]
collection = db["claude_memory"]

# 🧠 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔄 Store embeddings in DB
def store_embeddings():
    docs = collection.find()

    for doc in docs:
        if "embedding" not in doc:
            embedding = model.encode(doc["content"]).tolist()

            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"embedding": embedding}}
            )

    print("✅ Embeddings stored")

# 🔍 Semantic search
def semantic_search(query, top_k=3):
    query_embedding = model.encode(query)

    docs = list(collection.find())

    scores = []
    for doc in docs:
        if "embedding" in doc:
            doc_embedding = np.array(doc["embedding"])
            score = np.dot(query_embedding, doc_embedding)
            scores.append((score, doc))

    scores.sort(reverse=True, key=lambda x: x[0])

    return [doc for _, doc in scores[:top_k]]


# ▶️ Run embedding once
if __name__ == "__main__":
    store_embeddings()