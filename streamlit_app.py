import streamlit as st
from groq import Groq
import os
from semantic_memory import store_memory, retrieve_memory

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])


# 🔥 Response function with memory
def generate_response(user_query):

    if not user_query or user_query.strip() == "":
        return "⚠️ Please enter a valid question."

    context = retrieve_memory(user_query)

    prompt = f"""
You are a financial assistant.

Use this past context if relevant:
{context}

User Question:
{user_query}

Give a structured answer with:
- Definition
- Key points
- Example (if possible)
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

        # ✅ Save conversation
        store_memory(f"Q: {user_query} A: {answer}")

        return answer

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# 🎨 UI CONFIG
st.set_page_config(page_title="AI Financial Assistant", layout="wide")

st.markdown("""
<style>
.big-title {
    font-size:40px;
    font-weight:bold;
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">💰 AI Financial Assistant</div>', unsafe_allow_html=True)

st.caption("AI-powered assistant with memory + finance insights")

# 🧠 CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 🎯 INPUT
user_query = st.chat_input("Ask your financial question...")

# 🔄 RESPONSE FLOW
if user_query:

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing financial data..."):
            response = generate_response(user_query)
            st.write(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})


# 🧹 CLEAR CHAT BUTTON
if st.button("Clear Chat"):
    st.session_state.messages = []