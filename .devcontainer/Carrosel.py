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
# 3. LÓGICA DE FILTROS E BUSCA INTELIGENTE
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

    lista_funcoes = ['CONFERENTE', 'OPERADOR', 'RAMPA', 'SEPARADOR F', 'SEPARADOR G']
    lista_indicadores = ['Itens Sep', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Mov. Horizontal', 'Mov. Vert.']

    combinacoes = []
    for f in lista_funcoes:
        for ind in lista_indicadores:
            combinacoes.append({"funcao": f, "indicador": ind})

    if 'passo' not in st.session_state:
        st.session_state.passo = 0

    total_comb = len(combinacoes)
    combinacao_valida = False
    tentativas = 0

    while tentativas < total_comb:
        conf_atual = combinacoes[st.session_state.passo]
        f_atual = conf_atual['funcao']
        i_atual = conf_atual['indicador']

        df_tela = df[df['FUNCAO_BUSCA'] == f_atual].copy()
        df_tela = df_tela[df_tela[i_atual] > 0] 

        if not df_tela.empty:
            combinacao_valida = True
            break

        st.session_state.passo = (st.session_state.passo + 1) % total_comb
        tentativas += 1

    # ==========================================
    # 4. CONSTRUÇÃO VISUAL DA TV
    # ==========================================
    
    if not combinacao_valida:
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem; margin-top: 15%;'>⏳ {periodo_nome}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.5rem; color: #004aad;'>📅 Período: {dt_inicio_str} até {dt_fim_str}</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: gray;'>Aguardando os primeiros registros de produtividade...</h2>", unsafe_allow_html=True)
    
    else:
        st.markdown(f"""
            <div style='text-align: center;'>
                <h1 style='font-size: 3.2rem; margin-bottom: 0;'>{i_atual} - <span style='color: #ff4b4b;'>{f_atual}</span></h1>
                <p style='font-size: 1.4rem; color: #004aad; margin-top: 5px;'><b>📅 Período: de {dt_inicio_str} até {dt_fim_str}</b> | {periodo_nome}</p>
            </div>
        """, unsafe_allow_html=True)

        df_tela = df_tela.sort_values(by=i_atual, ascending=False).head(15)
        df_tela = df_tela.sort_values(by=i_atual, ascending=True)

        if i_atual == "Jornada Líq.":
            txt = df_tela[i_atual].apply(lambda x: f"{x:.0f}%")
        else:
            txt = df_tela[i_atual].apply(lambda x: f"{x:.0f}")

        fig = px.bar(
            df_tela, 
            x=i_atual, 
            y="NOME", 
            color="TURNO", 
            orientation='h',
            text=txt,
            color_discrete_map={'T1': '#004aad', 'T2': '#ffcc00', 'T3': '#ff4b4b'}
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None, yaxis_title=None,
            height=700,
            showlegend=True,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        # Limpa o eixo X invisível no fundo
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)

        # =========================================================
        # 🛠️ ÁREA DE AJUSTES MANUAIS DE TAMANHO
        # =========================================================
        
        fig.update_yaxes(tickfont=dict(size=22))
        largura_da_barra = 0.2 
        fig.update_traces(
            textfont_size=26, 
            textposition="outside", 
            width=largura_da_barra
        )
        
        # =========================================================

        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 5. TIMER E AVANÇO
    # ==========================================
    time.sleep(20) 
    st.session_state.passo = (st.session_state.passo + 1) % total_comb
    st.rerun()

except Exception as e:
    st.error(f"Erro no sistema de TV: {e}")
    time.sleep(10)
    st.rerun()
