# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI chatbot memory system. Loads chat history JSON files into MongoDB, then enables semantic search over them using sentence embeddings.

**Pipeline:**
1. `load_memory.py` — reads JSON files from `C:\Users\Virang Gupta\chat-data`, flattens messages into text, inserts into MongoDB collection `financial_db.claude_memory`
2. `semantic_memory.py` — generates embeddings via `all-MiniLM-L6-v2`, stores them back into each document, exposes `semantic_search(query, top_k=3)` using dot-product similarity

## Running

```bash
# Load chat data into MongoDB
python load_memory.py

# Store embeddings (one-time, run before searching)
python semantic_memory.py

# Use semantic search interactively
python -c "from semantic_memory import semantic_search; print(semantic_search('your query'))"
```

## Dependencies

```
pymongo
sentence-transformers
numpy
```

Install: `pip install pymongo sentence-transformers numpy`

## Architecture Notes

- MongoDB Atlas hosts all data — no local DB needed
- Embeddings computed client-side with `sentence-transformers`, stored as float arrays in Mongo
- Similarity = dot product (not cosine normalized) — works because `all-MiniLM-L6-v2` outputs unit-normalized vectors
- `semantic_search` loads all documents into memory on each call — will not scale beyond ~10k docs without adding a vector index (e.g., MongoDB Atlas Vector Search)

## Known Issues

- MongoDB connection string is hardcoded with credentials in both files — move to env var `MONGO_URI` before sharing or committing
- `load_memory.py` does not deduplicate — re-running inserts duplicate documents
- `semantic_search` fetches all docs from Mongo on every query (no caching)
