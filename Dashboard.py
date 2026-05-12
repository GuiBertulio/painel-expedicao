import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS (VISUAL)
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Força NEGRITO MÁXIMO nos Títulos e Subtítulos */
    h1, h2, h3 {
        font-weight: 900 !important;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetricValue"] {
        font-size: 50px !important;
        color: #3b82f6 !important; /* Azul mais claro e vibrante */
    }
    [data-testid="stMetricLabel"] > div {
        font-size: 20px !important;
        font-weight: bold !important;
        color: lightgray;
    }
    .card-meta {
        background-color: var(--background-color); 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 1px 1px 5px rgba(0,0,0,0.3); 
        margin-bottom: 15px;
        border-left: 8px solid #ccc; /* Borda mais grossa */
        border-top: 1px solid var(--secondary-background-color);
        border-right: 1px solid var(--secondary-background-color);
        border-bottom: 1px solid var(--secondary-background-color);
    }
    .texto-card-principal {
        font-size: 42px; /* Número maior */
        color: var(--text-color); 
        font-weight: 900; 
        line-height: 1.1;
    }
    .texto-card-titulo {
        font-size: 22px; /* Título do indicador maior e mais visível */
        color: var(--text-color); 
        font-weight: 900; 
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# PALETA DE CORES VIBRANTES (Para Dark Mode)
# ==========================================
C_AZUL = "#3b82f6"     # Azul Claro/Celeste
C_VERDE = "#2ecc71"    # Verde Esmeralda/Neon
C_AMARELO = "#ffca28"  # Amarelo Vivo
C_VERMELHO = "#ef4444" # Vermelho Alerta

# ==========================================
# 2. DICIONÁRIO MESTRE FINANCEIRO E DE METAS
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
            'Itens Conf.':  {'tipo': '>', 'prop': True,  'v100': 350.0, 't50': 80000, 't100': 110000, 't120': 140000}
        },
        'OPERADOR': {
            'Mov. Horizontal': {'tipo': '>', 'prop': True,  'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400}
        },
        'RAMPEIRO': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000}
        },
        'MESA': {
            'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 220.0, 't50': 65, 't100': 75, 't120': 85}
        },
        'MANOBRISTA': {
            'Itens Manob.': {'tipo': '>', 'prop': True,  'v100': 350.0, 't50': 200000, 't100': 250000, 't120': 300000}
        },
        'LÍDER': {
            'Jornada Líq. Eq.': {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 65, 't100': 75, 't120': 85},
            'Itens/Hora Eq.':   {'tipo': '>', 'prop': False, 'v100': 240.0, 't50': 60, 't100': 75, 't120': 90}
        }
    },
    'T2': {
        'SEPARADOR G': {
            'Ressup. Ap.': {'tipo': '>', 'prop': True,  'v100': 200.0, 't50': 600, 't100': 800, 't120': 1000},
            'Itens/Hora':  {'tipo': '>', 'prop': False, 'v100': 200.0, 't50': 50, 't100': 65, 't120': 80}
        },
        'CONFERENTE': {
            'Itens Conf.': {'tipo': '>', 'prop': True,  'v100': 300.0, 't50': 90000, 't100': 120000, 't120': 150000}
        },
        'OPERADOR': {
            'Mov. Horizontal': {'tipo': '>', 'prop': True,  'v100': 450.0, 't50': 1200, 't100': 1800, 't120': 2400}
        },
        'RAMPEIRO': {
            'Itens Rampa': {'tipo': '>', 'prop': False, 'v100': 150.0, 't50': 30000, 't100': 45000, 't120': 60000}
        }
    },
    'T1': {
        'CONFERENTE': {
            'Palets Conf.': {'tipo': '>', 'prop': True, 'v100': 300.0, 't50': 1750, 't100': 2500, 't120': 3250}
        },
        'DESCARGA': {
            'Carga Palet.': {'tipo': '>', 'prop': True, 'v100': 125.0, 't50': 3000, 't100': 3700, 't120': 4400},
            'Carga Bat.':   {'tipo': '>', 'prop': True, 'v100': 125.0, 't50': 1000, 't100': 1500, 't120': 2000}
        }
    }
}

# ==========================================
# 3. CARREGAMENTO DOS DADOS
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
    
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()

    colunas_texto = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']
    colunas_numericas = [col for col in df.columns if col not in colunas_texto]

    for col in colunas_numericas:
        df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# ==========================================
# 4. CONSTRUÇÃO DA TELA
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

    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26) if hoje.day >= 26 else datetime.date(hoje.year if hoje.month > 1 else hoje.year - 1, hoje.month - 1 if hoje.month > 1 else 12, 26)
    
    col_titulo, col_kpis = st.columns([1, 1.2])

    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {hoje.strftime('%d/%m/%Y')}")

    with col_kpis:
        st.markdown("## 🎯 Visão Geral do Período")
        kpi1, kpi2, kpi3 = st.columns(3)

        total_itens = df_filtrado['Itens Sep'].sum() if 'Itens Sep' in df_filtrado.columns else 0
        media_vel = df_filtrado[df_filtrado['Itens/Hora'] > 0]['Itens/Hora'].mean() if 'Itens/Hora' in df_filtrado.columns else 0
        total_horas = df_filtrado.loc[df_filtrado['Horas'] > 0, 'Horas'].sum() if 'Horas' in df_filtrado.columns else 0

        kpi1.metric("📦 Total de Itens", f"{total_itens:,.0f}".replace(',', '.'))
        kpi2.metric("⚡ Média (Itens/H)", f"{media_vel:.0f}" if not pd.isna(media_vel) else "0")
        kpi3.metric("⏱️ Horas Totais", f"{total_horas:.1f} h")

    st.divider()

    # ==========================================
    # 5. BLOCO CONDICIONAL: VISÃO INDIVIDUAL OU GERAL
    # ==========================================
    if pessoa_selecionada != "Nenhum":
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
                
                for idx, (ind, regra) in enumerate(metas_cargo.items()):
                    if ind in dados_pessoa.columns:
                        realizado = float(dados_pessoa[ind].values[0])
                        t50, t100, t120 = regra['t50'], regra['t100'], regra['t120']
                        v100, tipo, prop = regra['v100'], regra['tipo'], regra['prop']
                        
                        pagamento_ind = 0.0
                        
                        if tipo == '>':
                            atingimento_real = (realizado / t100 * 100) if t100 > 0 else 0
                            if realizado >= t120:
                                cor_texto, borda, icone, status_texto = C_AZUL, C_AZUL, "🔵", f"Meta 120% (Superou: {atingimento_real:.0f}%)"
                                pagamento_ind = (realizado / t100 * v100) if prop else (v100 * 1.2)
                            elif realizado >= t100:
                                cor_texto, borda, icone, status_texto = C_VERDE, C_VERDE, "🟢", f"Meta 100% (Atingiu: {atingimento_real:.0f}%)"
                                pagamento_ind = (realizado / t100 * v100) if prop else v100
                            elif realizado >= t50:
                                cor_texto, borda, icone, status_texto = C_AMARELO, C_AMARELO, "🟡", f"Meta 50% (Parcial: {atingimento_real:.0f}%)"
                                pagamento_ind = (realizado / t100 * v100) if prop else (v100 * 0.5)
                            else:
                                cor_texto, borda, icone, status_texto = C_VERMELHO, C_VERMELHO, "🔴", "Abaixo da Meta"
                                pagamento_ind = 0.0
                                
                        elif tipo == '<':
                            atingimento_real = (t100 / realizado * 100) if realizado > 0 else 120.0
                            if realizado <= t120:
                                cor_texto, borda, icone, status_texto = C_AZUL, C_AZUL, "🔵", f"Meta 120% (Superou: {atingimento_real:.0f}%)"
                                pagamento_ind = v100 * 1.2
                            elif realizado <= t100:
                                cor_texto, borda, icone, status_texto = C_VERDE, C_VERDE, "🟢", f"Meta 100% (Atingiu: {atingimento_real:.0f}%)"
                                pagamento_ind = v100
                            elif realizado <= t50:
                                cor_texto, borda, icone, status_texto = C_AMARELO, C_AMARELO, "🟡", f"Meta 50% (Parcial: {atingimento_real:.0f}%)"
                                pagamento_ind = v100 * 0.5
                            else:
                                cor_texto, borda, icone, status_texto = C_VERMELHO, C_VERMELHO, "🔴", "Abaixo da Meta"
                                pagamento_ind = 0.0

                        grafico_dados.append({
                            'Indicador': f"<b>{ind}</b>", 
                            'Atingimento (%)': min(atingimento_real, 150),
                            'Real': atingimento_real
                        })

                        bonus_acumulado += pagamento_ind
                        
                        texto_grana = f"R$ {pagamento_ind:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        # Dinheiro acompanha a cor Verde Neon para destacar sempre
                        html_dinheiro = f'<span style="color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;">💰 {texto_grana}</span>' if pagamento_ind > 0 else ""
                        
                        valor_tela = f"{realizado:.2f}%" if ind in ['Avaria', 'Dev. %', 'Corte %'] else f"{realizado:.0f}"
                        if "Líq." in ind: valor_tela = f"{realizado:.0f}%"
                        
                        with cols_meta[idx]:
                            st.markdown(f"""
                            <div class="card-meta" style="border-left-color: {borda};">
                                <div class="texto-card-titulo">{ind} (Alvo 100%: {t100})</div>
                                <div class="texto-card-principal">{valor_tela}</div>
                                <div style="font-size: 18px; color: {cor_texto}; font-weight: bold; margin-top: 8px;">
                                    {icone} {status_texto} {html_dinheiro}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                if bonus_acumulado > 0:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.success(f"💰 **Premiação Variável Acumulada TOTAL Estimada:** R$ {bonus_acumulado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                st.divider()

                st.markdown(f"### 📊 Análise de {pessoa_selecionada}")
                
                col_grafico, col_tabela = st.columns([1.2, 1])
                
                with col_grafico:
                    if grafico_dados:
                        df_grafico = pd.DataFrame(grafico_dados)
                        # Aplica as cores vibrantes também no gráfico
                        df_grafico['Cor'] = df_grafico['Real'].apply(
                            lambda x: C_AZUL if x >= 120 else (C_VERDE if x >= 100 else (C_AMARELO if x >= 50 else C_VERMELHO))
                        )
                        
                        # --- PONTO CHAVE: LÓGICA DE COR DO TEXTO DAS BARRAS ---
                        # Se a cor da barra for amarela (C_AMARELO), usamos texto preto (black) para contraste.
                        # Caso contrário (Azul, Verde, Vermelho), usamos branco (white).
                        df_grafico['Texto_Cor'] = df_grafico['Cor'].apply(
                            lambda color: "black" if color == C_AMARELO else "white"
                        )
                        
                        fig = px.bar(
                            df_grafico, 
                            x='Indicador', 
                            y='Atingimento (%)',
                            # Adiciona tags <b> para negrito no texto das porcentagens
                            text=df_grafico['Real'].apply(lambda x: f"<b>{x:.1f}%</b>"),
                            color='Cor',
                            color_discrete_map="identity"
                        )
                        fig.update_layout(
                            showlegend=False, 
                            yaxis_title="<b>% da Meta Atingida</b>",
                            xaxis_title=None,
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=350,
                            margin=dict(t=15, b=0, l=0, r=0)
                        )
                        # Linha pontilhada e texto mais claros (lightgray) para aparecer no fundo preto
                        fig.add_hline(y=100, line_dash="dash", line_color="lightgray", annotation_text="<b>Meta 100%</b>", annotation_font_color="lightgray")
                        
                        # Aplica a cor de texto dinâmica (Texto_Cor) para cada barra individualmente
                        # Adiciona uma borda fina branca nas barras para dar mais definição no dark mode
                        fig.update_traces(
                            textfont_size=24, 
                            textfont_color=df_grafico['Texto_Cor'].tolist(), # Passa a lista de cores de texto
                            marker=dict(line=dict(color='white', width=1)) # Borda fina nas barras
                        ) 
                        fig.update_xaxes(tickfont=dict(size=20, color="lightgray", family="Arial Black"))
                        fig.update_yaxes(tickfont=dict(size=14, color="lightgray"), title_font=dict(color="lightgray"))
                        
                        st.plotly_chart(fig, use_container_width=True)

                with col_tabela:
                    colunas_uteis = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO'] + list(metas_cargo.keys())
                    colunas_existentes = [c for c in colunas_uteis if c in df_filtrado.columns]
                    df_tabela_mini = dados_pessoa[colunas_existentes]
                    
                    config_colunas = {}
                    for col in df_tabela_mini.columns:
                        if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']: continue 
                        elif col in ['Avaria', 'Corte %', 'Dev. %']: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                        elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                        elif col == "Horas": config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f")
                        else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")
                        
                    st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=350, column_config=config_colunas)

            else:
                st.warning(f"Metas não cadastradas para o cargo: {cargo_p} ({turno_p}).")

    else:
        st.markdown("### 📋 Tabela de Produtividade Consolidada")
        df_tabela = df_filtrado.sort_values(by='NOME', ascending=True)
        config_colunas = {}
        for col in df_tabela.columns:
            if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO']: continue 
            elif col in ['Avaria', 'Corte %', 'Dev. %']: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
            elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
            elif col == "Horas": config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f")
            else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")

        st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=650, column_config=config_colunas)

except Exception as e:
    st.error(f"⚠️ Ocorreu um erro ao processar os dados: {e}")
