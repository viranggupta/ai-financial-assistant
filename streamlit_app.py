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
from streamlit_autorefresh import st_autorefresh

# ------------------- CONFIG -------------------
st.set_page_config(layout="wide")
st_autorefresh(interval=5000, key="refresh")

# ------------------- DB -------------------
mongo = MongoClient(os.environ["MONGO_URI"])
db = mongo["financial_db"]
users = db["users"]
portfolio_collection = db["portfolio"]
watchlist_collection = db["watchlist"]
alerts_collection = db["alerts"]

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
        ans = "⚠️ Error"

    store_memory(st.session_state.user,f"Q:{q} A:{ans}")
    return ans

# ------------------- STOCK -------------------
def detect_ticker(t):
    t=t.upper()
    if "." in t: return t
    if not yf.Ticker(t).history(period="1d").empty: return t
    if not yf.Ticker(t+".NS").history(period="1d").empty: return t+".NS"
    return None

@st.cache_data(ttl=5)
def get_price(t):
    h=yf.Ticker(t).history(period="1d")
    return None if h.empty else h["Close"].iloc[-1]

@st.cache_data(ttl=60)
def get_hist(t):
    h=yf.Ticker(t).history(period="1mo")
    return h["Close"] if not h.empty else None

# ------------------- PORTFOLIO DB -------------------
def load_portfolio():
    return list(portfolio_collection.find({"user": st.session_state.user}))

def save_stock(t,inv,sh):
    portfolio_collection.insert_one({
        "user":st.session_state.user,
        "ticker":t,
        "investment":inv,
        "shares":sh
    })

# ------------------- WATCHLIST -------------------
def add_watch(t): watchlist_collection.insert_one({"user":st.session_state.user,"ticker":t})
def get_watch(): return list(watchlist_collection.find({"user":st.session_state.user}))
def remove_watch(t): watchlist_collection.delete_one({"user":st.session_state.user,"ticker":t})

# ------------------- ALERTS -------------------
def add_alert(t,p):
    alerts_collection.insert_one({"user":st.session_state.user,"ticker":t,"target":p})

def check_alerts():
    alerts=alerts_collection.find({"user":st.session_state.user})
    for a in alerts:
        cur=get_price(a["ticker"])
        if cur and cur>=a["target"]:
            st.warning(f"🚨 {a['ticker']} hit ${a['target']}")

# ------------------- MARKOWITZ -------------------
def optimize_portfolio(tickers):
    data={}
    for t in tickers:
        data[t]=yf.Ticker(t).history(period="3mo")["Close"]
    df=pd.DataFrame(data).dropna()

    returns=df.pct_change().dropna()
    mean=returns.mean()
    cov=returns.cov()

    w=np.random.random(len(tickers))
    w/=np.sum(w)

    ret=np.dot(w,mean)
    vol=np.sqrt(np.dot(w.T,np.dot(cov,w)))

    return w,ret,vol

# ------------------- UI -------------------
st.title("💰 AI Financial Intelligence Platform")

st.sidebar.markdown(f"### 👤 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.user=None
    st.rerun()

# INPUT
st.sidebar.title("📊 Portfolio")
ticker=st.sidebar.text_input("Ticker")
amt=st.sidebar.number_input("Investment",0.0)

if ticker:
    t=detect_ticker(ticker)
    if t:
        price=get_price(t)
        st.sidebar.success(f"Live Price: ${price:.2f}")
    else:
        st.sidebar.error("Invalid ticker")

if st.sidebar.button("Add") and ticker:
    t=detect_ticker(ticker)
    if t:
        p=get_price(t)
        save_stock(t,amt,amt/p)
        st.rerun()

# LOAD DATA
portfolio=load_portfolio()

# METRICS
total_val,total_inv=0,0
rows=[]

for s in portfolio:
    price=get_price(s["ticker"])
    if price:
        val=s["shares"]*price
        total_val+=val
        total_inv+=s["investment"]
        rows.append({"ticker":s["ticker"],"value":val})

profit=total_val-total_inv
roi=(profit/total_inv*100) if total_inv else 0

c1,c2,c3,c4=st.columns(4)
c1.metric("Invested",f"${total_inv:.2f}")
c2.metric("Value",f"${total_val:.2f}")
c3.metric("P/L",f"${profit:.2f}")
c4.metric("ROI",f"{roi:.2f}%")

# LIVE PRICES
st.markdown("## ⚡ Live Prices")
for s in portfolio:
    p=get_price(s["ticker"])
    if p:
        st.metric(s["ticker"],f"${p:.2f}")

# CHART
if rows:
    st.bar_chart(pd.DataFrame(rows).set_index("ticker"))

for s in portfolio:
    h=get_hist(s["ticker"])
    if h is not None:
        st.line_chart(h)

# EDIT/DELETE
st.subheader("📂 Portfolio Manager")
for s in portfolio:
    col1,col2,col3,col4=st.columns(4)
    col1.write(s["ticker"])
    new=col2.number_input("Edit",value=float(s["investment"]),key=str(s["_id"]))
    if col3.button("Update",key="u"+str(s["_id"])):
        p=get_price(s["ticker"])
        portfolio_collection.update_one({"_id":s["_id"]},{"$set":{"investment":new,"shares":new/p}})
        st.rerun()
    if col4.button("Delete",key="d"+str(s["_id"])):
        portfolio_collection.delete_one({"_id":s["_id"]})
        st.rerun()

# WATCHLIST
st.markdown("## ⭐ Watchlist")
for w in get_watch():
    col1,col2,col3=st.columns(3)
    col1.write(w["ticker"])
    col2.write(f"${get_price(w['ticker']):.2f}")
    if col3.button("Remove",key=w["ticker"]):
        remove_watch(w["ticker"])
        st.rerun()

new_watch=st.text_input("Add watchlist")
if st.button("Add Watch"):
    t=detect_ticker(new_watch)
    if t: add_watch(t)

# ALERTS
st.markdown("## 🚨 Alerts")
at=st.text_input("Alert ticker")
ap=st.number_input("Target price")
if st.button("Set Alert"):
    t=detect_ticker(at)
    if t: add_alert(t,ap)

check_alerts()

# MARKOWITZ
st.markdown("## 📊 Optimization")
if portfolio:
    tickers=[s["ticker"] for s in portfolio]
    try:
        w,r,v=optimize_portfolio(tickers)
        st.dataframe(pd.DataFrame({"Ticker":tickers,"Weight":w}))
        st.success(f"Return: {r:.2%}")
        st.warning(f"Risk: {v:.2%}")
    except:
        st.error("Optimization failed")

# AI
st.markdown("## 🤖 AI Advisor")
if portfolio:
    st.write(ai_response(f"Analyze portfolio {portfolio}"))

st.markdown("## 🤖 Recommendations")
if portfolio:
    st.write(ai_response(f"Suggest stocks for {portfolio}"))

# CHAT
st.markdown("## 💬 Chat")
if "chat" not in st.session_state:
    st.session_state.chat=[]

for m in st.session_state.chat:
    with st.chat_message(m["r"]):
        st.write(m["c"])

q=st.chat_input("Ask")
if q:
    st.session_state.chat.append({"r":"user","c":q})
    r=ai_response(q)
    st.session_state.chat.append({"r":"assistant","c":r})
    st.rerun()