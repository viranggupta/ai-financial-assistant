import streamlit as st
from groq import Groq
import os
from semantic_memory import store_memory, retrieve_memory

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])


# 🔥 Response function with memory
def generate_response(user_query, use_memory=True):

    if not user_query or user_query.strip() == "":
        return "⚠️ Please enter a valid question."

    context = retrieve_memory(user_query) if use_memory else ""

    prompt = f"""
You are a senior investment banker.

Provide structured answers:
1. Definition
2. Key insights
3. Real-world example
4. Simple explanation

Context:
{context}

Question:
{user_query}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            answer = response.choices[0].message.content
        except:
            answer = "⚠️ No response generated."

        # ✅ Store only meaningful queries
        if len(user_query) > 5:
            store_memory(f"User: {user_query}\nAssistant: {answer}")

        return answer

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# 📊 Stock detection
def detect_stock(query):
    stocks = {
        "apple": "AAPL",
        "tesla": "TSLA",
        "amazon": "AMZN",
        "google": "GOOGL",
        "microsoft": "MSFT",
        "nvidia": "NVDA"
    }

    for name, ticker in stocks.items():
        if name in query.lower():
            return ticker

    return None


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

# 🧠 Memory toggle (NEW FEATURE)
use_memory = st.checkbox("Use past context", value=True)

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

    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    ticker = detect_stock(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing financial data..."):

            if ticker:
                response = f"""
📊 **{ticker} Stock Overview**

{ticker} is a major publicly traded company.

👉 You can ask:
- Analyze {ticker}
- Should I invest in {ticker}?
- Explain {ticker} fundamentals

(Real-time data integration coming next 🚀)
"""
            else:
                response = generate_response(user_query, use_memory)

            st.write(response)

    # Store assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})


# 🧹 CLEAR CHAT BUTTON
if st.button("Clear Chat"):
    st.session_state.messages = []