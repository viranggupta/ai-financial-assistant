import os
import json
from pymongo import MongoClient

# 🔗 Connect to MongoDB
from pymongo import MongoClient

client = MongoClient("mongodb+srv://viranggupta:j4pWpQBRV82djarF@gmp-21-19-virang.srl59.mongodb.net/?retryWrites=true&w=majority")

db = client["financial_db"]
collection = db["claude_memory"]

# 📂 Path to your JSON files
folder_path = r"C:\Users\Virang Gupta\chat-data"

# 🔄 Loop through all JSON files
for file in os.listdir(folder_path):
    if file.endswith(".json"):
        with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
            data = json.load(f)

            # 🧠 Convert messages into one searchable text
            content = ""
            for msg in data.get("messages", []):
                role = msg.get("role", "")
                text = msg.get("content", "")
                content += f"{role}: {text}\n"

            # 📦 Create document
            document = {
                "file_name": file,
                "content": content
            }

            # ⬆️ Insert into MongoDB
            collection.insert_one(document)

print("✅ All data uploaded successfully")