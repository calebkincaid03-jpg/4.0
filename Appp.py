# Corrected Appp.py code

# Updated Scatter traces and safe RSI calculation

import yfinance as yf

# Sample Function to calculate RSI safely

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Example usage of yfinance with progress set to False

def fetch_data(ticker):
    data = yf.download(ticker, progress=False)
    data['RSI'] = calculate_rsi(data)
    return data

# Example scatter plot usage

import plotly.express as px

# Scatter plot with updated mode

def create_plot(data):
    fig = px.scatter(data, x='Date', y='RSI', mode='lines')  # mode set to lines for Scatter
    fig.show()