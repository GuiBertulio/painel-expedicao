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
    
    # 1. Lê a planilha da nuvem
    df = pd.read_csv(link_csv)
    
    # Limpa espaços invisíveis nos nomes das colunas
    df.columns = df.columns.astype(str).str.strip()
    
    # --- NOVIDADE: EXTRAÇÃO INTELIGENTE DAS DATAS (Colunas L e M) ---
    data_inicio = "--/--/----"
    data_fim = "--/--/----"
    
    try:
        if 'Data inicio' in df.columns and 'Data Fim' in df.columns:
            # Pega a primeira linha preenchida nas colunas de data
            val_ini = str(df['Data inicio'].dropna().iloc[0]).split()[0] # .split()[0] corta a parte da hora (00:00:00)
            val_fim = str(df['Data Fim'].dropna().iloc[0]).split()[0]
            
            # Formata de AAAA-MM-DD para DD/MM/AAAA
            if '-' in val_ini:
                ano, mes, dia = val_ini.split('-')
                data_inicio = f"{dia}/{mes}/{ano}"
            else:
                data_inicio = val_ini
                
            if '-' in val_fim:
                ano, mes, dia = val_fim.split('-')
                data_fim = f"{dia}/{mes}/{ano}"
            else:
                data_fim = val_fim
    except Exception:
        pass # Se a coluna vier vazia, ele mantém os tracinhos
    # ----------------------------------------------------------------
    
    # 2. Remove quem não tem nome
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    # 3. Puxa só as colunas que importam para o Dashboard
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        pass 
    
    # 4. Tratamento da vírgula brasileira
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 5. Ajuste da Jornada (Decimal para Porcentagem)
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    # 6. Filtros de Turno e Função
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'TURNO', 'FUNÇÃO']):
        df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
        df = df[df['TURNO'] == 'T3']
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    return df, data_inicio, data_fim

# ==========================================
# 3. CONSTRUÇÃO DA TELA (LAYOUT FINAL)
# ==========================================
try:
    df, dt_inicio, dt_fim = carregar_dados()

    # --- LINHA 1: TÍTULO E PERÍODO NA ESQUERDA | KPIS NA DIREITA ---
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")
        # DATA MOVIDA PARA CÁ (Abaixo do título)
        st.markdown(f"**Período Apurado:** de {dt_inicio} à {dt_fim}")

    with col_kpis:
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

    # --- LINHA 2: GRÁFICO INTERATIVO E TABELA ---
    col_graf, col_tab = st.columns([1.2, 1]) 

    # LADO ESQUERDO: GRÁFICO COM CAIXA DE SELEÇÃO
    with col_graf:
        st.markdown("### 📈 Análise por Colaborador")
        
        # 1. A CAIXA DE OPÇÕES (Dropdown)
        opcao_grafico = st.selectbox(
            "Selecione a métrica para visualizar no gráfico:",
            ["Jornada Líq.", "Itens Sep", "Itens/Hora", "Horas"]
        )
        
        # 2. Prepara os dados filtrando quem está zerado na opção escolhida
        df_grafico = df[df[opcao_grafico] > 0].copy()
        df_grafico = df_grafico.sort_values(by=opcao_grafico, ascending=True)
        
        # 3. Formatação Inteligente dos números na barra
        if opcao_grafico == "Jornada Líq.":
            # Arredonda e coloca o símbolo de %
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}%")
        elif opcao_grafico == "Horas":
            # Coloca um 'h' no final
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.2f}h")
        else:
            # Mostra apenas o número inteiro (para Itens Sep e Itens/Hora)
            textos_barras = df_grafico[opcao_grafico].apply(lambda x: f"{x:.0f}")
        
        # 4. Desenha o gráfico
        fig = px.bar(
            df_grafico, 
            x=opcao_grafico, 
            y="NOME", 
            color="TURNO", 
            orientation='h',
            text=textos_barras # Usa os nossos textos formatados
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
        
        colunas_tabela = ['NOME', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
        df_tabela = df[colunas_tabela].sort_values(by='NOME', ascending=True)
        
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
