import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

# CSS para aumentar o tamanho dos números e títulos das métricas
# CSS para ajustar os tamanhos e puxar o layout para cima
st.markdown(
    """
    <style>
    /* 1. PUXA TUDO PARA CIMA (Reduz a margem do topo da página) */
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

st.title("📊 Monitor de Produtividade - Expedição")
st.markdown("Acompanhamento de desempenho da equipe.")

# ==========================================
# 2. CARREGAMENTO DOS DADOS DA NUVEM
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    # COLE AQUI O SEU LINK DO CSV DO GOOGLE SHEETS
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df = df.dropna(subset=['NOME'])
    
    colunas_desejadas = ['NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    try:
        df = df[colunas_desejadas]
    except KeyError:
        pass 
    
    # ---------------------------------------------------------
    # A SOLUÇÃO: O TRATAMENTO DA VÍRGULA BRASILEIRA E DO %
    # ---------------------------------------------------------
    colunas_numericas = ['Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
    for col in colunas_numericas:
        # Transforma em texto, tira o símbolo de % (se vier) e troca a vírgula pelo ponto
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        # Agora sim, converte para número em segurança
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Se o Google mandou a Jornada Líquida como decimal (ex: 0.39), multiplicamos por 100.
    # Mas se já veio como 39, não fazemos nada.
    if df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.'] * 100
        
    # Filtros
    df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
    df = df[df['TURNO'] == 'T3']
    df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    return df

# ==========================================
# 3. CONSTRUÇÃO DA TELA
# ==========================================
try:
    df = carregar_dados()

    # --- CARTÕES DE RESUMO (KPIs) ---
    st.markdown("# 🎯 Visão Geral")
    col1, col2, col3 = st.columns(3)

    total_itens = df['Itens Sep'].sum()
    media_velocidade = df[df['Itens/Hora'] > 0]['Itens/Hora'].mean() # Média só de quem trabalhou
    total_horas = df['Horas'].sum()

    col1.metric("📦 Total de Itens Separados", f"{total_itens:,.0f}".replace(',', '.'))
    col2.metric("⚡ Média da Equipe (Itens/H)", f"{media_velocidade:.0f}")
    col3.metric("⏱️ Horas Totais da Operação", f"{total_horas:.1f} h")

    st.divider()

    # --- DIVISÃO DA TELA: GRÁFICO E TABELA ---
    col_graf, col_tab = st.columns([1.2, 1]) 

    # LADO ESQUERDO: GRÁFICO DE ITENS SEPARADOS (TOP 10)
    with col_graf:
        st.markdown("### 🏆 Top 10 - Quantidade de Itens Separados")
        
        # Filtra quem teve produtividade
        df_grafico = df[df['Itens Sep'] > 0]
        
        # O TRUQUE DO TOP 10: Pega os 10 maiores e ordena do menor pro maior 
        # (O Plotly desenha de baixo para cima, então o maior de todos vai ficar no topo)
        df_top10 = df_grafico.nlargest(10, 'Itens Sep').sort_values(by="Itens Sep", ascending=True)
        
        fig = px.bar(
            df_top10, # Usando a nossa nova tabela filtrada com os 10 melhores
            x="Itens Sep", 
            y="NOME", 
            color="TURNO", 
            orientation='h',
            text_auto=True
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # LADO DIREITO: A TABELA DE DADOS 
    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        
        # 2. Prepara a Tabela: Seleciona as colunas limpas e ordena por ordem alfabética (A-Z)
        colunas_tabela = ['NOME', 'Itens Sep', 'Horas', 'Itens/Hora', 'Jornada Líq.']
        df_tabela = df[colunas_tabela].sort_values(by='NOME', ascending=True)
        
        # Formatação visual da tabela no Streamlit
        st.dataframe(
            df_tabela, # Usando a nossa tabela limpa e ordenada
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Itens Sep": st.column_config.NumberColumn("Itens Sep", format="%d"),
                "Horas": st.column_config.NumberColumn("Horas", format="%.2f"),
                "Itens/Hora": st.column_config.NumberColumn("Itens/Hora", format="%d"),
                "Jornada Líq.": st.column_config.NumberColumn("Jornada Líq.", format="%d%%") 
            }
        )

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao ler a planilha: {e}")
    st.info("Dica: Verifique se o arquivo está salvo e fechado antes de atualizar o dashboard.")
