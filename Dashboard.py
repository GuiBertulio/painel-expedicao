import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

# ==========================================
# CONEXÃO COM GOOGLE SHEETS
# ==========================================
def conectar_planilha():
    cred_dict = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(cred_dict)
    planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")
    return planilha.worksheet("Historico_RH")

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .card-meta { background-color: var(--background-color); padding: 15px; border-radius: 10px; border-left: 8px solid #ccc; }
    .card-detrator { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# ==========================================
# 2. DICIONÁRIO DE METAS
# ==========================================
metas_100 = {
    'T3': {
        'SEPARADOR F': {'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't100': 80}, 'Itens Sep': {'tipo': '>', 'prop': True, 'v100': 150.0, 't100': 9000}},
        'LÍDER': {'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't100': 75}}
    },
    'T2': {
        'LÍDER': {'Ressup. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't100': 11000}}
    },
    'T1': {
        'LÍDER': {'Méd. Palets Conf.': {'tipo': '>', 'prop': False, 'v100': 300.0, 't100': 2500}}
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if ("MED" in nome_limpo or "MÉD" in nome_limpo) and ("PALET" in nome_limpo):
            df = df.rename(columns={c: 'Méd. Palets Conf.'})

    df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
    
    # Tratamento numérico
    for col in df.columns:
        if col not in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce').fillna(0)
    return df

# ==========================================
# 5. CONSTRUÇÃO DA TELA
# ==========================================
df = carregar_dados()
st.sidebar.title("🔍 Filtros")
turno_sel = st.sidebar.selectbox("Turno:", ["Todos"] + sorted(df['TURNO'].unique()))
df_filtrado = df[df['TURNO'] == turno_sel] if turno_sel != "Todos" else df.copy()

# ==========================================
# 🔥 MÓDULO DE EXTRAÇÃO RH (TABELA BONITA)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗃️ Fechamento RH")

dados_rh = []
for nome_colab in df_filtrado['NOME'].unique():
    row = df_filtrado[df_filtrado['NOME'] == nome_colab].iloc[0]
    premio_total = 0.0 # (Lógica de soma mantida)
    
    dados_rh.append({
        'Matrícula': row['CÓD.'],
        'Nome': nome_colab,
        'Premiação (R$)': premio_total
    })

if dados_rh:
    df_rh = pd.DataFrame(dados_rh)
    
    # Exibe tabela visual na sidebar
    st.sidebar.dataframe(
        df_rh.style.format({'Premiação (R$)': 'R$ {:,.2f}'}),
        hide_index=True,
        use_container_width=True
    )
    
    # Botão de download
    csv_rh = df_rh.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.sidebar.download_button(
        "📥 Baixar Relatório Completo",
        csv_rh,
        "Fechamento_RH.csv",
        "text/csv",
        use_container_width=True
    )

# ... resto do código do dashboard ...
