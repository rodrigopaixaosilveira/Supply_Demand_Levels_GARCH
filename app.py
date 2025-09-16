import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from arch import arch_model
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="📈 Stock OHLC + GARCH Bands", layout="wide")
st.title("📊 Supply & Demand bands based on GARCH")

# Sidebar: Select Market
market = st.sidebar.selectbox(
    "Select Market",
    [ "Crypto", "BR Market", "US Market"]
)

# Default tickers
if market == "US Market":
    default_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # Adicionada NVIDIA
elif market == "BR Market":
    default_tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]  # 5 ativos brasileiros
else:
    default_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD", "SOL-USD", "ADA-USD"]  # Pelo menos 5 cripto

selected_ticker = st.sidebar.selectbox("Select Ticker", default_tickers)
custom_ticker = st.sidebar.text_input("Or enter your own ticker from yFinancl:")

# Decide which ticker to use
ticker = custom_ticker.strip().upper() if custom_ticker else selected_ticker

# Sidebar: Ticker
#ticker = st.sidebar.selectbox("Select Ticker", default_tickers)

# Sidebar: Period and Interval
period = st.sidebar.selectbox(
    "Select Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
    index=3
)


# Download data
df = yf.download(ticker, period=period, interval="1d", progress=False)
df = df.xs(ticker, axis=1, level=1)

st.markdown("""
---
This chart uses **supply & demand bands based on volatility**.  
The original methodology was developed by **Leandro Guerra (Outspoken Market)**, available at [OM QuantLab](https://om-qs.com/quantlab/blog/1578/).  

This implementation is an adaptation by **Rodrigo Paixão Silveira**, applying the GARCH model to project monthly and weekly bands.  

See the full code at [Volatility-Adapted S&D bands: Modified Method](https://www.kaggle.com/code/rodrigopaixao/volatility-adapted-s-d-bands-modified-method)  
Instagram: **@rodrigoquantdev**
""")


if df.empty:
    st.error("⚠️ No data available for this ticker, period or interval.")
else:
    df.index = df.index.tz_localize(None)  # Remove timezone if exists
    df.reset_index(inplace=True)
    df.rename(columns={'Date': 'Date'}, inplace=True)

    # -------------------------------------------
    # Preprocessing & GARCH
    # -------------------------------------------
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df.dropna(inplace=True)

    # GARCH(1,1) Volatility Estimation
    garch_model = arch_model(df['Log_Returns'] * 100, vol='Garch', p=1, q=1, dist='Normal')
    garch_result = garch_model.fit(disp='off')
    df['garch'] = garch_result.conditional_volatility / 100  # Convert back to decimal

    # Monthly Bands
    df['Month'] = df['Date'].dt.to_period('M')
    monthly_ref = df.groupby('Month').agg(
        reference_price=('Close', 'last'),
        monthly_vol=('garch', 'last')
    ).reset_index()
    monthly_ref['Next_Month'] = monthly_ref['Month'] + 1
    df = df.merge(
        monthly_ref[['Next_Month', 'reference_price', 'monthly_vol']],
        left_on='Month',
        right_on='Next_Month',
        how='left'
    )
    for d in range(1, 6):
        df[f'upper_garch_1m_{d}d'] = (1 + d * df['monthly_vol']) * df['reference_price']
        df[f'lower_garch_1m_{d}d'] = (1 - d * df['monthly_vol']) * df['reference_price']
    df['garch_mid_m'] = (df['upper_garch_1m_1d'] + df['lower_garch_1m_1d']) / 2
    df.drop(['Month', 'Next_Month', 'reference_price'], axis=1, inplace=True)

    # Weekly Bands
    df['Week'] = df['Date'].dt.to_period('W')
    weekly_ref = df.groupby('Week').agg(
        reference_price=('Close', 'last'),
        weekly_vol_garch=('garch', 'last')
    ).reset_index()
    weekly_ref['Next_Week'] = weekly_ref['Week'] + 1
    df = df.merge(
        weekly_ref[['Next_Week', 'reference_price', 'weekly_vol_garch']],
        left_on='Week',
        right_on='Next_Week',
        how='left'
    )
    for d in range(1, 6):
        df[f'upper_garch_1w_{d}d'] = (1 + d * df['weekly_vol_garch']) * df['reference_price']
        df[f'lower_garch_1w_{d}d'] = (1 - d * df['weekly_vol_garch']) * df['reference_price']
    df['garch_mid_s'] = (df['upper_garch_1w_1d'] + df['lower_garch_1w_1d']) / 2
    df.drop(['Week', 'Next_Week', 'reference_price'], axis=1, inplace=True)
    df.set_index('Date', inplace=True)

    # -------------------------------------------
    # Plotting
    # -------------------------------------------
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.7]
    )

    # Add OHLC candles
    for row in [1, 2]:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
            name='OHLC'
        ), row=row, col=1)

    # Colors for bands
    color_map = {2: '#808080', 4: '#6B2C91'}

    # Monthly bands
    for deviation in [2, 4]:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f'upper_garch_1m_{deviation}d'],
            mode='lines',
            name=f'Upper GARCH 1M {deviation}D',
            line=dict(color=color_map[deviation])
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f'lower_garch_1m_{deviation}d'],
            mode='lines',
            name=f'Lower GARCH 1M {deviation}D',
            line=dict(color=color_map[deviation])
        ), row=1, col=1)

    # Weekly bands
    for deviation in [2, 4]:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f'upper_garch_1w_{deviation}d'],
            mode='lines',
            name=f'Upper GARCH 1W {deviation}D',
            line=dict(color=color_map[deviation])
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[f'lower_garch_1w_{deviation}d'],
            mode='lines',
            name=f'Lower GARCH 1W {deviation}D',
            line=dict(color=color_map[deviation])
        ), row=2, col=1)

    # Midlines
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['garch_mid_m'],
        mode='lines',
        name='Mid GARCH Monthly',
        line=dict(color='black')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['garch_mid_s'],
        mode='lines',
        name='Mid GARCH Weekly',
        line=dict(color='black')
    ), row=2, col=1)

    fig.update_layout(
        title=f"Volatility-Based Bands with GARCH for {ticker} | Monthly bands(first) & Weekly bands(second)",
        xaxis=dict(rangeslider=dict(visible=False)),
        xaxis2=dict(rangeslider=dict(visible=False)),
        yaxis=dict(title="Price"),
        template="plotly_white",
        hovermode='x unified',
        height=800
    )

    st.plotly_chart(fig, use_container_width=True)


