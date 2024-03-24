import numpy as np
import pandas as pd
import yfinance as yf
import math
import datetime
import plotly.express as px
import plotly.graph_objects as go
from pykalman import KalmanFilter

today = datetime.datetime.today().strftime("%Y-%m-%d")
import os
import streamlit as st

def bt(df,ma,shift):
    df['volty'] = np.sqrt(df['Close'].rolling(ma).var())
    df['Range'] = np.sqrt(ma / 365) * df['volty']
    df['RH'] = (df['Close'] + df['Range']).shift(shift)
    df['RL'] = (df['Close'] - df['Range']).shift(shift)

    df['return_cum'] = 1.0
    df['Signal'] = np.nan

    current_position = None
    df = df.reset_index()

    ops = []
    cls = []
    sl = 0

    for index, row in df.iterrows():
        rh = row['RH']
        rl = row['RL']
        price = row['Close']
        date = row['Date']
        # mw = row['above_mw']

        if (price > rh) and (current_position is None):
            current_position = 'long'
            ops.append([date, price, rh, rl])
            sl = rl
            tp = 2 * (price - sl)


        elif (price < rh and current_position == 'long') or (price < sl and current_position == 'long'):
            current_position = None
            close_type = 'sl'
            cls.append([date, price, close_type])

    # df['Signal'] = df['Signal'].fillna(method='ffill')

    pos = pd.concat([pd.DataFrame(ops, columns=['open_date', 'open_price', 'RH_open', 'RL_open']),
                     pd.DataFrame(cls, columns=['close_date', 'close_price', 'type'])], axis=1)
    pos['open_date'] = pd.to_datetime(pos['open_date'])
    pos['close_date'] = pd.to_datetime(pos['close_date'])

    size = 1500
    pos['open_size'] = size / pos['open_price']
    pos['pos_close_price'] = np.where(pos['close_price'] > pos['RL_open'], pos['close_price'], pos['RL_open'])
    pos['return_nom'] = pos['pos_close_price'] - pos['open_price']
    pos['return_perc'] = (pos['pos_close_price'] / pos['open_price']) - 1
    pos['return_nom1'] = pos['close_price'] - pos['open_price']
    pos['return_perc1'] = (pos['close_price'] / pos['open_price']) - 1
    pos['cum_return'] = pos['return_perc'].cumsum()

    pos['is_profit'] = np.where(pos['return_nom'] > 0, 'tp', 'sl')
    pos['close_type'] = np.where(pos['close_price'] > pos['RL_open'], 'algo', 'stop')
    pos['if_sl'] = np.where(pos['return_nom'] > -100, pos['return_nom'], -100)
    pos['if_sl_pos'] = pos['if_sl'] * pos['open_size']
    pos['sl_per'] = pos['if_sl'] / pos['open_price']

    return pos


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

def calc1(tick, per, inter, mov, window):
    df = getData(tick, per, inter)
    # df['r_var'] = df['Close'].rolling(mov).var()
    # df['Volatility'] = np.sqrt(df['r_var'])
    # df['Range'] = np.sqrt(mov / 365) * df['Volatility']
    # df['RH'] = (df['Close'] + df['Range']).shift(window)
    # df['RL'] = (df['Close'] - df['Range']).shift(window)
    df = bt(df,mov,window)

    return df


def kalman(tick,per,inter,sma):
    df = getData(tick,per,inter)
    df[f'sma_{sma}']=df['Close'].rolling(sma).mean()

    x = df['Close']
    kf = KalmanFilter(transition_matrices=[1],
                      observation_matrices=[1],
                      initial_state_mean=0,
                      initial_state_covariance=1,
                      observation_covariance=1,
                      transition_covariance=.0001)

    mean, cov = kf.filter(x.values)
    mean = pd.Series(mean.flatten(), index=x.index)
    df['kalman']=mean

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

        intrv = st.selectbox(
            "Zaman Aralığı",
            ('1d', '1h', '15m', '5m')
        )

        period = tfs[intrv]

        ma_w = st.number_input("Hareketli Ortalama", value=30)
        sf_w = st.number_input("Kaydırma Aralığı", value=3)

        df = calc(tick, period, intrv, ma_w, sf_w)
        # st.dataframe(df)
    with col2:
        st.write(f"Chart for {tick}")
        color_map = {
            'Close': 'yellow',
            'RH': 'green',
            'RL': 'red'
        }

        fig = px.line(df[-90:], x='Date', y=['Close', 'RH', 'RL'], markers=True, color_discrete_map=color_map)

        if intrv != '1d':
            if tick == "EURUSD=X" or tick == "GBPUSD=X" or tick == "DX=F":
                fig.update_xaxes(
                    rangebreaks=[
                        dict(bounds=["sat", "mon"])  # hide weekends
                    ])
            elif tick == "AVAX-USD" or tick == "ETH-USD" or tick == "BTC-USD":
                fig.update_xaxes(
                    rangebreaks=[]  # reset/remove rangebreaks for these tickers
                )
            else :
                fig.update_xaxes(
                    rangebreaks=[
                        dict(bounds=["sat", "mon"]),  # hide weekends
                        dict(bounds=[18, 9], pattern="hour")
                    ])

        fig.update_layout(xaxis_showspikes=True,
                          hovermode='x'
                          # 'x unified'
                          )

        st.plotly_chart(fig, use_container_width=True)


        pos = calc1(tick, period, intrv, ma_w, sf_w)
        # st.dataframe(pos)
        st.write(f"backest result = %{(pos['return_perc'].cumsum().iloc[-1])*100}")


with st.container():
    st.write(f"{tick}")
    mvg_avg = st.number_input("Hareketli ortalama", value=30)
    df=kalman(tick,period,intrv,mvg_avg)

    df=df[mvg_avg:]

    # Create a candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                         open=df['Open'],
                                         high=df['High'],
                                         low=df['Low'],
                                         close=df['Close'],
                                         name='Candlestick')])

    # fig = go.Figure()

    # Add SMA line to the chart
    fig.add_trace(go.Scatter(x=df['Date'], y=df[f'sma_{mvg_avg}'], mode='lines', name=f'SMA_{mvg_avg}',line=dict(color='yellow')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df[f'kalman'], mode='lines', name='kalman', line=dict(color='red')))

    # Update the layout
    fig.update_layout(title='Stock Price Data with SMA',
                      xaxis_title='Date',
                      yaxis_title='Price',
                      xaxis_rangeslider_visible=False,height=800,
                      xaxis_showspikes=True,
                      hovermode='x'
                      )

    st.plotly_chart(fig, use_container_width=True)