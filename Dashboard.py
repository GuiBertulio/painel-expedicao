import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import gspread

# ==========================================
# CONEXÃO COM GOOGLE SHEETS PARA REGISTRO DE RH
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
# 2. CARREGAMENTO DOS DADOS (NOVA ABA RELATÓRIO)
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    # LINK DA ABA "RELATÓRIO_RH" - SUBSTITUA SE FOR DIFERENTE
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=1520498693&single=true&output=csv"
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # Mapeamento Inteligente das colunas expandidas do Relatório (Tira as repetições do Pandas como .1, .2)
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
        
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
        
    # Limpa valores nulos e converte moedas para números usáveis no Python
    for col in df.columns:
        if 'Valor' in col or 'Alvo' in col or 'Perc' in col or 'Realizado' in col or col == 'Valor Final':
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.replace('-', '0', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

# ==========================================
# 3. CONSTRUÇÃO DA TELA (TUDO INTEGRADO)
# ==========================================
try:
    df = carregar_dados()
    
    # Filtros Laterais
    st.sidebar.title("🔍 Filtros do Painel")
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()

    lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
    cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
    if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

    lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
    pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
    
    # Cabeçalho Principal
    st.title("📊 Monitor de Produtividade")
    st.info("💡 **Atenção:** Os dados exibidos abaixo são processados e validados na origem pela equipe de Logística.")
    st.divider()

    # ==========================================
    # VISÃO INDIVIDUAL DO COLABORADOR
    # ==========================================
    if pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        
        if not dados_pessoa.empty:
            row = dados_pessoa.iloc[0]
            
            # --- 1. RENDERIZA OS CARTÕES DE INDICADORES ---
            cols_meta = st.columns(4) 
            col_idx = 0
            grafico_dados = []
            
            # Loop pelos 4 possíveis indicadores dinâmicos vindos da planilha
            for n in range(1, 5):
                nome_ind = row.get(f'Ind_{n}_Nome', '-')
                
                # Se o indicador for válido (não for '-' ou NaN)
                if pd.notna(nome_ind) and str(nome_ind).strip() != '-' and str(nome_ind).strip() != '0':
                    
                    realizado = row.get(f'Ind_{n}_Realizado', 0)
                    alvo_100 = row.get(f'Ind_{n}_Alvo_100', 0)
                    perc_atingimento = row.get(f'Ind_{n}_Perc', 0)
                    valor_reais = row.get(f'Ind_{n}_Valor', 0)
                    
                    # Salva dados pro gráfico
                    grafico_dados.append({'Indicador': f"<b>{nome_ind}</b>", 'Atingimento (%)': min(perc_atingimento * 100 if perc_atingimento < 10 else perc_atingimento, 120), 'Real': perc_atingimento * 100 if perc_atingimento < 10 else perc_atingimento})
                    
                    # Define Cores e Status baseado na porcentagem validada pelo Excel
                    if perc_atingimento >= 1.2 or perc_atingimento >= 120:
                        cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif perc_atingimento >= 1.0 or perc_atingimento >= 100:
                        cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif perc_atingimento >= 0.5 or perc_atingimento >= 50:
                        cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else:
                        cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                        
                    html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""
                    
                    # Tratamento visual
                    if "Tempo" in str(nome_ind) or ":" in str(realizado):
                         val_tela = str(realizado) 
                         alvo_tela = str(alvo_100)
                    elif "%" in str(nome_ind) or "Avaria" in str(nome_ind):
                        val_tela = f"{realizado * 100:.2f}%" if realizado < 1 else f"{realizado:.2f}%"
                        alvo_tela = f"{alvo_100 * 100:.2f}%" if alvo_100 < 1 else f"{alvo_100:.2f}%"
                    else:
                        val_tela = f"{realizado:,.0f}".replace(',', '.')
                        alvo_tela = f"{alvo_100:,.0f}".replace(',', '.')

                    with cols_meta[col_idx]:
                        st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{nome_ind} (Alvo: {alvo_tela})</div><div class='texto-card-principal'>{val_tela}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status} {html_dinheiro}</div></div>", unsafe_allow_html=True)
                    
                    col_idx += 1
            
            # --- 2. RENDERIZA O TOTAL ACUMULADO DIRETO DO EXCEL ---
            valor_final = row.get('Valor Final', 0)
            if valor_final > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {valor_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

            # --- 3. GRÁFICOS E TABELA INDIVIDUAL ---
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
    # VISÃO GERAL EQUIPE (MÚLTIPLOS COLABORADORES)
    # ==========================================
    else:
        st.markdown("### 📋 Tabela de Produtividade (Relatório Gerencial)")
        
        # Filtra as colunas limpas para montar uma visão gerencial bonitona
        colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final']
        
        # Puxa dinamicamente os Indicadores Reais preenchidos
        for n in range(1, 5):
            nome_col = f'Ind_{n}_Realizado'
            if nome_col in df_filtrado.columns:
                colunas_exibicao.append(nome_col)

        df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()
        
        # Aplica uma formatação de grana na coluna de Valor Final
        config = {'Valor Final': st.column_config.NumberColumn("Valor R$", format="R$ %.2f")}
        
        st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    st.error(f"⚠️ Erro ao renderizar painel: {e}")
