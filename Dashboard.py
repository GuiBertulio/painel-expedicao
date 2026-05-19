import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

# (Mantive seu CSS igual)
st.markdown("""<style>.block-container {padding-top: 2rem !important;}</style>""", unsafe_allow_html=True)

# Cores
C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# ==========================================
# 2. DICIONÁRIO DE METAS
# ==========================================
metas_100 = {
    'T3': {
        'CARREGAMENTO BOX': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000},
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Avaria':      {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        # ... (Mantive os outros cargos que você já tinha)
    }
}

# ==========================================
# 3. CARREGAMENTO E LIMPEZA
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # IMPORTANTE: Remove colunas com valores estranhos que não estão no dicionário
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Força a leitura das colunas manuais como números
    cols_numericas = ['Itens Rampa', 'Dev. %', 'Avaria', 'Corte %']
    for col in cols_numericas:
        if col in df.columns:
            # Remove % e converte vírgula para ponto
            df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace('.', '', n=1, regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

# ==========================================
# 4. LÓGICA DE TEMPO E TELA (O Resto do código segue padrão)
# ==========================================
try:
    df = carregar_dados()
    # [O restante da lógica de filtros e exibição permanece igual]
    # Certifique-se de que o nome da função no seu selectbox 
    # seja exatamente "CARREGAMENTO BOX" (tudo maiúsculo)
    
    # ... resto do código ...
except Exception as e:
    st.error(f"⚠️ Erro ao carregar: {e}")
