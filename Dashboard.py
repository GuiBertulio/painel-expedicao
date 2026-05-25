import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

def conectar_planilha():
    # Puxa os dados do st.secrets
    cred_dict = dict(st.secrets["gcp_service_account"])
    
    # Autenticação direta e simplificada pelo próprio gspread
    client = gspread.service_account_from_dict(cred_dict)
    
    # Conecta na planilha
    planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")
    return planilha.worksheet("Historico_RH")

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; }
    h1, h2, h3 { font-weight: 900 !important; letter-spacing: 0.5px; }
    [data-testid="stMetricValue"] { font-size: 50px !important; color: #3b82f6 !important; }
    [data-testid="stMetricLabel"] > div { font-size: 20px !important; font-weight: bold !important; color: lightgray; }
    .card-meta {
        background-color: var(--background-color); 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 1px 1px 5px rgba(0,0,0,0.3); 
        margin-bottom: 15px;
        border-left: 8px solid #ccc; 
        border-top: 1px solid var(--secondary-background-color);
        border-right: 1px solid var(--secondary-background-color);
        border-bottom: 1px solid var(--secondary-background-color);
    }
    .texto-card-principal { font-size: 42px; color: var(--text-color); font-weight: 900; line-height: 1.1; }
    .texto-card-titulo { font-size: 22px; color: var(--text-color); font-weight: 900; margin-bottom: 5px; }
    .texto-card-secundario { font-size: 16px; color: gray; font-weight: normal; margin-left: 8px; }
    .card-detrator {
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
# 3. CARREGAMENTO DOS DADOS E SUPER AUTO-CORRETOR
# ==========================================
@st.cache_data(ttl=600) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 🔥 SUPER AUTO-CORRETOR DE COLUNAS
    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if ("MED" in nome_limpo or "MÉD" in nome_limpo) and ("PALET" in nome_limpo or "PALLET" in nome_limpo):
            df = df.rename(columns={c: 'Méd. Palets Conf.'})
        elif "JORNADA" in nome_limpo and "EQ" in nome_limpo:
            df = df.rename(columns={c: 'Jornada Líq. Eq.'})
        elif "RESSUP" in nome_limpo and "EQ" in nome_limpo:
            df = df.rename(columns={c: 'Ressup. Eq.'})

    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
        
    # Padronização de chaves de texto básicas antes dos cálculos
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()

    # Tratamento padrão das colunas numéricas que vêm da planilha
    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
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
        'Palets Px.', 'Palets Conf.', 'Jornada Líq. Eq.', 'Tempo Médio', 'Méd. Palets Conf.', 'Dias Trabalhados'
    ]
    
    colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
    df = df[colunas_existentes]
    
    return df

# ==========================================
# 4. LÓGICA DE TEMPO: D-1
# ==========================================
data_apuracao = datetime.date.today() - datetime.timedelta(days=1)
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

dias_uteis_totais = pd.bdate_range(start=dt_inicio, end=dt_fim_ciclo)
dias_decorridos = pd.bdate_range(start=dt_inicio, end=data_apuracao)

try:
    import holidays
    feriados_br = holidays.Brazil(years=[dt_inicio.year, dt_fim_ciclo.year])
    dias_uteis_totais = dias_uteis_totais.drop([d for d in dias_uteis_totais if d.date() in feriados_br])
    dias_decorridos = dias_decorridos.drop([d for d in dias_decorridos if d.date() in feriados_br])
except ImportError:
    pass 

DIAS_UTEIS_MES = float(len(dias_uteis_totais))
DIAS_DECORRIDOS = float(len(dias_decorridos))
FATOR_PROPORCIONAL = DIAS_DECORRIDOS / DIAS_UTEIS_MES

# ==========================================
# 5. CONSTRUÇÃO DA TELA
# ==========================================
try:
    df = carregar_dados()
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

    col_titulo, col_kpis = st.columns([1, 1.2])
    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')} | 🏢 **{int(DIAS_DECORRIDOS)} Dias Corridos de {int(DIAS_UTEIS_MES)}**")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral do Período")
        kpi1, kpi2, kpi3 = st.columns(3)
        
        col_volumes = [
            'Itens Sep', 'Itens Conf.', 'Itens Rampa', 'Itens Manob.', 
            'Palets Conf.', 'Carga Palet.', 'Carga Bat.', 'Mov. Horizontal', 
            'Mov. Vert.', 'Palets Px.', 'Ressup. Ap.', 'Ressup. Eq.'
        ]
        total_volume = sum(df_filtrado[c].sum() for c in col_volumes if c in df_filtrado.columns)
        
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
        
        kpi1.metric("📦 Volume Produtivo Total", f"{total_volume:,.0f}".replace(',', '.'))
        kpi2.metric(kpi2_label, kpi2_val)
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # ==========================================
    # MODALIDADE: PAINEL DE DETRATORES 
    # ==========================================
    if focar_detratores:
        st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
        st.write("Abaixo estão listados os colaboradores que não atingiram 100% da meta em seus principais indicadores de volume ou velocidade.")
        
        houve_detrator = False
        for idx, row in df_filtrado.iterrows():
            turno_c = row['TURNO']
            cargo_c = row['FUNÇÃO']
            nome_c = row['NOME']
            cod_c = row['CÓD.']
            dias_c = float(row['Dias Trabalhados']) if 'Dias Trabalhados' in df_filtrado.columns else DIAS_UTEIS_MES
            
            regras = metas_100.get(turno_c, {}).get(cargo_c, {})
            if not regras:
                continue
                
            itens_realizados = 0
            itens_hora_realizado = 0
            metrica_volume_nome = "Volume"
            abaixo_da_meta = False
            detalhes_gargalo = []
            
            for ind, regra in regras.items():
                if ind in df_filtrado.columns:
                    realizado = float(row[ind])
                    t100 = regra['t100'] * (dias_c / DIAS_UTEIS_MES) if regra['prop'] else regra['t100']
                    
                    if "Itens" in ind or "Palets" in ind or "Carga" in ind or "Mov" in ind:
                        itens_realizados = realizado
                        metrica_volume_nome = ind
                    if "Hora" in ind or "Médio" in ind:
                        itens_hora_realizado = realizado
                    
                    if regra['tipo'] == '>':
                        if realizado < t100:
                            abaixo_da_meta = True
                            detalhes_gargalo.append(f"❌ {ind}: {realizado:,.0f} realizado vs Alvo Proporcional de {t100:,.0f}".replace(',', '.'))
                    else:
                        if realizado > t100:
                            abaixo_da_meta = True
                            detalhes_gargalo.append(f"❌ {ind}: {realizado:.2f}% realizado vs Alvo de {t100:.2f}%")
            
            if abaixo_da_meta:
                houve_detrator = True
                with st.container():
                    st.markdown(f"""
                    <div class="card-detrator">
                        <span style="font-size: 22px; font-weight: bold; color: {C_VERMELHO};">⚠️ [{cod_c}] {nome_c}</span><br>
                        <b>Turno:</b> {turno_c} | <b>Função:</b> {cargo_c} | <b>Dias Ativos no Ciclo:</b> {int(dias_c)} dias
                        <p style="margin-top: 10px; font-size: 16px; line-height: 1.4; color: lightgray;">
                            <b>📝 Análise Operacional Automática:</b><br>
                            Nos {int(dias_c)} dias computados, o colaborador realizou um volume total de {itens_realizados:,.0f} no indicador <i>{metrica_volume_nome}</i>. 
                            Dividindo a operação pelo tempo de execução, sua velocidade média fechou cravada em {itens_hora_realizado:.1f} por hora, ficando abaixo da régua de eficiência da companhia.
                        </p>
                        <span style="font-weight: bold; color: #ffca28;">Pontos de Desvio Identificados:</span><br>
                        {"<br>".join(detalhes_gargalo)}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_feed, col_trein = st.columns(2)
                    
                    # --- INTEGRAÇÃO COM BANCO DE DADOS APLICADA AQUI ---
                    with col_feed:
                        with st.expander(f"💬 Registrar Feedback 1-a-1: {nome_c}"):
                            with st.form(key=f"form_feed_{idx}"):
                                st.write(f"**Novo Registro de Alinhamento**")
                                texto_feedback = st.text_area("Descreva o que foi conversado:")
                                salvar_feed = st.form_submit_button("Salvar no Histórico")
                                
                                if salvar_feed:
                                    if texto_feedback:
                                        try:
                                            aba_rh = conectar_planilha()
                                            agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                            aba_rh.append_row([agora, str(cod_c), nome_c, "Feedback 1-a-1", texto_feedback])
                                            st.success(f"✅ Feedback de {nome_c} registrado com sucesso na base de dados!")
                                        except Exception as erro_sheet:
                                            st.error(f"Erro ao salvar na planilha: {erro_sheet}")
                                    else:
                                        st.error("⚠️ Digite algo antes de salvar.")

                    with col_trein:
                        with st.expander(f"🎯 Solicitar Reciclagem: {nome_c}"):
                            with st.form(key=f"form_trein_{idx}"):
                                st.write(f"**Abertura de Chamado para Treinamento**")
                                motivo = st.selectbox("Identifique o gargalo principal:", ["Baixa Velocidade de Separação", "Muitos Erros/Avarias", "Dificuldade com o Sistema Consinco", "Processo de Carga/Descarga"])
                                pedir_treinamento = st.form_submit_button("Enviar Solicitação")
                                
                                if pedir_treinamento:
                                    try:
                                        aba_rh = conectar_planilha()
                                        agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                        aba_rh.append_row([agora, str(cod_c), nome_c, "Solicitação de Reciclagem", motivo])
                                        st.success(f"📧 Chamado enviado para a base de dados do RH!")
                                    except Exception as erro_sheet:
                                        st.error(f"Erro ao salvar na planilha: {erro_sheet}")
                    # --------------------------------------------------
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
        if not houve_detrator:
            st.success("🎉 Excelente! Nenhum colaborador desse filtro está operando abaixo das metas estabelecidas.")

    # ==========================================
    # VISÃO INDIVIDUAL E RANKINGS (MÓDULO NOVO)
    # ==========================================
    elif pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento do Colaborador: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        
        if not dados_pessoa.empty:
            turno_p = dados_pessoa['TURNO'].values[0]
            cargo_p = dados_pessoa['FUNÇÃO'].values[0]
            metas_cargo = metas_100.get(turno_p, {}).get(cargo_p, {})
            bonus_acumulado = 0.0 
            
            if metas_cargo:
                cols_meta = st.columns(len(metas_cargo))
                grafico_dados = []
                dias_trab = float(dados_pessoa['Dias Trabalhados'].values[0]) if 'Dias Trabalhados' in dados_pessoa.columns else DIAS_UTEIS_MES
                if dias_trab <= 0: dias_trab = 1.0 
                fator_colaborador = dias_trab / DIAS_UTEIS_MES
                
                for idx, (ind, regra) in enumerate(metas_cargo.items()):
                    if ind in dados_pessoa.columns:
                        realizado = float(dados_pessoa[ind].values[0])
                        tipo, prop = regra['tipo'], regra['prop']
                        
                        t100 = regra['t100'] * fator_colaborador if prop else regra['t100']
                        t120 = regra['t120'] * fator_colaborador if prop else regra['t120']
                        t50 = regra['t50'] * fator_colaborador if prop else regra['t50']
                        v100 = regra['v100'] * fator_colaborador if prop else regra['v100']
                        
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
                        html_dinheiro = f'<span style="color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;">💰 {texto_grana}</span>' if pagamento_ind > 0 else ""
                        aviso_prop = f" <span style='font-size: 14px; font-weight: normal;'>(Prop. a {int(dias_trab)}d)</span>" if prop else ""
                        
                        if "Tempo Médio" in ind:
                            valor_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                            t100_tela = f"{int(t100)//3600:02d}:{(int(t100)%3600)//60:02d}:{int(t100)%60:02d}"
                        elif ind in ['Avaria', 'Dev. %', 'Corte %']:
                            valor_tela = f"{realizado:.2f}%"
                            t100_tela = f"{t100:.2f}%"
                        elif "Líq" in ind:
                            valor_tela, t100_tela = f"{realizado:.0f}%", f"{t100:.0f}%"
                        else:
                            valor_tela = f"{realizado:,.0f}".replace
