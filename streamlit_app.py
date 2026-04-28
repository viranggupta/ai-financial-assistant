import streamlit as st
from groq import Groq
import os

# Initialize client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Response function
def generate_response(user_query, context=""):
    
    if not user_query or user_query.strip() == "":
        return "⚠️ Please enter a question."

    prompt = f"""
You are a financial assistant.

Question:
{user_query}
"""

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

            output = response.choices[0].message.content

            if output:
                return output

        except Exception:
            continue

    return "⚠️ Model temporarily unavailable. Try again."


# UI
st.set_page_config(page_title="AI Financial Assistant")
st.title("💰 AI Financial Assistant")

user_query = st.chat_input("Ask your question")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    response = generate_response(user_query)

    with st.chat_message("assistant"):
        st.write(response)