# app.py
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Título do app
st.title("Gráfico OHLC de Ativos")

# Lista de ativos (exemplos)
ativos = ['AAPL', 'GOOGL', 'MSFT', 'BTC-USD', 'ETH-USD']
ativo_selecionado = st.selectbox("Selecione o ativo:", ativos)

# Período de dados
dias = st.slider("Quantidade de dias:", min_value=7, max_value=365, value=30)
data_final = datetime.today()
data_inicial = data_final - timedelta(days=dias)

# Baixando dados do ativo
dados = yf.download(ativo_selecionado, start=data_inicial, end=data_final)

# Verificar se há dados
if dados.empty:
    st.warning("Não foi possível obter os dados do ativo selecionado.")
else:
    # Criando gráfico OHLC
    fig = go.Figure(data=[go.Ohlc(
        x=dados.index,
        open=dados['Open'],
        high=dados['High'],
        low=dados['Low'],
        close=dados['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name=ativo_selecionado
    )])

    fig.update_layout(
        title=f"Gráfico OHLC - {ativo_selecionado}",
        xaxis_title="Data",
        yaxis_title="Preço",
        xaxis_rangeslider_visible=False
    )

    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
