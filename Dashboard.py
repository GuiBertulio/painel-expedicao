import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

# ==========================================
# 2. DICIONÁRIO DE METAS (Estrutura Segura)
# ==========================================
metas_100 = {
    'T3': {
        'CARREGAMENTO BOX': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000},
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Avaria':      {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'SEPARADOR F': {
            'Itens Sep':    {'tipo': '>', 'prop': True,  'v100': 150.0, 't50': 7000, 't100': 9000, 't120': 11000}
        }
    }
}

# ==========================================
# 3. CARREGAMENTO DE DADOS (Blindado)
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    try:
        df = pd.read_csv(link_csv)
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

# ==========================================
# 4. EXIBIÇÃO
# ==========================================
df = carregar_dados()
if not df.empty:
    st.title("Dashboard Funcionando")
    st.write(df.head())
else:
    st.warning("O arquivo está vazio ou inacessível.")
