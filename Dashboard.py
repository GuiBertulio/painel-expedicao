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
        'SEPARADOR F': {
            'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 75, 't100': 80, 't120': 85},
            'Itens Sep':    {'tipo': '>', 'prop': True,  'v100': 150.0, 't50': 7000, 't100': 9000, 't120': 11000},
            'Itens/Hora':   {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 60, 't100': 75, 't120': 90}
        },
        'SEPARADOR G': {
            'Jornada Líq.': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 68, 't100': 72, 't120': 77},
            'Itens Sep':    {'tipo': '>', 'prop': True,  'v100': 150.0, 't50': 6300, 't100': 8100, 't120': 9900},
            'Itens/Hora':   {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 60, 't100': 75, 't120': 90}
        },
        'CONFERENTE': {
            'Itens Conf.':  {'tipo': '>', 'prop': True,  'v100': 350.0, 't50': 80000, 't100': 110000, 't120': 140000},
            'Dev. %':       {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}
        },
        'OPERADOR': {
            'Mov. Horizontal': {'tipo': '>', 'prop': True,  'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400},
            'Avaria':          {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'CARREGAMENTO BOX': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000},
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Avaria':      {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'MESA': {
            'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 65, 't100': 75, 't120': 85},
            'Dev. %':           {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Corte %':          {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.65, 't100': 0.45, 't120': 0.25}
        },
        'MANOBRISTA': {
            'Itens Manob.': {'tipo': '>', 'prop': True,  'v100': 350.0, 't50': 200000, 't100': 250000, 't120': 300000},
            'Dev. %':       {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Avaria':       {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'LÍDER': {
            'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 65, 't100': 75, 't120': 85},
            'Dev. %':           {'tipo': '<', 'prop': False, 'v100': 240.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Itens/Hora Eq.':   {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 60, 't100': 75, 't120': 90}
        }
    },
    'T2': {
        'AVARIA': {
            'Avaria':          {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'CONFERENTE': {
            'Itens Conf.': {'tipo': '>', 'prop': True,  'v100': 300.0, 't50': 90000, 't100': 120000, 't120': 150000},
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}
        },
        'DEVOLUÇÃO': {
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}
        },
        'INVENTARIO': {
            'Corte %':     {'tipo': '<', 'prop': False, 'v100': 200.0, 't50': 0.65, 't100': 0.45, 't120': 0.25}
        },
        'LÍDER': {
            'Ressup. Eq.':     {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 8000, 't100': 11000, 't120': 14000},
            'Dev. %':          {'tipo': '<', 'prop': False, 'v100': 240.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Itens/Hora Eq.':  {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 50, 't100': 65, 't120': 80}
        },
        'MESA': {
            'Ressup. Eq.':     {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 8000, 't100': 11000, 't120': 14000},
            'Dev. %':          {'tipo': '<', 'prop': False, 'v100': 220.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Itens/Hora Eq.':  {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 50, 't100': 65, 't120': 80}
        },
        'OPERADOR': {
            'Mov. Horizontal': {'tipo': '>', 'prop': True,  'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400},
            'Avaria':          {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'RAMPEIRO': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000},
            'Dev. %':      {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40},
            'Avaria':      {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 0.07, 't100': 0.07, 't120': 0.00}
        },
        'SEPARADOR G': {
            'Ressup. Ap.': {'tipo': '>', 'prop': True,  'v100': 200.0, 't50': 600, 't100': 800, 't120': 1000},
            'Itens/Hora':  {'tipo': '>', 'prop': False, 'v100': 200.0, 't50': 50, 't100': 65, 't120': 80}
        }
    },
    'T1': {
        'CONFERENTE': {
            'Palets Conf.': {'tipo': '>', 'prop': True,  'v100': 300.0, 't50': 1750, 't100': 2500, 't120': 3250},
            'Tempo Médio':  {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}
        },
        'DESCARGA': {
            'Carga Palet.': {'tipo': '>', 'prop': False, 'v100': 125.0, 't50': 3000, 't100': 3700, 't120': 4400},
            'Tempo Médio':  {'tipo': '<', 'prop': False, 'v100': 125.0, 't50': 3900, 't100': 3300, 't120': 2700},
            'Carga Bat.':   {'tipo': '>', 'prop': False, 'v100': 125.0, 't50': 1000, 't100': 1500, 't120': 2000}
        },
        'DEVOLUÇÃO': {
            'Dev. %':       {'tipo': '<', 'prop': False, 'v100': 150.0, 't50': 0.50, 't100': 0.46, 't120': 0.40}
        },
        'LÍDER': {
            'Méd. Palets Conf.': {'tipo': '>', 'prop': False, 'v100': 300.0, 't50': 1750, 't100': 2500, 't120': 3250},
            'Tempo Médio':       {'tipo': '<', 'prop': False, 'v100': 300.0, 't50': 3900, 't100': 3300, 't120': 2700}
        },
        'OPERADOR': {
            'Mov. Vert.':  {'tipo': '>', 'prop': True,  'v100': 350.0, 't50': 2000, 't100': 2750, 't120': 3500},
            'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}
        },
        'PUXA': {
            'Palets Px.':  {'tipo': '>', 'prop': True,  'v100': 200.0, 't50': 1800, 't100': 3000, 't120': 4200},
            'Tempo Médio': {'tipo': '<', 'prop': False, 'v100': 100.0, 't50': 3900, 't100': 3300, 't120': 2700}
        }
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS (BLINDADO)
# ==========================================
#@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 🔥 SUPER AUTO-CORRETOR PARA AS COLUNAS NOVAS
    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if "MED" in nome_limpo and ("PALET" in nome_limpo or "PALLET" in nome_limpo):
            df = df.rename(columns={c: 'Méd. Palets Conf.'})
        elif "JORNADA" in nome_limpo and "EQ" in nome_limpo:
            df = df.rename(columns={c: 'Jornada Líq. Eq.'})
        elif "RESSUP" in nome_limpo and "EQ" in nome_limpo:
            df = df.rename(columns={c: 'Ressup. Eq.'})
        elif "TRAB" in nome_limpo and "DIAS" in nome_limpo:
            df = df.rename(columns={c: 'Dias Trabalhados'})
        elif "META" in nome_limpo and "DIAS" in nome_limpo:
            df = df.rename(columns={c: 'Dias Meta'})
        elif ("UT" in nome_limpo or "ÚT" in nome_limpo) and "DIAS" in nome_limpo:
            df = df.rename(columns={c: 'Dias Uteis'})
        # Auto-corretor das Novas Colunas de Data (Planilha dita as regras)
        elif "DATA" in nome_limpo and ("INICIO" in nome_limpo or "INÍCIO" in nome_limpo or "INICIAL" in nome_limpo):
            df = df.rename(columns={c: 'Data Inicio'})
        elif "DATA" in nome_limpo and ("FIM" in nome_limpo or "FINAL" in nome_limpo or "APURA" in nome_limpo):
            df = df.rename(columns={c: 'Data Fim'})

    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
        
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()

    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Data Inicio', 'Data Fim']
    for col in df.columns:
        if col not in colunas_texto:
            if col == 'Tempo Médio': 
                texto_limpo = df[col].astype(str).str.split('.').str[0].str.strip()
                df[col] = pd.to_timedelta(texto_limpo, errors='coerce').dt.total_seconds().fillna(0)
            else:
                texto_limpo = df[col].astype(str).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(texto_limpo, errors='coerce').fillna(0)
    
    colunas_desejadas = [
        'CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Itens Sep', 'Itens/Hora Eq.', 'Horas', 
        'Itens/Hora', 'Ressup. Ap.', 'Erros', 'Jornada Líq.', 'Ressup.', 'Ressup. Eq.', 
        'Mov. Horizontal', 'Mov. Vert.', 'Itens Conf.', 'Avaria', 'Corte %', 'Dev. %',
        'Conf Base', 'Itens Manob.', 'Itens Rampa', 'Carga Bat.', 'Carga Palet.', 
        'Palets Px.', 'Palets Conf.', 'Jornada Líq. Eq.', 'Tempo Médio', 'Méd. Palets Conf.', 
        'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Data Inicio', 'Data Fim'
    ]
    
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    return df[colunas_existentes]

# ==========================================
# 4. LÓGICA DE TEMPO: DATA-DRIVEN (A PLANILHA MANDA)
# ==========================================
try:
    df = carregar_dados()
    
    # Verifica se as colunas existem e possuem dados válidos (formato DD/MM/AAAA)
    if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
        # Pega a data da primeira linha do arquivo
        dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0], dayfirst=True).date()
        data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0], dayfirst=True).date()
        
        # O Fim do ciclo (teto) ainda usa a regra do dia 25 baseada na data de início extraída
        if dt_inicio.day >= 26:
            mes_fim = dt_inicio.month + 1 if dt_inicio.month < 12 else 1
            ano_fim = dt_inicio.year if dt_inicio.month < 12 else dt_inicio.year + 1
            dt_fim_ciclo = datetime.date(ano_fim, mes_fim, 25)
        else:
            dt_fim_ciclo = datetime.date(dt_inicio.year, dt_inicio.month, 25)
            
    else:
        # PLANO B (Fallback): Caso a planilha venha sem as colunas novas, usa o relógio
        hoje_brasil = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).date()
        data_apuracao = hoje_brasil - datetime.timedelta(days=1)

        if data_apuracao.day >= 26:
            dt_inicio = datetime.date(data_apuracao.year, data_apuracao.month, 26)
            mes_fim = data_apuracao.month + 1 if data_apuracao.month < 12 else 1
            ano_fim = data_apuracao.year if data_apuracao.month < 12 else data_apuracao.year + 1
            dt_fim_ciclo = datetime.date(ano_fim, mes_fim, 25)
        else:
            mes_ant = data_apuracao.month - 1 if data_apuracao.month > 1 else 12
            ano_ant = data_apuracao.year if data_apuracao.month > 1 else data_apuracao.year - 1
            dt_inicio = datetime.date(ano_ant, mes_ant, 26)
            dt_fim_ciclo = datetime.date(data_apuracao.year, data_apuracao.month, 25)

    # 🔥 MÁGICA DO 6x1: Pega todos os dias do período e remove APENAS os domingos (dia 6)
    dias_totais_calendario = pd.date_range(start=dt_inicio, end=dt_fim_ciclo)
    dias_uteis_totais = dias_totais_calendario[dias_totais_calendario.weekday != 6]

    dias_decorridos_calendario = pd.date_range(start=dt_inicio, end=data_apuracao)
    dias_decorridos = dias_decorridos_calendario[dias_decorridos_calendario.weekday != 6]

    DIAS_UTEIS_MES = float(len(dias_uteis_totais))
    DIAS_DECORRIDOS = float(len(dias_decorridos))
    FATOR_PROPORCIONAL = DIAS_DECORRIDOS / DIAS_UTEIS_MES

except Exception as e:
    st.error(f"⚠️ Erro crítico na leitura de datas: {e}")
    st.stop()

# ==========================================
# 5. CONSTRUÇÃO DA TELA
# ==========================================
try:
    st.sidebar.title("🔍 Filtros do Painel")
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()
    
    lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
    cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
    if cargo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]
        
    lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
    pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)

    st.sidebar.markdown("---")
    focar_detratores = st.sidebar.checkbox("🚨 Filtrar Desempenho Abaixo da Meta")

    # ==========================================
    # 🔥 MÓDULO DE EXTRAÇÃO PARA O RH
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗃️ Fechamento RH")
    
    dados_rh = []
    for nome_colab in df_filtrado['NOME'].unique():
        row = df_filtrado[df_filtrado['NOME'] == nome_colab].iloc[0]
        turno_c = row['TURNO']
        cargo_c = row['FUNÇÃO']
        cod_c = row['CÓD.']
        
        # 🔥 PROTEÇÃO CONTRA VALORES ZERADOS OU VAZIOS NO EXCEL
        val_du = float(row.get('Dias Uteis', 0))
        dias_uteis_excel = val_du if pd.notna(val_du) and val_du > 0 else DIAS_UTEIS_MES
        
        val_dt = float(row.get('Dias Trabalhados', 0))
        d_trab = val_dt if pd.notna(val_dt) and val_dt > 0 else dias_uteis_excel
        
        val_dm = float(row.get('Dias Meta', 0))
        d_meta = val_dm if pd.notna(val_dm) and val_dm > 0 else dias_uteis_excel
        
        fator_meta = d_meta / dias_uteis_excel
        fator_premio = d_trab / dias_uteis_excel
        
        metas_c = metas_100.get(turno_c, {}).get(cargo_c, {})
        premio_total = 0.0
        
        if metas_c:
            for ind, regra in metas_c.items():
                if ind in row:
                    realizado = float(row[ind])
                    tipo, prop = regra['tipo'], regra['prop']
                    
                    t100 = regra['t100'] * fator_meta if prop else regra['t100']
                    t120 = regra['t120'] * fator_meta if prop else regra['t120']
                    t50 = regra['t50'] * fator_meta if prop else regra['t50']
                    
                    v100 = regra['v100'] * fator_premio
                    
                    if tipo == '>':
                        if realizado >= t120: premio_total += v100 * 1.2
                        elif realizado >= t100: premio_total += v100
                        elif realizado >= t50: premio_total += v100 * 0.5
                    else:
                        if pd.notna(realizado): 
                            if realizado <= t120: premio_total += v100 * 1.2
                            elif realizado <= t100: premio_total += v100
                            elif realizado <= t50: premio_total += v100 * 0.5
            
            metrica_rank = None
            for ind, regra in metas_c.items():
                if regra['prop']: 
                    metrica_rank = ind
                    break
            if not metrica_rank: metrica_rank = list(metas_c.keys())[0]
            
            if metrica_rank in df.columns:
                df_eq = df[(df['TURNO'] == turno_c) & (df['FUNÇÃO'] == cargo_c)].copy()
                ordem_cresc = False if metas_c[metrica_rank]['tipo'] == '>' else True
                df_eq = df_eq.sort_values(by=metrica_rank, ascending=ordem_cresc).reset_index(drop=True)
                
                try:
                    pos = df_eq[df_eq['NOME'] == nome_colab].index[0] + 1
                    val_rank = 0.0
                    if pos == 1:
                        if turno_c == 'T3' and 'SEPARADOR' in cargo_c: val_rank = 250.0
                        elif turno_c == 'T2' and 'SEPARADOR' in cargo_c: val_rank = 150.0
                    elif pos == 2:
                        if turno_c == 'T3' and 'SEPARADOR' in cargo_c: val_rank = 200.0
                        elif turno_c == 'T2' and 'SEPARADOR' in cargo_c: val_rank = 100.0
                    elif pos == 3:
                        if turno_c == 'T3' and 'SEPARADOR' in cargo_c: val_rank = 100.0
                        elif turno_c == 'T2' and 'SEPARADOR' in cargo_c: val_rank = 50.0
                    
                    premio_total += (val_rank * fator_premio)
                except:
                    pass
                    
        dados_rh.append({
            'Matrícula': cod_c,
            'Nome': nome_colab,
            'Premiação (R$)': round(premio_total, 2)
        })

    if dados_rh:
        df_rh = pd.DataFrame(dados_rh).sort_values(by='Nome')
        st.sidebar.dataframe(df_rh.style.format({'Premiação (R$)': 'R$ {:,.2f}'}), hide_index=True, use_container_width=True)
        csv_rh = df_rh.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.sidebar.download_button(label="📥 Baixar Planilha do RH", data=csv_rh, file_name=f"Fechamento_RH_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv", mime="text/csv", type="primary", use_container_width=True)
    else:
        st.sidebar.info("Nenhum dado processado.")

    col_titulo, col_kpis = st.columns([1, 1.2])
    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')} | 🏢 **{int(DIAS_DECORRIDOS)} Dias Úteis (6x1) de {int(DIAS_UTEIS_MES)}**")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral do Período")
        kpi1, kpi2, kpi3 = st.columns(3)
        
        if turno_selecionado == 'T1' or (cargo_selecionado != "Todos" and cargo_selecionado in ['OPERADOR', 'DESCARGA', 'PUXA']):
            col_volumes_t1 = ['Carga Palet.', 'Carga Bat.', 'Palets Conf.', 'Palets Px.', 'Mov. Vert.', 'Méd. Palets Conf.']
            total_volume = sum(df_filtrado[c].sum() for c in col_volumes_t1 if c in df_filtrado.columns)
            label_volume = "📦 Paletes/Movimentações"
        else:
            total_volume = df_filtrado['Itens Sep'].sum() if 'Itens Sep' in df_filtrado.columns else 0
            label_volume = "📦 Total Itens Separados"
            
        if turno_selecionado == 'T1' or (cargo_selecionado != "Todos" and cargo_selecionado in ['OPERADOR', 'DESCARGA', 'PUXA']):
            if 'Tempo Médio' in df_filtrado.columns:
                med_vel = df_filtrado[df_filtrado['Tempo Médio'] > 0]['Tempo Médio'].mean()
                kpi2_label = "⚡ Tempo Médio"
                kpi2_val = f"{int(med_vel)//3600:02d}:{(int(med_vel)%3600)//60:02d}:{(int(med_vel)%60):02d}" if pd.notna(med_vel) else "00:00:00"
            else:
                kpi2_label = "⚡ Tempo Médio"
                kpi2_val = "-"
        else:
            media_vel = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean() if 'Itens/Hora' in df_filtrado.columns else 0
            kpi2_label = "⚡ Média (Itens/H)"
            kpi2_val = f"{media_vel:.0f}" if pd.notna(media_vel) else "0"
            
        total_horas = df_filtrado.loc[df_filtrado['Horas'] > 0, 'Horas'].sum() if 'Horas' in df_filtrado.columns else 0
        
        kpi1.metric(label_volume, f"{total_volume:,.0f}".replace(',', '.'))
        kpi2.metric(kpi2_label, kpi2_val)
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # ==========================================
    # MODALIDADE: PAINEL DE DETRATORES 
    # ==========================================
    if focar_detratores:
        st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
        
        houve_detrator = False
        for idx, row in df_filtrado.iterrows():
            turno_c = row['TURNO']
            cargo_c = row['FUNÇÃO']
            nome_c = row['NOME']
            cod_c = row['CÓD.']
            
            val_du = float(row.get('Dias Uteis', 0))
            dias_uteis_excel = val_du if pd.notna(val_du) and val_du > 0 else DIAS_UTEIS_MES
            
            val_dm = float(row.get('Dias Meta', 0))
            d_meta = val_dm if pd.notna(val_dm) and val_dm > 0 else dias_uteis_excel
            
            fator_meta = d_meta / dias_uteis_excel
            
            regras = metas_100.get(turno_c, {}).get(cargo_c, {})
            if not regras: continue
                
            itens_realizados, itens_hora_realizado, metrica_volume_nome = 0, 0, "Volume"
            abaixo_da_meta = False
            detalhes_gargalo = []
            
            for ind, regra in regras.items():
                if ind in df_filtrado.columns:
                    realizado = float(row[ind])
                    t100 = regra['t100'] * fator_meta if regra['prop'] else regra['t100']
                    
                    if "Itens" in ind or "Palets" in ind or "Carga" in ind or "Mov" in ind:
                        itens_realizados = realizado
                        metrica_volume_nome = ind
                    if "Hora" in ind or "Médio" in ind:
                        itens_hora_realizado = realizado
                    
                    if regra['tipo'] == '>':
                        if realizado < t100:
                            abaixo_da_meta = True
                            detalhes_gargalo.append(f"❌ {ind}: {realizado:,.0f} realizado vs Alvo de {t100:,.0f}".replace(',', '.'))
                    else:
                        if realizado > t100:
                            abaixo_da_meta = True
                            detalhes_gargalo.append(f"❌ {ind}: {realizado:.2f}% realizado vs Alvo de {t100:.2f}%")
            
            if abaixo_da_meta:
                houve_detrator = True
                with st.container():
                    st.markdown(f"<div class='card-detrator'><span style='font-size: 22px; font-weight: bold; color: {C_VERMELHO};'>⚠️ [{cod_c}] {nome_c}</span><br><b>Turno:</b> {turno_c} | <b>Função:</b> {cargo_c} | <b>Dias Ativos no Ciclo:</b> {int(d_meta)} dias<p style='margin-top: 10px; font-size: 16px; line-height: 1.4; color: lightgray;'><b>📝 Análise Operacional Automática:</b><br>Nos {int(d_meta)} dias computados para meta, o colaborador realizou um volume total de {itens_realizados:,.0f} no indicador <i>{metrica_volume_nome}</i>. Velocidade média de {itens_hora_realizado:.1f} por hora.</p><span style='font-weight: bold; color: #ffca28;'>Pontos de Desvio Identificados:</span><br>{'<br>'.join(detalhes_gargalo)}</div>", unsafe_allow_html=True)
                    
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
    # VISÃO INDIVIDUAL
    # ==========================================
    elif pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        if not dados_pessoa.empty:
            turno_p = dados_pessoa['TURNO'].values[0]
            cargo_p = dados_pessoa['FUNÇÃO'].values[0]
            metas_cargo = metas_100.get(turno_p, {}).get(cargo_p, {})
            
            val_du = float(dados_pessoa['Dias Uteis'].values[0]) if 'Dias Uteis' in dados_pessoa.columns and pd.notna(dados_pessoa['Dias Uteis'].values[0]) else 0
            dias_uteis_excel = val_du if val_du > 0 else DIAS_UTEIS_MES
            
            val_dt = float(dados_pessoa['Dias Trabalhados'].values[0]) if 'Dias Trabalhados' in dados_pessoa.columns and pd.notna(dados_pessoa['Dias Trabalhados'].values[0]) else 0
            d_trab = val_dt if val_dt > 0 else dias_uteis_excel
            
            val_dm = float(dados_pessoa['Dias Meta'].values[0]) if 'Dias Meta' in dados_pessoa.columns and pd.notna(dados_pessoa['Dias Meta'].values[0]) else 0
            d_meta = val_dm if val_dm > 0 else dias_uteis_excel
            
            fator_meta = d_meta / dias_uteis_excel
            fator_premio = d_trab / dias_uteis_excel

            valor_premio_ranking = 0.0
            
            if metas_cargo:
                metrica_ranking = next((ind for ind, r in metas_cargo.items() if r['prop']), list(metas_cargo.keys())[0])
                
                if metrica_ranking in df.columns:
                    df_equipe = df[(df['TURNO'] == turno_p) & (df['FUNÇÃO'] == cargo_p)].copy()
                    ordem_cresc = False if metas_cargo[metrica_ranking]['tipo'] == '>' else True
                    df_equipe = df_equipe.sort_values(by=metrica_ranking, ascending=ordem_cresc).reset_index(drop=True)
                    
                    try:
                        posicao = df_equipe[df_equipe['NOME'] == pessoa_selecionada].index[0] + 1
                        total_eq = len(df_equipe)
                        
                        if posicao == 1: 
                            medalha, cor_rank = "🥇", "#ffd700"
                            if turno_p == 'T3' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 250.0
                            elif turno_p == 'T2' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 150.0
                        elif posicao == 2: 
                            medalha, cor_rank = "🥈", "#c0c0c0"
                            if turno_p == 'T3' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 200.0
                            elif turno_p == 'T2' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 100.0
                        elif posicao == 3: 
                            medalha, cor_rank = "🥉", "#cd7f32"
                            if turno_p == 'T3' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 100.0
                            elif turno_p == 'T2' and 'SEPARADOR' in cargo_p: valor_premio_ranking = 50.0
                        else: 
                            medalha, cor_rank, valor_premio_ranking = "🏅", "gray", 0.0
                            
                        valor_premio_ranking = valor_premio_ranking * fator_premio
                            
                        texto_premio_rank = f" | <span style='color: #2ecc71;'><b>💰 Prêmio: R$ {valor_premio_ranking:,.2f}</b></span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_premio_ranking > 0 else ""
                        st.markdown(f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'><b>{medalha} Posição no Ranking:</b> {posicao}º lugar de {total_eq} na equipe de {cargo_p} <i>(Critério: {metrica_ranking})</i>{texto_premio_rank}</div>", unsafe_allow_html=True)
                    except IndexError: pass

            bonus_acumulado = valor_premio_ranking 
            
            if metas_cargo:
                cols_meta = st.columns(len(metas_cargo))
                grafico_dados = []
                
                for idx, (ind, regra) in enumerate(metas_cargo.items()):
                    if ind in dados_pessoa.columns:
                        realizado = float(dados_pessoa[ind].values[0])
                        tipo, prop = regra['tipo'], regra['prop']
                        
                        t100 = regra['t100'] * fator_meta if prop else regra['t100']
                        t120 = regra['t120'] * fator_meta if prop else regra['t120']
                        t50 = regra['t50'] * fator_meta if prop else regra['t50']
                        
                        v100 = regra['v100'] * fator_premio
                        
                        pagamento_ind = 0.0
                        if tipo == '>':
                            atingimento_real = (realizado / t100 * 100) if t100 > 0 else 0
                            if realizado >= t120: cor_texto, icone, status_texto, pagamento_ind = C_AZUL, "🔵", "Superou", v100 * 1.2
                            elif realizado >= t100: cor_texto, icone, status_texto, pagamento_ind = C_VERDE, "🟢", "Atingiu", v100
                            elif realizado >= t50: cor_texto, icone, status_texto, pagamento_ind = C_AMARELO, "🟡", "Parcial", v100 * 0.5
                            else: cor_texto, icone, status_texto, pagamento_ind = C_VERMELHO, "🔴", "Abaixo", 0.0
                        else: 
                            atingimento_real = (t100 / realizado * 100) if realizado > 0 else 120.0
                            if realizado <= t120: cor_texto, icone, status_texto, pagamento_ind = C_AZUL, "🔵", "Superou", v100 * 1.2
                            elif realizado <= t100: cor_texto, icone, status_texto, pagamento_ind = C_VERDE, "🟢", "Atingiu", v100
                            elif realizado <= t50: cor_texto, icone, status_texto, pagamento_ind = C_AMARELO, "🟡", "Parcial", v100 * 0.5
                            else: cor_texto, icone, status_texto, pagamento_ind = C_VERMELHO, "🔴", "Abaixo", 0.0
                        
                        grafico_dados.append({'Indicador': f"<b>{ind}</b>", 'Atingimento (%)': min(atingimento_real, 120), 'Real': atingimento_real})
                        bonus_acumulado += pagamento_ind
                        texto_grana = f"R$ {pagamento_ind:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 {texto_grana}</span>" if pagamento_ind > 0 else ""
                        
                        aviso_prop = f" <span style='font-size: 14px; font-weight: normal;'>(Meta a {int(d_meta)}d)</span>" if prop else ""
                            
                        if "Tempo Médio" in ind:
                            valor_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                            t100_tela = f"{int(t100)//3600:02d}:{(int(t100)%3600)//60:02d}:{int(t100)%60:02d}"
                        elif ind in ['Avaria', 'Dev. %', 'Corte %']:
                            valor_tela, t100_tela = f"{realizado:.2f}%", f"{t100:.2f}%"
                        elif "Líq" in ind:
                            valor_tela, t100_tela = f"{realizado:.0f}%", f"{t100:.0f}%"
                        else:
                            valor_tela, t100_tela = f"{realizado:,.0f}".replace(',','.'), f"{t100:,.0f}".replace(',','.')

                        with cols_meta[idx]:
                            st.markdown(f"<div class='card-meta' style='border-left-color: {cor_texto};'><div class='texto-card-titulo'>{ind} (Alvo: {t100_tela}){aviso_prop}</div><div class='texto-card-principal'>{valor_tela}</div><div style='font-size: 18px; color: {cor_texto}; font-weight: bold; margin-top: 8px;'>{icone} {status_texto} {html_dinheiro}</div></div>", unsafe_allow_html=True)
                
                if bonus_acumulado > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.success(f"💰 **Premiação Variável Acumulada TOTAL Estimada:** R$ {bonus_acumulado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                st.divider()
                st.markdown(f"### 📊 Análise de {pessoa_selecionada}")
                col_grafico, col_tabela = st.columns([1.2, 1])
                
                with col_grafico:
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

                with col_tabela:
                    col_uteis = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Data Inicio', 'Data Fim'] + list(metas_cargo.keys())
                    df_tabela_mini = dados_pessoa[[c for c in col_uteis if c in df_filtrado.columns]].copy()
                    if 'Tempo Médio' in df_tabela_mini.columns:
                        df_tabela_mini['Tempo Médio'] = df_tabela_mini['Tempo Médio'].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if pd.notna(s) else "00:00:00")
                    config_colunas = {}
                    for col in df_tabela_mini.columns:
                        if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim']: continue 
                        elif col in ['Avaria', 'Corte %', 'Dev. %']: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                        elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                        else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")
                    st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=350, column_config=config_colunas)

    # ==========================================
    # VISÃO GERAL EQUIPE / TURNO
    # ==========================================
    else:
        cargos_render = [cargo_selecionado] if cargo_selecionado != "Todos" else sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
        for cargo_atual in cargos_render:
            df_cargo = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_atual]
            if df_cargo.empty: continue
            metas_equipe = metas_100.get(df_cargo['TURNO'].mode()[0], {}).get(cargo_atual, {})
            
            if metas_equipe:
                if len(cargos_render) > 1: st.markdown(f"<h4 style='color: lightgray; margin-top: 15px;'>🔹 Equipe: {cargo_atual}</h4>", unsafe_allow_html=True)
                cols_eq = st.columns(len(metas_equipe))
                for idx, (ind, regra) in enumerate(metas_equipe.items()):
                    if ind in df_cargo.columns:
                        df_valido = df_cargo[df_cargo[ind] > 0]
                        if not df_valido.empty:
                            valores = df_valido[ind]
                            pesos = df_valido['Dias Trabalhados'].apply(lambda x: x if pd.notna(x) and x > 0 else DIAS_UTEIS_MES) if 'Dias Trabalhados' in df_valido.columns else 1
                            real_med, soma_total = float((valores * pesos).sum() / pesos.sum()), float(valores.sum())
                        else:
                            real_med, soma_total = 0.0, 0.0
                        
                        tipo, prop = regra['tipo'], regra['prop']
                        t100 = regra['t100'] * FATOR_PROPORCIONAL if prop else regra['t100']
                        t50 = regra['t50'] * FATOR_PROPORCIONAL if prop else regra['t50']
                        t120 = regra['t120'] * FATOR_PROPORCIONAL if prop else regra['t120']
                        
                        if tipo == '>':
                            if real_med >= t120: cor, icone, status = C_AZUL, "🔵", "Superando"
                            elif real_med >= t100: cor, icone, status = C_VERDE, "🟢", "Na Meta"
                            elif real_med >= t50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                            else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                        else:
                            if real_med <= t120: cor, icone, status = C_AZUL, "🔵", "Superando"
                            elif real_med <= t100: cor, icone, status = C_VERDE, "🟢", "Na Meta"
                            elif real_med <= t50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                            else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                        
                        aviso_prop = f" <span style='font-size: 14px; font-weight: normal;'>(Prop. a {int(DIAS_DECORRIDOS)}d)</span>" if prop else ""
                        
                        if "Tempo Médio" in ind:
                            v_tela, t_tela, html_soma = f"{int(real_med)//3600:02d}:{(int(real_med)%3600)//60:02d}:{(int(real_med)%60):02d}", f"{int(t100)//3600:02d}:{(int(t100)%3600)//60:02d}:{(int(t100)%60):02d}", ""
                        elif ind in ['Avaria', 'Dev. %', 'Corte %']:
                            v_tela, t_tela, html_soma = f"{real_med:.2f}%", f"{t100:.2f}%", ""
                        elif "Líq." in ind: 
                            v_tela, t_tela, html_soma = f"{real_med:.0f}%", f"{t100:.0f}%", ""
                        else:
                            v_tela, t_tela, html_soma = f"{real_med:,.0f}".replace(',','.'), f"{t100:,.0f}".replace(',','.'), f"<span class='texto-card-secundario'>| Soma Equipe: {soma_total:,.0f}</span>".replace(',', '.')
                            
                        with cols_eq[idx]:
                            st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>Média: {ind} (Alvo: {t_tela}){aviso_prop}</div><div class='texto-card-principal'>{v_tela} {html_soma}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div></div>", unsafe_allow_html=True)
        
        if len(cargos_render) > 0: st.divider()

        st.markdown("### 📋 Tabela de Produtividade Consolidada")
        df_tabela = df_filtrado.sort_values(by='NOME', ascending=True).copy()
        cols_basicas, todas_metricas = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Data Inicio', 'Data Fim'], set()
        
        if cargo_selecionado != "Todos": todas_metricas.update(metas_100.get(df_tabela['TURNO'].mode()[0], {}).get(cargo_selecionado, {}).keys())
        elif turno_selecionado != "Todos":
            for kpis in metas_100.get(turno_selecionado, {}).values(): todas_metricas.update(kpis.keys())
        
        if todas_metricas: df_tabela = df_tabela[[c for c in (cols_basicas + sorted(list(todas_metricas))) if c in df_tabela.columns]]
        if 'Tempo Médio' in df_tabela.columns: df_tabela['Tempo Médio'] = df_tabela['Tempo Médio'].apply(lambda s: f"{int(s)//3600:02d}:{(int(s)%3600)//60:02d}:{(int(s)%60):02d}")

        config = {}
        for c in df_tabela.columns:
            if c in cols_basicas or c == 'Tempo Médio': continue
            elif c in ['Avaria', 'Corte %', 'Dev. %']: config[c] = st.column_config.NumberColumn(c, format="%.2f%%")
            elif "Líq." in c: config[c] = st.column_config.NumberColumn(c, format="%d%%")
            else: config[c] = st.column_config.NumberColumn(c, format="%d")
            
        st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    st.error(f"⚠️ Erro: {e}")
