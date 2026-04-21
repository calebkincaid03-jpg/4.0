import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AI Stock Scanner Pro + Live Dashboard", layout="wide")

# -------------------------
# LOAD / SAVE PERFORMANCE DATA
# -------------------------
DATA_FILE = "scanner_results.json"

def load_results():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_results(results):
    with open(DATA_FILE, "w") as f:
        json.dump(results, f)

results = load_results()

# -------------------------
# SELF-LEARNING WEIGHTS
# -------------------------
base_weights = {"rsi": 10, "volume": 15, "vwap": 10, "trend": 10, "momentum": 10}

if len(results) > 5:
    wins = [r for r in results if r["outcome"] == "win"]
    if len(wins) > 0:
        base_weights["volume"] += 3
        base_weights["trend"] += 2

# -------------------------
# AI CONFIDENCE SCORE
# -------------------------
def ai_score(rsi, volume_ratio, above_vwap, trend_strength, momentum):
    score = 50
    if 55 <= rsi <= 70:
        score += base_weights["rsi"]
    score += min(volume_ratio * 5, base_weights["volume"])
    if above_vwap:
        score += base_weights["vwap"]
    score += trend_strength * base_weights["trend"]
    score += momentum * base_weights["momentum"]
    return max(1, min(99, round(score)))

# -------------------------
# SAMPLE LIVE ALERTS
# -------------------------
alerts = [
    {"ticker": "TSLA", "type": "Breakout", "rsi": 63, "volume": 2.3, "vwap": True, "trend": 0.8, "momentum": 0.7},
    {"ticker": "NVDA", "type": "Reversal", "rsi": 44, "volume": 1.5, "vwap": True, "trend": 0.5, "momentum": 0.4},
    {"ticker": "SPY", "type": "Momentum", "rsi": 59, "volume": 1.9, "vwap": True, "trend": 0.7, "momentum": 0.6},
]

# Auto refresh every 15 sec
st_autorefresh(interval=15000, key="refresh")

# -------------------------
# MAIN UI
# -------------------------
st.title("🚀 AI Stock Scanner Pro + 📈 Live Trend Dashboard")

tab1, tab2 = st.tabs(["Scanner Alerts", "Live Chart"])

# =========================================
# TAB 1: AI STOCK SCANNER
# =========================================
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Live Alerts")
        
        for alert in alerts:
            confidence = ai_score(alert["rsi"], alert["volume"], alert["vwap"], alert["trend"], alert["momentum"])
            
            if confidence >= 80:
                badge = "🟢 STRONG"
            elif confidence >= 65:
                badge = "🟡 MEDIUM"
            else:
                badge = "🔴 WEAK"
            
            st.markdown(f"### {alert['ticker']} - {alert['type']}")
            st.metric("Confidence", f"{confidence}%")
            st.write(badge)
            
            if confidence >= 80:
                st.success(f"🔥 Push Alert: {alert['ticker']} High Probability Setup!")
            
            outcome = st.selectbox(f"Mark Result {alert['ticker']}", ["pending", "win", "loss"], key=alert["ticker"])
            
            if st.button(f"Save {alert['ticker']}", key=f"btn{alert['ticker']}"): 
                results.append({"ticker": alert["ticker"], "confidence": confidence, "outcome": outcome})
                save_results(results)
                st.success("Saved")
            
            st.divider()
    
    with col2:
        st.subheader("Performance Dashboard")
        
        total = len(results)
        wins = len([r for r in results if r["outcome"] == "win"])
        losses = len([r for r in results if r["outcome"] == "loss"])
        win_rate = round((wins / total) * 100, 1) if total > 0 else 0
        
        st.metric("Total Trades", total)
        st.metric("Wins", wins)
        st.metric("Losses", losses)
        st.metric("Win Rate", f"{win_rate}%")
        
        if total > 5:
            st.success("AI Learning Active")

# =========================================
# TAB 2: LIVE TREND DASHBOARD
# =========================================
with tab2:
    st.sidebar.header("Chart Controls")
    
    ticker = st.sidebar.text_input("Ticker", "SPY").upper()
    timeframe = st.sidebar.selectbox("Candlestick Timeframe", ["1m", "5m", "15m", "30m", "60m", "1d"])
    
    show_ema9 = st.sidebar.checkbox("EMA 9", True)
    show_ema20 = st.sidebar.checkbox("EMA 20", True)
    show_ema50 = st.sidebar.checkbox("EMA 50", False)
    show_vwap = st.sidebar.checkbox("VWAP", True)
    
    # Fetch data
    period_map = {"1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo", "60m": "1mo", "1d": "6mo"}
    
    data = yf.download(ticker, period=period_map[timeframe], interval=timeframe, auto_adjust=True)
    
    if data.empty:
        st.error("No data found.")
    else:
        # Calculate indicators
        data["EMA9"] = data["Close"].ewm(span=9).mean()
        data["EMA20"] = data["Close"].ewm(span=20).mean()
        data["EMA50"] = data["Close"].ewm(span=50).mean()
        
        # VWAP
        data["Typical"] = (data["High"] + data["Low"] + data["Close"]) / 3
        data["CumVol"] = data["Volume"].cumsum()
        data["CumPV"] = (data["Typical"] * data["Volume"]).cumsum()
        data["VWAP"] = data["CumPV"] / data["CumVol"]
        
        # RSI
        delta = data["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))
        
        # Create chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        
        fig.add_trace(go.Candlestick(x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"], name="Price"), row=1, col=1)
        
        if show_ema9:
            fig.add_trace(go.Scatter(x=data.index, y=data["EMA9"], name="EMA 9"), row=1, col=1)
        if show_ema20:
            fig.add_trace(go.Scatter(x=data.index, y=data["EMA20"], name="EMA 20"), row=1, col=1)
        if show_ema50:
            fig.add_trace(go.Scatter(x=data.index, y=data["EMA50"], name="EMA 50"), row=1, col=1)
        if show_vwap:
            fig.add_trace(go.Scatter(x=data.index, y=data["VWAP"], name="VWAP"), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI"), row=2, col=1)
        
        fig.update_layout(title=f"{ticker} Live Chart ({timeframe})", height=850, dragmode="pan", hovermode="x unified", xaxis_rangeslider_visible=False)
        fig.update_xaxes(fixedrange=False)
        fig.update_yaxes(fixedrange=False)
        
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True, "doubleClick": "reset"})
        
        # Live metrics
        last_price = data["Close"].iloc[-1]
        prev_price = data["Close"].iloc[-2]
        change = last_price - prev_price
        pct = (change / prev_price) * 100
        
        st.metric(label=f"{ticker} Current Price", value=f"${last_price:.2f}", delta=f"{change:.2f} ({pct:.2f}%)")