import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh

# -------------------------
# PAGE
# -------------------------
st.set_page_config(page_title="Live Market Dashboard", layout="wide")
st.title("📈 Interactive Live Trend Dashboard")

# Auto refresh every 15 sec
st_autorefresh(interval=15000, key="refresh")

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.header("Controls")

ticker = st.sidebar.text_input("Ticker", "SPY").upper()

timeframe = st.sidebar.selectbox(
    "Candlestick Timeframe",
    ["1m", "5m", "15m", "30m", "60m", "1d"]
)

show_ema9 = st.sidebar.checkbox("EMA 9", True)
show_ema20 = st.sidebar.checkbox("EMA 20", True)
show_ema50 = st.sidebar.checkbox("EMA 50", False)
show_vwap = st.sidebar.checkbox("VWAP", True)

# -------------------------
# DATA
# -------------------------
period_map = {
    "1m": "1d",
    "5m": "5d",
    "15m": "5d",
    "30m": "1mo",
    "60m": "1mo",
    "1d": "6mo"
}

data = yf.download(
    ticker,
    period=period_map[timeframe],
    interval=timeframe,
    auto_adjust=True
)

if data.empty:
    st.error("No data found.")
    st.stop()

# -------------------------
# INDICATORS
# -------------------------
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

# -------------------------
# CHART
# -------------------------
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.75, 0.25]
)

# Candles
fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price"
    ),
    row=1, col=1
)

# Overlays
if show_ema9:
    fig.add_trace(go.Scatter(x=data.index, y=data["EMA9"], name="EMA 9"), row=1, col=1)

if show_ema20:
    fig.add_trace(go.Scatter(x=data.index, y=data["EMA20"], name="EMA 20"), row=1, col=1)

if show_ema50:
    fig.add_trace(go.Scatter(x=data.index, y=data["EMA50"], name="EMA 50"), row=1, col=1)

if show_vwap:
    fig.add_trace(go.Scatter(x=data.index, y=data["VWAP"], name="VWAP"), row=1, col=1)

# RSI
fig.add_trace(
    go.Scatter(x=data.index, y=data["RSI"], name="RSI"),
    row=2, col=1
)

# -------------------------
# INTERACTIVE SETTINGS
# -------------------------
fig.update_layout(
    title=f"{ticker} Live Chart ({timeframe})",
    height=850,
    dragmode="pan",          # finger drag to move chart
    hovermode="x unified",   # shows values for chosen candle
    xaxis_rangeslider_visible=False
)

# Zoom with fingers on mobile
fig.update_xaxes(fixedrange=False)
fig.update_yaxes(fixedrange=False)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "doubleClick": "reset"
    }
)

# -------------------------
# LIVE METRIC
# -------------------------
last_price = data["Close"].iloc[-1]
prev_price = data["Close"].iloc[-2]
change = last_price - prev_price
pct = (change / prev_price) * 100

st.metric(
    label=f"{ticker} Current Price",
    value=f"${last_price:.2f}",
    delta=f"{change:.2f} ({pct:.2f}%)"
)
