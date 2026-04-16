import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; }
    [data-testid="stMetricValue"] { font-size: 50px !important; }
    [data-testid="stMetricLabel"] > div { font-size: 20px !important; }
    /* Estiliza as abas para ficarem maiores */
    button[data-baseweb="tab"] { font-size: 18px !important; font-weight: bold !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    # Adicionamos a coluna DATA aqui
    colunas_desejadas = ['DATA', 'NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        # Se a coluna DATA não existir na planilha, cria uma vazia para o site não quebrar
        if 'DATA' not in df.columns:
            df['DATA'] = datetime.date.today().strftime('%d/%m/%Y')
        df = df[[col for col in colunas_desejadas if col in df.columns]]
    
    # Converte a coluna DATA de texto para formato de data real do Python
    if 'DATA' in df.columns:
        df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce').dt.date
    
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'FUNÇÃO']):
        df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    return df

# ==========================================
# 3. O "MOTOR" QUE DESENHA A TELA (FUNÇÃO REUTILIZÁVEL)
# ==========================================
# Criamos essa função para não precisar repetir o código do gráfico duas vezes
def desenhar_painel(df_aba, chave_unica):
    # 1. Filtro de Turno Horizontal no topo
    st.markdown("### 🎯 Visão Geral")
    lista_turnos = ["Todos"] + sorted(df_aba['TURNO'].dropna().unique().tolist())
    # O key=chave_unica garante que o filtro da Aba 1 não dê conflito com a Aba 2
    turno_selecionado = st.radio("Filtre por Turno:", lista_turnos, horizontal=True, key=f"turno_{chave_unica}")

    if turno_selecionado != "Todos":
        df_filtrado = df_aba[df_aba['TURNO'] == turno_selecionado].copy()
    else:
        df_filtrado = df_aba.copy()

    # 2. Cartões (KPIs)
    kpi1, kpi2, kpi3 = st.columns(3)
    total_itens = df_filtrado['Itens Sep'].sum()
    media_velocidade = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean()
    if pd.isna(media_velocidade): media_velocidade = 0
    total_horas = df_filtrado['Horas'].sum()

    kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
    kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
    kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # 3. Gráfico e Tabela Lado a Lado
    col_graf, col_tab = st.columns([1.2, 1]) 

    with col_graf:
        st.markdown("### 📈 Análise por Colaborador")
        opcao_grafico = st.selectbox(
            "Selecione a métrica para o gráfico:",
            ["Jornada Líq.", "Itens Sep", "Itens/Hora", "Horas"],
            key=f"metrica_{chave_unica}"
        )
        
        df_grafico = df_filtrado[df_filtrado[opcao_grafico] > 0].copy()
        
        # Como pode haver a mesma pessoa em vários dias, precisamos SOMAR ou fazer a MÉDIA antes de desenhar o gráfico
        if opcao_grafico in ["Itens Sep", "Horas"]:
            df_grafico = df_grafico.groupby(['NOME', 'TURNO'])[opcao_grafico].sum().reset_index()
        else: # Para Jornada e Itens/Hora, tiramos a média
            df_grafico = df_grafico.groupby(['NOME', 'TURNO'])[opcao_grafico].mean().reset_index()

        df_grafico = df_grafico.sort_values(by=opcao_grafico, ascending=True)
        
        if opcao_grafico == "Jornada Líq.":
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}%")
        elif opcao_grafico == "Horas":
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.2f}h")
        else:
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}")
        
        fig = px.bar(df_grafico, x=opcao_grafico, y="NOME", color="TURNO", orientation='h', text=textos_barras)
        fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None, height=650)
        st.plotly_chart(fig, use_container_width=True, key=f"graf_plotly_{chave_unica}")

    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        colunas_tabela = ['NOME', 'TURNO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
        
        # Agrupamento da tabela para somar/fazer média caso a pessoa tenha trabalhado vários dias filtrados
        df_tabela = df_filtrado.groupby(['NOME', 'TURNO']).agg({
            'Itens Sep': 'sum',
            'Horas': 'sum',
            'Itens/Hora': 'mean',
            'Jornada Líq.': 'mean'
        }).reset_index()

        df_tabela = df_tabela.sort_values(by='NOME', ascending=True)
        
        st.dataframe(
            df_tabela, hide_index=True, use_container_width=True, height=650, 
            column_config={
                "Itens Sep": st.column_config.NumberColumn("Itens Sep", format="%d"),
                "Horas": st.column_config.NumberColumn("Horas", format="%.2f"),
                "Itens/Hora": st.column_config.NumberColumn("Itens/Hora", format="%d"),
                "Jornada Líq.": st.column_config.NumberColumn("Jornada Líq.", format="%d%%") 
            }
        )

# ==========================================
# 4. CONSTRUÇÃO FINAL DA TELA E DAS ABAS
# ==========================================
try:
    df_completo = carregar_dados()

    # Cálculo do Ciclo Atual (Dia 26)
    hoje = datetime.date.today()
    if hoje.day >= 26:
        data_inicio_ciclo = datetime.date(hoje.year, hoje.month, 26)
    else:
        mes_ant = hoje.month - 1 if hoje.month > 1 else 12
        ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
        data_inicio_ciclo = datetime.date(ano_ant, mes_ant, 26)

    st.title("📊 Monitor de Produtividade")
    st.markdown("Acompanhamento de desempenho da equipe.")
    st.write("") # Espaço

    # CRIANDO AS DUAS ABAS
    aba_acumulado, aba_diaria = st.tabs(["📈 Acumulado do Ciclo (Dia 26 até Hoje)", "📅 Visão Específica por Data"])

    # ----------------------------------------
    # CONTEÚDO DA ABA 1: ACUMULADO DO CICLO
    # ----------------------------------------
    with aba_acumulado:
        st.info(f"**Período Apurado:** Exibindo dados automaticamente de **{data_inicio_ciclo.strftime('%d/%m/%Y')}** até **{hoje.strftime('%d/%m/%Y')}**.")
        
        # Filtra o dataframe da base para pegar apenas do dia 26 em diante
        if 'DATA' in df_completo.columns:
            df_ciclo = df_completo[df_completo['DATA'] >= data_inicio_ciclo]
        else:
            df_ciclo = df_completo # Se der erro na data, puxa tudo por segurança
            
        # Chama o nosso motor para desenhar a tela!
        desenhar_painel(df_ciclo, "aba1")

    # ----------------------------------------
    # CONTEÚDO DA ABA 2: VISÃO ESPECÍFICA (COM CALENDÁRIO)
    # ----------------------------------------
    with aba_diaria:
        # Coloca o calendário na tela
        datas_selecionadas = st.date_input(
            "Selecione o Dia ou o Período que deseja analisar:",
            value=(hoje, hoje), # Começa marcando o dia de hoje
            max_value=hoje,
            format="DD/MM/YYYY"
        )
        
        # Tratamento de segurança caso o usuário selecione só uma data no calendário
        if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2:
            data_ini, data_fim = datas_selecionadas
        else:
            data_ini = datas_selecionadas[0] if isinstance(datas_selecionadas, tuple) else datas_selecionadas
            data_fim = data_ini
            
        # Filtra o dataframe com base no que foi escolhido no calendário
        if 'DATA' in df_completo.columns:
            df_especifico = df_completo[(df_completo['DATA'] >= data_ini) & (df_completo['DATA'] <= data_fim)]
        else:
            df_especifico = df_completo

        # Chama o nosso motor para desenhar a tela novamente, agora com os dados filtrados!
        if df_especifico.empty:
            st.warning("Nenhum dado encontrado para as datas selecionadas.")
        else:
            desenhar_painel(df_especifico, "aba2")

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao processar os dados: {e}")
