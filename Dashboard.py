import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    /* 1. PUXA TUDO PARA CIMA */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* 2. Aumenta o tamanho do número gigante */
    [data-testid="stMetricValue"] {
        font-size: 50px !important;
    }
    
    /* 3. Aumenta o título (ex: Total de Itens Separados) */
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
    
    # 1. Lê a planilha direto (já que o cabeçalho agora está certinho na Linha 1)
    df = pd.read_csv(link_csv)
    
    # Limpa espaços invisíveis nos nomes das colunas
    df.columns = df.columns.astype(str).str.strip()
    
    # 2. Remove quem não tem nome
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    # 3. Puxa só as colunas que importam
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        pass # Evita que o site quebre se uma coluna sumir
    
    # 4. Tratamento da vírgula brasileira para o Python conseguir calcular
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 5. Ajuste da Jornada (Decimal para Porcentagem)
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    # 6. Filtros Mágicos
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'TURNO', 'FUNÇÃO']):
        df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
        df = df[df['TURNO'] == 'T3']
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    # Como as datas sumiram da planilha, vamos deixar um texto fixo.
    # Você pode alterar esses textos abaixo sempre que quiser!
    data_inicio = "01/04"
    data_fim = "Hoje"
            
    return df, data_inicio, data_fim

# ==========================================
# 3. CONSTRUÇÃO DA TELA (NOVO LAYOUT)
# ==========================================
try:
    df, dt_inicio, dt_fim = carregar_dados()

    # --- LINHA 1: TÍTULO NA ESQUERDA | KPIS NA DIREITA ---
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")

    with col_kpis:
        # Coloca as Datas alinhadas à direita
        st.markdown(f"<div style='text-align: right; font-size: 18px; margin-bottom: 10px;'><b>Período Apurado:</b> de {dt_inicio} à {dt_fim}</div>", unsafe_allow_html=True)
        
        # Os Cartões de Visão Geral
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)

        total_itens = df['Itens Sep'].sum()
        media_velocidade = df[df['Itens/Hora'] > 0]['Itens/Hora'].mean()
        if pd.isna(media_velocidade):
            media_velocidade = 0
        total_horas = df['Horas'].sum()

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # --- LINHA 2: GRÁFICO GIGANTE E TABELA ---
    col_graf, col_tab = st.columns([1.2, 1]) 

    # LADO ESQUERDO: GRÁFICO (COM TODOS OS NOMES E JORNADA LÍQUIDA)
    with col_graf:
        st.markdown("### 📈 Jornada Líquida por Colaborador")
        
        df_grafico = df[df['Jornada Líq.'] > 0]
        
        fig = px.bar(
            df_grafico.sort_values(by="Jornada Líq.", ascending=True), 
            x="Jornada Líq.", 
            y="NOME", 
            color="TURNO", 
            orientation='h',
            text_auto=True
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None,
            height=650 # Altura fixada para caber todo mundo sem espremer
        )
        st.plotly_chart(fig, use_container_width=True)

    # LADO DIREITO: TABELA DINÂMICA
    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        
        colunas_tabela = ['NOME', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
        df_tabela = df[colunas_tabela].sort_values(by='NOME', ascending=True)
        
        st.dataframe(
            df_tabela, 
            hide_index=True, 
            use_container_width=True,
            height=650, # Deixa a tabela na mesma altura exata do gráfico
            column_config={
                "Itens Sep": st.column_config.NumberColumn("Itens Sep", format="%d"),
                "Horas": st.column_config.NumberColumn("Horas", format="%.2f"),
                "Itens/Hora": st.column_config.NumberColumn("Itens/Hora", format="%d"),
                "Jornada Líq.": st.column_config.NumberColumn("Jornada Líq.", format="%d%%") 
            }
        )

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao processar os dados: {e}")
