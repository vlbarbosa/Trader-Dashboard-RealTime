import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(
    page_title="Crypto Intelligence Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÕES DE EXTRAÇÃO (ETL) ---
def buscar_dados_binance(simbolo):
    # Minha lógica: Busco o preço instantâneo.
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"
    try:
        resposta = requests.get(url)
        return float(resposta.json()['price'])
    except:
        return 0.0

def buscar_historico(simbolo, intervalo="1d", limite=30):
    # Minha lógica: O parâmetro {intervalo} entra na URL para definir se quero velas de dia ou horas
    url = f"https://api.binance.com/api/v3/klines?symbol={simbolo}&interval={intervalo}&limit={limite}"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        df = pd.DataFrame(dados, columns=[
            'tempo_abertura', 'open', 'high', 'low', 'close', 'volume', 
            'tempo_fechamento', 'quote_asset_volume', 'trades', 'base_asset_volume', 'ignore', 'ignore'
        ])
        df['data'] = pd.to_datetime(df['tempo_abertura'], unit='ms')
        cols_numericas = ['open', 'high', 'low', 'close']
        df[cols_numericas] = df[cols_numericas].astype(float)
        return df
    except:
        return pd.DataFrame()

# --- INTERFACE E LÓGICA DE NEGÓCIO ---

st.sidebar.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)
st.sidebar.title("🎛️ Setup do Trader")

# Mapeamento de Moedas
opcoes_moedas = {"Bitcoin (BTC)": "BTCUSDT", "Ethereum (ETH)": "ETHUSDT", "Solana (SOL)": "SOLUSDT"}
nome_moeda = st.sidebar.selectbox("Ativo:", list(opcoes_moedas.keys()))
codigo_moeda = opcoes_moedas[nome_moeda]

st.title(f"📊 Análise Técnica: {nome_moeda}")

# Buscando dados
preco_atual = buscar_dados_binance(codigo_moeda)
df_historico = buscar_historico(codigo_moeda)

# --- MINHA LÓGICA DE INTELIGÊNCIA (MÉDIA MÓVEL) ---
if not df_historico.empty:
    df_historico['media_movel'] = df_historico['close'].rolling(window=7).mean()
    ultima_media = df_historico['media_movel'].iloc[-1]
    
    if preco_atual > ultima_media:
        tendencia = "ALTA (Bullish) 🐂"
        cor_tendencia = "off"
    else:
        tendencia = "BAIXA (Bearish) 🐻"
        cor_tendencia = "inverse"

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Preço Atual", f"$ {preco_atual:,.2f}")
if not df_historico.empty:
    col2.metric("Média de 7 Dias", f"$ {ultima_media:,.2f}")
    
    if cor_tendencia == "off":
        col3.success(f"Tendência: **{tendencia}**")
    else:
        col3.error(f"Tendência: **{tendencia}**")

st.markdown("---")

# --- GRÁFICO AVANÇADO ---
st.subheader("📈 Gráfico de Tendência + Média Móvel")

if not df_historico.empty:
    fig = go.Figure()

    # Adiciono as Velas
    fig.add_trace(go.Candlestick(
        x=df_historico['data'],
        open=df_historico['open'],
        high=df_historico['high'],
        low=df_historico['low'],
        close=df_historico['close'],
        name="Preço Real"
    ))

    # Adiciono a Linha de Média
    fig.add_trace(go.Scatter(
        x=df_historico['data'],
        y=df_historico['media_movel'],
        mode='lines',
        name='Média 7 Dias',
        line=dict(color='yellow', width=2)
    ))

    fig.update_layout(
        title=f"Evolução: {nome_moeda}",
        yaxis_title="Preço (US$)",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=500
    )

    # CORREÇÃO AQUI: Removi o 'use_container_width=True' para silenciar o aviso.
    st.plotly_chart(fig)
else:
    st.warning("Aguardando dados da API...")