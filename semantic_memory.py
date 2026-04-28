from pymongo import MongoClient
import os

client = MongoClient(os.environ["MONGO_URI"])
db = client["financial_db"]
collection = db["memory"]

# Store per user
def store_memory(user, text):
    collection.insert_one({
        "user": user,
        "content": text
    })

# Retrieve per user
def get_memory(user, limit=3):
    docs = list(collection.find({"user": user}).sort("_id", -1).limit(limit))

    if not docs:
        return ""

    return "\n".join([doc["content"] for doc in docs])