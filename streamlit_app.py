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

# ------------------- CONFIG -------------------
st.set_page_config(layout="wide")

# ------------------- PREMIUM UI -------------------
st.markdown("""
<style>
.stApp { background-color: #0E1117; color: white; }
h1 { font-size: 42px; font-weight: 700; color: #00FFA3; }
.metric-card {
    background: linear-gradient(145deg, #1A1F2B, #11151F);
    padding: 20px; border-radius: 12px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    text-align: center;
}
section[data-testid="stSidebar"] { background-color: #11151F; }
.stButton>button {
    background: linear-gradient(90deg, #00FFA3, #00C2FF);
    color: black; border-radius: 10px; font-weight: bold;
}
[data-testid="stChatMessage"] {
    background-color: #1A1F2B;
    padding: 10px; border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1>💰 AI Financial Intelligence Platform</h1>
<p style='color:#aaa;'>AI-powered portfolio analytics & investment insights</p>
""", unsafe_allow_html=True)

# ------------------- ANALYTICS -------------------
def sharpe_ratio(returns):
    return np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0

def risk_score(vol):
    return "🟢 Low Risk" if vol < 0.15 else "🟡 Moderate Risk" if vol < 0.30 else "🔴 High Risk"

def diversification_score(p):
    return "⚠️ Poor" if len(p)<=2 else "🟡 Moderate" if len(p)<=5 else "🟢 Good"

# ------------------- DB -------------------
mongo = MongoClient(os.environ["MONGO_URI"])
db = mongo["financial_db"]
users = db["users"]

# ------------------- AUTH -------------------
def hash_password(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt())
def check_password(p,h): return bcrypt.checkpw(p.encode(),h)

def register(u,p):
    if users.find_one({"username":u}): return False
    users.insert_one({"username":u,"password":hash_password(p)})
    return True

def login(u,p):
    user = users.find_one({"username":u})
    return user and check_password(p,user["password"])

# ------------------- LOGIN -------------------
if "user" not in st.session_state:
    st.session_state.user=None

if not st.session_state.user:
    st.title("🔐 Login")
    t1,t2=st.tabs(["Login","Register"])

    with t1:
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Login"):
            if login(u,p):
                st.session_state.user=u
                st.rerun()
            else:
                st.error("Invalid login")

    with t2:
        u2=st.text_input("New Username")
        p2=st.text_input("New Password",type="password")
        if st.button("Register"):
            if register(u2,p2):
                st.success("Account created")
            else:
                st.error("User exists")
    st.stop()

# ------------------- INIT -------------------
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def ai_response(q):
    context = get_memory(st.session_state.user)
    prompt = f"You are a financial advisor.\nContext:{context}\nQ:{q}"
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}]
        )
        ans = res.choices[0].message.content
    except:
        ans = "Error"
    store_memory(st.session_state.user,f"Q:{q} A:{ans}")
    return ans

# ------------------- STOCK -------------------
def format_ticker(t):
    t=t.upper()
    return t if t.endswith(".NS") or t.endswith(".BO") else t+".NS"

@st.cache_data(ttl=60)
def get_price(t):
    h=yf.Ticker(format_ticker(t)).history(period="1d")
    return None if h.empty else h["Close"].iloc[-1]

@st.cache_data(ttl=60)
def get_hist(t):
    h=yf.Ticker(format_ticker(t)).history(period="1mo")
    return h["Close"] if not h.empty else None

# ------------------- NEWS -------------------
def get_news():
    try:
        url=f"https://newsapi.org/v2/everything?q=stock&apiKey={os.environ['NEWS_API_KEY']}"
        return requests.get(url).json().get("articles",[])[:5]
    except:
        return [{"title":"News unavailable","url":""}]

def sentiment(t):
    return "🟢" if "rise" in t.lower() else "🔴" if "fall" in t.lower() else "⚪"

# ------------------- PORTFOLIO -------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio=[]

st.sidebar.markdown(f"### 👤 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.user=None
    st.rerun()

# ------------------- TABS -------------------
tab1,tab2,tab3=st.tabs(["📊 Dashboard","📰 News","💬 Chat"])

# ================= DASHBOARD =================
with tab1:

    st.sidebar.title("📊 Portfolio")
    t=st.sidebar.text_input("Ticker")
    amt=st.sidebar.number_input("Investment",0.0)

    if st.sidebar.button("Add") and t:
        price=get_price(t)
        if price:
            st.session_state.portfolio.append({
                "ticker":t,
                "investment":amt,
                "shares":amt/price
            })

    total_val,total_inv=0,0
    data=[]

    for s in st.session_state.portfolio:
        price=get_price(s["ticker"])
        if price:
            val=s["shares"]*price
            total_val+=val
            total_inv+=s["investment"]

            hist=get_hist(s["ticker"])
            if hist is not None:
                r=(hist.iloc[-1]-hist.iloc[0])/hist.iloc[0]
                v=np.std(hist.pct_change().dropna())
                data.append((r,v))

    profit=total_val-total_inv
    roi=(profit/total_inv*100) if total_inv else 0

    # Premium Cards
    def card(t,v):
        return f"<div class='metric-card'><h4>{t}</h4><h2>{v}</h2></div>"

    c1,c2,c3,c4=st.columns(4)
    c1.markdown(card("Invested",f"${total_inv:.2f}"),unsafe_allow_html=True)
    c2.markdown(card("Value",f"${total_val:.2f}"),unsafe_allow_html=True)
    c3.markdown(card("P/L",f"${profit:.2f}"),unsafe_allow_html=True)
    c4.markdown(card("ROI",f"{roi:.2f}%"),unsafe_allow_html=True)

    # Allocation
    rows=[]
    for s in st.session_state.portfolio:
        price=get_price(s["ticker"])
        if price:
            rows.append({"ticker":s["ticker"],"value":s["shares"]*price})

    if rows:
        df=pd.DataFrame(rows)
        st.bar_chart(df.set_index("ticker"))

    # Charts
    for s in st.session_state.portfolio:
        hist=get_hist(s["ticker"])
        if hist is not None:
            st.line_chart(hist)

    # Analytics
    if data:
        r=[d[0] for d in data]
        v=[d[1] for d in data]

        st.markdown("## 📊 Advanced Analytics")

        c1,c2,c3=st.columns(3)
        c1.metric("Sharpe",f"{sharpe_ratio(r):.2f}")
        c2.metric("Risk",risk_score(np.mean(v)))
        c3.metric("Diversification",diversification_score(st.session_state.portfolio))

        st.markdown("## 🤖 AI Advisor")
        st.write(ai_response(f"Analyze portfolio: {data}"))

# ================= NEWS =================
with tab2:
    st.markdown("## 📰 Market News")
    for n in get_news():
        st.write(f"**{n['title']}** {sentiment(n['title'])}")
        st.write(n["url"])

# ================= CHAT =================
with tab3:
    st.markdown("## 💬 AI Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat=[]

    for m in st.session_state.chat:
        with st.chat_message(m["r"]):
            st.write(m["c"])

    q=st.chat_input("Ask anything")

    if q:
        st.session_state.chat.append({"r":"user","c":q})
        with st.chat_message("assistant"):
            r=ai_response(q)
            st.write(r)
        st.session_state.chat.append({"r":"assistant","c":r})