from pymongo import MongoClient
import os

client = MongoClient(os.environ["MONGO_URI"])
db = client["financial_db"]
collection = db["memory"]

# Store conversation
def store_memory(text):
    collection.insert_one({"content": text})

# Retrieve last few conversations
def retrieve_memory(query, limit=3):
    docs = list(collection.find().sort("_id", -1).limit(limit))

    if not docs:
        return ""

    return "\n".join([doc["content"] for doc in docs])