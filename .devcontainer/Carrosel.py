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
# 3. LÓGICA DE FILTROS E DICIONÁRIO
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

    mapa_funcoes = {
        'SEPARADOR F': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'SEPARADOR G': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'CONFERENTE': ['Itens Conf.', 'Ressup. Eq.'], 
        'OPERADOR': ['Mov. Horizontal', 'Mov. Vert.'],
        'RAMPA': ['Itens Rampa']
    }

    lista_funcoes = list(mapa_funcoes.keys())

    if 'passo' not in st.session_state or st.session_state.passo >= len(lista_funcoes):
        st.session_state.passo = 0

    total_funcoes = len(lista_funcoes)
    combinacao_valida = False
    tentativas = 0

    while tentativas < total_funcoes:
        f_atual = lista_funcoes[st.session_state.passo]
        df_tela = df[df['FUNCAO_BUSCA'] == f_atual].copy()
        
        inds_da_funcao = mapa_funcoes[f_atual]
        tem_dados = any(df_tela[ind].sum() > 0 for ind in inds_da_funcao if ind in df_tela.columns)

        if tem_dados:
            combinacao_valida = True
            break

        st.session_state.passo = (st.session_state.passo + 1) % total_funcoes
        tentativas += 1

    # ==========================================
    # 4. MOTOR DE COLUNAS
    # ==========================================
    if not combinacao_valida:
        st.markdown(f"<h1 style='text-align: center; margin-top: 15%;'>⏳ {periodo_nome}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>📅 Período: {dt_inicio_str} a {dt_fim_str}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h1 style='font-size: 3.8rem; margin-bottom: 0; color: #ff4b4b;'>{f_atual}</h1>
                <p style='font-size: 1.2rem; color: gray;'>📅 <b>{dt_inicio_str} a {dt_fim_str}</b> | {periodo_nome}</p>
            </div>
        """, unsafe_allow_html=True)

        inds_da_funcao = mapa_funcoes[f_atual]
        blocos_principais = []
        blocos_extras = []

        for ind in inds_da_funcao:
            if ind in df_tela.columns:
                df_ind = df_tela[df_tela[ind] > 0].copy()
            else:
                df_ind = pd.DataFrame()
                
            if df_ind.empty:
                blocos_principais.append({"ind": ind, "data": pd.DataFrame(), "vazio": True, "titulo": ind})
            else:
                df_ind = df_ind.sort_values(by=ind, ascending=False).drop_duplicates(subset=['NOME'])
                chunk1 = df_ind.head(15).sort_values(by=ind, ascending=True)
                blocos_principais.append({"ind": ind, "data": chunk1, "vazio": False, "titulo": ind})

                if len(df_ind) > 15:
                    chunk2 = df_ind.iloc[15:30].sort_values(by=ind, ascending=True)
                    blocos_extras.append({"ind": ind, "data": chunk2, "vazio": False, "titulo": f"{ind} (Cont.)"})
                if len(df_ind) > 30:
                    chunk3 = df_ind.iloc[30:45].sort_values(by=ind, ascending=True)
                    blocos_extras.append({"ind": ind, "data": chunk3, "vazio": False, "titulo": f"{ind} (Cont. 2)"})

        blocos_finais = []
        for b in blocos_principais:
            blocos_finais.append(b)
            
        for b in blocos_extras:
            if len(blocos_finais) < 3:
                blocos_finais.append(b)

        while len(blocos_finais) < 3:
            blocos_finais.append({"ind": "", "data": pd.DataFrame(), "vazio": True, "titulo": ""})

        blocos_finais = blocos_finais[:3]

        # ==========================================
        # 5. DESENHO NA TELA
        # ==========================================
        colunas_ui = st.columns(3)
        mapa_cores = {'T1': '#004aad', 'T2': '#ffcc00', 'T3': '#ff4b4b', 'FANTASMA': 'rgba(0,0,0,0)'}

        for i in range(3):
            with colunas_ui[i]:
                bloco = blocos_finais[i]
                
                # A grande mudança: Se estiver vazio, não invocamos o Plotly de jeito nenhum!
                if bloco['vazio']:
                    if bloco['titulo']:
                        st.markdown(f"<h3 style='text-align: center; color: #333;'>{bloco['titulo']}</h3>", unsafe_allow_html=True)
                        st.info("Sem dados no momento.")
                    else:
                        # Coluna extra inutilizada fica apenas como um espaço em branco estrutural
                        st.markdown("<div style='height: 650px;'></div>", unsafe_allow_html=True)
                else:
                    ind = bloco['ind']
                    df_graf = bloco['data']
                    titulo = bloco['titulo']
                    
                    st.markdown(f"<h3 style='text-align: center; color: #333;'>{titulo}</h3>", unsafe_allow_html=True)

                    qtd_faltante = 15 - len(df_graf)
                    if qtd_faltante > 0:
                        espaco_magico = "\u200B"
                        linhas_vazias = pd.DataFrame({
                            'NOME': [espaco_magico * (x+1) for x in range(qtd_faltante)],
                            ind: [0.0] * qtd_faltante,
                            'TURNO': ['FANTASMA'] * qtd_faltante
                        })
                        df_graf = pd.concat([linhas_vazias, df_graf], ignore_index=True)

                    txt = df_graf[ind].apply(lambda x: "" if x == 0 else (f"{x:.0f}%" if 'Jornada' in ind else f"{x:.0f}"))

                    fig = px.bar(df_graf, x=ind, y="NOME", orientation='h', text=txt)
                    
                    fig.update_yaxes(type='category', categoryorder='array', categoryarray=df_graf['NOME'].tolist(), tickfont=dict(size=14))
                    
                    fig.update_layout(
                        height=650, 
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_title=None, yaxis_title=None, 
                        showlegend=False,
                        margin=dict(l=5, r=40, t=5, b=5), 
                        bargap=0.3 
                    )
                    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
                    
                    cores = df_graf['TURNO'].map(mapa_cores).fillna('gray').tolist()
                    fig.update_traces(
                        marker_color=cores, 
                        textfont_size=16, 
                        textposition="outside",
                        cliponaxis=False 
                    )
                    
                    # Uma chave única e dinâmica mata qualquer chance de cache antigo da tela anterior
                    st.plotly_chart(fig, use_container_width=True, key=f"plot_{f_atual}_{ind}_{i}")

    time.sleep(10)
    st.session_state.passo = (st.session_state.passo + 1) % total_funcoes
    st.rerun()

except Exception as e:
    st.error(f"Erro: {e}")
    time.sleep(10)
    st.rerun()
