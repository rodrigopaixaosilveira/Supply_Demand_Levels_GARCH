import streamlit as st
import yfinance as yf
import plotly.graph_objs as go

st.set_page_config(page_title="📈 Stock OHLC Viewer", layout="wide")
st.title("📊 Stock OHLC Chart Viewer")

# Sidebar: Market selection
market = st.sidebar.selectbox(
    "Select Market",
    ["US Market", "Indian Market", "Crypto"]
)

if market == "US Market":
    default_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
elif market == "Indian Market":
    default_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "TATASTEEL.NS"]
else:
    default_tickers = ["BTC-USD", "ETH-USD", "DOGE-USD"]

# Sidebar: Select single ticker
ticker = st.sidebar.selectbox(
    "Select Ticker",
    options=default_tickers
)

# Sidebar: Time controls
period = st.sidebar.selectbox(
    "Select Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
    index=1
)
interval = st.sidebar.selectbox(
    "Select Interval",
    ["1d", "1wk", "1mo"],
    index=0
)

# Fetch data
try:
    df = yf.download(ticker, period=period, interval=interval, progress=False)

    if df.empty:
        st.error("⚠️ No data found. Try different ticker or period/interval.")
    else:
        # OHLC Chart
        fig = go.Figure(data=[go.Ohlc(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
            name=ticker
        )])

        fig.update_layout(
            title=f"OHLC Chart for {ticker}",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark",
            hovermode='x unified',
            rangeslider=dict(visible=False)
        )

        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error fetching data: {e}")
