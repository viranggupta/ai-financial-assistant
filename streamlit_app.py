import streamlit as st
from groq import Groq
import os
import yfinance as yf
import numpy as np
import pandas as pd
import requests
import bcrypt
from pymongo import MongoClient
from semantic_memory import store_memory, get_memory

# ------------------- DB -------------------
mongo = MongoClient(os.environ["MONGO_URI"])
db = mongo["financial_db"]
users = db["users"]

# ------------------- AUTH -------------------
def hash_password(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt())

def check_password(p, hashed):
    return bcrypt.checkpw(p.encode(), hashed)

def register(u, p):
    if users.find_one({"username": u}):
        return False
    users.insert_one({"username": u, "password": hash_password(p)})
    return True

def login(u, p):
    user = users.find_one({"username": u})
    return user and check_password(p, user["password"])

# ------------------- LOGIN UI -------------------
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if login(u, p):
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:
        u2 = st.text_input("New Username")
        p2 = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register(u2, p2):
                st.success("Created")
            else:
                st.error("User exists")

    st.stop()

# ------------------- INIT -------------------
client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ------------------- MEMORY -------------------


# ------------------- AI -------------------
def ai_response(q):
    context = get_memory(st.session_state.user)

    prompt = f"""
You are a financial advisor.

Context:
{context}

Question:
{q}
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    ans = res.choices[0].message.content

    store_memory(st.session_state.user, f"Q:{q} A:{ans}")
    return ans

# ------------------- STOCK -------------------
def format_ticker(t):
    t = t.upper()
    if not t.endswith(".NS") and not t.endswith(".BO"):
        return t + ".NS"
    return t

@st.cache_data(ttl=60)
def get_price(t):
    t = format_ticker(t)
    h = yf.Ticker(t).history(period="1d")
    if h.empty:
        return None
    return h["Close"].iloc[-1]

@st.cache_data(ttl=60)
def get_hist(t):
    t = format_ticker(t)
    h = yf.Ticker(t).history(period="1mo")
    return h["Close"] if not h.empty else None

# ------------------- NEWS -------------------
def get_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=stock&apiKey={os.environ['NEWS_API_KEY']}"
        return requests.get(url).json().get("articles", [])[:5]
    except:
        return [{"title": "News unavailable", "url": ""}]

def sentiment(t):
    t = t.lower()
    if "rise" in t or "gain" in t:
        return "🟢"
    if "fall" in t or "loss" in t:
        return "🔴"
    return "⚪"

# ------------------- PORTFOLIO -------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# ------------------- UI -------------------
st.title("💰 AI Financial Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📰 News", "💬 AI Chat"])

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# ================= DASHBOARD =================
with tab1:

    st.sidebar.title("Portfolio")
    t = st.sidebar.text_input("Ticker")
    amt = st.sidebar.number_input("Investment", 0.0)

    if st.sidebar.button("Add") and t:
        price = get_price(t)
        if price:
            shares = amt / price
            st.session_state.portfolio.append({
                "ticker": t,
                "investment": amt,
                "shares": shares
            })

    total_val = 0
    total_inv = 0

    data = []

    for s in st.session_state.portfolio:
        price = get_price(s["ticker"])
        if price:
            value = s["shares"] * price
            total_val += value
            total_inv += s["investment"]

            hist = get_hist(s["ticker"])
            if hist is not None:
                returns = (hist.iloc[-1]-hist.iloc[0])/hist.iloc[0]
                vol = np.std(hist.pct_change().dropna())
                data.append((returns, vol))

    profit = total_val - total_inv
    roi = (profit / total_inv * 100) if total_inv else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Invested", f"${total_inv:.2f}")
    c2.metric("Value", f"${total_val:.2f}")
    c3.metric("P/L", f"${profit:.2f}")
    c4.metric("ROI", f"{roi:.2f}%")

    # Allocation chart
    if st.session_state.portfolio:
        df = pd.DataFrame([
            {"ticker": s["ticker"], "value": s["shares"] * get_price(s["ticker"])}
            for s in st.session_state.portfolio if get_price(s["ticker"])
        ])
        st.bar_chart(df.set_index("ticker"))

    # Charts
    for s in st.session_state.portfolio:
        hist = get_hist(s["ticker"])
        if hist is not None:
            st.line_chart(hist)

    # AI Advisor
    if data:
        prompt = f"Analyze portfolio returns and risk: {data}"
        st.subheader("🤖 AI Advice")
        st.write(ai_response(prompt))

# ================= NEWS =================
with tab2:
    st.subheader("📰 Market News")

    for n in get_news():
        st.write(f"**{n['title']}** {sentiment(n['title'])}")
        st.write(n["url"])

# ================= CHAT =================
with tab3:
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        with st.chat_message(m["r"]):
            st.write(m["c"])

    q = st.chat_input("Ask anything")

    if q:
        st.session_state.chat.append({"r":"user","c":q})

        with st.chat_message("assistant"):
            r = ai_response(q)
            st.write(r)

        st.session_state.chat.append({"r":"assistant","c":r})

