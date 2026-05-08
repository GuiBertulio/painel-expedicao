import streamlit as st
import pandas as pd
import plotly.express as px
import time
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (TRAVA TOTAL)
# ==========================================
st.set_page_config(page_title="TV Gestão à Vista", page_icon="📺", layout="wide")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
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

placeholder = st.empty()

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
    
    colunas_texto = ['NOME', 'TURNO', 'FUNÇÃO', 'FUNCAO_BUSCA', 'Tempo Médio']
    for col in df.columns:
        if col not in colunas_texto:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if 'Jornada' in col: 
                df.loc[(df[col] > 0) & (df[col] <= 2.0), col] = df[col] * 100
    return df

# ==========================================
# 3. DICIONÁRIO MESTRE (MAPA DA OPERAÇÃO)
# ==========================================
mapa_completo = {
    'T3': {
        'SEPARADOR F': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'SEPARADOR G': ['Jornada Líq.', 'Itens Sep', 'Itens/Hora'],
        'CONFERENTE': ['Itens Conf.'],
        'OPERADOR': ['Mov. Horizontal'], 
        'RAMPEIRO': ['Itens Rampa'],
        'MANOBRISTA': ['Itens Manob.'],
    },
    'T2': {
        'CONFERENTE': ['Itens Conf.'],
        'OPERADOR': ['Mov. Horizontal'],
        'RAMPEIRO': ['Itens Rampa'],
        'SEPARADOR G': ['Ressup. Ap.', 'Itens/Hora']
    },
    'T1': {
        'CONFERENTE': ['Palets Conf.', 'Tempo Médio'],
        'DESCARGA': ['Carga Palet.', 'Tempo Médio', 'Carga Bat.'],
        'OPERADOR': ['Mov. Vert.', 'Tempo Médio'],
        'PUXA': ['Palets Px.', 'Tempo Médio']
    }
}

apelidos_cargos = {
    "OPERADOR": "OPERADOR DE EMPILHADEIRA"
}

try:
    df_base = carregar_dados()
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26) if hoje.day >= 26 else datetime.date(hoje.year if hoje.month > 1 else hoje.year - 1, hoje.month - 1 if hoje.month > 1 else 12, 26)
    
    agora_brasil = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    turnos_permitidos = ['T3'] if (18 <= agora_brasil.hour or agora_brasil.hour < 6) else ['T1', 'T2']
    df = df_base[df_base['TURNO'].isin(turnos_permitidos)].copy()

    lista_telas = []
    for turno_ativo in turnos_permitidos:
        if turno_ativo in mapa_completo:
            for funcao, indicadores in mapa_completo[turno_ativo].items():
                lista_telas.append({'turno': turno_ativo, 'funcao': funcao, 'indicadores': indicadores})

    if 'passo' not in st.session_state or st.session_state.passo >= len(lista_telas):
        st.session_state.passo = 0

    with placeholder.container():
        tela_atual = lista_telas[st.session_state.passo]
        t_atual = tela_atual['turno']
        f_planilha = tela_atual['funcao'] 
        inds_f = tela_atual['indicadores']
        
        f_exibicao = apelidos_cargos.get(f_planilha, f_planilha)
        df_tela = df[(df['TURNO'] == t_atual) & (df['FUNCAO_BUSCA'] == f_planilha)].copy()
        
        # === FILTRO INTELIGENTE ANTI-ERRO (Aceita tanto número quanto texto) ===
        def tem_dado_valido(serie):
            s = serie.astype(str).str.strip()
            validos = s[(s != '0') & (s != '0.0') & (s != '00:00:00') & (s != 'nan') & (s != '') & (s != 'None')]
            return len(validos) > 0

        if not any(tem_dado_valido(df_tela[ind]) for ind in inds_f if ind in df_tela.columns):
            st.session_state.passo = (st.session_state.passo + 1) % len(lista_telas)
            st.rerun()

        st.markdown(f"<h1 style='text-align: center; color: #ff4b4b; font-size: 3.5rem;'>{f_exibicao}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray;'>📅 {dt_inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

        blocos = []
        for ind in inds_f:
            if ind in df_tela.columns:
                # O Segredo: Filtramos convertendo temporariamente para string para não dar conflito
                mascara_validos = (
                    (df_tela[ind].astype(str).str.strip() != '0') & 
                    (df_tela[ind].astype(str).str.strip() != '0.0') & 
                    (df_tela[ind].astype(str).str.strip() != '00:00:00') &
                    (df_tela[ind].astype(str).str.strip() != 'nan') &
                    (df_tela[ind].astype(str).str.strip() != '')
                )
                df_ind = df_tela[mascara_validos].copy()
                
                if not df_ind.empty:
                    # Tempo Médio também entra na lista de "Quanto menor, melhor"
                    ordem_crescente = True if ind in ['Avaria', 'Corte %', 'Dev. %', 'Tempo Médio'] else False
                    
                    df_ind = df_ind.sort_values(by=ind, ascending=ordem_crescente).drop_duplicates(subset=['NOME'])
                    
                    chunk = df_ind.head(15).sort_values(by=ind, ascending=not ordem_crescente)
                    blocos.append({"titulo": ind, "data": chunk, "ind": ind})
                    
                    if len(df_ind) > 15:
                        chunk2 = df_ind.iloc[15:30].sort_values(by=ind, ascending=not ordem_crescente)
                        blocos.append({"titulo": f"{ind} (Cont.)", "data": chunk2, "ind": ind})

        mapa_cores = {'T1': '#ffcc00', 'T2': '#ffcc00', 'T3': '#004aad', 'FANTASMA': 'rgba(0,0,0,0)'}
        
        def formatar_kpi(row, coluna_ind):
            if row['TURNO'] == 'FANTASMA': return ""
            valor = row[coluna_ind]
            if pd.isna(valor) or valor == '' or valor == 0: return ""
            
            if coluna_ind in ['Avaria', 'Corte %', 'Dev. %']: return f"{float(valor):.2f}%"
            elif 'Jornada' in coluna_ind: return f"{float(valor):.0f}%"
            elif coluna_ind == 'Tempo Médio': return str(valor).split('.')[0] # Limpa os milissegundos
            else: return f"{float(valor):.0f}"

        num_blocos = len(blocos)
        
        if num_blocos == 1:
            colunas_ui = st.columns([1, 1.5, 1]) 
            alvos = [colunas_ui[1]]
        elif num_blocos == 2:
            colunas_ui = st.columns([0.5, 2, 2, 0.5]) 
            alvos = [colunas_ui[1], colunas_ui[2]]
        else:
            colunas_ui = st.columns(3) 
            alvos = [colunas_ui[0], colunas_ui[1], colunas_ui[2]]

        for i in range(min(num_blocos, len(alvos))):
            with alvos[i]:
                b = blocos[i]
                st.markdown(f"<h3 style='text-align: center;'>{b['titulo']}</h3>", unsafe_allow_html=True)
                
                df_graf = b['data']
                qtd = 15 - len(df_graf)
                if qtd > 0:
                    fantasmas = pd.DataFrame({'NOME': ["\u200B"*(x+1) for x in range(qtd)], b['ind']: [0.0]*qtd, 'TURNO': ['FANTASMA']*qtd})
                    df_graf = pd.concat([fantasmas, df_graf], ignore_index=True)

                txt = df_graf.apply(lambda row: formatar_kpi(row, b['ind']), axis=1)
                
                fig = px.bar(df_graf, x=b['ind'], y="NOME", orientation='h', text=txt)
                fig.update_yaxes(type='category', tickfont=dict(size=14))
                
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
                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True}, key=f"slot_{f_planilha}_{i}")

    time.sleep(10)
    st.session_state.passo = (st.session_state.passo + 1) % len(lista_telas)
    st.rerun()

except Exception as e:
    st.error(f"Erro: {e}")
    time.sleep(10)
    st.rerun()
