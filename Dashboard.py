import streamlit as st
import pandas as pd
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
        color: #004aad !important;
    }
    [data-testid="stMetricLabel"] > div {
        font-size: 20px !important;
        color: gray;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. DICIONÁRIO DE METAS
# ==========================================
metas_100 = {
    'T3': {
        'SEPARADOR F': {'Jornada Líq.': 80, 'Itens Sep': 9000, 'Itens/Hora': 75},
        'SEPARADOR G': {'Jornada Líq.': 72, 'Itens Sep': 8100, 'Itens/Hora': 75},
        'CONFERENTE': {'Itens Conf.': 110000, 'Dev. %': 0.46},
        'OPERADOR': {'Mov. Horizontal': 1800, 'Avaria': 0.07},
        'RAMPEIRO': {'Itens Rampa': 45000, 'Dev. %': 0.46, 'Avaria': 0.07},
        'MESA': {'Jornada Líq. Eq.': 75, 'Dev. %': 0.46, 'Corte %': 0.45},
        'MANOBRISTA': {'Itens Manob.': 250000, 'Dev. %': 0.46, 'Avaria': 0.07},
        'LÍDER': {'Jornada Líq. Eq.': 75, 'Dev. %': 0.46, 'Itens/Hora Eq.': 75}
    },
    'T2': {
        'AVARIA': {'Avaria': 0.07},
        'CONFERENTE': {'Itens Conf.': 120000, 'Dev. %': 0.46},
        'DEVOLUÇÃO': {'Dev. %': 0.46},
        'INVENTARIO': {'Corte %': 0.45},
        'LÍDER': {'Ressup. Eq.': 11000, 'Dev. %': 0.46, 'Itens/Hora Eq.': 65},
        'MESA': {'Ressup. Eq.': 11000, 'Dev. %': 0.46, 'Itens/Hora Eq.': 65},
        'OPERADOR': {'Mov. Horizontal': 1800, 'Avaria': 0.07},
        'RAMPEIRO': {'Itens Rampa': 45000, 'Dev. %': 0.46, 'Avaria': 0.07},
        'SEPARADOR G': {'Ressup. Ap.': 800, 'Itens/Hora': 65}
    },
    'T1': {
        'CONFERENTE': {'Palets Conf.': 2500},
        'DESCARGA': {'Carga Palet.': 3700, 'Carga Bat.': 1500},
        'DEVOLUÇÃO': {'Dev. %': 0.46},
        'LÍDER': {'Palets Conf.': 2500}, 
        'OPERADOR': {'Mov. Vert.': 2750},
        'PUXA': {'Palets Px.': 3000}
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS DA NUVEM
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
    
    colunas_desejadas = [
        'CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Itens/Hora Eq.', 'Horas', 
        'Itens/Hora', 'Ressup. Ap.', 'Erros', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 
        'Mov. Horizontal', 'Mov. Vert.', 'Avaria', 'Corte %', 'Dev. %', 'Itens Conf.', 
        'Conf Base', 'Itens Manob.', 'Itens Rampa', 'Carga Bat.', 'Carga Palet.', 
        'Palets Px.', 'Palets Conf.', 'Jornada Líq. Eq.'
    ]
    
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    df = df[colunas_existentes]
    
    # TRATAMENTO ANTI-ERRO (MAIÚSCULAS)
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()

    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
    colunas_numericas = [col for col in df.columns if col not in colunas_texto]

    for col in colunas_numericas:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Jornada Líq.' in df.columns and df['Jornada Líq.'].mean() < 2: 
        df['Jornada Líq.'] = df['Jornada Líq.']
        
    return df

# ==========================================
# 4. CONSTRUÇÃO DA TELA E FILTROS
# ==========================================
try:
    df = carregar_dados()

    # --- BARRA LATERAL (FILTROS EM LISTA) ---
    st.sidebar.title("🔍 Filtros do Painel")
    
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)

    if turno_selecionado != "Todos":
        df_filtrado = df[df['TURNO'] == turno_selecionado].copy()
    else:
        df_filtrado = df.copy()

    lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
    cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
    
    if cargo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

    lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
    pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)

    # --- CÁLCULO DO PERÍODO ---
    hoje = datetime.date.today()
    if hoje.day >= 26:
        dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    else:
        mes_ant = hoje.month - 1 if hoje.month > 1 else 12
        ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
        dt_inicio = datetime.date(ano_ant, mes_ant, 26)
    
    dt_inicio_str = dt_inicio.strftime('%d/%m/%Y')
    dt_fim_str = hoje.strftime('%d/%m/%Y')

    # --- LINHA 1: TÍTULO E KPIS GERAIS ---
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.markdown("Acompanhamento de desempenho da equipe.")
        st.info(f"📅 **Período Apurado:** de {dt_inicio_str} até {dt_fim_str}")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral do Período")
        kpi1, kpi2, kpi3 = st.columns(3)

        total_itens = df_filtrado['Itens Sep'].sum() if 'Itens Sep' in df_filtrado.columns else 0
        media_velocidade = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean() if 'Itens/Hora' in df_filtrado.columns else 0
        if pd.isna(media_velocidade): media_velocidade = 0
        
        # BLINDAGEM DAS HORAS NEGATIVAS
        if 'Horas' in df_filtrado.columns:
            total_horas = df_filtrado.loc[df_filtrado['Horas'] > 0, 'Horas'].sum()
        else:
            total_horas = 0

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_velocidade:.0f}")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # --- BLOCO DE METAS INDIVIDUAIS ---
    # --- BLOCO DE METAS INDIVIDUAIS E FINANCEIRO ---
    if pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento do Colaborador: {pessoa_selecionada}")
        
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        
        if not dados_pessoa.empty:
            turno_p = dados_pessoa['TURNO'].values[0]
            cargo_p = dados_pessoa['FUNÇÃO'].values[0]
            metas_cargo = metas_100.get(turno_p, {}).get(cargo_p, {})
            
            # Variável para acumular o dinheiro do colaborador
            bonus_acumulado = 0.0 
            
            if metas_cargo:
                cols_meta = st.columns(len(metas_cargo))
                for idx, (ind, valor_meta) in enumerate(metas_cargo.items()):
                    if ind in dados_pessoa.columns:
                        realizado = dados_pessoa[ind].values[0]
                        
                        # Inverte a lógica para % de erros (Quanto menor, melhor)
                        if ind in ['Avaria', 'Dev. %', 'Corte %']:
                            atingimento = (valor_meta / realizado * 100) if realizado > 0 else 100
                        else:
                            atingimento = (realizado / valor_meta * 100) if valor_meta > 0 else 0
                        
                        # ==========================================
                        # LÓGICA FINANCEIRA (A SER REFINADA POR VOCÊ)
                        # ==========================================
                        # Exemplo genérico: Se atingiu 100%, ganha R$ 150 naquele indicador
                        if atingimento >= 100:
                            bonus_acumulado += 150.00
                        elif atingimento >= 50:
                            bonus_acumulado += 75.00 # Ganha metade se bateu 50%
                            
                        with cols_meta[idx]:
                            st.metric(
                                label=f"{ind} (Meta: {valor_meta})", 
                                value=f"{realizado:.2f}", 
                                delta=f"{atingimento:.1f}% da meta",
                                delta_color="normal" if ind not in ['Avaria', 'Dev. %', 'Corte %'] else "inverse"
                            )
                
                # --- PAINEL FINANCEIRO (NOVO) ---
                st.markdown("<br>", unsafe_allow_html=True) # Espaçamento
                st.success(f"💰 **Premiação Variável Acumulada Estimada:** R$ {bonus_acumulado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                
            else:
                st.warning(f"Metas não cadastradas para o cargo: {cargo_p} ({turno_p}).")
        st.divider()

    # --- TABELA DINÂMICA (FULL WIDTH) ---
    st.markdown("### 📋 Tabela de Produtividade Consolidada")
    
    df_tabela = df_filtrado.sort_values(by='NOME', ascending=True)
    
    configuracao_colunas = {}
    for col in df_tabela.columns:
        if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']:
            continue 
        elif col in ['Avaria', 'Corte %', 'Dev. %']:
            configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
        elif "Líq." in col:
            configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
        elif col == "Horas":
            configuracao_colunas[col] = st.column_config.NumberColumn(col, format="%.2f")
        else:
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
