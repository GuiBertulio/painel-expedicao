import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .card-meta {
        background-color: var(--background-color); 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 1px 1px 5px rgba(0,0,0,0.3); 
        margin-bottom: 15px;
        border-left: 8px solid #ccc; 
        border-top: 1px solid var(--secondary-background-color);
        border-right: 1px solid var(--secondary-background-color);
        border-bottom: 1px solid var(--secondary-background-color);
    }
    .texto-card-principal { font-size: 42px; font-weight: 900; line-height: 1.1; }
    .texto-card-titulo { font-size: 20px; font-weight: 900; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

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
        'SEPARADOR F': {
            'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 75, 't100': 80, 't120': 85},
            'Itens Sep':    {'tipo': '>', 'prop': True,  'v100': 150.0, 't50': 7000, 't100': 9000, 't120': 11000},
            'Itens/Hora':   {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 60, 't100': 75, 't120': 90}
        },
        'LÍDER': {
            'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 65, 't100': 75, 't120': 85},
            'Dev. %':           {'tipo': '<', 'prop': False, 'v100': 240.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Itens/Hora Eq.':   {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 60, 't100': 75, 't120': 90}
        }
    }
    # ... (Mantenha os outros turnos iguais, removi o resto só para caber aqui)
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # Limpeza numérica
    col_numericas = ['Itens Rampa', 'Dev. %', 'Avaria', 'Corte %', 'Itens Sep', 'Itens/Hora', 'Itens Conf.']
    for col in col_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '.').str.replace('.', '', n=1, regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# ==========================================
# 4. EXIBIÇÃO E TABELA (SEM COLUNA HORAS)
# ==========================================
try:
    df = carregar_dados()
    # ... (Seu código de filtros segue aqui) ...

    # TABELA DINÂMICA (REMOVIDA A COLUNA 'Horas')
    st.markdown("### 📋 Tabela de Produtividade Consolidada")
    df_tabela = df.sort_values(by='NOME', ascending=True).copy()
    
    # Aqui eu defini explicitamente as colunas que você quer ver (SEM HORAS)
    colunas_finais = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO'] + [c for c in df_tabela.columns if c not in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Horas']]
    df_tabela = df_tabela[colunas_finais]

    st.dataframe(df_tabela, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")
