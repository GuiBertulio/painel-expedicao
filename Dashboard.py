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
# 2. CARREGAMENTO DOS DADOS E CÁLCULO DE RANKING
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # --- MAPEAMENTO INTELIGENTE DO EXCEL (AUX CALC) ---
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

    # Limpeza de nomes
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
            if col == 'Tempo Médio': 
                texto_limpo = df[col].astype(str).str.split('.').str[0].str.strip()
                df[col] = pd.to_timedelta(texto_limpo, errors='coerce').dt.total_seconds().fillna(0)
            else:
                texto_limpo = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(texto_limpo, errors='coerce').fillna(0)
    
    # ========================================================
    # INJEÇÃO DO BÔNUS DE RANKING NO DATAFRAME
    # ========================================================
    df['Valor Ranking'] = 0.0
    df['Posicao Ranking'] = 0
    
    for turno in ['T2', 'T3']:
        for cargo in df['FUNÇÃO'].unique():
            if 'SEPARADOR' in str(cargo).upper():
                df_eq = df[(df['TURNO'] == turno) & (df['FUNÇÃO'] == cargo)].copy()
                if df_eq.empty: continue
                
                kpis = [c.replace('_Racional', '') for c in df_eq.columns if '_Racional' in c]
                if not kpis: continue
                metrica_rank = kpis[0] 
                
                racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
                ordem_cresc = False if racional == 1 else True
                
                df_eq = df_eq.sort_values(by=metrica_rank, ascending=ordem_cresc)
                
                pos = 1
                for idx, row_eq in df_eq.iterrows():
                    if float(row_eq.get(metrica_rank, 0)) <= 0: continue
                    
                    df.at[idx, 'Posicao Ranking'] = pos
                    
                    if pos == 1: val_base = 250.0 if turno == 'T3' else 150.0
                    elif pos == 2: val_base = 200.0 if turno == 'T3' else 100.0
                    elif pos == 3: val_base = 100.0 if turno == 'T3' else 50.0
                    else: val_base = 0.0
                    
                    if val_base > 0:
                        d_uteis = float(row_eq.get('Dias Uteis', 26))
                        d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                        fator = d_trab / d_uteis if d_uteis > 0 else 1
                        df.at[idx, 'Valor Ranking'] = val_base * fator
                    
                    pos += 1

    colunas_valor = [c for c in df.columns if c.endswith('_Valor')]
    df['Valor Final'] = df[colunas_valor].sum(axis=1) + df['Valor Ranking']

    return df

df = carregar_dados()

# ==========================================
# 3. LÓGICA DE DATAS E FILTROS
# ==========================================
if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
    dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0], dayfirst=True).date()
    data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0], dayfirst=True).date()
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)

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
# 🔥 MÓDULO DE EXTRAÇÃO RH
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗃️ Fechamento RH")

if not df_filtrado.empty:
    df_rh = df_filtrado[['CÓD.', 'NOME', 'FUNÇÃO', 'TURNO', 'Valor Final']].copy()
    df_rh = df_rh.rename(columns={'CÓD.': 'Matrícula', 'NOME': 'Nome', 'Valor Final': 'Premiação (R$)'})
    df_rh = df_rh.sort_values(by='Nome')
    
    st.sidebar.dataframe(df_rh.style.format({'Premiação (R$)': 'R$ {:,.2f}'}), hide_index=True, use_container_width=True)
    csv_rh = df_rh.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    
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
# 4. RENDERIZAÇÃO DA TELA (COM TRY/EXCEPT)
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
                meta2 = float(meta2)

                abaixo_da_meta = False
                if racional == 1 and realizado < meta2: abaixo_da_meta = True
                elif racional == 0 and realizado > meta2: abaixo_da_meta = True

                if abaixo_da_meta:
                    if "%" in kpi or "Avaria" in kpi:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado * 100:.2f}% vs Alvo Base {meta2 * 100:.2f}%")
                    else:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado:,.0f} vs Alvo Base {meta2:,.0f}".replace(',', '.'))

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
            
            if row.get('Valor Ranking', 0) > 0:
                pos = int(row.get('Posicao Ranking', 0))
                cargo_p = row.get('FUNÇÃO', '')
                total_eq = len(df_filtrado[(df_filtrado['TURNO'] == row.get('TURNO')) & (df_filtrado['FUNÇÃO'] == cargo_p)])
                val_rank = row.get('Valor Ranking', 0)
                
                if pos == 1: medalha, cor_rank = "🥇", "#ffd700"
                elif pos == 2: medalha, cor_rank = "🥈", "#c0c0c0"
                elif pos == 3: medalha, cor_rank = "🥉", "#cd7f32"
                else: medalha, cor_rank = "🏅", "gray"
                
                texto_premio_rank = f" | <span style='color: #2ecc71;'><b>💰 Prêmio: R$ {val_rank:,.2f}</b></span>".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.markdown(f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'><b>{medalha} Posição no Ranking:</b> {pos}º lugar de {total_eq} na equipe de {cargo_p}{texto_premio_rank}</div>", unsafe_allow_html=True)

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
                    if realizado >= meta3: cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif realizado >= meta2: cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif realizado >= meta1: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                else: 
                    perc_atingimento = (meta2 / realizado) if realizado > 0 else 1.2
                    if realizado <= meta3: cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif realizado <= meta2: cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif realizado <= meta1: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"

                real_perc = perc_atingimento * 100
                grafico_dados.append({'Indicador': f"<b>{kpi}</b>", 'Atingimento (%)': min(real_perc, 120), 'Real': real_perc})

                html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""

                if "Tempo" in str(kpi) or ":" in str(realizado):
                     val_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                     alvo_tela = f"{int(meta3)//3600:02d}:{(int(meta3)%3600)//60:02d}:{int(meta3)%60:02d}"
                elif "%" in str(kpi) or "Avaria" in str(kpi):
                    val_tela = f"{realizado * 100:.2f}%" if realizado < 1 else f"{realizado:.2f}%"
                    alvo_tela = f"{meta3 * 100:.2f}%" if meta3 < 1 else f"{meta3:.2f}%"
                else:
                    val_tela = f"{realizado:,.0f}".replace(',', '.')
                    alvo_tela = f"{meta3:,.0f}".replace(',', '.')

                # --- [COMO EDITAR: LAYOUT DO CARD INDIVIDUAL] ---
                # A variável 'alvo_formatado' insere a meta ao lado do valor com texto menor
                titulo_card = kpi
                alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo (Meta 3): {alvo_tela}</span>"

                with cols_meta[col_idx % 4]:
                    st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{titulo_card}</div><div class='texto-card-principal'>{val_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status} {html_dinheiro}</div></div>", unsafe_allow_html=True)
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
                    col_uteis = ['CÓD.', 'NOME', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final'] + kpis_mapeados
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
    # 👥 VISÃO GERAL EQUIPE (MÉDIAS)
    # ==========================================
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
                    meta2_med = df_cargo[f"{kpi}_Meta2"].mean()
                    if pd.isna(meta2_med) or meta2_med <= 0: continue

                    real_med = df_cargo[kpi].mean()
                    racional = df_cargo[f"{kpi}_Racional"].mode()[0] if not df_cargo[f"{kpi}_Racional"].empty else 1
                    soma_total = df_cargo[kpi].sum()

                    if racional == 1: perc = (real_med / meta2_med) if meta2_med > 0 else 0
                    else: perc = (meta2_med / real_med) if real_med > 0 else 1.2

                    real_perc = perc * 100

                    if real_perc >= 120: cor, icone, status = C_AZUL, "🔵", "Superando"
                    elif real_perc >= 100: cor, icone, status = C_VERDE, "🟢", "Na Meta"
                    elif real_perc >= 50: cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else: cor, icone, status = C_VERMELHO, "🔴", "Abaixo"

                    meta3_med = df_cargo[f"{kpi}_Meta3"].mean()
                    
                    # --- [COMO EDITAR: LISTA DE MÉTRICAS GLOBAIS] ---
                    # Adicione aqui palavras-chave dos indicadores que NÃO devem ter a palavra 'Média' nem exibir 'Soma Equipe'
                    metricas_globais = ['DEV', 'CORTE', 'AVARIA', 'ITENS RAMPA', 'CARGA PALET', 'CARGA BAT', 'PALETS PX', 'TEMPO', 'MÉD. PALET']
                    eh_global = any(g in str(kpi).upper() for g in metricas_globais)
                    
                    if "Tempo" in str(kpi):
                        v_tela = f"{int(real_med)//3600:02d}:{(int(real_med)%3600)//60:02d}:{(int(real_med)%60):02d}"
                        t_tela = f"{int(meta3_med)//3600:02d}:{(int(meta3_med)%3600)//60:02d}:{(int(meta3_med)%60):02d}"
                    elif "%" in str(kpi) or "Avaria" in str(kpi):
                        v_tela = f"{real_med * 100:.2f}%" if real_med < 1 else f"{real_med:.2f}%"
                        t_tela = f"{meta3_med * 100:.2f}%" if meta3_med < 1 else f"{meta3_med:.2f}%"
                    else:
                        v_tela = f"{real_med:,.0f}".replace(',', '.')
                        t_tela = f"{meta3_med:,.0f}".replace(',', '.')

                    # --- [COMO EDITAR: LAYOUT DO CARD DA EQUIPE] ---
                    # Se for métrica global, o título é só o nome (ex: "Avaria").
                    # Se não for, ele mostra "Média: Itens Sep (Soma: 52.000)"
                    if eh_global:
                        titulo_card = f"{kpi}"
                    else:
                        soma_str = f"{soma_total:,.0f}".replace(',', '.')
                        titulo_card = f"Média: {kpi} <span style='color: #888; font-weight: normal; font-size: 16px;'>(Soma: {soma_str})</span>"
                        
                    alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo (Meta 3): {t_tela}</span>"

                    with cols_eq[col_idx % 4]:
                        st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{titulo_card}</div><div class='texto-card-principal'>{v_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div></div>", unsafe_allow_html=True)
                    col_idx += 1

        if len(cargos_render) > 0: st.divider()
        st.markdown("### 📋 Tabela de Produtividade Consolidada (Relatório Gerencial)")
        
        colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Ranking', 'Valor Final'] + kpis_mapeados
        df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()

        config = {
            'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f"),
            'Valor Ranking': st.column_config.NumberColumn("Rank R$", format="R$ %.2f")
        }
        st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    st.error(f"⚠️ Erro ao renderizar painel: {e}")
