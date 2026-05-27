import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .card-meta { background-color: var(--background-color); padding: 15px; border-radius: 10px; border-left: 8px solid #ccc; margin-bottom: 15px; }
    .texto-card-principal { font-size: 42px; color: var(--text-color); font-weight: 900; line-height: 1.1; }
    .texto-card-titulo { font-size: 22px; color: var(--text-color); font-weight: 900; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# ==========================================
# 2. CARREGAMENTO DOS DADOS (NOVA ESTRUTURA)
# ==========================================
@st.cache_data(ttl=60) 
def carregar_dados():
    # LINK DA ABA "RELATÓRIO_RH" GERADA PELO SEU ROBÔ (Mude se necessário)
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=SEU_GID_AQUI&single=true&output=csv"
    
    # IMPORTANTE: Você precisa trocar o link acima para apontar especificamente para a aba 'Relatorio_RH'
    # Vá na planilha > Arquivo > Compartilhar > Publicar na Web > Escolha a aba Relatório e pegue o link CSV.
    
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    
    # O Pandas renomeia colunas repetidas com ".1", ".2". Vamos mapear isso de forma inteligente:
    colunas_renomeadas = {}
    
    # MAPEAMENTO INTELIGENTE DAS COLUNAS EXPANDIDAS
    # Baseado na estrutura do seu print "image_659428.png"
    prefixos = [
        ('', '', '', '', '', '', '', '', ''), # Indicador 1
        ('.1', '.1', '.1', '.1', '.1', '.1', '.1', '.1', '.1'), # Indicador 2
        ('.2', '.2', '.2', '.2', '.2', '.2', '.2', '.2', '.2'), # Indicador 3
        ('.3', '.3', '.3', '.3', '.3', '.3', '.3', '.3', '.3')  # Indicador 4
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
        df = df[df['NOME'] != '-'] # Remove linhas vazias do Excel
        
    if 'FUNÇÃO' in df.columns:
        df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns:
        df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
        
    # Limpa valores nulos e converte moedas
    for col in df.columns:
        if 'Valor' in col or 'Alvo' in col or 'Perc' in col or 'Realizado' in col or col == 'Valor Final':
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.replace('-', '0', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df

# ==========================================
# 3. LÓGICA DE DADOS PREVIA E FILTROS
# ==========================================
try:
    df = carregar_dados()
    
    st.sidebar.title("🔍 Filtros do Painel")
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()

    lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
    cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
    if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

    lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
    pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
    
    st.title("📊 Monitor de Produtividade")
    st.info("💡 **Atenção:** Os dados exibidos abaixo são processados e validados pela equipe de Logística no Excel.")

    # ==========================================
    # 4. VISÃO INDIVIDUAL DO COLABORADOR
    # ==========================================
    if pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]
        
        if not dados_pessoa.empty:
            row = dados_pessoa.iloc[0]
            
            # --- 1. RENDERIZA OS CARTÕES DE INDICADORES ---
            cols_meta = st.columns(4) # Prepara 4 colunas para os 4 indicadores possíveis
            col_idx = 0
            
            # Loop pelos 4 possíveis indicadores
            for n in range(1, 5):
                nome_ind = row.get(f'Ind_{n}_Nome', '-')
                
                # Se o indicador for válido (não for '-' ou NaN) e tiver um valor realizado
                if pd.notna(nome_ind) and str(nome_ind).strip() != '-' and str(nome_ind).strip() != '0':
                    
                    realizado = row.get(f'Ind_{n}_Realizado', 0)
                    alvo_100 = row.get(f'Ind_{n}_Alvo_100', 0)
                    perc_atingimento = row.get(f'Ind_{n}_Perc', 0)
                    valor_reais = row.get(f'Ind_{n}_Valor', 0)
                    
                    # Define Cores e Status baseado na porcentagem mastigada pelo Excel
                    if perc_atingimento >= 1.2 or perc_atingimento >= 120:
                        cor, icone, status = C_AZUL, "🔵", "Superou"
                    elif perc_atingimento >= 1.0 or perc_atingimento >= 100:
                        cor, icone, status = C_VERDE, "🟢", "Atingiu"
                    elif perc_atingimento >= 0.5 or perc_atingimento >= 50:
                        cor, icone, status = C_AMARELO, "🟡", "Parcial"
                    else:
                        cor, icone, status = C_VERMELHO, "🔴", "Abaixo"
                        
                    # Formatação Visual
                    html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""
                    
                    if "Tempo" in str(nome_ind) or ":" in str(realizado):
                         # Simplificação para exibição, pode ajustar se o excel mandar decimal
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
            
            # --- 2. RENDERIZA O TOTAL ACUMULADO ---
            valor_final = row.get('Valor Final', 0)
            if valor_final > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {valor_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    else:
        st.write("👈 Selecione um colaborador no menu lateral para visualizar os indicadores processados.")

except Exception as e:
    st.error(f"⚠️ Erro ao processar os dados: {e}")
