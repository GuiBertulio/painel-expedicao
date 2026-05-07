import streamlit as st
import pandas as pd
import plotly.express as px
import time
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (MODO TV)
# ==========================================
st.set_page_config(page_title="TV Expedição", page_icon="📺", layout="wide")

# CSS para esconder menus do Streamlit e deixar em tela cheia limpa
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO DOS DADOS DA NUVEM
# ==========================================
# Tempo de cache menor (3 minutos) para a TV sempre pegar dados novos sozinha
@st.cache_data(ttl=180) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        pass 
    
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    colunas_novas = ['Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    for col in colunas_novas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    # Filtro Sênior Blindado
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'Ressup.', 'Mov. Vert.']):
        cols_para_testar = ['Itens Sep', 'Horas', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
        for c in cols_para_testar:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        df = df[
            (df['Itens Sep'] > 0) | 
            (df['Horas'] > 0) | 
            (df['Ressup.'] > 0) | 
            (df['Ressup. Eq.'] > 0) | 
            (df['Mov. Horizontal'] > 0) | 
            (df['Mov. Vert.'] > 0)
        ]
        
    # --- NOVO: Juntando Nome e Função para mostrar na TV ---
    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['NOME_FUNCAO'] = df['NOME'] + " (" + df['FUNÇÃO'] + ")"
            
    return df

# ==========================================
# 3. MOTOR DO CARROSSEL
# ==========================================
try:
    df = carregar_dados()

    # Lista dos indicadores que vão ficar rodando na tela
    indicadores = ["Itens Sep", "Itens/Hora", "Jornada Líq.", "Horas", "Ressup.", "Ressup. Eq.", "Mov. Horizontal", "Mov. Vert."]

    # Cria uma memória para o Streamlit saber em qual indicador estamos
    if 'indice_carrossel' not in st.session_state:
        st.session_state.indice_carrossel = 0

    # Puxa o indicador atual baseado na memória
    indicador_atual = indicadores[st.session_state.indice_carrossel]

    # ==========================================
    # 4. CONSTRUÇÃO DA TELA DA TV
    # ==========================================
    st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>📺 Desempenho em Tempo Real: <span style='color: #ff4b4b;'>{indicador_atual}</span></h1>", unsafe_allow_html=True)
    st.divider()
    
    # Filtra apenas quem tem resultado maior que zero naquele indicador específico
    df_grafico = df[df[indicador_atual] > 0].copy()
    
    if df_grafico.empty:
        st.warning(f"Nenhum dado registrado para {indicador_atual} no momento.")
    else:
        # Ordena do maior para o menor (Ranking)
        df_grafico = df_grafico.sort_values(by=indicador_atual, ascending=True)
        
        # Formatação dos textos nas barras
        if indicador_atual == "Jornada Líq.":
            textos_barras = df_grafico[indicador_atual].apply(lambda x: f"{x:.0f}%")
        elif indicador_atual == "Horas":
            textos_barras = df_grafico[indicador_atual].apply(lambda x: f"{x:.2f}h")
        else:
            textos_barras = df_grafico[indicador_atual].apply(lambda x: f"{x:.0f}")
        
        # Gráfico Gigante
        fig = px.bar(
            df_grafico, 
            x=indicador_atual, 
            y="NOME_FUNCAO", # Usa a nossa coluna nova que tem Nome + Função
            color="TURNO", 
            orientation='h',
            text=textos_barras
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None,
            height=750, # Altura maior para preencher a TV
            showlegend=True,
            font=dict(size=16) # Letra maior para ler de longe
        )
        
        # Aumenta a fonte dos números dentro das barras
        fig.update_traces(textfont_size=20, textposition="outside")
        
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 5. O TIMER DO REFRESH (A MÁGICA ACONTECE AQUI)
    # ==========================================
    # Mostra uma barrinha de progresso visual simulada no rodapé (opcional, só para ficar chique)
    st.markdown("<p style='text-align: center; color: gray;'>Próximo indicador em 60 segundos...</p>", unsafe_allow_html=True)
    
    # Para o código por 60 segundos
    time.sleep(60)
    
    # Avança para o próximo indicador (se chegar no final da lista, volta pro começo)
    st.session_state.indice_carrossel = (st.session_state.indice_carrossel + 1) % len(indicadores)
    
    # Força a página a recarregar sozinha
    st.rerun()

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro: {e}")
