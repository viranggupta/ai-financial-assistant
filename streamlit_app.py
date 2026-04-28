import streamlit as st
from huggingface_hub import InferenceClient
import os
import time
from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Load API
def generate_response(user_query, context=""):
    prompt = f"""
You are a financial assistant.

Context:
{context}

Question:
{user_query}

Answer clearly and professionally.
"""

    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",   # ✅ updated model
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)