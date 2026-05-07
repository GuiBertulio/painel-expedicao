import streamlit as st
import pandas as pd
import plotly.express as px
import time
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (MODO TV)
# ==========================================
st.set_page_config(page_title="TV Gestão à Vista", page_icon="📺", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO E LIMPEZA DE DADOS
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    df = df[[col for col in colunas_desejadas if col in df.columns]]
    
    cols_num = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['FUNCAO_BUSCA'] = df['FUNÇÃO'].str.upper().str.strip()
            
    return df

# ==========================================
# 3. LÓGICA DE FILTROS E DICIONÁRIO DE METAS
# ==========================================
try:
    df_base = carregar_dados()

    hoje = datetime.date.today()
    if hoje.day >= 26:
        dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    else:
        mes_ant = hoje.month - 1 if hoje.month > 1 else 12
        ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
        dt_inicio = datetime.date(ano_ant, mes_ant, 26)
    
    dt_inicio_str = dt_inicio.strftime('%d/%m/%Y')
    dt_fim_str = hoje.strftime('%d/%m/%Y')

    agora_brasil = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    hora_atual = agora_brasil.hour
    
    if 18 <= hora_atual or hora_atual < 6:
        turnos_permitidos = ['T3']
        periodo_nome = "🌙 Turno da Noite (T3)"
    else:
        turnos_permitidos = ['T1', 'T2']
        periodo_nome = "☀️ Turnos do Dia (T1 e T2)"

    df = df_base[df_base['TURNO'].isin(turnos_permitidos)].copy()

    # ---------------------------------------------------------
    # 🧠 CÉREBRO DA TV: MAPEAMENTO DE FUNÇÃO X INDICADORES
    # ---------------------------------------------------------
    mapa_funcoes = {
        'SEPARADOR F': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'SEPARADOR G': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'CONFERENTE': ['Itens Sep', 'Ressup.'], 
        'OPERADOR': ['Mov. Horizontal', 'Mov. Vert.'],
        'RAMPA': ['Itens Sep']
    }

    lista_funcoes = list(mapa_funcoes.keys())

    # --- A TRAVA DE SEGURANÇA (CORREÇÃO DO ERRO) ---
    # Se a memória lembrar de um passo muito alto, ele zera e recomeça!
    if 'passo' not in st.session_state or st.session_state.passo >= len(lista_funcoes):
        st.session_state.passo = 0
    # -----------------------------------------------

    total_funcoes = len(lista_funcoes)
    combinacao_valida = False
    tentativas = 0

    while tentativas < total_funcoes:
        f_atual = lista_funcoes[st.session_state.passo]
        
        df_tela = df[df['FUNCAO_BUSCA'] == f_atual].copy()
        
        indicadores_da_funcao = mapa_funcoes[f_atual]
        tem_dados = False
        for ind in indicadores_da_funcao:
            if ind in df_tela.columns and df_tela[ind].sum() > 0:
                tem_dados = True
                break

        if tem_dados:
            combinacao_valida = True
            break

        st.session_state.passo = (st.session_state.passo + 1) % total_funcoes
        tentativas += 1

    # ==========================================
    # 4. CONSTRUÇÃO VISUAL DA TV (COLUNAS)
    # ==========================================
    
    if not combinacao_valida:
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem; margin-top: 15%;'>⏳ {periodo_nome}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.5rem; color: #004aad;'>📅 Período: {dt_inicio_str} até {dt_fim_str}</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: gray;'>Aguardando os primeiros registros de produtividade...</h2>", unsafe_allow_html=True)
    
    else:
        st.markdown(f"""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h1 style='font-size: 4rem; margin-bottom: 0; color: #ff4b4b; text-transform: uppercase;'>{f_atual}</h1>
                <p style='font-size: 1.2rem; color: gray; margin-top: 0px;'><b>📅 de {dt_inicio_str} até {dt_fim_str}</b> | {periodo_nome}</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        colunas_ui = [col1, col2, col3]
        indicadores_para_mostrar = mapa_funcoes[f_atual]

        mapa_cores = {'T1': '#004aad', 'T2': '#ffcc00', 'T3': '#ff4b4b'}

        for i in range(3):
            with colunas_ui[i]:
                if i < len(indicadores_para_mostrar):
                    ind_atual = indicadores_para_mostrar[i]
                    
                    df_col = df_tela[df_tela[ind_atual] > 0].copy()
                    
                    if df_col.empty:
                        st.markdown(f"<h3 style='text-align: center;'>{ind_atual}</h3>", unsafe_allow_html=True)
                        st.info("Sem dados.")
                        continue
                    
                    df_col = df_col.sort_values(by=ind_atual, ascending=False).head(15)
                    df_col = df_col.sort_values(by=ind_atual, ascending=True)

                    if ind_atual == "Jornada Líq.":
                        txt = df_col[ind_atual].apply(lambda x: f"{x:.0f}%")
                    else:
                        txt = df_col[ind_atual].apply(lambda x: f"{x:.0f}")

                    st.markdown(f"<h2 style='text-align: center; margin-bottom: 0px;'>{ind_atual}</h2>", unsafe_allow_html=True)

                    fig = px.bar(
                        df_col, x=ind_atual, y="NOME", orientation='h', text=txt
                    )

                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_title=None, yaxis_title=None,
                        height=650, showlegend=False,
                        margin=dict(l=5, r=5, t=5, b=5) 
                    )
                    
                    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)

                    cores_aplicadas = df_col['TURNO'].map(mapa_cores).fillna('gray').tolist()

                    fig.update_yaxes(tickfont=dict(size=14)) 
                    largura_da_barra = 0.5 
                    fig.update_traces(
                        marker_color=cores_aplicadas, 
                        textfont_size=16, 
                        textposition="outside", 
                        width=largura_da_barra
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.empty()

    # ==========================================
    # 5. TIMER E AVANÇO
    # ==========================================
    time.sleep(15) 
    st.session_state.passo = (st.session_state.passo + 1) % total_funcoes
    st.rerun()

except Exception as e:
    st.error(f"Erro no sistema de TV: {e}")
    time.sleep(10)
    st.rerun()
