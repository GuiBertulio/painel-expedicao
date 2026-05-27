import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

# ==========================================
# CONEXÃO COM GOOGLE SHEETS
# ==========================================
def conectar_planilha():
    cred_dict = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(cred_dict)
    planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")
    return planilha.worksheet("Historico_RH")

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .card-meta { background-color: var(--background-color); padding: 15px; border-radius: 10px; border-left: 8px solid #ccc; margin-bottom: 15px; }
    .card-detrator { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; margin-bottom: 15px; }
    .texto-card-principal { font-size: 42px; color: var(--text-color); font-weight: 900; line-height: 1.1; }
    .texto-card-titulo { font-size: 22px; color: var(--text-color); font-weight: 900; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)
C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# ==========================================
# 2. DICIONÁRIO DE METAS
# ==========================================
metas_100 = {
    'T3': {
        'SEPARADOR F': {'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 75, 't100': 80, 't120': 85}, 'Itens Sep': {'tipo': '>', 'prop': True, 'v100': 150.0, 't50': 7000, 't100': 9000, 't120': 11000}, 'Itens/Hora': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 60, 't100': 75, 't120': 90}},
        'SEPARADOR G': {'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 68, 't100': 72, 't120': 77}, 'Itens Sep': {'tipo': '>', 'prop': True, 'v100': 150.0, 't50': 6300, 't100': 8100, 't120': 9900}, 'Itens/Hora': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 60, 't100': 75, 't120': 90}},
        'CONFERENTE': {'Itens Conf.': {'tipo': '>', 'prop': True, 'v100': 350.0, 't50': 80000, 't100': 110000, 't120': 140000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}},
        'OPERADOR': {'Mov. Horizontal': {'tipo': '>', 'prop': True, 'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400}, 'Avaria': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'CARREGAMENTO BOX': {'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Avaria': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'MESA': {'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 65, 't100': 75, 't120': 85}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Corte %': {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.65, 't100': 0.45, 't120': 0.25}},
        'MANOBRISTA': {'Itens Manob.': {'tipo': '>', 'prop': True, 'v100': 350.0, 't50': 200000, 't100': 250000, 't120': 300000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Avaria': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'LÍDER': {'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 65, 't100': 75, 't120': 85}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 240.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Itens/Hora Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 60, 't100': 75, 't120': 90}}
    },
    'T2': {
        'AVARIA': {'Avaria': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'CONFERENTE': {'Itens Conf.': {'tipo': '>', 'prop': True, 'v100': 300.0, 't50': 90000, 't100': 120000, 't120': 150000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}},
        'DEVOLUÇÃO': {'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}},
        'INVENTARIO': {'Corte %': {'tipo': '<', 'prop': False, 'v100': 200.0, 't50': 0.65, 't100': 0.45, 't120': 0.25}},
        'LÍDER': {'Ressup. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 8000, 't100': 11000, 't120': 14000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 240.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Itens/Hora Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 50, 't100': 65, 't120': 80}},
        'MESA': {'Ressup. Eq.': {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 8000, 't100': 11000, 't120': 14000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Itens/Hora Eq.': {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 50, 't100': 65, 't120': 80}},
        'OPERADOR': {'Mov. Horizontal': {'tipo': '>', 'prop': True, 'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400}, 'Avaria': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'RAMPEIRO': {'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000}, 'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}, 'Avaria': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}},
        'SEPARADOR G': {'Ressup. Ap.': {'tipo': '>', 'prop': True, 'v100': 200.0, 't50': 600, 't100': 800, 't120': 1000}, 'Itens/Hora': {'tipo': '>', 'prop': False, 'v100': 200.0, 't50': 50, 't100': 65, 't120': 80}}
    },
    'T1': {
        'CONFERENTE': {'Palets Conf.': {'tipo': '>', 'prop': True, 'v100': 300.0, 't50': 1750, 't100': 2500, 't120': 3250}, 'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}},
        'DESCARGA': {'Carga Palet.': {'tipo': '>', 'prop': False, 'v100': 125.0, 't50': 3000, 't100': 3700, 't120': 4400}, 'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 125.0, 't50': 3900, 't100': 3300, 't120': 2700}, 'Carga Bat.': {'tipo': '>', 'prop': False, 'v100': 125.0, 't50': 1000, 't100': 1500, 't120': 2000}},
        'DEVOLUÇÃO': {'Dev. %': {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}},
        'LÍDER': {'Méd. Palets Conf.': {'tipo': '>', 'prop': False, 'v100': 300.0, 't50': 1750, 't100': 2500, 't120': 3250}, 'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 300.0, 't50': 3900, 't100': 3300, 't120': 2700}},
        'OPERADOR': {'Mov. Vert.': {'tipo': '>', 'prop': True, 'v100': 350.0, 't50': 2000, 't100': 2750, 't120': 3500}, 'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}},
        'PUXA': {'Palets Px.': {'tipo': '>', 'prop': True, 'v100': 200.0, 't50': 1800, 't100': 3000, 't120': 4200}, 'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}}
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Auto-corretor de colunas
    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if "MED" in nome_limpo and ("PALET" in nome_limpo or "PALLET" in nome_limpo): df = df.rename(columns={c: 'Méd. Palets Conf.'})
        elif "JORNADA" in nome_limpo and "EQ" in nome_limpo: df = df.rename(columns={c: 'Jornada Líq. Eq.'})
        elif "RESSUP" in nome_limpo and "EQ" in nome_limpo: df = df.rename(columns={c: 'Ressup. Eq.'})
        elif "TRAB" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Trabalhados'})
        elif "META" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Meta'})
        elif ("UT" in nome_limpo or "ÚT" in nome_limpo) and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Uteis'})
        elif "DATA" in nome_limpo and ("INICIO" in nome_limpo or "INÍCIO" in nome_limpo or "INICIAL" in nome_limpo): df = df.rename(columns={c: 'Data Inicio'})
        elif "DATA" in nome_limpo and ("FIM" in nome_limpo or "FINAL" in nome_limpo or "APURA" in nome_limpo): df = df.rename(columns={c: 'Data Fim'})
    
    if 'NOME' in df.columns: df = df.dropna(subset=['NOME'])
    if 'FUNÇÃO' in df.columns: df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns: df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
    
    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Data Inicio', 'Data Fim']
    for col in df.columns:
        if col not in colunas_texto:
            if col == 'Tempo Médio': 
                texto_limpo = df[col].astype(str).str.split('.').str[0].str.strip()
                df[col] = pd.to_timedelta(texto_limpo, errors='coerce').dt.total_seconds().fillna(0)
            else:
                texto_limpo = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(texto_limpo, errors='coerce').fillna(0)
    
    return df

df = carregar_dados()

# ==========================================
# 4. LÓGICA DE DATAS
# ==========================================
if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
    dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0], dayfirst=True).date()
    data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0], dayfirst=True).date()
    dt_fim_ciclo = data_apuracao
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)
    dt_fim_ciclo = datetime.date(hoje.year, hoje.month, 25)

dias_totais_range = pd.date_range(start=dt_inicio, end=dt_fim_ciclo)
dias_uteis_totais = dias_totais_range[dias_totais_range.weekday != 6]
dias_decorridos_range = pd.date_range(start=dt_inicio, end=data_apuracao)
dias_decorridos = dias_decorridos_range[dias_decorridos_range.weekday != 6]
DIAS_UTEIS_MES = float(len(dias_uteis_totais))
DIAS_DECORRIDOS = float(len(dias_decorridos))
FATOR_PROPORCIONAL = DIAS_DECORRIDOS / DIAS_UTEIS_MES

# ==========================================
# 5. CONSTRUÇÃO DA TELA
# ==========================================
st.sidebar.title("🔍 Filtros do Painel")
lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()

lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
focar_detratores = st.sidebar.checkbox("🚨 Filtrar Desempenho Abaixo da Meta")

# ==========================================
# 🔥 MÓDULO DE EXTRAÇÃO RH (CORRIGIDO)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗃️ Fechamento RH")
dados_rh = []

for nome_colab in df_filtrado['NOME'].unique():
    row = df_filtrado[df_filtrado['NOME'] == nome_colab].iloc[0]
    turno_c, cargo_c, cod_c = row['TURNO'], row['FUNÇÃO'], row['CÓD.']
    
    val_du = float(row.get('Dias Uteis', 0))
    dias_uteis_excel = val_du if pd.notna(val_du) and val_du > 0 else DIAS_UTEIS_MES
    val_dt = float(row.get('Dias Trabalhados', 0))
    d_trab = val_dt if pd.notna(val_dt) and val_dt > 0 else dias_uteis_excel
    val_dm = float(row.get('Dias Meta', 0))
    d_meta = val_dm if pd.notna(val_dm) and val_dm > 0 else dias_uteis_excel
    
    fator_premio = d_trab / dias_uteis_excel
    metas_c = metas_100.get(turno_c, {}).get(cargo_c, {})
    premio_total = 0.0
    
    if metas_c:
        for ind, regra in metas_c.items():
            # AQUI ESTAVA O ERRO: validamos se a coluna existe antes de processar
            if ind in row.index:
                realizado = float(row[ind])
                tipo = regra['tipo']
                if d_meta > 0: proporcao_meta = dias_uteis_excel / d_meta
                else: proporcao_meta = 1.0
                
                if regra['prop']:
                    t50 = regra['t50'] * proporcao_meta
                    t100 = regra['t100'] * proporcao_meta
                    t120 = regra['t120'] * proporcao_meta
                else:
                    t50, t100, t120 = regra['t50'], regra['t100'], regra['t120']
                
                v100 = regra['v100'] * fator_premio
                
                if tipo == '>':
                    if realizado >= t120: premio_total += v100 * 1.2
                    elif realizado >= t100: premio_total += v100
                    elif realizado >= t50: premio_total += v100 * 0.5
                else:
                    if pd.notna(realizado) and realizado > 0:
                        if realizado <= t120: premio_total += v100 * 1.2
                        elif realizado <= t100: premio_total += v100
                        elif realizado <= t50: premio_total += v100 * 0.5
        
        # Ranking
        metrica_rank = next((ind for ind, r in metas_c.items() if r['prop']), list(metas_c.keys())[0])
        if metrica_rank in df.columns:
            df_eq = df[(df['TURNO'] == turno_c) & (df['FUNÇÃO'] == cargo_c)].copy()
            ordem_cresc = False if metas_c[metrica_rank]['tipo'] == '>' else True
            df_eq = df_eq.sort_values(by=metrica_rank, ascending=ordem_cresc).reset_index(drop=True)
            try:
                pos = df_eq[df_eq['NOME'] == nome_colab].index[0] + 1
                if pos == 1: val_rank = 250.0 if turno_c == 'T3' and 'SEPARADOR' in cargo_c else (150.0 if turno_c == 'T2' and 'SEPARADOR' in cargo_c else 0.0)
                elif pos == 2: val_rank = 200.0 if turno_c == 'T3' and 'SEPARADOR' in cargo_c else (100.0 if turno_c == 'T2' and 'SEPARADOR' in cargo_c else 0.0)
                elif pos == 3: val_rank = 100.0 if turno_c == 'T3' and 'SEPARADOR' in cargo_c else (50.0 if turno_c == 'T2' and 'SEPARADOR' in cargo_c else 0.0)
                else: val_rank = 0.0
                premio_total += (val_rank * fator_premio)
            except: pass
    
    dados_rh.append({'Matrícula': cod_c, 'Nome': nome_colab, 'Premiação (R$)': round(premio_total, 2)})

if dados_rh:
    df_rh = pd.DataFrame(dados_rh).sort_values(by='Nome')
    st.sidebar.dataframe(df_rh.style.format({'Premiação (R$)': 'R$ {:,.2f}'}), hide_index=True, use_container_width=True)
    csv_rh = df_rh.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.sidebar.download_button("📥 Baixar Planilha do RH", csv_rh, f"Fechamento_RH_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv", "text/csv", type="primary", use_container_width=True)
    else:
        st.sidebar.info("Nenhum dado processado.")

    # ==========================================
    # 🌟 CABEÇALHO E KPIs GERAIS
    # ==========================================
    col_titulo, col_kpis = st.columns([1, 1.2])
    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')} | 🏢 **{dias_decorridos_base} Dias Processados de {dias_uteis_base}**")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral do Período")
        kpi1, kpi2, kpi3 = st.columns(3)
        
        # Como as colunas reais mudam dinamicamente, vamos somar e fazer médias buscando os termos nos Indicadores
        vol_total = 0
        hora_total = 0
        
        for n in range(1, 5):
            nome_col = f'Ind_{n}_Nome'
            real_col = f'Ind_{n}_Realizado'
            if nome_col in df_filtrado.columns and real_col in df_filtrado.columns:
                # Soma tudo que parece "Volume"
                mascara_vol = df_filtrado[nome_col].astype(str).str.contains('Itens|Carga|Palets|Mov', case=False, na=False)
                vol_total += df_filtrado.loc[mascara_vol, real_col].sum()

        kpi1.metric("📦 Volume Total Geral", f"{vol_total:,.0f}".replace(',', '.'))
        kpi2.metric("👥 Colaboradores Ativos", f"{len(df_filtrado)}")
        
        if 'Horas' in df_filtrado.columns: hora_total = df_filtrado['Horas'].sum()
        kpi3.metric("⏱️ Horas Registradas", f"{hora_total:.1f} h" if hora_total > 0 else "-")

    st.divider()

    # ==========================================
    # 🚨 MÓDULO DETRATORES
    # ==========================================
    if focar_detratores:
        st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
        houve_detrator = False
        
        for idx, row in df_filtrado.iterrows():
            detalhes_gargalo = []
            
            for n in range(1, 5):
                nome_ind = row.get(f'Ind_{n}_Nome', '-')
                if pd.notna(nome_ind) and str(nome_ind).strip() != '-' and str(nome_ind).strip() != '0':
                    perc = row.get(f'Ind_{n}_Perc', 0)
                    realizado = row.get(f'Ind_{n}_Realizado', 0)
                    alvo = row.get(f'Ind_{n}_Alvo_100', 0)
                    
                    # Se o percentual do Excel for menor que 100% (ou 1.0)
                    if perc < 1.0:
                        if "%" in str(nome_ind) or "Avaria" in str(nome_ind) or perc < 0.10: # Formatação
                            detalhes_gargalo.append(f"❌ {nome_ind}: {realizado * 100:.2f}% atingido vs Alvo {alvo * 100:.2f}%")
                        else:
                            detalhes_gargalo.append(f"❌ {nome_ind}: {realizado:,.0f} atingido vs Alvo {alvo:,.0f}".replace(',','.'))
                            
            if detalhes_gargalo:
                houve_detrator = True
                nome_c, cod_c, cargo_c, turno_c = row['NOME'], row['CÓD.'], row['FUNÇÃO'], row['TURNO']
                d_trab = int(row.get('Dias Trabalhados', 0))
                
                with st.container():
                    st.markdown(f"<div class='card-detrator'><span style='font-size: 22px; font-weight: bold; color: {C_VERMELHO};'>⚠️ [{cod_c}] {nome_c}</span><br><b>Turno:</b> {turno_c} | <b>Função:</b> {cargo_c} | <b>Dias Lançados:</b> {d_trab} dias<br><br><span style='font-weight: bold; color: #ffca28;'>Pontos de Desvio Identificados:</span><br>{'<br>'.join(detalhes_gargalo)}</div>", unsafe_allow_html=True)
                    
                    col_feed, col_trein = st.columns(2)
                    with col_feed:
                        with st.expander(f"💬 Registrar Feedback: {nome_c}"):
                            with st.form(key=f"form_feed_{idx}"):
                                texto_feedback = st.text_area("Descreva o que foi conversado:")
                                if st.form_submit_button("Salvar no Histórico"):
                                    if texto_feedback:
                                        try:
                                            aba_rh = conectar_planilha()
                                            agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                            aba_rh.append_row([agora, str(cod_c), nome_c, "Feedback", texto_feedback])
                                            st.success("✅ Salvo!")
                                        except Exception as e: st.error(f"Erro: {e}")
                                    else: st.error("⚠️ Digite algo.")

                    with col_trein:
                        with st.expander(f"🎯 Solicitar Reciclagem: {nome_c}"):
                            with st.form(key=f"form_trein_{idx}"):
                                motivo = st.selectbox("Gargalo:", ["Velocidade", "Erros/Avarias", "Sistema", "Processo"])
                                if st.form_submit_button("Enviar Solicitação"):
                                    try:
                                        aba_rh = conectar_planilha()
                                        agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                        aba_rh.append_row([agora, str(cod_c), nome_c, "Reciclagem", motivo])
                                        st.success("📧 Enviado!")
                                    except Exception as e: st.error(f"Erro: {e}")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
        if not houve_detrator: st.success("🎉 Nenhum detrator encontrado!")

    # ==========================================
    # 👁️ VISÃO INDIVIDUAL DO COLABORADOR
    # ==========================================
    elif pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        
        if not dados_pessoa.empty:
            row = dados_pessoa.iloc[0]
            cols_meta = st.columns(4) 
            col_idx = 0
            grafico_dados = []
            
            for n in range(1, 5):
                nome_ind = row.get(f'Ind_{n}_Nome', '-')
                if pd.notna(nome_ind) and str(nome_ind).strip() != '-' and str(nome_ind).strip() != '0':
                    
                    realizado = row.get(f'Ind_{n}_Realizado', 0)
                    alvo_100 = row.get(f'Ind_{n}_Alvo_100', 0)
                    perc_atingimento = row.get(f'Ind_{n}_Perc', 0)
                    valor_reais = row.get(f'Ind_{n}_Valor', 0)
                    
                    # Converte decimal pra % pra não dar bug no gráfico
                    real_perc = perc_atingimento * 100 if perc_atingimento <= 2.0 else perc_atingimento 
                    grafico_dados.append({'Indicador': f"<b>{nome_ind}</b>", 'Atingimento (%)': min(real_perc, 120), 'Real': real_perc})
                    
                    if real_perc >= 120: cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif real_perc >= 100: cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif real_perc >= 50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                        
                    html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""
                    
                    if "Tempo" in str(nome_ind) or ":" in str(realizado):
                         val_tela, alvo_tela = str(realizado), str(alvo_100)
                    elif "%" in str(nome_ind) or "Avaria" in str(nome_ind):
                        val_tela = f"{realizado * 100:.2f}%" if realizado < 1 else f"{realizado:.2f}%"
                        alvo_tela = f"{alvo_100 * 100:.2f}%" if alvo_100 < 1 else f"{alvo_100:.2f}%"
                    else:
                        val_tela = f"{realizado:,.0f}".replace(',', '.')
                        alvo_tela = f"{alvo_100:,.0f}".replace(',', '.')

                    with cols_meta[col_idx]:
                        st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{nome_ind} (Alvo: {alvo_tela})</div><div class='texto-card-principal'>{val_tela}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status} {html_dinheiro}</div></div>", unsafe_allow_html=True)
                    
                    col_idx += 1
            
            valor_final = row.get('Valor Final', 0)
            if valor_final > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {valor_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

            st.divider()
            st.markdown(f"### 📊 Análise de {pessoa_selecionada}")
            
            if grafico_dados:
                df_grafico = pd.DataFrame(grafico_dados)
                df_grafico['Cor'] = df_grafico['Real'].apply(lambda x: C_AZUL if x >= 120 else (C_VERDE if x >= 100 else (C_AMARELO if x >= 50 else C_VERMELHO)))
                df_grafico['Texto_Cor'] = df_grafico['Cor'].apply(lambda color: "black" if color == C_AMARELO else "white")
                fig = px.bar(df_grafico, x='Indicador', y='Atingimento (%)', text=df_grafico['Real'].apply(lambda x: f"<b>{x:.1f}%</b>"))
                fig.update_layout(showlegend=False, yaxis_title="<b>% da Meta Atingida</b>", xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(t=15, b=0, l=0, r=0))
                fig.add_hline(y=100, line_dash="dash", line_color="lightgray", annotation_text="<b>Meta 100%</b>", annotation_font_color="lightgray")
                fig.update_traces(textfont=dict(size=24, color=df_grafico['Texto_Cor'].tolist()), marker=dict(color=df_grafico['Cor'].tolist(), line=dict(color='white', width=1)))
                fig.update_xaxes(tickfont=dict(size=20, color="lightgray", family="Arial Black"))
                fig.update_yaxes(tickfont=dict(size=14, color="lightgray"), title_font=dict(color="lightgray"))
                st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 👥 VISÃO GERAL EQUIPE (MÉDIAS)
    # ==========================================
    else:
        cargos_render = [cargo_selecionado] if cargo_selecionado != "Todos" else sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
        
        for cargo_atual in cargos_render:
            df_cargo = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_atual]
            if df_cargo.empty: continue
            
            st.markdown(f"<h4 style='color: lightgray; margin-top: 15px;'>🔹 Média da Equipe: {cargo_atual}</h4>", unsafe_allow_html=True)
            cols_eq = st.columns(4)
            col_idx = 0
            
            for n in range(1, 5):
                nome_col_ind = f'Ind_{n}_Nome'
                if nome_col_ind in df_cargo.columns:
                    # Pega o nome do indicador (o mais comum pra essa função)
                    nomes_validos = df_cargo[df_cargo[nome_col_ind] != '-'][nome_col_ind]
                    if nomes_validos.empty or str(nomes_validos.mode()[0]) == '0': continue
                    
                    nome_ind_equipe = nomes_validos.mode()[0]
                    real_med = df_cargo[f'Ind_{n}_Realizado'].mean()
                    alvo_med = df_cargo[f'Ind_{n}_Alvo_100'].mean()
                    perc_med = df_cargo[f'Ind_{n}_Perc'].mean()
                    soma_total = df_cargo[f'Ind_{n}_Realizado'].sum()
                    
                    real_perc = perc_med * 100 if perc_med <= 2.0 else perc_med
                    
                    if real_perc >= 120: cor, icone, status = C_AZUL, "🔵", "Superando"
                    elif real_perc >= 100: cor, icone, status = C_VERDE, "🟢", "Na Meta"
                    elif real_perc >= 50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                    
                    if "Tempo" in str(nome_ind_equipe):
                         v_tela, t_tela, html_soma = f"{real_med:.0f}", f"{alvo_med:.0f}", ""
                    elif "%" in str(nome_ind_equipe) or "Avaria" in str(nome_ind_equipe):
                        v_tela = f"{real_med * 100:.2f}%" if real_med < 1 else f"{real_med:.2f}%"
                        t_tela = f"{alvo_med * 100:.2f}%" if alvo_med < 1 else f"{alvo_med:.2f}%"
                        html_soma = ""
                    else:
                        v_tela = f"{real_med:,.0f}".replace(',','.')
                        t_tela = f"{alvo_med:,.0f}".replace(',','.')
                        html_soma = f"<span class='texto-card-secundario'>| Soma Equipe: {soma_total:,.0f}</span>".replace(',', '.')
                        
                    with cols_eq[col_idx]:
                        st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>Média: {nome_ind_equipe} (Alvo: {t_tela})</div><div class='texto-card-principal'>{v_tela} {html_soma}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div></div>", unsafe_allow_html=True)
                    
                    col_idx += 1
        
        if len(cargos_render) > 0: st.divider()

        st.markdown("### 📋 Tabela de Produtividade Consolidada (Relatório Gerencial)")
        colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final']
        
        # Puxa dinamicamente as colunas de "Perc" (Atingimento) para a tabela de resumo
        for n in range(1, 5):
            nome_col = f'Ind_{n}_Perc'
            if nome_col in df_filtrado.columns:
                colunas_exibicao.append(nome_col)

        df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()
        
        # Converte as colunas Perc para % bonito na tabela
        for col in df_tabela.columns:
            if 'Perc' in col:
                df_tabela[col] = df_tabela[col].apply(lambda x: f"{x * 100:.1f}%" if x <= 2.0 else f"{x:.1f}%")
                
        df_tabela = df_tabela.rename(columns={'Ind_1_Perc': 'Ating. Ind 1', 'Ind_2_Perc': 'Ating. Ind 2', 'Ind_3_Perc': 'Ating. Ind 3', 'Ind_4_Perc': 'Ating. Ind 4'})
        config = {'Valor Final': st.column_config.NumberColumn("Valor R$", format="R$ %.2f")}
        
        st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    st.error(f"⚠️ Erro ao renderizar painel: {e}")
