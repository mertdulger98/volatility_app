import numpy as np
import pandas as pd
import yfinance as yf
import math
import datetime
import plotly.express as px

today = datetime.datetime.today().strftime("%Y-%m-%d")
import os
import streamlit as st


def getData(stockName, period, interval):
    if interval == '1d':
        dtt = 'Date'
    else:
        dtt = 'Datetime'
    df = yf.download(tickers=stockName, period=period, interval=interval).reset_index().drop(columns=['Close']).rename(
        columns={'Adj Close': 'Close', dtt: 'Date'})

    return df


def calc(tick, per, inter, mov, window):
    df = getData(tick, per, inter)
    df['r_var'] = df['Close'].rolling(mov).var()
    df['Volatility'] = np.sqrt(df['r_var'])
    df['Range'] = np.sqrt(mov / 365) * df['Volatility']
    df['RH'] = (df['Close'] + df['Range']).shift(window)
    df['RL'] = (df['Close'] - df['Range']).shift(window)

    return df


tfs = {
    '1d': '6mo',
    '1h': '60d',
    '15m': '30d',
    '5m': '3d'
}

st.set_page_config(layout="wide",
                   page_icon=":sunglasses:",
                   initial_sidebar_state="collapsed",
                   # theme="dark"
                   )
st.markdown("""
<style>
body {
    background-color: #121212; /* Dark background color */
    color: #FFFFFF; /* Text color for contrast */
}
</style>
""", unsafe_allow_html=True)

st.title("Bist Volatility App")

col1, col2 = st.columns((1, 4))

with col1:
    tick = st.text_input('hisse', "eurusd").upper()
    if tick == "EURUSD":
        tick = "EURUSD=X"
    elif tick == "GBPUSD":
        tick = "GBPUSD=X"
    elif tick == "DXY":
        tick = "DX=F"
    else:
        tick = tick + '.IS'

    intrv = st.selectbox(
        "Zaman Aralığı",
        ('1d', '1h', '15m', '5m')
    )

    period = tfs[intrv]

    ma_w = st.number_input("Hareketli Ortalama", value=30)
    sf_w = st.number_input("Kaydırma Aralığı", value=3)

    df = calc(tick, period, intrv, ma_w, sf_w)

with col2:
    st.write(f"Chart for {tick}")
    color_map = {
        'Close': 'yellow',
        'RH': 'green',
        'RL': 'red'
    }

    fig = px.line(df[-90:], x='Date', y=['Close', 'RH', 'RL'], markers=True, color_discrete_map=color_map)

    if intrv != '1d':
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # hide weekends
                dict(bounds=[18, 9], pattern="hour")
            ])

        if tick == "EURUSD=X" or tick == "GBPUSD=X" or tick=='DX=F':
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"])  # hide weekends
                ])

    fig.update_layout(xaxis_showspikes=True,
                      hovermode='x'
                      # 'x unified'
                      )

    st.plotly_chart(fig, use_container_width=True)


