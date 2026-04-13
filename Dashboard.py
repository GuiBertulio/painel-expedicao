import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    /* PUXA TUDO PARA CIMA */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    /* Aumenta o tamanho do número gigante */
    [data-testid="stMetricValue"] {
        font-size: 50px !important;
    }
    /* Aumenta o título (ex: Total de Itens Separados) */
    [data-testid="stMetricLabel"] > div {
        font-size: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO DOS DADOS DA NUVEM
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    
    # Limpa espaços invisíveis
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        pass 
    
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    # --- O FILTRO DE TURNO "T3" FIXO FOI REMOVIDO DAQUI ---
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'FUNÇÃO']):
        df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    return df

# ==========================================
# 3. CONSTRUÇÃO DA TELA E FILTROS
# ==========================================
try:
    # Carrega a base inteira (todos os turnos)
    df = carregar_dados()

    # --- LINHA 1: TÍTULO + FILTRO NA ESQUERDA | KPIS NA DIREITA ---
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")
        
        # 1. O NOVO FILTRO DE TURNO GLOBAL
        # Puxa automaticamente os nomes dos turnos que existem na planilha
        lista_turnos = ["Todos os Turnos"] + sorted(df['TURNO'].dropna().unique().tolist())
        turno_selecionado = st.selectbox("Filtre por Turno:", lista_turnos)

    # 2. APLICAÇÃO DO FILTRO (A mágica que atualiza a tela toda)
    if turno_selecionado != "Todos os Turnos":
        df_filtrado = df[df['TURNO'] == turno_selecionado].copy()
    else:
        df_filtrado = df.copy()

    with col_kpis:
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)

        # Os cálculos agora usam a tabela já filtrada pelo turno selecionado
        total_itens = df_filtrado['Itens Sep'].sum()
        media_velocidade = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean()
        if pd.isna(media_velocidade):
            media_velocidade = 0
        total_horas = df_filtrado['Horas'].sum()

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # --- LINHA 2: GRÁFICO INTERATIVO E TABELA ---
    col_graf, col_tab = st.columns([1.2, 1]) 

    # LADO ESQUERDO: GRÁFICO 
    with col_graf:
        st.markdown("### 📈 Análise por Colaborador")
        
        # 3. O FILTRO DO GRÁFICO (Métricas)
        opcao_grafico = st.selectbox(
            "Selecione a métrica para o gráfico:",
            ["Jornada Líq.", "Itens Sep", "Itens/Hora", "Horas"]
        )
        
        # Prepara os dados tirando quem está zerado e organizando
        df_grafico = df_filtrado[df_filtrado[opcao_grafico] > 0].copy()
        df_grafico = df_grafico.sort_values(by=opcao_grafico, ascending=True)
        
        # Coloca % na jornada, 'h' nas horas e deixa itens normais
        if opcao_grafico == "Jornada Líq.":
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}%")
        elif opcao_grafico == "Horas":
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.2f}h")
        else:
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}")
        
        fig = px.bar(
            df_grafico, 
            x=opcao_grafico, 
            y="NOME", 
            color="TURNO", 
            orientation='h',
            text=textos_barras
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None,
            height=650 
        )
        st.plotly_chart(fig, use_container_width=True)

    # LADO DIREITO: TABELA DINÂMICA
    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        
        # Adicionei a coluna TURNO na tabela para visualização ficar mais clara
        colunas_tabela = ['NOME', 'TURNO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
        df_tabela = df_filtrado[colunas_tabela].sort_values(by='NOME', ascending=True)
        
        st.dataframe(
            df_tabela, 
            hide_index=True, 
            use_container_width=True,
            height=650, 
            column_config={
                "Itens Sep": st.column_config.NumberColumn("Itens Sep", format="%d"),
                "Horas": st.column_config.NumberColumn("Horas", format="%.2f"),
                "Itens/Hora": st.column_config.NumberColumn("Itens/Hora", format="%d"),
                "Jornada Líq.": st.column_config.NumberColumn("Jornada Líq.", format="%d%%") 
            }
        )

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao processar os dados: {e}")
