import streamlit as st
import pandas as pd
import plotly.express as px
import time
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (TRAVA TOTAL)
# ==========================================
st.set_page_config(page_title="TV Gestão à Vista", page_icon="📺", layout="wide")

# CSS para matar o scroll e esconder qualquer "fantasma" que tente fugir pro rodapé
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* Trava a tela para não ter scroll de jeito nenhum */
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden;
        height: 100vh;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

# CRIAMOS UM ESPAÇO VAZIO QUE OCUPA A TELA TODA
placeholder = st.empty()

# ==========================================
# 2. CARREGAMENTO DE DADOS
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['FUNCAO_BUSCA'] = df['FUNÇÃO'].str.upper().str.strip()
    
    colunas_texto = ['NOME', 'TURNO', 'FUNÇÃO', 'FUNCAO_BUSCA']
    for col in df.columns:
        if col not in colunas_texto:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if 'Jornada' in col: 
                df.loc[(df[col] > 0) & (df[col] <= 2.0), col] = df[col] * 100
    return df

# ==========================================
# 3. LÓGICA DO CARROSSEL
# ==========================================
try:
    df_base = carregar_dados()
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26) if hoje.day >= 26 else datetime.date(hoje.year if hoje.month > 1 else hoje.year - 1, hoje.month - 1 if hoje.month > 1 else 12, 26)
    
    agora_brasil = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    turnos_permitidos = ['T3'] if (18 <= agora_brasil.hour or agora_brasil.hour < 6) else ['T1', 'T2']
    df = df_base[df_base['TURNO'].isin(turnos_permitidos)].copy()

    mapa_funcoes = {
        'SEPARADOR F': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'SEPARADOR G': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'CONFERENTE': ['Itens Conf.', 'Ressup.'], 
        'OPERADOR': ['Mov. Horizontal', 'Mov. Vert.'],
        'RAMPA': ['Itens Rampa']
    }

    lista_funcoes = list(mapa_funcoes.keys())
    if 'passo' not in st.session_state or st.session_state.passo >= len(lista_funcoes):
        st.session_state.passo = 0

    # TUDO O QUE FOR DESENHADO VAI DENTRO DESSE CONTAINER
    with placeholder.container():
        f_atual = lista_funcoes[st.session_state.passo]
        df_tela = df[df['FUNCAO_BUSCA'] == f_atual].copy()
        inds_f = mapa_funcoes[f_atual]
        
        # Se não tem dados, pula para o próximo
        if not any(df_tela[ind].sum() > 0 for ind in inds_f if ind in df_tela.columns):
            st.session_state.passo = (st.session_state.passo + 1) % len(lista_funcoes)
            st.rerun()

        # Cabeçalho
        st.markdown(f"<h1 style='text-align: center; color: #ff4b4b; font-size: 3.5rem;'>{f_atual}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray;'>📅 {dt_inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

        colunas_ui = st.columns(3)
        blocos = []
        for ind in inds_f:
            df_ind = df_tela[df_tela[ind] > 0].copy()
            if not df_ind.empty:
                df_ind = df_ind.sort_values(by=ind, ascending=False).drop_duplicates(subset=['NOME'])
                blocos.append({"titulo": ind, "data": df_ind.head(15).sort_values(by=ind, ascending=True), "ind": ind})
                if len(df_ind) > 15:
                    blocos.append({"titulo": f"{ind} (Cont.)", "data": df_ind.iloc[15:30].sort_values(by=ind, ascending=True), "ind": ind})

        # Desenha exatamente nos 3 slots
        # Ajuste de Cores: T1 e T2 Amarelo, T3 Azul Escuro
        mapa_cores = {'T1': '#ffcc00', 'T2': '#ffcc00', 'T3': '#004aad', 'FANTASMA': 'rgba(0,0,0,0)'}
        for i in range(3):
            with colunas_ui[i]:
                if i < len(blocos):
                    b = blocos[i]
                    st.markdown(f"<h3 style='text-align: center;'>{b['titulo']}</h3>", unsafe_allow_html=True)
                    
                    # Preenchimento de barras (Fantasmas)
                    df_graf = b['data']
                    qtd = 15 - len(df_graf)
                    if qtd > 0:
                        fantasmas = pd.DataFrame({'NOME': ["\u200B"*(x+1) for x in range(qtd)], b['ind']: [0.0]*qtd, 'TURNO': ['FANTASMA']*qtd})
                        df_graf = pd.concat([fantasmas, df_graf], ignore_index=True)

                    txt = df_graf[b['ind']].apply(lambda x: "" if x == 0 else (f"{x:.0f}%" if 'Jornada' in b['ind'] else f"{x:.0f}"))
                    fig = px.bar(df_graf, x=b['ind'], y="NOME", orientation='h', text=txt)
                    
                    fig.update_yaxes(type='category', tickfont=dict(size=14))
                    
                    # Ajuste: yaxis_title=None remove a palavra "NOME" do eixo vertical
                    fig.update_layout(
                        height=600, 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        paper_bgcolor="rgba(0,0,0,0)", 
                        showlegend=False, 
                        margin=dict(l=5, r=40, t=5, b=5), 
                        bargap=0.3,
                        yaxis_title=None 
                    )
                    
                    fig.update_xaxes(visible=False)
                    fig.update_traces(marker_color=df_graf['TURNO'].map(mapa_cores).fillna('gray').tolist(), textposition="outside", cliponaxis=False)
                    st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True}, key=f"slot_{i}")
                else:
                    st.empty() # Coluna vazia real

    time.sleep(10)
    st.session_state.passo = (st.session_state.passo + 1) % len(lista_funcoes)
    st.rerun()

except Exception as e:
    st.error(f"Erro: {e}")
    time.sleep(10)
    st.rerun()
