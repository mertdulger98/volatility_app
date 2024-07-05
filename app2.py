import numpy as np
import pandas as pd
import yfinance as yf
import math
import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide",
                   page_icon=":sunglasses:",
                   initial_sidebar_state="collapsed",
                   # theme="dark"
                   )
st.title("TradingApp")


def getData(stockName, period, interval):
    if interval == '1d':
        dtt = 'Date'
    else:
        dtt = 'Datetime'
    df = yf.download(tickers=stockName, period=period, interval=interval).reset_index().drop(columns=['Close']).rename(
        columns={'Adj Close': 'Close', dtt: 'Date'})

    return df


def atr(data, period=14):
    data['H-L'] = data['High'] - data['Low']
    data['H-PC'] = np.abs(data['High'] - data['Close'].shift(1))
    data['L-PC'] = np.abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    # Calculate the ATR
    data['ATR'] = data['TR'].rolling(window=period).mean()

    # Drop intermediate columns
    data.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)

    return data['ATR']


def indc(data, atr_lag=5):
    data['sma5'] = data['Close'].rolling(window=5).mean()
    data['ATR'] = atr(data)
    data['ATR_lag'] = data['ATR'].shift(atr_lag)
    data['upper'] = data['Close'] + data['ATR_lag']
    data['lower'] = data['Close'] - data['ATR_lag']

    buy_signal = (data['Low'] < data['upper']) & (data['Close'] > data['sma5'])
    sell_signal = (data['High'] > data['upper']) & (data['Close'] < data['sma5'])

    data['signal'] = np.where(buy_signal, 'buy', np.where(sell_signal, 'sell', None))
    data['signal_fill']=data['signal'].fillna(method='ffill')

    return data


# Begining of Streamlit
with st.container():
    col1, col2 = st.columns((1, 4))

    with col1:
        tick = st.text_input('hisse', "BTC").upper()
        if tick == "EURUSD":
            tick = "EURUSD=X"
        elif tick == "GBPUSD":
            tick = "GBPUSD=X"
        elif tick == "DXY":
            tick = "DX=F"
        elif tick == "BTC":
            tick = "BTC-USD"
        elif tick == "ETH":
            tick = "ETH-USD"
        elif tick == "AVAX":
            tick = "AVAX-USD"
        else:
            tick = tick + '.IS'

    with col2:
        st.write(tick)
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.write("15m")
            d1 = getData(tick, period='1mo', interval='15m')
            st.write(indc(d1).iloc[-1]['signal_fill'])
        with c2:
            st.write("30m")
            d2 = getData(tick, period='1mo', interval='30m')
            st.write(indc(d2).iloc[-1]['signal_fill'])
        with c3:
            st.write("1h")
            d3 = getData(tick, period='3mo', interval='1h')
            st.write(indc(d3).iloc[-1]['signal_fill'])
        with c4:
            st.write("1d")
            d4 = getData(tick, period='6mo', interval='1d')
            st.write(indc(d4).iloc[-1]['signal_fill'])


with st.container():
    cl1,cl2 = st.columns((1,5))
    with cl1:
        timeframe = st.selectbox(
            "Zaman Aralığı",
            ('15m', '30m', '1h', '1d')
        )
    with cl2:
        
        if timeframe == '15m':
            df = d1[-180:]

        elif timeframe == '30m':
            df = d2[-180:]

        elif timeframe == '1h':
            df = d3[-180:]

        elif timeframe == '1d':
            df = d4[-180:]

        # Create a candlestick chart
        fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                             open=df['Open'],
                                             high=df['High'],
                                             low=df['Low'],
                                             close=df['Close'],
                                             name='Candlestick')])

        # Add SMA line to the chart
        fig.add_trace(go.Scatter(x=df['Date'], y=df[f'sma5'], mode='lines', name=f'SMA5',
                                 line=dict(color='yellow')))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['upper'], mode='lines', name='upper', line=dict(color='red')))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['lower'], mode='lines', name='lower', line=dict(color='green')))

        if tick == "EURUSD=X" or tick == "GBPUSD=X" or tick == "DX=F":
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"])  # hide weekends
                ])
        elif tick == "AVAX-USD" or tick == "ETH-USD" or tick == "BTC-USD":
            fig.update_xaxes(
                rangebreaks=[]  # reset/remove rangebreaks for these tickers
            )
        else:
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),  # hide weekends
                    dict(bounds=[18, 9], pattern="hour")
                ])
        # Update the layout
        fig.update_layout(title='Stock Price Data with SMA',
                          xaxis_title='Date',
                          yaxis_title='Price',
                          xaxis_rangeslider_visible=False, height=800,
                          xaxis_showspikes=True,
                          hovermode='x'
                          )

        st.plotly_chart(fig, use_container_width=True)