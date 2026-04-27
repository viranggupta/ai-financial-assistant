import streamlit as st
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
load_dotenv()
import time


# Load API
client = InferenceClient(
    model="tiiuae/falcon-rw-1b",
    token=os.environ["HF_TOKEN"]
)
import time  

def generate_response(user_query):
    prompt = f"""
You are a financial assistant.

Answer clearly and professionally:
{user_query}
"""

    for _ in range(3):  # retry 3 times
        try:
            response = client.text_generation(prompt, max_new_tokens=100)
            return response
        except Exception:
            time.sleep(2)

    return "⚠️ Server busy. Please try again in a few seconds."
# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.text_input("Ask your question:")

if user_query:
    with st.spinner("Thinking..."):
        response = generate_response(user_query)
        st.write(response)