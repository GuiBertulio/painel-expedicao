import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Monitor de Produtividade", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem !important; }
    [data-testid="stMetricValue"] { font-size: 45px !important; color: #004aad; }
    [data-testid="stMetricLabel"] > div { font-size: 18px !important; color: gray; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. DICIONÁRIO DE METAS (MATRIZ 100%)
# ==========================================
# Preencha com os valores reais da sua matriz de 100%
metas_100 = {
    'T3': {
        'SEPARADOR F': {'Jornada Líq.': 80, 'Itens Sep': 9000},
        'SEPARADOR G': {'Jornada Líq.': 72, 'Itens Sep': 8100},
        'CONFERENTE': {'Itens Conf.': 110000, 'Dev. %': 0.46},
        'OPERADOR': {'Mov. Horizontal': 1800, 'Avaria': 0.07},
        'RAMPEIRO': {'Itens Rampa': 45000, 'Dev. %': 0.46},
        'MANOBRISTA': {'Itens Manob.': 250000, 'Avaria': 0.07}
    },
    'T1': {
        'CONFERENTE': {'Palets Conf.': 2500},
        'OPERADOR': {'Mov. Vert.': 2750}
    },
    'T2': {
        'SEPARADOR G': {'Ressup. Ap.': 500, 'Itens/Hora': 150} # Exemplo, ajuste conforme sua base
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS DA NUVEM
# ==========================================
@st.cache_data(ttl=300) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df_raw = pd.read_csv(link_csv)
    df_raw.columns = df_raw.columns.astype(str).str.strip()

    # Se a base vier no formato Longo (Power Query), ele pivota para formato de Tabela Larga
    if 'Indicador' in df_raw.columns and 'Resultado' in df_raw.columns:
        df = df_raw.pivot_table(
            index=['Data', 'NOME', 'TURNO', 'FUNÇÃO'], 
            columns='Indicador', 
            values='Resultado',
            aggfunc='sum'
        ).reset_index()
        df.columns.name = None
    else:
        df = df_raw.copy()

    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])

    # Garante que a coluna de data seja lida como Calendário
    col_data = 'Data' if 'Data' in df.columns else df.columns[0]
    df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.date

    # Tratamento Numérico
    colunas_texto = [col_data, 'CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
    for col in df.columns:
        if col not in colunas_texto:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Ajuste de Jornada para %
            if "Líq." in col and df[col].mean() < 2:
                df[col] = df[col] * 100
                
    return df, col_data

# ==========================================
# 4. CONSTRUÇÃO DA TELA E BARRA LATERAL
# ==========================================
try:
    df, col_data = carregar_dados()
    hoje = datetime.date.today()

    st.sidebar.title("🔍 Painel de Filtros")
    
    # Filtro 1: Data (Diário)
    data_sel = st.sidebar.date_input("1. Escolha o Dia:", hoje)
    df_dia = df[df[col_data] == data_sel].copy()

    # Filtro 2: Turno
    turnos_disp = sorted(df_dia['TURNO'].dropna().unique().tolist())
    turno_sel = st.sidebar.multiselect("2. Turno:", turnos_disp, default=turnos_disp)
    df_filtrado = df_dia[df_dia['TURNO'].isin(turno_sel)] if turno_sel else df_dia

    # Filtro 3: Cargo
    cargos_disp = sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
    cargo_sel = st.sidebar.multiselect("3. Cargo / Função:", cargos_disp, default=cargos_disp)
    if cargo_sel:
        df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'].isin(cargo_sel)]

    # Filtro 4: Indicadores (Colunas da Tabela)
    colunas_base = [col_data, 'CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
    indicadores_disp = [c for c in df.columns if c not in colunas_base]
    indicador_sel = st.sidebar.multiselect("4. Indicadores na Tabela:", indicadores_disp, default=indicadores_disp[:5] if len(indicadores_disp) > 5 else indicadores_disp)

    # Filtro 5: Pessoa (Metas)
    pessoas_disp = sorted(df_filtrado['NOME'].dropna().unique().tolist())
    pessoa_sel = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", ["Nenhum"] + pessoas_disp)

    # ==========================================
    # 5. ÁREA PRINCIPAL DO DASHBOARD
    # ==========================================
    st.title("📋 Monitor de Produtividade")
    st.markdown(f"**Visão Quantitativa Diária:** {data_sel.strftime('%d/%m/%Y')}")

    # Bloco de Metas Individuais
    if pessoa_sel != "Nenhum":
        st.divider()
        st.subheader(f"🎯 Atingimento de Metas: {pessoa_sel}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_sel]
        
        if not dados_pessoa.empty:
            turno_p = dados_pessoa['TURNO'].values[0]
            cargo_p = dados_pessoa['FUNÇÃO'].values[0]
            metas_cargo = metas_100.get(turno_p, {}).get(cargo_p, {})
            
            if metas_cargo:
                cols_meta = st.columns(len(metas_cargo))
                for idx, (ind, valor_meta) in enumerate(metas_cargo.items()):
                    if ind in dados_pessoa.columns:
                        realizado = dados_pessoa[ind].values[0]
                        
                        # Calcula a % de atingimento (Se for erro/avaria, inverte a lógica)
                        if ind in ['Avaria', 'Dev. %', 'Corte %']:
                            atingimento = (valor_meta / realizado * 100) if realizado > 0 else 100
                        else:
                            atingimento = (realizado / valor_meta * 100) if valor_meta > 0 else 0
                        
                        with cols_meta[idx]:
                            st.metric(
                                label=f"{ind} (Meta: {valor_meta})", 
                                value=f"{realizado:.2f}", 
                                delta=f"{atingimento:.1f}% da meta atingida",
                                delta_color="normal" if ind not in ['Avaria', 'Dev. %', 'Corte %'] else "inverse"
                            )
            else:
                st.warning(f"Metas não cadastradas no sistema para o cargo: {cargo_p} ({turno_p}).")

    st.divider()

    # Tabela Dinâmica Gigante
    if df_filtrado.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # Prepara as colunas que vão aparecer na tabela
        colunas_mostrar = ['NOME', 'TURNO', 'FUNÇÃO'] + indicador_sel
        df_tabela = df_filtrado[colunas_mostrar].sort_values(by='NOME', ascending=True)

        # Formatação Visual da Tabela
        config_colunas = {}
        for col in df_tabela.columns:
            if col in ['NOME', 'TURNO', 'FUNÇÃO']:
                continue
            elif col in ['Avaria', 'Corte %', 'Dev. %']:
                config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
            elif "Líq." in col:
                config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
            elif col == "Horas":
                config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f h")
            else:
                config_colunas[col] = st.column_config.NumberColumn(col, format="%d")

        st.dataframe(
            df_tabela, 
            hide_index=True, 
            use_container_width=True,
            height=600,
            column_config=config_colunas
        )

except Exception as e:
    st.error(f"⚠️ Erro ao carregar os dados: {e}")
