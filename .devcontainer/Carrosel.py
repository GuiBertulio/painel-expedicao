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
    
    # Limpeza básica e conversão numérica
    cols_num = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    # Criando a coluna Nome (Função) para o gráfico
    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['NOME_FUNCAO'] = df['NOME'] + " (" + df['FUNÇÃO'] + ")"
        # Padroniza para busca
        df['FUNCAO_BUSCA'] = df['FUNÇÃO'].str.upper().str.strip()
            
    return df

# ==========================================
# 3. LÓGICA DE FILTROS (HORÁRIO E FUNÇÃO)
# ==========================================
try:
    df_base = carregar_dados()

    # --- A. FILTRO POR HORÁRIO (TURNOS) ---
    hora_atual = datetime.datetime.now().hour
    # Das 18:00 às 05:59 -> T3 | Das 06:00 às 17:59 -> T1 e T2
    if 18 <= hora_atual or hora_atual < 6:
        turnos_permitidos = ['T3']
        periodo_nome = "🌙 Turno da Noite (T3)"
    else:
        turnos_permitidos = ['T1', 'T2']
        periodo_nome = "☀️ Turnos do Dia (T1 e T2)"

    df = df_base[df_base['TURNO'].isin(turnos_permitidos)].copy()

    # --- B. DEFINIÇÃO DO CICLO DO CARROSSEL ---
    # Funções que você solicitou
    lista_funcoes = ['CONFERENTE', 'OPERADOR', 'RAMPA', 'SEPARADOR']
    # Indicadores principais
    lista_indicadores = ['Itens Sep', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Mov. Horizontal', 'Mov. Vert.']

    # Criamos uma lista de combinações (Função x Indicador)
    combinacoes = []
    for f in lista_funcoes:
        for ind in lista_indicadores:
            combinacoes.append({"funcao": f, "indicador": ind})

    # Controle do índice via Session State
    if 'passo' not in st.session_state:
        st.session_state.passo = 0

    conf_atual = combinacoes[st.session_state.passo]
    f_atual = conf_atual['funcao']
    i_atual = conf_atual['indicador']

    # ==========================================
    # 4. CONSTRUÇÃO VISUAL
    # ==========================================
    
    # Cabeçalho da TV
    st.markdown(f"""
        <div style='text-align: center;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 0;'>{i_atual}</h1>
            <h2 style='color: #ff4b4b; font-size: 2.5rem; margin-top: 0;'>Setor: {f_atual}</h2>
            <p style='font-size: 1.2rem; color: gray;'>{periodo_nome} | Próxima atualização em 60s</p>
        </div>
    """, unsafe_allow_html=True)

    # Filtrando os dados para a função e indicador da vez
    df_tela = df[df['FUNCAO_BUSCA'].str.contains(f_atual, na=False)].copy()
    df_tela = df_tela[df_tela[i_atual] > 0] # Só mostra quem produziu algo

    if df_tela.empty:
        st.info(f"Sem dados de {i_atual} para {f_atual} neste turno.")
    else:
        df_tela = df_tela.sort_values(by=i_atual, ascending=True)

        # Formatação do Label
        if i_atual == "Jornada Líq.":
            txt = df_tela[i_atual].apply(lambda x: f"{x:.0f}%")
        else:
            txt = df_tela[i_atual].apply(lambda x: f"{x:.0f}")

        fig = px.bar(
            df_tela, 
            x=i_atual, 
            y="NOME", # Usei só NOME aqui para não ficar repetindo a função na barra, já que o título já diz
            color="TURNO", 
            orientation='h',
            text=txt,
            color_discrete_map={'T1': '#004aad', 'T2': '#ffcc00', 'T3': '#ff4b4b'} # Cores padrão
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
    # 5. TIMER E REEXECUÇÃO
    # ==========================================
    time.sleep(60) # Espera 1 minuto
    
    # Avança o passo
    st.session_state.passo = (st.session_state.passo + 1) % len(combinacoes)
    
    st.rerun()

except Exception as e:
    st.error(f"Erro no sistema de TV: {e}")
    time.sleep(10)
    st.rerun()
