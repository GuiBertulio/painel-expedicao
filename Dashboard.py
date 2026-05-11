import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 50px !important;
    }
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
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    # 1. LISTA ATUALIZADA COM TODAS AS SUAS COLUNAS
    colunas_desejadas = [
        'CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Itens/Hora Eq.', 'Horas', 
        'Itens/Hora', 'Ressup. Ap.', 'Erros', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 
        'Mov. Horizontal', 'Mov. Vert.', 'Avaria', 'Corte %', 'Dev. %', 'Itens Conf.', 
        'Conf Base', 'Itens Manob.', 'Itens Rampa', 'Carga Bat.', 'Carga Palet.', 
        'Palets Px.', 'Palets Conf.', 'Jornada Líq. Eq.'
    ]
    
    # Filtra mantendo apenas as colunas que realmente vieram do Sheets (evita erro se faltar alguma)
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    df = df[colunas_existentes]
    
    # 2. TRATAMENTO DINÂMICO: Transforma todas as métricas em números automaticamente
    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
    colunas_numericas = [col for col in df.columns if col not in colunas_texto]

    for col in colunas_numericas:
        # Tira o % e troca vírgula por ponto antes de converter
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.']
        
    return df

# ==========================================
# 3. CONSTRUÇÃO DA TELA E FILTROS
# ==========================================
try:
    df = carregar_dados()

    # --- CÁLCULO DO PERÍODO (DIA 26 ATÉ HOJE) PARA EXIBIR NA TELA ---
    hoje = datetime.date.today()
    if hoje.day >= 26:
        dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    else:
        mes_ant = hoje.month - 1 if hoje.month > 1 else 12
        ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
        dt_inicio = datetime.date(ano_ant, mes_ant, 26)
    
    dt_inicio_str = dt_inicio.strftime('%d/%m/%Y')
    dt_fim_str = hoje.strftime('%d/%m/%Y')

    # --- LINHA 1: TÍTULO + FILTRO NA ESQUERDA | KPIS NA DIREITA ---
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")
        
        st.info(f"📅 **Período Apurado:** de {dt_inicio_str} até {dt_fim_str}")
        
        lista_turnos = ["Todos os Turnos"] + sorted(df['TURNO'].dropna().unique().tolist())
        turno_selecionado = st.radio("Filtre por Turno:", lista_turnos, horizontal=True)

    if turno_selecionado != "Todos os Turnos":
        df_filtrado = df[df['TURNO'] == turno_selecionado].copy()
    else:
        df_filtrado = df.copy()

    with col_kpis:
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)

        total_itens = df_filtrado['Itens Sep'].sum() if 'Itens Sep' in df_filtrado.columns else 0
        
        if 'Itens/Hora' in df_filtrado.columns:
            media_velocidade = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean()
        else:
            media_velocidade = 0
            
        if pd.isna(media_velocidade): media_velocidade = 0
        
        total_horas = df_filtrado['Horas'].sum() if 'Horas' in df_filtrado.columns else 0

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # --- LINHA 2: GRÁFICO INTERATIVO E TABELA ---
    col_graf, col_tab = st.columns([1.2, 1]) 

    with col_graf:
        st.markdown("### 📈 Análise por Colaborador")
        
        # O Selectbox agora puxa as opções automaticamente baseado nas colunas numéricas
        colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
        opcoes_grafico = [col for col in df_filtrado.columns if col not in colunas_texto]
        
        opcao_grafico = st.selectbox(
            "Selecione a métrica para o gráfico:",
            opcoes_grafico
        )
        
        df_grafico = df_filtrado[df_filtrado[opcao_grafico] > 0].copy()
        df_grafico = df_grafico.sort_values(by=opcao_grafico, ascending=True)
        
        # Formatação dinâmica das barras
        if "Líq." in opcao_grafico or "%" in opcao_grafico:
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
            height=650,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_tab:
        st.markdown("### 📋 Tabela Dinâmica")
        
        df_tabela = df_filtrado.sort_values(by='NOME', ascending=True)
        
        # --- MÁGICA DA FORMATAÇÃO DINÂMICA ---
        configuracao_colunas = {}
        for col in df_tabela.columns:
            if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']:
                continue # Deixa as colunas de texto em paz
                
            elif col in ['Avaria', 'Corte %', 'Dev. %']:
                # Regra nova: Porcentagem com duas casas decimais
                configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                
            elif "Líq." in col:
                # Mantém a Jornada Líq. como porcentagem inteira
                configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                
            elif col == "Horas":
                # Horas mantemos com 2 casas decimais
                configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%.2f")
                
            else:
                # O resto todo fica como número inteiro, sem zeros!
                configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%d")

        st.dataframe(
            df_tabela, 
            hide_index=True, 
            use_container_width=True,
            height=650,
            column_config=configuracao_colunas 
        )

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao processar os dados: {e}")
