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
    /* PUXA TUDO PARA CIMA */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    /* Aumenta o tamanho do número gigante */
    [data-testid="stMetricValue"] {
        font-size: 50px !important;
    }
    /* Aumenta o título */
    [data-testid="stMetricLabel"] > div {
        font-size: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO DOS DADOS (COM AS DATAS)
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # --- EXTRAÇÃO DAS DATAS ---
    data_inicio = "--/--/----"
    data_fim = "--/--/----"
    try:
        if 'Data inicio' in df.columns and 'Data Fim' in df.columns:
            val_ini = str(df['Data inicio'].dropna().iloc[0]).split()[0] 
            val_fim = str(df['Data Fim'].dropna().iloc[0]).split()[0]
            
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
        pass 
    # --------------------------
    
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
        
    if all(col in df.columns for col in ['Itens Sep', 'Horas', 'FUNÇÃO']):
        df = df[(df['Itens Sep'] > 0) | (df['Horas'] > 0)]
        df = df[df['FUNÇÃO'].isin(['Separador F', 'Separador G'])]
            
    # AGORA SIM ELE DEVOLVE AS 3 COISAS CORRETAMENTE
    return df, data_inicio, data_fim

# ==========================================
# 3. CONSTRUÇÃO DA TELA (LAYOUT AVANÇADO)
# ==========================================
try:
    df, dt_inicio, dt_fim = carregar_dados()

    # 1. RESERVANDO OS ESPAÇOS NO TOPO DA TELA
    col_topo_esq, col_topo_dir = st.columns([1, 1.2])
    
    espaco_titulo = col_topo_esq.empty() 
    espaco_kpis = col_topo_dir.empty()

    st.divider()

    # 2. CONSTRUÇÃO DA ÁREA DO GRÁFICO E DO FILTRO LATERAL
    col_graf, col_tab = st.columns([1.2, 1]) 

    with col_graf:
        st.markdown("### 📈 Análise por Colaborador")
        
        opcao_grafico = st.selectbox(
            "Selecione a métrica para o gráfico:",
            ["Jornada Líq.", "Itens Sep", "Itens/Hora", "Horas"]
        )
        
        area_grafico, area_filtro_turno = st.columns([4, 1])

        with area_filtro_turno:
            st.write("") 
            st.write("")
            st.markdown("**Turno:**")
            
            lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
            turno_selecionado = st.radio("Filtro de Turnos", lista_turnos, label_visibility="collapsed")

    # 3. APLICAÇÃO DO FILTRO DE TURNO
    if turno_selecionado != "Todos":
        df_filtrado = df[df['TURNO'] == turno_selecionado].copy()
    else:
        df_filtrado = df.copy()

    # 4. PREENCHENDO OS ESPAÇOS VAZIOS LÁ DO TOPO
    with espaco_titulo.container():
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")
        st.markdown(f"**Período Apurado:** de {dt_inicio} à {dt_fim}")

    with espaco_kpis.container():
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)

        total_itens = df_filtrado['Itens Sep'].sum()
        media_velocidade = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean()
        if pd.isna(media_velocidade): media_velocidade = 0
        total_horas = df_filtrado['Horas'].sum()

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    # 5. DESENHANDO O GRÁFICO E A TABELA
    with area_grafico:
        df_grafico = df_filtrado[df_filtrado[opcao_grafico] > 0].copy()
        df_grafico = df_grafico.sort_values(by=opcao_grafico, ascending=True)
        
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
            showlegend=False, 
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title=None,
            height=650 
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        
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
