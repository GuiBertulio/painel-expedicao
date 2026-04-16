import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem !important; }
    [data-testid="stMetricValue"] { font-size: 45px !important; }
    button[data-baseweb="tab"] { font-size: 18px !important; font-weight: bold !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO E LIMPEZA (TRANSFORMAÇÃO)
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # Tratamento da Coluna DATAAPURACAO
    if 'DATAAPURACAO' in df.columns:
        df['DATAAPURACAO'] = pd.to_datetime(df['DATAAPURACAO'], format='%d/%m/%Y', errors='coerce').dt.date
    else:
        # Se não houver a coluna, cria uma com o dia de hoje para não quebrar
        df['DATAAPURACAO'] = datetime.date.today()

    # Tratamento Numérico (Vírgula para Ponto)
    colunas_num = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100

    # Filtro de Segurança
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
        
    if 'FUNÇÃO' in df.columns:
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    return df

# ==========================================
# 3. MOTOR DO PAINEL (COM ACÚMULO AUTOMÁTICO)
# ==========================================
def desenhar_painel(df_entrada, chave_unica):
    # FILTRO DE TURNO
    lista_turnos = ["Todos"] + sorted(df_entrada['TURNO'].dropna().unique().tolist())
    turno = st.radio("Selecione o Turno:", lista_turnos, horizontal=True, key=f"t_{chave_unica}")

    df_f = df_entrada.copy()
    if turno != "Todos":
        df_f = df_f[df_f['TURNO'] == turno]

    # AGRUPAMENTO: Transforma várias linhas em um total acumulado por nome
    df_acumulado = df_f.groupby(['NOME', 'TURNO']).agg({
        'Itens Sep': 'sum',
        'Horas': 'sum',
        'Itens/Hora': 'mean',
        'Jornada Líq.': 'mean'
    }).reset_index()

    # BLOCO DE INDICADORES (KPIs)
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Total Itens", f"{df_acumulado['Itens Sep'].sum():,.0f}".replace(',', '.'))
    c2.metric("⚡ Média Equipe", f"{df_acumulado[df_acumulado['Itens/Hora']>0]['Itens/Hora'].mean():.0f}")
    c3.metric("⏱️ Horas Totais", f"{df_acumulado['Horas'].sum():.1f}h")

    st.divider()

    # GRÁFICO E TABELA
    col_g, col_t = st.columns([1.2, 1])

    with col_g:
        metrica = st.selectbox("Métrica do Gráfico:", ["Jornada Líq.", "Itens Sep", "Itens/Hora", "Horas"], key=f"m_{chave_unica}")
        df_graf = df_acumulado[df_acumulado[metrica] > 0].sort_values(by=metrica)
        
        # Formatação do texto nas barras
        if metrica == "Jornada Líq.": textos = df_graf[metrica].apply(lambda x: f"{x:.0f}%")
        elif metrica == "Horas": textos = df_graf[metrica].apply(lambda x: f"{x:.1f}h")
        else: textos = df_graf[metrica].apply(lambda x: f"{x:.0f}")

        fig = px.bar(df_graf, x=metrica, y="NOME", color="TURNO", orientation='h', text=textos)
        fig.update_layout(showlegend=False, height=600, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, key=f"fig_{chave_unica}")

    with col_t:
        st.markdown("### 📋 Detalhamento")
        st.dataframe(
            df_acumulado.sort_values(by="NOME"),
            hide_index=True, use_container_width=True, height=600,
            column_config={
                "Itens Sep": st.column_config.NumberColumn(format="%d"),
                "Horas": st.column_config.NumberColumn(format="%.2f"),
                "Itens/Hora": st.column_config.NumberColumn(format="%d"),
                "Jornada Líq.": st.column_config.NumberColumn(format="%d%%")
            }
        )

# ==========================================
# 4. EXECUÇÃO PRINCIPAL (ABAS)
# ==========================================
try:
    df_raw = carregar_dados()
    
    # Lógica do Ciclo (Dia 26)
    hoje = datetime.date.today()
    if hoje.day >= 26: data_ini_ciclo = datetime.date(hoje.year, hoje.month, 26)
    else: data_ini_ciclo = datetime.date(hoje.year if hoje.month > 1 else hoje.year-1, hoje.month-1 if hoje.month > 1 else 12, 26)

    st.title("📊 Monitor de Produtividade")
    
    aba_mes, aba_dia = st.tabs(["📈 Acumulado do Mês", "📅 Relatório Diário"])

    with aba_mes:
        st.info(f"Dados acumulados de {data_ini_ciclo.strftime('%d/%m/%Y')} até hoje.")
        # Usando a coluna DATAAPURACAO
        df_ciclo = df_raw[df_raw['DATAAPURACAO'] >= data_ini_ciclo]
        desenhar_painel(df_ciclo, "mes")

    with aba_dia:
        # Puxando a lista de datas da DATAAPURACAO
        datas_lista = sorted(df_raw['DATAAPURACAO'].unique(), reverse=True)
        data_sel = st.selectbox("Escolha o dia para visualizar:", datas_lista, format_func=lambda x: x.strftime('%d/%m/%Y'))
        
        # Filtrando pela DATAAPURACAO
        df_dia = df_raw[df_raw['DATAAPURACAO'] == data_sel]
        desenhar_painel(df_dia, "dia")

except Exception as e:
    st.error(f"Erro ao carregar o dashboard: {e}")
