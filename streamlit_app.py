import streamlit as st
from semantic_memory import semantic_search
from huggingface_hub import InferenceClient
import os

# Load API
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct",
    token=os.environ["HF_TOKEN"]
)

def build_context(query):
    results = semantic_search(query)

    context = ""
    for doc in results:
        content = doc["content"]

        if "$caveman" in content.lower():
            continue

        context += content + "\n\n"

    return context


def generate_response(user_query):
    context = build_context(user_query)

    if context.strip() == "":
        prompt = f"""
You are a financial assistant.

Answer clearly and professionally:
{user_query}
"""
    else:
        prompt = f"""
You are a financial assistant.

Use relevant past knowledge:
{context}

Answer clearly and professionally:
{user_query}
"""

    response = client.text_generation(prompt, max_new_tokens=300)

    return response


# 🎨 UI
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)