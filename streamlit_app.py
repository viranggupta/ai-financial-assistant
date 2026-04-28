import streamlit as st
from groq import Groq
import os
from semantic_memory import store_memory, retrieve_memory
import yfinance as yf
import numpy as np

# Initialize Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# 🔥 AI RESPONSE
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

        if len(user_query) > 5:
            store_memory(f"User: {user_query}\nAssistant: {answer}")

        return answer

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# 📊 STOCK DETECTION
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

# 📈 STOCK DATA
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")

    if hist.empty:
        return None, None

    price = round(hist["Close"].iloc[-1], 2)
    prev_close = round(hist["Close"].iloc[-2], 2) if len(hist) > 1 else price

    return price, prev_close

# 📉 HISTORY FOR ANALYTICS
def get_stock_history(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")

    if hist.empty:
        return None

    return hist["Close"]

def calculate_returns(prices):
    return (prices[-1] - prices[0]) / prices[0]

def calculate_volatility(prices):
    returns = prices.pct_change().dropna()
    return np.std(returns) * np.sqrt(252)

# 🎨 UI CONFIG
st.set_page_config(page_title="AI Financial Assistant", layout="wide")

st.title("💰 AI Financial Assistant")
st.caption("AI + Finance + Portfolio Analytics 🚀")

# 🧠 MEMORY TOGGLE
use_memory = st.checkbox("Use past context", value=True)

# 📊 SIDEBAR PORTFOLIO
st.sidebar.title("📊 Portfolio Tracker")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

ticker_input = st.sidebar.text_input("Add Stock (e.g. AAPL)")
investment = st.sidebar.number_input("Investment ($)", min_value=0.0)

if st.sidebar.button("Add"):
    if ticker_input:
        st.session_state.portfolio.append({
            "ticker": ticker_input.upper(),
            "investment": investment
        })

# 📊 PORTFOLIO ANALYTICS
st.sidebar.subheader("📊 Portfolio Analytics")

total_value = 0
total_invested = 0
portfolio_data = []

for stock in st.session_state.portfolio:
    ticker = stock["ticker"]
    invested = stock["investment"]

    price, _ = get_stock_data(ticker)

    if price:
        shares = invested / price
        value = shares * price

        total_value += value
        total_invested += invested

        hist = get_stock_history(ticker)

        if hist is not None:
            returns = calculate_returns(hist.values)
            volatility = calculate_volatility(hist)

            portfolio_data.append({
                "ticker": ticker,
                "return": returns,
                "volatility": volatility
            })

        st.sidebar.write(f"{ticker} → ${value:.2f}")

# 📈 PERFORMANCE
profit = total_value - total_invested
roi = (profit / total_invested) * 100 if total_invested > 0 else 0

st.sidebar.write(f"💼 Invested: ${total_invested:.2f}")
st.sidebar.write(f"📈 Value: ${total_value:.2f}")
st.sidebar.write(f"💰 P/L: ${profit:.2f}")
st.sidebar.write(f"📊 ROI: {roi:.2f}%")

# ⚖️ RISK ANALYSIS
st.sidebar.subheader("⚖️ Risk Analysis")

for data in portfolio_data:
    st.sidebar.write(
        f"{data['ticker']} → Return: {data['return']*100:.2f}% | Volatility: {data['volatility']:.2f}"
    )

# 📊 ALLOCATION
st.sidebar.subheader("📊 Allocation")

for stock in st.session_state.portfolio:
    percentage = (stock["investment"] / total_invested) * 100 if total_invested > 0 else 0
    st.sidebar.write(f"{stock['ticker']} → {percentage:.1f}%")

# 🧠 CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 🎯 INPUT
user_query = st.chat_input("Ask your financial question...")

# 🔄 RESPONSE FLOW
if user_query:

    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    ticker = detect_stock(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):

            if ticker:
                price, prev = get_stock_data(ticker)

                if price:
                    change = price - prev

                    response = f"""
📊 **{ticker} Analysis**

💰 Price: ${price}
📉 Change: {round(change,2)}

👉 Ask:
- “Should I invest in {ticker}?”
- “Future outlook of {ticker}”
"""

                    st.write(response)

                    # 📊 STOCK CHART
                    hist = yf.Ticker(ticker).history(period="1mo")
                    st.line_chart(hist["Close"])

                else:
                    st.write("⚠️ Could not fetch stock data")

            else:
                response = generate_response(user_query, use_memory)
                st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

# 🧹 CLEAR CHAT
if st.button("Clear Chat"):
    st.session_state.messages = []