import streamlit as st
from huggingface_hub import InferenceClient
import os

# Load API
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct",
    token=os.environ["HF_TOKEN"]
)

def generate_response(user_query):
    prompt = f"""
You are a financial assistant.

Answer clearly and professionally:
{user_query}
"""

    response = client.text_generation(prompt, max_new_tokens=300)
    return response


# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)