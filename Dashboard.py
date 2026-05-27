import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

# ==========================================
# CONEXÃO COM GOOGLE SHEETS (FEEDBACK/RECICLAGEM)
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
# 2. CARREGAMENTO DOS DADOS (ABA RELATÓRIO)
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    # LINK DA ABA "RELATÓRIO_RH" 
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=1520498693&single=true&output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    colunas_renomeadas = {}
    prefixos = [
        ('', '', '', '', '', '', '', '', ''), 
        ('.1', '.1', '.1', '.1', '.1', '.1', '.1', '.1', '.1'), 
        ('.2', '.2', '.2', '.2', '.2', '.2', '.2', '.2', '.2'), 
        ('.3', '.3', '.3', '.3', '.3', '.3', '.3', '.3', '.3')
    ]
    
    for i, prefs in enumerate(prefixos):
        n = i + 1
        colunas_renomeadas[f'Indicador {n}'] = f'Ind_{n}_Nome'
        colunas_renomeadas[f'Tipo Ating.{prefs[0]}'] = f'Ind_{n}_Tipo'
        colunas_renomeadas[f'Prop.{prefs[1]}'] = f'Ind_{n}_Prop'
        colunas_renomeadas[f'0,5{prefs[2]}'] = f'Ind_{n}_Alvo_50'
        colunas_renomeadas[f'1{prefs[3]}'] = f'Ind_{n}_Alvo_100'
        colunas_renomeadas[f'1,2{prefs[4]}'] = f'Ind_{n}_Alvo_120'
        colunas_renomeadas[f'Atingimento{prefs[5]}'] = f'Ind_{n}_Realizado'
        colunas_renomeadas[f'%{prefs[6]}'] = f'Ind_{n}_Perc'
        colunas_renomeadas[f'R${prefs[7]}'] = f'Ind_{n}_Valor'

    df = df.rename(columns=colunas_renomeadas)
    
    if 'NOME' in df.columns:
        df = df.dropna(subset=['NOME'])
        df = df[df['NOME'] != '-'] 
        
    if 'FUNÇÃO' in df.columns: df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns: df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
        
    for col in df.columns:
        if 'Valor' in col or 'Alvo' in col or 'Perc' in col or 'Realizado' in col or col == 'Valor Final':
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.replace('-', '0', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Garante que as colunas de dias existam mesmo se não vierem do Sheets
    if 'Dias Meta' not in df.columns: df['Dias Meta'] = 26
    if 'Dias Uteis' not in df.columns: df['Dias Uteis'] = 26
    if 'Dias Trabalhados' not in df.columns: df['Dias Trabalhados'] = 26

    return df

# ==========================================
# 3. LÓGICA DE DATAS E FILTROS
# ==========================================
try:
    df = carregar_dados()
    
    # --- DATAS ---
    if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
        dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0], dayfirst=True).date()
        data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0], dayfirst=True).date()
    else:
        hoje = datetime.date.today()
        dt_inicio = datetime.date(hoje.year, hoje.month, 26) if hoje.day >= 26 else datetime.date(hoje.year if hoje.month > 1 else hoje.year - 1, hoje.month - 1 if hoje.month > 1 else 12, 26)
        data_apuracao = hoje - datetime.timedelta(days=1)

    dias_uteis_base = int(df['Dias Uteis'].max()) if not df.empty and df['Dias Uteis'].max() > 0 else 26
    dias_decorridos_base = int(df['Dias Trabalhados'].max()) if not df.empty and df['Dias Trabalhados'].max() > 0 else dias_uteis_base

    # --- FILTROS ---
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
    # 🔥 MÓDULO FECHAMENTO RH
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗃️ Fechamento RH")
    
    # O cálculo do RH agora é instantâneo: apenas puxamos a coluna 'Valor Final' já mastigada!
    df_rh = df_filtrado[['CÓD.', 'NOME', 'FUNÇÃO', 'TURNO', 'Valor Final']].copy()
    df_rh = df_rh.rename(columns={'Valor Final': 'Premiação (R$)'})
    df_rh = df_rh.sort_values(by='NOME')
    
    if not df_rh.empty:
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
