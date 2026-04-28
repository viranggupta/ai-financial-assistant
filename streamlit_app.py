import streamlit as st
from huggingface_hub import InferenceClient
import os
import time
from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Load API
def generate_response(user_query, context=""):
    prompt = f"..."

    models = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile"
    ]

    for m in models:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception:
            continue

    return "⚠️ Model temporarily unavailable. Try again."

# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)