import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread
import io # <-- Import para gerar o Excel em memória adicionado aqui no topo

# ==========================================
# 🔐 CONFIGURAÇÃO DE USUÁRIOS E SENHAS
# ==========================================
USUARIOS = {
    "diegoc": {"senha": "ger#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "nilo": {"senha": "esp#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "flamarion": {"senha": "sub#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "guilherme": {"senha": "estag#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "adriano": {"senha": "Adriano@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "luciano": {"senha": "Luciano@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "wagner": {"senha": "Wagner@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "jorge": {"senha": "Jorge@26TAF", "perfil": "Líder", "turno_acesso": "T2"},
    "diego": {"senha": "Diego@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "carlos": {"senha": "Carlos@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "luis": {"senha": "Luis@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "luiz": {"senha": "Luiz@26TAF", "perfil": "Líder", "turno_acesso": "T3"}
}

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
# 🚪 TELA DE LOGIN (BARREIRA DE SEGURANÇA)
# ==========================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("🔐 Login - Dashboard Logístico")
        
        usuario = st.text_input("Usuário").strip().lower()
        senha = st.text_input("Senha", type="password").strip() 
        btn_entrar = st.button("Entrar", type="primary", use_container_width=True)
        
        if btn_entrar:
            if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["perfil"] = USUARIOS[usuario]["perfil"]
                st.session_state["turno_acesso"] = USUARIOS[usuario]["turno_acesso"]
                st.rerun() 
            else:
                st.error("❌ Usuário ou senha incorretos.")
    st.stop() 

# ==========================================
# CONEXÃO COM GOOGLE SHEETS
# ==========================================
def conectar_planilha():
    cred_dict = dict(st.secrets["gcp_service_account"])
    client = gspread.service_account_from_dict(cred_dict)
    planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")
    return planilha

# ==========================================
# 2. CARREGAMENTO DOS DADOS E CÁLCULO DE RANKING
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    colunas = list(df.columns)
    for i, col in enumerate(colunas):
        if "RACIONAL" in col.upper():
            nome_kpi = colunas[i-1] 
            try:
                df.rename(columns={
                    colunas[i]: f"{nome_kpi}_Racional",
                    colunas[i+1]: f"{nome_kpi}_Meta1",
                    colunas[i+2]: f"{nome_kpi}_Meta2", 
                    colunas[i+3]: f"{nome_kpi}_Meta3",
                    colunas[i+4]: f"{nome_kpi}_Valor"
                }, inplace=True)
            except IndexError:
                pass 

    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if "TRAB" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Trabalhados'})
        elif "META" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Meta'})
        elif ("UT" in nome_limpo or "ÚT" in nome_limpo) and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Uteis'})
        elif "DATA" in nome_limpo and ("INICIO" in nome_limpo or "INÍCIO" in nome_limpo or "INICIAL" in nome_limpo): df = df.rename(columns={c: 'Data Inicio'})
        elif "DATA" in nome_limpo and ("FIM" in nome_limpo or "FINAL" in nome_limpo or "APURA" in nome_limpo): df = df.rename(columns={c: 'Data Fim'})

    df = df.loc[:, ~df.columns.duplicated()].copy()

    if 'NOME' in df.columns: df = df.dropna(subset=['NOME'])
    if 'FUNÇÃO' in df.columns: df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns: df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
    
    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Data Inicio', 'Data Fim']
    for col in df.columns:
        if col not in colunas_texto:
            if 'TEMPO' in col.upper() and not col.upper().endswith('_VALOR') and not col.upper().endswith('_RACIONAL'): 
                texto_limpo = df[col].astype(str).str.split('.').str[0].str.strip()
                df[col] = pd.to_timedelta(texto_limpo, errors='coerce').dt.total_seconds().fillna(0)
            else:
                s = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
                mask_virgula = s.str.contains(',', regex=False)
                s_br = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(s_br.where(mask_virgula, s), errors='coerce').fillna(0)
    
    df['Valor Ranking'] = 0.0
    df['Posicao Ranking'] = 0
    
    for turno in ['T2', 'T3']:
        for cargo in df['FUNÇÃO'].unique():
            if 'SEPARADOR' in str(cargo).upper():
                df_eq = df[(df['TURNO'] == turno) & (df['FUNÇÃO'] == cargo)].copy()
                if df_eq.empty: continue
                
                kpis = [c.replace('_Racional', '') for c in df_eq.columns if '_Racional' in c]
                if not kpis: continue
                
                # --- [NOVA LÓGICA DE RANKING ESPECÍFICA POR TURNO] ---
                if turno == 'T2':
                    metrica_rank = next((k for k in kpis if 'RESSUP' in k.upper()), kpis[0])
                else:
                    metrica_rank = next((k for k in kpis if 'ITENS' in k.upper()), kpis[0])
                
                racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
                ordem_cresc = False if racional == 1 else True
                
                df_eq = df_eq.sort_values(by=metrica_rank, ascending=ordem_cresc)
                
                pos = 1
                for idx, row_eq in df_eq.iterrows():
                    if float(row_eq.get(metrica_rank, 0)) <= 0: continue
                    
                    df.at[idx, 'Posicao Ranking'] = pos
                    
                    if turno == 'T3':
                        if pos == 1: val_base = 250.0
                        elif pos == 2: val_base = 200.0
                        elif pos == 3: val_base = 100.0
                        else: val_base = 0.0
                    elif turno == 'T2':
                        if pos == 1: val_base = 100.0
                        elif pos == 2: val_base = 80.0
                        elif pos == 3: val_base = 50.0
                        else: val_base = 0.0
                    else:
                        val_base = 0.0
                    
                    if val_base > 0:
                        d_uteis = float(row_eq.get('Dias Uteis', 26))
                        d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                        fator = d_trab / d_uteis if d_uteis > 0 else 1
                        df.at[idx, 'Valor Ranking'] = val_base * fator
                    
                    pos += 1

    colunas_valor = [c for c in df.columns if c.endswith('_Valor')]
    df['Valor Final'] = df[colunas_valor].sum(axis=1) + df['Valor Ranking']

    return df

@st.cache_data(ttl=60)
def carregar_diario():
    try:
        planilha = conectar_planilha()
        aba = planilha.worksheet("Relatorio Diario") 
        dados = aba.get_all_values()
        
        if len(dados) > 0:
            cabecalhos = dados[0] 
            df_d = pd.DataFrame(dados[1:], columns=cabecalhos)
            df_d.columns = df_d.columns.astype(str).str.strip()
            return df_d
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

df = carregar_dados()
df_diario = carregar_diario()

# ==========================================
# 3. LÓGICA DE DATAS E FILTROS (C/ AUTENTICAÇÃO)
# ==========================================
if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
    dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0]).date()
    data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0]).date()
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)

# --- CABEÇALHO DA BARRA LATERAL ---
st.sidebar.markdown(f"👤 **Logado como:** {st.session_state['usuario'].capitalize()} ({st.session_state['perfil']})")
if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state["logado"] = False
    st.rerun()

# ==========================================
# 📥 BOTÃO DE AUDITORIA (MOVIDO PARA A BARRA LATERAL)
# ==========================================
if st.session_state.get("usuario") in ["guilherme", "nilo"]:
    # Regra de Fechamento: Começa dia 26 e termina dia 25
    is_fechado = (dt_inicio.day == 26 and data_apuracao.day == 25)
    
    if is_fechado:
        df_auditoria = []
        kpis_gerais = [c.replace('_Racional', '') for c in df.columns if '_Racional' in c]
        
        for idx, row in df.iterrows():
            cod = row.get('CÓD.', '')
            nome = row.get('NOME', '')
            funcao = row.get('FUNÇÃO', '')
            turno = row.get('TURNO', '')
            
            d_uteis = float(row.get('Dias Uteis', 0))
            d_meta = float(row.get('Dias Meta', 0))
            d_trab = float(row.get('Dias Trabalhados', 0))
            
            pos = int(row.get('Posicao Ranking', 0))
            if pos > 0 and 'SEPARADOR' in str(funcao).upper():
                pos_str = f"{pos}º Lugar"
            else:
                pos_str = "-"
            
            for kpi in kpis_gerais:
                meta2 = float(row.get(f"{kpi}_Meta2", 0))
                
                if meta2 > 0:
                    real = float(row.get(kpi, 0))
                    valor = float(row.get(f"{kpi}_Valor", 0))
                    
                    meta1 = float(row.get(f"{kpi}_Meta1", 0))
                    meta3 = float(row.get(f"{kpi}_Meta3", 0))
                    racional = float(row.get(f"{kpi}_Racional", 1))
                    
                    if meta1 <= 0: meta1 = meta2
                    if meta3 <= 0: meta3 = meta2
                    
                    if racional == 1: 
                        if real < meta1: faixa_meta = "0%"
                        elif real < meta2: faixa_meta = "50%"
                        elif real < meta3: faixa_meta = "100%"
                        else: faixa_meta = "120%"
                    else: 
                        if real > meta1: faixa_meta = "0%"
                        elif real > meta2: faixa_meta = "50%"
                        elif real > meta3: faixa_meta = "100%"
                        else: faixa_meta = "120%"
                    
                    def formata(v):
                        if "Tempo" in str(kpi): return f"{int(v)//3600:02d}:{(int(v)%3600)//60:02d}:{(int(v)%60):02d}"
                        elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi): return f"{v:.2f}%".replace('.', ',')
                        else: return f"{v:,.0f}".replace(',', '.')
                    
                    real_str = formata(real)
                    
                    df_auditoria.append({
                        "CÓD.": cod,
                        "NOME": nome,
                        "TURNO": turno,
                        "FUNÇÃO": funcao,
                        "POSIÇÃO RANKING": pos_str,
                        "DIAS ÚTEIS": int(d_uteis),
                        "DIAS META": int(d_meta),
                        "DIAS TRAB.": int(d_trab),
                        "INDICADOR": kpi,
                        "REALIZADO": real_str,
                        "VALOR GANHO (R$)": valor,
                        "META ATINGIDA": faixa_meta
                    })
        
        df_export = pd.DataFrame(df_auditoria)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Auditoria_Fechamento', header=False, startrow=1)
            
            workbook  = writer.book
            worksheet = writer.sheets['Auditoria_Fechamento']
            
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
            formato_central = workbook.add_format({'align': 'center'})
            
            (max_row, max_col) = df_export.shape
            
            col_settings = [{'header': column} for column in df_export.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': col_settings,
                'style': 'Table Style Medium 2'
            })
            
            worksheet.set_column('A:A', 10, formato_central) 
            worksheet.set_column('B:B', 38)                  
            worksheet.set_column('C:C', 12, formato_central) 
            worksheet.set_column('D:D', 22)                  
            worksheet.set_column('E:E', 18, formato_central) 
            worksheet.set_column('F:H', 13, formato_central) 
            worksheet.set_column('I:I', 25)                  
            worksheet.set_column('J:J', 15, formato_central) 
            worksheet.set_column('K:K', 20, formato_moeda)   
            worksheet.set_column('L:L', 18, formato_central) 
        
        st.sidebar.download_button(
            label="📥 Baixar Auditoria",
            data=buffer.getvalue(),
            file_name=f"Auditoria_Produtividade_Fechamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        st.sidebar.button("🔒 Fechamento (Auditoria)", disabled=True, use_container_width=True, help="A Auditoria é liberada apenas quando o período for exato: do dia 26 ao dia 25.")

st.sidebar.markdown("---")
st.sidebar.title("🔍 Filtros do Painel")

# --- LÓGICA DO FILTRO DE TURNO ---
turno_logado = st.session_state["turno_acesso"]

if turno_logado == "Todos":
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
else:
    turno_selecionado = turno_logado
    st.sidebar.info(f"🔒 Acesso restrito ao Turno: **{turno_selecionado}**")

df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()

lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
focar_detratores = st.sidebar.checkbox("🚨 Filtrar Desempenho Abaixo da Meta")

# ==========================================
# 🔥 MÓDULO DE EXTRAÇÃO RH
# ==========================================
if st.session_state["perfil"] == "Gerente":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗃️ Fechamento RH")

    if not df_filtrado.empty:
        df_rh = df_filtrado[['CÓD.', 'NOME', 'FUNÇÃO', 'TURNO', 'Valor Final']].copy()
        df_rh = df_rh.rename(columns={'CÓD.': 'Matrícula', 'NOME': 'Nome', 'Valor Final': 'Premiação (R$)'})
        
        df_rh['Premiação (R$)'] = df_rh['Premiação (R$)'].round(2)
        df_rh = df_rh.drop_duplicates(subset=['Matrícula', 'Nome'])
        df_rh = df_rh.sort_values(by='Nome')
        
        config_rh = {
            "Matrícula": st.column_config.TextColumn("Matrícula"), 
            "Premiação (R$)": st.column_config.NumberColumn("Premiação (R$)", format="R$ %.2f")
        }
        
        st.sidebar.dataframe(df_rh, hide_index=True, use_container_width=True, column_config=config_rh)
        
        df_download = df_rh.copy()
        df_download['Premiação (R$)'] = df_download['Premiação (R$)'].apply(
            lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
        
        csv_rh = df_download.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        
        st.sidebar.download_button(
            label="📥 Baixar Planilha do RH",
            data=csv_rh,
            file_name=f"Fechamento_RH_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
            key="btn_rh_unico_download"
        )
    else:
        st.sidebar.info("Nenhum dado processado.")

# ==========================================
# 4. RENDERIZAÇÃO DA TELA
# ==========================================
try:
    kpis_mapeados = [c.replace('_Racional', '') for c in df_filtrado.columns if '_Racional' in c]

    col_titulo, col_kpis = st.columns([1, 1.2])
    
    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')}")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)
        col_vol = next((k for k in kpis_mapeados if 'itens' in k.lower() or 'palet' in k.lower() or 'mov' in k.lower()), kpis_mapeados[0] if kpis_mapeados else None)
        total_vol = df_filtrado[col_vol].sum() if col_vol and col_vol in df_filtrado.columns else 0
        
        kpi1.metric(f"📦 {col_vol or 'Volume'}", f"{total_vol:,.0f}".replace(',', '.'))
        kpi2.metric("👥 Colaboradores", len(df_filtrado))
        total_horas = df_filtrado['Horas'].sum() if 'Horas' in df_filtrado.columns else 0
        kpi3.metric("⏱️ Horas Registradas", f"{total_horas:.1f} h" if total_horas > 0 else "—")

    st.divider()

    # ==========================================
    # 🚨 MÓDULO DETRATORES
    # ==========================================
    if focar_detratores:
        st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
        houve_detrator = False

        for idx, row in df_filtrado.iterrows():
            detalhes_gargalo = []
            
            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                if pd.isna(meta2) or str(meta2).strip() in ['0', '0.0', '-', '']: continue
                
                realizado = float(row.get(kpi, 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                meta1 = float(row.get(f"{kpi}_Meta1", meta2))

                if racional == 1 and realizado == 0: continue 

                abaixo_da_meta = False
                if racional == 1 and realizado < meta1: abaixo_da_meta = True
                elif racional == 0 and realizado > meta1: abaixo_da_meta = True

                if abaixo_da_meta:
                    if "%" in kpi or "Avaria" in kpi or "Corte" in kpi or "Dev" in kpi:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado:.2f}% vs Alvo Mínimo (Meta 1) {meta1:.2f}%")
                    else:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado:,.0f} vs Alvo Mínimo (Meta 1) {meta1:,.0f}".replace(',', '.'))

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
                                            aba_rh = conectar_planilha().worksheet("Historico_RH")
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
                                        aba_rh = conectar_planilha().worksheet("Historico_RH")
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
            
            pos = int(row.get('Posicao Ranking', 0))
            val_rank = row.get('Valor Ranking', 0)
            cargo_p = str(row.get('FUNÇÃO', '')).upper()
            
            if pos > 0 and 'SEPARADOR' in cargo_p:
                funcao_original = row.get('FUNÇÃO', '')
                total_eq = len(df_filtrado[(df_filtrado['TURNO'] == row.get('TURNO')) & (df_filtrado['FUNÇÃO'] == funcao_original)])
                
                if pos == 1: medalha, cor_rank = "🥇", "#ffd700"
                elif pos == 2: medalha, cor_rank = "🥈", "#c0c0c0"
                elif pos == 3: medalha, cor_rank = "🥉", "#cd7f32"
                else: medalha, cor_rank = "🏅", "#555555" 
                
                if val_rank > 0:
                    texto_premio_rank = f" | <span style='color: #2ecc71;'><b>💰 Prêmio Ranking: R$ {val_rank:,.2f}</b></span>".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    texto_premio_rank = ""
                
                st.markdown(f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'><b>{medalha} Posição no Ranking:</b> {pos}º lugar de {total_eq} na equipe de {funcao_original}{texto_premio_rank}</div>", unsafe_allow_html=True)

            cols_meta = st.columns(4)
            col_idx = 0
            grafico_dados = []

            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                if pd.isna(meta2) or str(meta2).strip() in ['0', '0.0', '-', '']: continue

                realizado = float(row.get(kpi, 0))
                meta1, meta2, meta3 = float(row.get(f"{kpi}_Meta1", 0)), float(meta2), float(row.get(f"{kpi}_Meta3", 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                valor_reais = float(row.get(f"{kpi}_Valor", 0))

                if racional == 1: 
                    perc_atingimento = (realizado / meta2) if meta2 > 0 else 0
                    if realizado < meta1: alvo_atual, nome_alvo = meta1, "Meta 1"
                    elif realizado < meta2: alvo_atual, nome_alvo = meta2, "Meta 2"
                    elif realizado < meta3: alvo_atual, nome_alvo = meta3, "Meta 3"
                    else: alvo_atual, nome_alvo = meta3, "Meta Máx"
                    
                    if realizado >= meta3: cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif realizado >= meta2: cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif realizado >= meta1: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                else: 
                    perc_atingimento = (meta2 / realizado) if realizado > 0 else 1.2
                    if realizado > meta1: alvo_atual, nome_alvo = meta1, "Meta 1"
                    elif realizado > meta2: alvo_atual, nome_alvo = meta2, "Meta 2"
                    elif realizado > meta3: alvo_atual, nome_alvo = meta3, "Meta 3"
                    else: alvo_atual, nome_alvo = meta3, "Meta Máx"

                    if realizado <= meta3: cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif realizado <= meta2: cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif realizado <= meta1: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"

                real_perc = perc_atingimento * 100
                grafico_dados.append({'Indicador': f"<b>{kpi}</b>", 'Atingimento (%)': min(real_perc, 120), 'Real': real_perc})
                html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""

                if "Tempo" in str(kpi) or ":" in str(realizado):
                     val_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                     alvo_tela = f"{int(alvo_atual)//3600:02d}:{(int(alvo_atual)%3600)//60:02d}:{int(alvo_atual)%60:02d}"
                elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi):
                    val_tela = f"{realizado:.2f}%"
                    alvo_tela = f"{alvo_atual:.2f}%"
                else:
                    val_tela = f"{realizado:,.0f}".replace(',', '.')
                    alvo_tela = f"{alvo_atual:,.0f}".replace(',', '.')

                alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {alvo_tela}</span>"

                with cols_meta[col_idx % 4]:
                    st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{kpi}</div><div class='texto-card-principal'>{val_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status} {html_dinheiro}</div></div>", unsafe_allow_html=True)
                col_idx += 1

            valor_final_total = row.get('Valor Final', 0)
            if valor_final_total > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {valor_final_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

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
                
                col_grafico, col_tabela = st.columns([1.2, 1])
                with col_grafico:
                    st.plotly_chart(fig, use_container_width=True)
                with col_tabela:
                    cargo_p = str(row.get('FUNÇÃO', '')).upper()
                    turno_p = str(row.get('TURNO', '')).upper()

                    # ==========================================
                    # 🔥 NOVO: DRILL-DOWN DIÁRIO (APENAS T3 SEPARADOR)
                    # ==========================================
                    if turno_p == "T3" and "SEPARADOR" in cargo_p:
                        if not df_diario.empty:
                            df_pessoa_diario = df_diario[df_diario['NOME'] == pessoa_selecionada]
                            if not df_pessoa_diario.empty:
                                pessoa_d_row = df_pessoa_diario.iloc[0]
                                
                                cols_datas_reais = []
                                opcoes_datas_formatadas = []
                                
                                for c in df_diario.columns:
                                    c_str = str(c).strip()
                                    if any(char.isdigit() for char in c_str) and ('/' in c_str or '-' in c_str) and 'Inicio' not in c_str and 'Horas' not in c_str and 'Itens' not in c_str and 'JL' not in c_str:
                                        cols_datas_reais.append(c_str)
                                        
                                        data_limpa = c_str.split(' ')[0] 
                                        if '-' in data_limpa and len(data_limpa.split('-')[0]) == 4:
                                            ano, mes, dia = data_limpa.split('-')
                                            opcoes_datas_formatadas.append(f"{dia}/{mes}/{ano}")
                                        else:
                                            opcoes_datas_formatadas.append(data_limpa)
                                
                                if cols_datas_reais:
                                    col_tit_diario, col_data_diario = st.columns([1.6, 1])
                                    
                                    with col_tit_diario:
                                        st.markdown("### 📅 Resultado Diário")
                                        
                                    with col_data_diario:
                                        data_escolhida_display = st.selectbox(
                                            "Data Apuração", 
                                            opcoes_datas_formatadas, 
                                            label_visibility="collapsed", 
                                            key="sel_data_diario_alinhado"
                                        )
                                    
                                    idx_escolha = opcoes_datas_formatadas.index(data_escolhida_display)
                                    nome_coluna_real = cols_datas_reais[idx_escolha]
                                    col_index = list(df_diario.columns).index(nome_coluna_real)
                                    
                                    val_itens = str(pessoa_d_row.iloc[col_index]).strip()
                                    val_horas = str(pessoa_d_row.iloc[col_index + 1]).strip()
                                    val_itens_hora = str(pessoa_d_row.iloc[col_index + 2]).strip()
                                    val_jl_raw = str(pessoa_d_row.iloc[col_index + 3]).strip()
                                    
                                    val_itens = val_itens if val_itens and val_itens.lower() not in ['nan', 'none'] else "0"
                                    val_horas = val_horas if val_horas and val_horas.lower() not in ['nan', 'none'] else "0"
                                    val_itens_hora = val_itens_hora if val_itens_hora and val_itens_hora.lower() not in ['nan', 'none'] else "0"
                                    
                                    try:
                                        if val_jl_raw and val_jl_raw.lower() not in ['nan', 'none']:
                                            val_jl_num = float(val_jl_raw.replace(',', '.').replace('%', ''))
                                            if val_jl_num <= 2.0 and "%" not in val_jl_raw: 
                                                val_jl_num = val_jl_num * 100
                                            jl_display = f"{int(val_jl_num)}%" 
                                        else:
                                            jl_display = "0%"
                                    except:
                                        jl_display = "0%"
                                        
                                    try: val_itens = f"{float(val_itens.replace(',', '.')):,.0f}".replace(',', '.')
                                    except: pass
                                    
                                    try: val_itens_hora = f"{int(round(float(val_itens_hora.replace(',', '.'))))}"
                                    except: val_itens_hora = "0"

                                    try:
                                        horas_dec = float(val_horas.replace(',', '.'))
                                        h = int(horas_dec)
                                        m = int((horas_dec - h) * 60)
                                        s = int((((horas_dec - h) * 60) - m) * 60)
                                        val_horas_formatado = f"{h:02d}:{m:02d}:{s:02d}"
                                    except:
                                        val_horas_formatado = "00:00:00"

                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("⏱️ Horas", val_horas_formatado)
                                    c2.metric("⚡ Itens/Hora", val_itens_hora)
                                    c3.metric("🎯 JL", jl_display)
                                    
                                    st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>Itens Separados</h4><h2 style='margin:0; color: {C_AZUL};'>{val_itens}</h2></div>", unsafe_allow_html=True)
                                    
                                else:
                                    st.markdown("### 📅 Resultado Diário")
                                    st.info("Nenhuma data foi identificada no cabeçalho do Relatório Diário.")
                            else:
                                st.markdown("### 📅 Resultado Diário")
                                st.warning("Colaborador não encontrado na aba 'Relatorio Diario'.")
                        else:
                            st.markdown("### 📅 Resultado Diário")
                            st.warning("⚠️ Não foi possível carregar os dados. Verifique se o nome da aba é 'Relatorio Diario'.")

                    # ==========================================
                    # TABELA NORMAL (PARA CONFERENTES, T1 E T2)
                    # ==========================================
                    else:
                        kpis_ativos_pessoa = []
                        for k in kpis_mapeados:
                            m2 = pd.to_numeric(row.get(f"{k}_Meta2", 0), errors='coerce')
                            if pd.notna(m2) and m2 > 0:
                                kpis_ativos_pessoa.append(k)

                        col_uteis = ['CÓD.', 'NOME', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final'] + kpis_ativos_pessoa
                        df_tabela_mini = dados_pessoa[[c for c in col_uteis if c in df_filtrado.columns]].copy()
                        
                        if 'Tempo Médio' in df_tabela_mini.columns:
                            df_tabela_mini['Tempo Médio'] = df_tabela_mini['Tempo Médio'].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if pd.notna(s) else "00:00:00")
                        
                        config_colunas = {'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")}
                        
                        for col in df_tabela_mini.columns:
                            if col in ['CÓD.', 'NOME', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim', 'Valor Final']: continue 
                            elif col in ['Avaria', 'Corte %', 'Dev. %']: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                            elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                            else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")
                        
                        st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=350, column_config=config_colunas)

    # ==========================================
    # 👥 VISÃO GERAL EQUIPE (MÉDIAS) E TABELAS
    # ==========================================
    else:
        filtros_ativos = (turno_selecionado != "Todos") or (cargo_selecionado != "Todos")

        if not filtros_ativos:
            # --- 🚀 TELA DE BOAS-VINDAS (LANDING PAGE) ---
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; color: lightgray;'>👋 Bem-vindo ao Painel de Comando da Expedição</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 18px; color: #888;'>O painel de produtividade está pronto. Utilize o menu lateral para direcionar sua análise.</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_AZUL}; height: 100%;'><h4>👥 Visão de Equipe</h4><p style='color: #ccc; font-size: 15px;'>Filtre por <b>Turno</b> ou <b>Função</b> para carregar os indicadores coletivos. O sistema calculará as médias automaticamente e indicará o atingimento das metas.</p></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_VERDE}; height: 100%;'><h4>🎯 Análise Individual</h4><p style='color: #ccc; font-size: 15px;'>Selecione um <b>Colaborador</b> para auditar seu desempenho real, prêmios conquistados, posição no Ranking e o detalhamento da produção diária.</p></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_VERMELHO}; height: 100%;'><h4>🚨 Gestão de Detratores</h4><p style='color: #ccc; font-size: 15px;'>Ative o filtro de <b>Desempenho Abaixo da Meta</b> para identificar gargalos na operação, registrar feedbacks diretos e solicitar reciclagens para o RH.</p></div>", unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)

        else:
            cargos_render = [cargo_selecionado] if cargo_selecionado != "Todos" else sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())

            for cargo_atual in cargos_render:
                df_cargo = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_atual]
                if df_cargo.empty: continue

                st.markdown(f"<h4 style='color: lightgray; margin-top: 15px;'>🔹 Equipe: {cargo_atual}</h4>", unsafe_allow_html=True)
                cols_eq = st.columns(4)
                col_idx = 0

                for kpi in kpis_mapeados:
                    if f"{kpi}_Meta2" in df_cargo.columns:
                        racional_temp = df_cargo[f"{kpi}_Racional"].mode()[0] if not df_cargo[f"{kpi}_Racional"].empty else 1
                        
                        if racional_temp == 1: df_kpi_valido = df_cargo[df_cargo[kpi] > 0]
                        else: df_kpi_valido = df_cargo[df_cargo['Dias Trabalhados'] > 0]
                            
                        if df_kpi_valido.empty: continue

                        meta2_med = df_kpi_valido[f"{kpi}_Meta2"].mean()
                        if pd.isna(meta2_med) or meta2_med <= 0: continue

                        meta1_med = df_kpi_valido[f"{kpi}_Meta1"].mean() if f"{kpi}_Meta1" in df_kpi_valido.columns else meta2_med
                        meta3_med = df_kpi_valido[f"{kpi}_Meta3"].mean() if f"{kpi}_Meta3" in df_kpi_valido.columns else meta2_med
                        
                        real_med = df_kpi_valido[kpi].mean()
                        racional = racional_temp
                        soma_total = df_kpi_valido[kpi].sum()

                        if racional == 1: 
                            if real_med < meta1_med: alvo_atual_med, nome_alvo = meta1_med, "Meta 1"
                            elif real_med < meta2_med: alvo_atual_med, nome_alvo = meta2_med, "Meta 2"
                            elif real_med < meta3_med: alvo_atual_med, nome_alvo = meta3_med, "Meta 3"
                            else: alvo_atual_med, nome_alvo = meta3_med, "Meta Máx"
                            perc = (real_med / meta2_med) if meta2_med > 0 else 0
                        else: 
                            if real_med > meta1_med: alvo_atual_med, nome_alvo = meta1_med, "Meta 1"
                            elif real_med > meta2_med: alvo_atual_med, nome_alvo = meta2_med, "Meta 2"
                            elif real_med > meta3_med: alvo_atual_med, nome_alvo = meta3_med, "Meta 3"
                            else: alvo_atual_med, nome_alvo = meta3_med, "Meta Máx"
                            perc = (meta2_med / real_med) if real_med > 0 else 1.2

                        real_perc = perc * 100

                        if real_perc >= 120: cor, icone, status = C_AZUL, "🔵", "Superando"
                        elif real_perc >= 100: cor, icone, status = C_VERDE, "🟢", "Na Meta"
                        elif real_perc >= 50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                        else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"

                        metricas_globais = ['DEV', 'CORTE', 'AVARIA', 'ITENS RAMPA', 'CARGA PALET', 'CARGA BAT', 'PALETS PX', 'TEMPO MÉDIO', 'MÉD. PALET']
                        eh_global = any(g in str(kpi).upper() for g in metricas_globais)
                        
                        if "Tempo" in str(kpi):
                            v_tela = f"{int(real_med)//3600:02d}:{(int(real_med)%3600)//60:02d}:{(int(real_med)%60):02d}"
                            t_tela = f"{int(alvo_atual_med)//3600:02d}:{(int(alvo_atual_med)%3600)//60:02d}:{(int(alvo_atual_med)%60):02d}"
                        elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi):
                            v_tela = f"{real_med:.2f}%"
                            t_tela = f"{alvo_atual_med:.2f}%"
                        else:
                            v_tela = f"{real_med:,.0f}".replace(',', '.')
                            t_tela = f"{alvo_atual_med:,.0f}".replace(',', '.')

                        if eh_global:
                            titulo_card = f"{kpi}"
                        else:
                            soma_str = f"{soma_total:,.0f}".replace(',', '.')
                            titulo_card = f"Média: {kpi} <span style='color: #888; font-weight: normal; font-size: 16px;'>(Soma: {soma_str})</span>"
                            
                        alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {t_tela}</span>"

                        with cols_eq[col_idx % 4]:
                            st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{titulo_card}</div><div class='texto-card-principal'>{v_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div></div>", unsafe_allow_html=True)
                        col_idx += 1

        # ==========================================
        # 🔥 TABELA GERENCIAL (SÓ APARECE SE FILTRAR)
        # ==========================================
        if filtros_ativos:
            if 'cargos_render' in locals() and len(cargos_render) > 0: st.divider()
            
            st.markdown("### 📋 Tabela de Produtividade Consolidada (Relatório Gerencial)")
            
            kpis_ativos_tabela = []
            for kpi in kpis_mapeados:
                if f"{kpi}_Meta2" in df_filtrado.columns:
                    metas_validas = pd.to_numeric(df_filtrado[f"{kpi}_Meta2"], errors='coerce').fillna(0)
                    if metas_validas.sum() > 0:
                        kpis_ativos_tabela.append(kpi)

            colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final'] + kpis_ativos_tabela
            df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()

            config = {
                'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")
            }
            st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    st.error(f"⚠️ Erro ao renderizar painel: {e}")
