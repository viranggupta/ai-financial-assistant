import streamlit as st
from huggingface_hub import InferenceClient
import os

# Load API
client = InferenceClient(
    model="google/flan-t5-base",
    token=os.environ["HF_TOKEN"]
)

def generate_response(user_query):
    prompt = f"""
You are a financial assistant.

Answer clearly and professionally:
{user_query}
"""

    try:
        response = client.text_generation(prompt, max_new_tokens=100)
        return response
    except Exception as e:
        return "⚠️ Server busy. Please try again."

# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)