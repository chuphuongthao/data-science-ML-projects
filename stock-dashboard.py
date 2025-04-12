import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import ta # Technical Analysis library

# Pulling, processing, creating technical indicators

def get_stock_data(ticker, period, interval):
    # fetch stock data based on the period and interval from Yahoo Finance
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data

def process_data(data):
    # ensure data is timezoned and has correct format
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

def calculate_metrics(data):
    # calculate basic metrics
    last_close = data['Close'].iloc[-1].item()
    prev_close = data['Close'].iloc[0].item()
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = data['High'].max().item()
    low = data['Low'].min().item()
    volume = data['Volume'].sum().item()
    return last_close, change, pct_change, high, low, volume

def add_technical_indicators(data):
    # add technical indicators using the ta library
    # simple moving average
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'].iloc[:,0], window=20)
    # exponential moving average
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'].iloc[:,0], window=20)
    return data

# Dashboard layout

st.set_page_config(page_title="My Real-Time Stock Dashboard", layout="wide")

## Sidebar
st.sidebar.title("Set chart parameters")
ticker = st.sidebar.text_input("Enter ticker", "AAPL")
time_period = st.sidebar.selectbox("Select time period", ["1d", "1wk", "1mo", "1y"])
chart_type = st.sidebar.selectbox("Select chart type", ["Line", "Candlestick"])
indicators = st.sidebar.multiselect("Select indicators", ["SMA_20", "EMA_20"])

## interval mapping
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

## main content
if st.sidebar.button("Update"):
    data = get_stock_data(ticker, time_period, interval_mapping[time_period])
    data = process_data(data)
    data = add_technical_indicators(data)

    last_close, change, pct_change, high, low, volume = calculate_metrics(data)

    # display metrics
    st.metric(label=f"{ticker} Last Price", value=f"${last_close:.2f} USD", delta=f"${change:.2f} ({pct_change:.2f}%)")

    col1, col2, col3 = st.columns(3)
    col1.metric(label="High", value=f"${high:.2f} USD")
    col2.metric(label="Low", value=f"${low:.2f} USD")
    col3.metric(label="Volume", value=f"{volume:,} shares") 

    # plot chart
    fig = go.Figure()
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close')


# add technical indicators to the plot
    for indicator in indicators:
        if indicator == 'SMA_20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
        elif indicator == 'EMA_20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))
        elif indicator == 'RSI':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['RSI'], name='RSI', yaxis='y2'))

    fig.update_layout(title=f"{ticker} {time_period.upper()} Chart", 
                    xaxis_title="Date", 
                    yaxis_title="Price (USD)", 
                    height=600,
                    xaxis_rangeslider_visible=False)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader('Historical Data')
    st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(10), use_container_width=True)

    st.subheader('Technical Indicators')
    st.dataframe(data[['Datetime'] + indicators].tail(10), use_container_width=True)


# sidebar for selected tickers

# sidebar information
st.sidebar.subheader("About")
st.sidebar.info("This is a real-time stock dashboard built with Streamlit and Plotly. Use the sidebar to visualize stock data, technical indicators, and real-time prices for selected stocks.")
