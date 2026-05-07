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
        padding-top: 1rem !important;
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
    
    cols_num = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['NOME_FUNCAO'] = df['NOME'] + " (" + df['FUNÇÃO'] + ")"
        df['FUNCAO_BUSCA'] = df['FUNÇÃO'].str.upper().str.strip()
            
    return df

# ==========================================
# 3. LÓGICA DE FILTROS E BUSCA INTELIGENTE
# ==========================================
try:
    df_base = carregar_dados()

    # --- A. FILTRO POR HORÁRIO ---
    hora_atual = datetime.datetime.now().hour
    if 18 <= hora_atual or hora_atual < 6:
        turnos_permitidos = ['T3']
        periodo_nome = "🌙 Turno da Noite (T3)"
    else:
        turnos_permitidos = ['T1', 'T2']
        periodo_nome = "☀️ Turnos do Dia (T1 e T2)"

    df = df_base[df_base['TURNO'].isin(turnos_permitidos)].copy()

    # --- B. LISTA DE EXIBIÇÃO ---
    lista_funcoes = ['CONFERENTE', 'OPERADOR', 'RAMPA', 'SEPARADOR']
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

    # --- C. MOTOR DE BUSCA ANTECIPADA (O PULO AUTOMÁTICO) ---
    # Fica testando até achar uma tela que tenha dados ou até esgotar as opções
    while tentativas < total_comb:
        conf_atual = combinacoes[st.session_state.passo]
        f_atual = conf_atual['funcao']
        i_atual = conf_atual['indicador']

        df_tela = df[df['FUNCAO_BUSCA'].str.contains(f_atual, na=False)].copy()
        df_tela = df_tela[df_tela[i_atual] > 0] 

        if not df_tela.empty:
            combinacao_valida = True
            break # Achou uma tela com dados! Sai do loop de busca.

        # Se a tela estaria vazia, pula silenciosamente para a próxima
        st.session_state.passo = (st.session_state.passo + 1) % total_comb
        tentativas += 1

    # ==========================================
    # 4. CONSTRUÇÃO VISUAL DA TV
    # ==========================================
    
    # Se todo mundo do galpão estiver zerado em tudo (início de expediente)
    if not combinacao_valida:
        st.markdown(f"<h1 style='text-align: center; font-size: 3rem; margin-top: 15%;'>⏳ {periodo_nome}</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: gray;'>Aguardando os primeiros registros de produtividade do turno...</h2>", unsafe_allow_html=True)
    
    # Se encontrou dados válidos, desenha o gráfico normalmente
    else:
        st.markdown(f"""
            <div style='text-align: center;'>
                <h1 style='font-size: 3.5rem; margin-bottom: 0;'>{i_atual}</h1>
                <h2 style='color: #ff4b4b; font-size: 2.5rem; margin-top: 0;'>Setor: {f_atual}</h2>
                <p style='font-size: 1.2rem; color: gray;'>{periodo_nome} | Próxima tela em 60s</p>
            </div>
        """, unsafe_allow_html=True)

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
            font=dict(size=18),
            showlegend=True
        )
        fig.update_traces(textfont_size=22, textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 5. TIMER E AVANÇO
    # ==========================================
    time.sleep(20) 
    
    # Prepara o passo seguinte para a próxima vez que a página recarregar
    st.session_state.passo = (st.session_state.passo + 1) % total_comb
    
    st.rerun()

except Exception as e:
    st.error(f"Erro no sistema de TV: {e}")
    time.sleep(10)
    st.rerun()
