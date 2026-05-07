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
    
    # Limpeza reforçada para evitar barras sobrepostas ou erros de soma
    for col in ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 'Mov. Horizontal', 'Mov. Vert.']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Se a Jornada Líquida vier como 0.85, converte para 85
            if col == 'Jornada Líq.':
                df.loc[(df[col] > 0) & (df[col] <= 2.0), col] = df[col] * 100

    if 'NOME' in df.columns and 'FUNÇÃO' in df.columns:
        df['FUNCAO_BUSCA'] = df['FUNÇÃO'].str.upper().str.strip()
            
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
        'CONFERENTE': ['Itens Sep', 'Ressup.'], 
        'OPERADOR': ['Mov. Horizontal', 'Mov. Vert.'],
        'RAMPA': ['Itens Sep']
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
    # 4. MOTOR INTELIGENTE DE COLUNAS (A GRANDE MÁGICA)
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
        blocos = []

        # PASSO 1: Pega os primeiros 15 colocados de cada indicador
        for ind in inds_da_funcao:
            df_ind = df_tela[df_tela[ind] > 0].copy()
            if df_ind.empty:
                blocos.append({"ind": ind, "data": None, "vazio": True, "parte": 1})
            else:
                # Ordena e remove nomes duplicados para não dar bug na barra
                df_ind = df_ind.sort_values(by=ind, ascending=False).drop_duplicates(subset=['NOME'])
                chunk = df_ind.head(15).sort_values(by=ind, ascending=True)
                blocos.append({"ind": ind, "data": chunk, "vazio": False, "parte": 1})

        # PASSO 2: Se sobrar espaço na tela, continua a lista com a galera da posição 16 até 30!
        if len(blocos) < 3:
            for ind in inds_da_funcao:
                df_ind = df_tela[df_tela[ind] > 0].copy()
                df_ind = df_ind.sort_values(by=ind, ascending=False).drop_duplicates(subset=['NOME'])
                if len(df_ind) > 15:
                    chunk = df_ind.iloc[15:30].sort_values(by=ind, ascending=True)
                    blocos.append({"ind": ind, "data": chunk, "vazio": False, "parte": 2})
                    if len(blocos) == 3: break

        # PASSO 3: Se AINDA sobrar espaço (ex: Rampa que só tem 1 indicador), mostra a posição 31 até 45!
        if len(blocos) < 3:
            for ind in inds_da_funcao:
                df_ind = df_tela[df_tela[ind] > 0].copy()
                df_ind = df_ind.sort_values(by=ind, ascending=False).drop_duplicates(subset=['NOME'])
                if len(df_ind) > 30:
                    chunk = df_ind.iloc[30:45].sort_values(by=ind, ascending=True)
                    blocos.append({"ind": ind, "data": chunk, "vazio": False, "parte": 3})
                    if len(blocos) == 3: break

        # ==========================================
        # 5. DESENHANDO OS BLOCOS NA TELA
        # ==========================================
        colunas_ui = st.columns(3)
        mapa_cores = {'T1': '#004aad', 'T2': '#ffcc00', 'T3': '#ff4b4b'}

        for i in range(3):
            with colunas_ui[i]:
                if i < len(blocos):
                    bloco = blocos[i]
                    
                    if bloco['vazio']:
                        st.markdown(f"<h3 style='text-align: center; color: #333;'>{bloco['ind']}</h3>", unsafe_allow_html=True)
                        st.info("Sem dados no momento.")
                    else:
                        ind = bloco['ind']
                        df_graf = bloco['data']
                        parte = bloco['parte']
                        
                        # Se for a continuação da lista, ele adiciona um "(Cont.)" no título
                        titulo = f"{ind}" if parte == 1 else f"{ind} (Cont.)"
                        st.markdown(f"<h3 style='text-align: center; color: #333;'>{titulo}</h3>", unsafe_allow_html=True)
                        
                        txt = df_graf[ind].apply(lambda x: f"{x:.0f}%" if ind == 'Jornada Líq.' else f"{x:.0f}")

                        # ALTURA DINÂMICA: Fim do bug das Barras Gigantes e Finas!
                        altura_dinamica = max(150, len(df_graf) * 40 + 50)

                        fig = px.bar(df_graf, x=ind, y="NOME", orientation='h', text=txt)
                        
                        fig.update_yaxes(type='category', categoryorder='array', categoryarray=df_graf['NOME'], tickfont=dict(size=14))
                        
                        fig.update_layout(
                            height=altura_dinamica, # Aplica a altura inteligente aqui
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            xaxis_title=None, yaxis_title=None, 
                            showlegend=False,
                            margin=dict(l=5, r=40, t=5, b=5), 
                            bargap=0.3 # Mantém todas as barras padronizadas
                        )
                        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
                        
                        cores = df_graf['TURNO'].map(mapa_cores).fillna('gray').tolist()
                        fig.update_traces(
                            marker_color=cores, 
                            textfont_size=16, 
                            textposition="outside",
                            cliponaxis=False 
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, key=f"plot_{f_atual}_{ind}_{parte}")
                else:
                    # Mata o Gráfico Fantasma forçando a coluna a ficar vazia
                    st.empty()

    time.sleep(10)
    st.session_state.passo = (st.session_state.passo + 1) % total_funcoes
    st.rerun()

except Exception as e:
    st.error(f"Erro: {e}")
    time.sleep(10)
    st.rerun()
