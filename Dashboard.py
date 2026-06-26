# =============================================================================
# 📦 IMPORTAÇÃO DE BIBLIOTECAS (O que o Python precisa para funcionar)
# =============================================================================
import streamlit as st          # O motor principal do site (cria botões, telas, textos)
import pandas as pd             # O "Excel" do Python (manipula as tabelas de dados)
import datetime                 # Lida com o calendário (data de hoje, apuração, etc)
import plotly.express as px     # Desenha os gráficos interativos
import gspread                  # Conecta com a nuvem do Google Sheets
import io                       # Cria arquivos direto na memória RAM (usado para gerar o Excel de Auditoria)

# =============================================================================
# 🔐 CONFIGURAÇÃO DE USUÁRIOS E SENHAS (Seu Banco de Dados Interno)
# =============================================================================
# Para adicionar alguém, basta copiar uma linha e mudar os dados. 
# O "turno_acesso" pode ser um texto único (ex: "T3") ou uma lista (ex: ["T1", "T2"])
USUARIOS = {
    "diegoc": {"senha": "ger#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "nilo": {"senha": "esp#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "flamarion": {"senha": "sub#26", "perfil": "Líder", "turno_acesso": ["T1", "T2"]}, # Acesso a múltiplos turnos
    "guilherme": {"senha": "estag#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "adriano": {"senha": "Adriano@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "luciano": {"senha": "Luciano@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "wagner": {"senha": "Wagner@26TAF", "perfil": "Líder", "turno_acesso": "T1"},
    "jorge": {"senha": "Jorge@26TAF", "perfil": "Líder", "turno_acesso": "T2"},
    "diego": {"senha": "Diego@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "carlos": {"senha": "Carlos@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "luis": {"senha": "Luis@26TAF", "perfil": "Líder", "turno_acesso": "T3"},
    "luiz": {"senha": "Luiz@26TAF", "perfil": "Líder", "turno_acesso": "T3"} # <-- Lembre-se: O último da lista NUNCA tem vírgula no final
}

# =============================================================================
# 🎨 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (O CSS do site)
# =============================================================================
# Aqui você muda o título que fica na aba do navegador e o ícone
st.set_page_config(page_title="Dashboard Expedição", page_icon="📊", layout="wide")

# O bloco abaixo é o "CSS". É aqui que você altera tamanhos de letras, cores de fundo e bordas.
st.markdown("""
    <style>
    /* Diminui o espaço em branco no topo do site */
    .block-container { padding-top: 2rem !important; }
    
    /* Configuração dos Cartões (Cards) das Métricas (ex: Tempo Médio, Avaria) */
    .card-meta { 
        background-color: var(--background-color); /* Puxa a cor de fundo automática do Streamlit */
        padding: 15px;                             /* Espaço interno do cartão (se quiser mais gordinho, aumente para 25px) */
        border-radius: 10px;                       /* Arredondamento das pontas do cartão */
        border-left: 8px solid #ccc;               /* Espessura da barra colorida lateral do cartão */
        margin-bottom: 15px;                       /* Espaço entre um cartão e outro (para baixo) */
    }
    
    /* Configuração do Cartão Vermelho dos Detratores */
    .card-detrator { 
        background-color: rgba(239, 68, 68, 0.1);  /* Fundo vermelho bem transparente */
        border: 1px solid #ef4444;                 /* Borda vermelha fina */
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
    }
    
    /* Tamanho do NÚMERO GIGANTE dentro dos cartões de métrica */
    .texto-card-principal { 
        font-size: 42px;                           /* <-- MUDE AQUI PARA AUMENTAR/DIMINUIR OS NÚMEROS DO SITE */
        color: var(--text-color); 
        font-weight: 900;                          /* Grossura da letra (900 é bem grosso/negrito) */
        line-height: 1.1; 
    }
    
    /* Tamanho do TÍTULO do cartão (ex: a palavra "Avaria" ou "Tempo Médio") */
    .texto-card-titulo { 
        font-size: 22px;                           /* <-- MUDE AQUI PARA AUMENTAR/DIMINUIR O NOME DOS INDICADORES */
        color: var(--text-color); 
        font-weight: 900; 
        margin-bottom: 5px; 
    }
    </style>
""", unsafe_allow_html=True)

# Cores oficiais do painel (Padrão HEX). Se quiser mudar o tom de verde, altere o código entre aspas.
C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# =============================================================================
# 🚪 TELA DE LOGIN (BARREIRA DE SEGURANÇA)
# =============================================================================
# Cria a memória de login. Se o cara não logou, prende ele nessa tela.
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    # Divide a tela em 3 colunas e bota o login na coluna do meio (para ficar centralizado)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # Pula 3 linhas
        st.title("🔐 Login - Dashboard Logístico")
        
        usuario = st.text_input("Usuário").strip().lower() # Pega o texto e converte pra minúsculo
        senha = st.text_input("Senha", type="password").strip() # Esconde a senha com bolinhas
        btn_entrar = st.button("Entrar", type="primary", use_container_width=True)
        
        # Verifica se bate com o dicionário lá de cima
        if btn_entrar:
            if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["perfil"] = USUARIOS[usuario]["perfil"]
                st.session_state["turno_acesso"] = USUARIOS[usuario]["turno_acesso"]
                st.rerun() # Atualiza a tela logado
            else:
                st.error("❌ Usuário ou senha incorretos.")
    st.stop() # Para o robô aqui. Nada abaixo dessa linha roda se não logar.

# =============================================================================
# 🔗 CONEXÃO COM GOOGLE SHEETS (Para salvar feedbacks)
# =============================================================================
def conectar_planilha():
    cred_dict = dict(st.secrets["gcp_service_account"]) # Puxa a chave oculta do GitHub/Streamlit
    client = gspread.service_account_from_dict(cred_dict)
    planilha = client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")
    return planilha

# =============================================================================
# 🧠 2. CARREGAMENTO E TRATAMENTO DOS DADOS (O "Cérebro" do Sistema)
# =============================================================================
@st.cache_data(ttl=60) # Guarda os dados na memória por 60 segundos para o site ficar ultra rápido
def carregar_dados():
    # Link da sua planilha de Produtividade que sobe na nuvem
    link_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSDct-pz8fIwAXk-GX5Zcd-dknBBq4Dy4B0pbz6W8vDIvwjdWE2_e7ZQfefMRQcKG4-tvqdQR1Z4zMp/pub?gid=0&single=true&output=csv"
    df = pd.read_csv(link_csv)
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Limpa colunas vazias
    
    # --- TRATAMENTO DOS INDICADORES (Mágica do "_Racional") ---
    # O Python caça a palavra RACIONAL na planilha e renomeia as colunas vizinhas para Metas e Valores
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

    # --- PADRONIZAÇÃO DE NOMES DE COLUNAS ---
    for c in list(df.columns):
        nome_limpo = c.strip().upper()
        if "TRAB" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Trabalhados'})
        elif "META" in nome_limpo and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Meta'})
        elif ("UT" in nome_limpo or "ÚT" in nome_limpo) and "DIAS" in nome_limpo: df = df.rename(columns={c: 'Dias Uteis'})
        elif "DATA" in nome_limpo and ("INICIO" in nome_limpo or "INÍCIO" in nome_limpo or "INICIAL" in nome_limpo): df = df.rename(columns={c: 'Data Inicio'})
        elif "DATA" in nome_limpo and ("FIM" in nome_limpo or "FINAL" in nome_limpo or "APURA" in nome_limpo): df = df.rename(columns={c: 'Data Fim'})

    df = df.loc[:, ~df.columns.duplicated()].copy()

    # --- LIMPEZA DE DADOS (Joga fora o que não tem nome ou função) ---
    if 'NOME' in df.columns: df = df.dropna(subset=['NOME'])
    if 'FUNÇÃO' in df.columns: df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns: df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
    
    # --- CONVERSÃO DE TEXTOS PARA NÚMEROS MATEMÁTICOS E TEMPO ---
    colunas_texto = ["CÓD.", "NOME", "TURNO", "FUNÇÃO", "Data Inicio", "Data Fim"]
    for col in df.columns:
        if col not in colunas_texto:
            # BLINDAGEM: Converte o Tempo Médio E as suas respectivas Metas para segundos
            if col in ["Tempo Médio", "Tempo Médio_Meta1", "Tempo Médio_Meta2", "Tempo Médio_Meta3"]:
                texto_limpo = df[col].astype(str).str.split(".").str[0].str.strip()
                df[col] = (
                    pd.to_timedelta(texto_limpo, errors="coerce")
                    .dt.total_seconds()
                    .fillna(0)
                )
            else:
                # Remove o R$ e o % para o Excel conseguir fazer contas de soma e divisão
                s = (
                    df[col]
                    .astype(str)
                    .str.replace("R$", "", regex=False)
                    .str.replace("%", "", regex=False)
                    .str.strip()
                )
                mask_virgula = s.str.contains(",", regex=False)
                s_br = s.str.replace(".", "", regex=False).str.replace(
                    ",", ".", regex=False
                )
                df[col] = pd.to_numeric(
                    s_br.where(mask_virgula, s), errors="coerce"
                ).fillna(0)
                
    # =============================================================================
    # 🏆 CÁLCULO DE RANKING (O Campeonato das Equipes)
    # =============================================================================
    df['Valor Ranking'] = 0.0
    df['Posicao Ranking'] = 0
    
    for turno in ['T2', 'T3']:
        for cargo in df['FUNÇÃO'].unique():
            cargo_str = str(cargo).upper()
            df_eq = df[(df['TURNO'] == turno) & (df['FUNÇÃO'] == cargo)].copy()
            if df_eq.empty: continue
            
            kpis = [c.replace('_Racional', '') for c in df_eq.columns if '_Racional' in c]
            if not kpis: continue
            
            # -------------------------------------------------------------
            # REGRA 1: SEPARADORES (T2 e T3 competem por ITENS)
            # -------------------------------------------------------------
            if 'SEPARADOR' in cargo_str:
                # 🛡️ BLINDAGEM: Lê o indicador criado no Excel, mas ignora o "Itens Rampa" para focar na separação real
                metrica_rank = next((k for k in kpis if k.upper().strip() == 'ITENS'), 
                                    next((k for k in kpis if 'ITENS' in k.upper() and 'RAMPA' not in k.upper()), kpis[0]))
                
                racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
                
                df_eq[metrica_rank] = pd.to_numeric(df_eq[metrica_rank], errors='coerce').fillna(0)
                ordem_cresc = False if racional == 1 else True
                df_eq = df_eq.sort_values(by=metrica_rank, ascending=ordem_cresc)
                
                pos = 1
                for idx, row_eq in df_eq.iterrows():
                    if float(row_eq.get(metrica_rank, 0)) <= 0: continue # Pula quem tem 0 itens
                    df.at[idx, 'Posicao Ranking'] = pos
                    
                    # Distribui o dinheiro (AQUI VOCÊ MUDA OS VALORES DOS PRÊMIOS DO PÓDIO SE O RH PEDIR)
                    if turno == 'T3':
                        if pos == 1: val_base = 250.0 
                        elif pos == 2: val_base = 200.0
                        elif pos == 3: val_base = 100.0
                        else: val_base = 0.0
                    elif turno == 'T2':
                        if pos == 1: val_base = 150.0 
                        elif pos == 2: val_base = 100.0 
                        elif pos == 3: val_base = 80.0 
                        else: val_base = 0.0
                    else:
                        val_base = 0.0
                    
                    # Proporção de faltas (Desconta o prêmio se o cara faltou no mês)
                    if val_base > 0:
                        d_uteis = float(row_eq.get('Dias Uteis', 26))
                        d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                        fator = d_trab / d_uteis if d_uteis > 0 else 1
                        df.at[idx, 'Valor Ranking'] += val_base * fator
                    pos += 1

            # -------------------------------------------------------------
            # REGRA 2: CONFERENTES (Apenas T3) - 2 Campeonatos Separados
            # -------------------------------------------------------------
            elif 'CONFERENTE' in cargo_str and turno == 'T3':
                # Procura as colunas de Fracionado e Grandeza dinamicamente
                metrica_frac = next((k for k in kpis if 'FRAC' in k.upper() or 'ITENS CONF' in k.upper()), None)
                metrica_grand = next((k for k in kpis if 'GRAND' in k.upper() or 'PALETS CONF' in k.upper()), None)
                
                # 🏆 CAMPEONATO 1: FRACIONADO (Apenas o 1º Lugar = R$ 200)
                if metrica_frac:
                    racional = df_eq[f"{metrica_frac}_Racional"].mode()[0] if not df_eq[f"{metrica_frac}_Racional"].empty else 1
                    df_eq[metrica_frac] = pd.to_numeric(df_eq[metrica_frac], errors='coerce').fillna(0)
                    df_frac = df_eq.sort_values(by=metrica_frac, ascending=(racional != 1))
                    
                    pos = 1
                    for idx, row_eq in df_frac.iterrows():
                        if float(row_eq.get(metrica_frac, 0)) <= 0: continue
                        
                        # Salva a melhor posição no perfil dele para mostrar a medalha na tela
                        if df.at[idx, 'Posicao Ranking'] == 0 or pos < df.at[idx, 'Posicao Ranking']:
                            df.at[idx, 'Posicao Ranking'] = pos
                            
                        # Se for o 1º lugar do Fracionado, PAGA!
                        if pos == 1:
                            d_uteis = float(row_eq.get('Dias Uteis', 26))
                            d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                            fator = d_trab / d_uteis if d_uteis > 0 else 1
                            df.at[idx, 'Valor Ranking'] += 200.0 * fator
                        pos += 1

                # 🏆 CAMPEONATO 2: GRANDEZA (Apenas o 1º Lugar = R$ 200)
                if metrica_grand:
                    racional = df_eq[f"{metrica_grand}_Racional"].mode()[0] if not df_eq[f"{metrica_grand}_Racional"].empty else 1
                    df_eq[metrica_grand] = pd.to_numeric(df_eq[metrica_grand], errors='coerce').fillna(0)
                    df_grand = df_eq.sort_values(by=metrica_grand, ascending=(racional != 1))
                    
                    pos = 1
                    for idx, row_eq in df_grand.iterrows():
                        if float(row_eq.get(metrica_grand, 0)) <= 0: continue
                        
                        # Atualiza a posição da medalha, caso ele tenha ido melhor na Grandeza
                        if df.at[idx, 'Posicao Ranking'] == 0 or pos < df.at[idx, 'Posicao Ranking']:
                            df.at[idx, 'Posicao Ranking'] = pos
                            
                        # Se for o 1º lugar da Grandeza, PAGA!
                        if pos == 1: 
                            d_uteis = float(row_eq.get('Dias Uteis', 26))
                            d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                            fator = d_trab / d_uteis if d_uteis > 0 else 1
                            df.at[idx, 'Valor Ranking'] += 200.0 * fator
                        pos += 1

            # -------------------------------------------------------------
            # REGRA 3: OPERADORES (Apenas T3) - 1º Lugar Ganha R$ 200
            # -------------------------------------------------------------
            elif 'OPERADOR' in cargo_str and turno == 'T3':
                # Acha a métrica de Movimentação do operador
                metrica_rank = next((k for k in kpis if 'MOV' in k.upper()), kpis[0])
                
                racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
                df_eq[metrica_rank] = pd.to_numeric(df_eq[metrica_rank], errors='coerce').fillna(0)
                df_eq = df_eq.sort_values(by=metrica_rank, ascending=(racional != 1))
                
                pos = 1
                for idx, row_eq in df_eq.iterrows():
                    if float(row_eq.get(metrica_rank, 0)) <= 0: continue
                    df.at[idx, 'Posicao Ranking'] = pos
                    
                    if pos == 1: # PAGA SÓ PARA O PRIMEIRO
                        val_base = 200.0
                        d_uteis = float(row_eq.get('Dias Uteis', 26))
                        d_trab = float(row_eq.get('Dias Trabalhados', d_uteis))
                        fator = d_trab / d_uteis if d_uteis > 0 else 1
                        df.at[idx, 'Valor Ranking'] += val_base * fator
                    pos += 1

    # Soma todo o dinheiro final do colaborador (Métricas + Prêmio do Ranking)
    colunas_valor = [c for c in df.columns if c.endswith('_Valor')]
    df['Valor Final'] = df[colunas_valor].sum(axis=1) + df['Valor Ranking']

    return df

# =============================================================================
# 🗂️ 2.1 CARREGAMENTO DOS RELATÓRIOS DIÁRIOS (Separador, Operador, Conferente)
# =============================================================================
@st.cache_data(ttl=60)
def carregar_diarios():
    # Cria gavetas (dicionário) para guardar as 3 bases de dados diferentes com segurança
    dfs = {'sep': pd.DataFrame(), 'op': pd.DataFrame(), 'conf': pd.DataFrame()}
    try:
        planilha = conectar_planilha()
        
        # Puxa o Diário dos Separadores
        try:
            aba_sep = planilha.worksheet("Relatorio Diario").get_all_values()
            if aba_sep: dfs['sep'] = pd.DataFrame(aba_sep[1:], columns=aba_sep[0]).rename(columns=lambda x: str(x).strip())
        except: pass
        
        # Puxa o Diário dos Operadores
        try:
            aba_op = planilha.worksheet("Relatorio Operador").get_all_values()
            if aba_op: dfs['op'] = pd.DataFrame(aba_op[1:], columns=aba_op[0]).rename(columns=lambda x: str(x).strip())
        except: pass
        
        # Puxa o Diário dos Conferentes
        try:
            aba_conf = planilha.worksheet("Relatorio Diario Conferente").get_all_values()
            if aba_conf: dfs['conf'] = pd.DataFrame(aba_conf[1:], columns=aba_conf[0]).rename(columns=lambda x: str(x).strip())
        except: pass
        
    except Exception as e:
        pass
    
    return dfs['sep'], dfs['op'], dfs['conf']

# Dispara as funções para encher a memória do site com TODAS as planilhas
df = carregar_dados()
df_diario, df_operador, df_conferente = carregar_diarios()

# =============================================================================
# 📅 3. LÓGICA DE DATAS E BARRA LATERAL (Filtros de Menu)
# =============================================================================
# Define se o site diz que estamos do dia 26 ao dia 25
if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
    dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0]).date()
    data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0]).date()
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)

# --- CABEÇALHO DA BARRA LATERAL ---
# Escreve na tela esquerda quem está logado (ex: "Logado como: Guilherme (Gerente)")
st.sidebar.markdown(f"👤 **Logado como:** {st.session_state['usuario'].capitalize()} ({st.session_state['perfil']})")
if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state["logado"] = False
    st.rerun()

# =============================================================================
# 📥 BOTÃO DE AUDITORIA (EXCLUSIVO PARA GESTÃO E DIAS DE FECHAMENTO)
# =============================================================================
# Verifica se é a alta gestão acessando
if st.session_state.get("usuario") in ["guilherme", "nilo"]:
    # Trava: O botão só funciona do dia 26 ao 25.
    is_fechado = (dt_inicio.day == 26 and data_apuracao.day == 25)
    
    if is_fechado:
        # --- LÓGICA DO UNPIVOT (Desdobramento da tabela Larga para Longa) ---
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
            
            # --- 1. GERA AS LINHAS DOS INDICADORES NORMAIS ---
            for kpi in kpis_gerais:
                meta2 = float(row.get(f"{kpi}_Meta2", 0))
                
                # Se a meta2 for maior que zero, o colaborador faz essa função. Cria a linha no Excel.
                if meta2 > 0:
                    real = float(row.get(kpi, 0))
                    valor = float(row.get(f"{kpi}_Valor", 0))
                    
                    meta1 = float(row.get(f"{kpi}_Meta1", 0))
                    meta3 = float(row.get(f"{kpi}_Meta3", 0))
                    racional = float(row.get(f"{kpi}_Racional", 1))
                    
                    if meta1 <= 0: meta1 = meta2
                    if meta3 <= 0: meta3 = meta2
                    
                    # Calcula qual foi a Meta Atingida (0, 50, 100 ou 120%) para a última coluna do Excel
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
                    
                    # Coloca as máscaras visuais nos números antes de jogar pro Excel (%, horas, milhares)
                    def formata(v):
                        if "Tempo" in str(kpi): return f"{int(v)//3600:02d}:{(int(v)%3600)//60:02d}:{(int(v)%60):02d}"
                        elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi): return f"{v:.2f}%".replace('.', ',')
                        else: return f"{v:,.0f}".replace(',', '.')
                    
                    real_str = formata(real)
                    
                    # Adiciona essa métrica no banco de dados temporário da Auditoria
                    df_auditoria.append({
                        "CÓD.": cod,
                        "NOME": nome,
                        "TURNO": turno,
                        "FUNÇÃO": funcao,
                        "DIAS ÚTEIS": int(d_uteis),
                        "DIAS META": int(d_meta),
                        "DIAS TRAB.": int(d_trab),
                        "INDICADOR": kpi,
                        "REALIZADO": real_str,
                        "VALOR GANHO (R$)": valor,
                        "META ATINGIDA": faixa_meta
                    })
            
            # --- 2. GERA A LINHA EXCLUSIVA DO RANKING NA AUDITORIA ---
            pos = int(row.get('Posicao Ranking', 0))
            funcao_upper = str(funcao).upper()
            
            # Trava: O ranking aparece para Separador (todos) e Conferente/Operador (só T3)
            if pos > 0 and ('SEPARADOR' in funcao_upper or ('CONFERENTE' in funcao_upper and turno == 'T3') or ('OPERADOR' in funcao_upper and turno == 'T3')):
                val_rank = float(row.get('Valor Ranking', 0))
                
                # Se não ganhou nada (ex: ficou em 4º), não precisa lançar zero na planilha do RH
                if val_rank > 0: 
                    df_auditoria.append({
                        "CÓD.": cod,
                        "NOME": nome,
                        "TURNO": turno,
                        "FUNÇÃO": funcao,
                        "DIAS ÚTEIS": int(d_uteis),
                        "DIAS META": int(d_meta),
                        "DIAS TRAB.": int(d_trab),
                        "INDICADOR": "Ranking",
                        "REALIZADO": f"{pos}º Lugar",
                        "VALOR GANHO (R$)": val_rank,
                        "META ATINGIDA": "-"
                    })
        
        # Converte a lista em uma Tabela do Pandas
        df_export = pd.DataFrame(df_auditoria)
        
        # --- CRIADOR NATIVO DO ARQUIVO EXCEL FORMATADO ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # startrow=1 joga os dados para a linha 2, liberando a linha 1 para o cabeçalho Azul do Excel
            df_export.to_excel(writer, index=False, sheet_name='Auditoria_Fechamento', header=False, startrow=1)
            
            workbook  = writer.book
            worksheet = writer.sheets['Auditoria_Fechamento']
            
            # Cria os estilos customizados para o Excel (Moeda R$ e Centralizado)
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
            formato_central = workbook.add_format({'align': 'center'})
            
            (max_row, max_col) = df_export.shape
            
            # Desenha a tabela com a propriedade de Autofiltro e zebrado (Table Style Medium 2)
            col_settings = [{'header': column} for column in df_export.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': col_settings,
                'style': 'Table Style Medium 2'
            })
            
            # Regula a largura das colunas do Excel baixado para nada ficar espremido e aplica os formatos
            worksheet.set_column('A:A', 10, formato_central) # CÓD.
            worksheet.set_column('B:B', 38)                  # NOME
            worksheet.set_column('C:C', 12, formato_central) # TURNO
            worksheet.set_column('D:D', 22)                  # FUNÇÃO
            worksheet.set_column('E:G', 13, formato_central) # DIAS
            worksheet.set_column('H:H', 25)                  # INDICADOR
            worksheet.set_column('I:I', 15, formato_central) # REALIZADO
            worksheet.set_column('J:J', 20, formato_moeda)   # VALOR GANHO
            worksheet.set_column('K:K', 18, formato_central) # META ATINGIDA
        
        # O botão físico azul na tela que cospe o arquivo formatado acima
        st.sidebar.download_button(
            label="📥 Baixar Auditoria",
            data=buffer.getvalue(),
            file_name=f"Auditoria_Produtividade_Fechamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    else:
        # Se não estiver no dia do fechamento, o botão vira um cadeado cinza bloqueado
        st.sidebar.button("🔒 Fechamento (Auditoria)", disabled=True, use_container_width=True, help="A Auditoria é liberada apenas quando o período for exato: do dia 26 ao dia 25.")

# =============================================================================
# 🎛️ FILTROS DE SELEÇÃO (Como o Líder navega pelo painel)
# =============================================================================
st.sidebar.markdown("---")
st.sidebar.title("🔍 Filtros do Painel")

turno_logado = st.session_state["turno_acesso"]

# Se tem acesso total (Gerente)
if turno_logado == "Todos":
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()

# Se tem acesso a uma LISTA de turnos (Líder Flamarion T1 e T2)
elif isinstance(turno_logado, list):
    st.sidebar.info(f"🔒 Acesso restrito aos Turnos: **{', '.join(turno_logado)}**")
    lista_turnos = ["Todos Permitidos"] + turno_logado
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    
    if turno_selecionado == "Todos Permitidos":
        df_filtrado = df[df['TURNO'].isin(turno_logado)].copy()
    else:
        df_filtrado = df[df['TURNO'] == turno_selecionado].copy()

# Se tem acesso a apenas UM turno (Líder normal)
else:
    turno_selecionado = turno_logado
    st.sidebar.info(f"🔒 Acesso restrito ao Turno: **{turno_selecionado}**")
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy()

# Filtro de Cargos (Ex: Só mostrar Empilhador)
lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

# Filtro de Pessoas (Abre a ficha individual)
lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
focar_detratores = st.sidebar.checkbox("🚨 Filtrar Desempenho Abaixo da Meta")

# =============================================================================
# 🗃️ MÓDULO DE EXTRAÇÃO DO RH (Dinheiro final de folha)
# =============================================================================
# Só quem é 'Gerente' vê esse módulo na barra lateral inferior. O arquivo sai em .CSV limpo.
if st.session_state["perfil"] == "Gerente":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗃️ Fechamento RH")

    if not df_filtrado.empty:
        df_rh = df_filtrado[['CÓD.', 'NOME', 'FUNÇÃO', 'TURNO', 'Valor Final']].copy()
        df_rh = df_rh.rename(columns={'CÓD.': 'Matrícula', 'NOME': 'Nome', 'Valor Final': 'Premiação (R$)'})
        
        df_rh['Premiação (R$)'] = df_rh['Premiação (R$)'].round(2)
        df_rh = df_rh.drop_duplicates(subset=['Matrícula', 'Nome'])
        df_rh = df_rh.sort_values(by='Nome')
        
        # Desenha a mini-tabela do RH na própria barra lateral para conferência rápida
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

# =============================================================================
# 🖥️ 4. RENDERIZAÇÃO DA TELA CENTRAL (O que aparece na tela grande)
# =============================================================================
try:
    kpis_mapeados = [c.replace('_Racional', '') for c in df_filtrado.columns if '_Racional' in c]

    # Divide a tela principal em duas colunas (Título na esquerda, KPIs globais na direita)
    col_titulo, col_kpis = st.columns([1, 1.2])
    
    with col_titulo:
        st.title("📊 Monitor de Produtividade")
        st.info(f"📅 **Período Apurado:** de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')}")

    # Os 3 grandes números do topo do site: Volume, Colaboradores e Horas.
    with col_kpis:
        st.markdown("## 🎯 Visão Geral")
        kpi1, kpi2, kpi3 = st.columns(3)
        col_vol = next((k for k in kpis_mapeados if 'itens' in k.lower() or 'palet' in k.lower() or 'mov' in k.lower()), kpis_mapeados[0] if kpis_mapeados else None)
        total_vol = df_filtrado[col_vol].sum() if col_vol and col_vol in df_filtrado.columns else 0
        
        kpi1.metric(f"📦 {col_vol or 'Volume'}", f"{total_vol:,.0f}".replace(',', '.'))
        kpi2.metric("👥 Colaboradores", len(df_filtrado))
        total_horas = df_filtrado['Horas'].sum() if 'Horas' in df_filtrado.columns else 0
        kpi3.metric("⏱️ Horas Registradas", f"{total_horas:.1f} h" if total_horas > 0 else "—")

    st.divider() # Linha cinza separadora de seções

    # =============================================================================
    # 🚨 MÓDULO DETRATORES (Quem não bateu a meta 1)
    # =============================================================================
    if focar_detratores:
        st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
        houve_detrator = False

        # Varre a planilha inteira pessoa por pessoa
        for idx, row in df_filtrado.iterrows():
            detalhes_gargalo = []
            
            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                if pd.isna(meta2) or str(meta2).strip() in ['0', '0.0', '-', '']: continue
                
                realizado = float(row.get(kpi, 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                meta1 = float(row.get(f"{kpi}_Meta1", meta2))

                if racional == 1 and realizado == 0: continue # Pula folguistas/afastados

                # Identifica se a pessoa falhou com base na regra de ser MAIOR que a meta, ou MENOR.
                abaixo_da_meta = False
                if racional == 1 and realizado < meta1: abaixo_da_meta = True
                elif racional == 0 and realizado > meta1: abaixo_da_meta = True

                # Se falhou, salva a informação vermelha
                if abaixo_da_meta:
                    if "%" in kpi or "Avaria" in kpi or "Corte" in kpi or "Dev" in kpi:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado:.2f}% vs Alvo Mínimo (Meta 1) {meta1:.2f}%")
                    else:
                        detalhes_gargalo.append(f"❌ {kpi}: {realizado:,.0f} vs Alvo Mínimo (Meta 1) {meta1:,.0f}".replace(',', '.'))

            # Se a pessoa teve pelo menos 1 gargalo, desenha a tela vermelha dela
            if detalhes_gargalo:
                houve_detrator = True
                nome_c, cod_c, cargo_c, turno_c = row['NOME'], row['CÓD.'], row['FUNÇÃO'], row['TURNO']
                d_trab = int(row.get('Dias Trabalhados', 0))

                with st.container():
                    st.markdown(f"<div class='card-detrator'><span style='font-size: 22px; font-weight: bold; color: {C_VERMELHO};'>⚠️ [{cod_c}] {nome_c}</span><br><b>Turno:</b> {turno_c} | <b>Função:</b> {cargo_c} | <b>Dias Lançados:</b> {d_trab} dias<br><br><span style='font-weight: bold; color: #ffca28;'>Pontos de Desvio Identificados:</span><br>{'<br>'.join(detalhes_gargalo)}</div>", unsafe_allow_html=True)
                    
                    # Caxinhas de Ação de RH dentro da visão de Detratores
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
                                            gestor = st.session_state["usuario"].capitalize() # <--- NOME DO LÍDER
                                            aba_rh.append_row([agora, str(cod_c), nome_c, "Feedback", texto_feedback, gestor])
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
                                        gestor = st.session_state["usuario"].capitalize() # <--- NOME DO LÍDER
                                        aba_rh.append_row([agora, str(cod_c), nome_c, "Reciclagem", motivo, gestor])
                                        st.success("📧 Enviado!")
                                    except Exception as e: st.error(f"Erro: {e}")
                    st.markdown("<br>", unsafe_allow_html=True)

        if not houve_detrator: st.success("🎉 Nenhum detrator encontrado! Operação saudável.")

    # =============================================================================
    # 👤 VISÃO INDIVIDUAL DO COLABORADOR (A ficha completa da pessoa)
    # =============================================================================
    elif pessoa_selecionada != "Nenhum":
        st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]

        if not dados_pessoa.empty:
            row = dados_pessoa.iloc[0]
            
            # --- RENDERIZA O TROFÉU DE RANKING DO COLABORADOR ---
            pos = int(row.get('Posicao Ranking', 0))
            val_rank = row.get('Valor Ranking', 0)
            cargo_p = str(row.get('FUNÇÃO', '')).upper()
            turno_p = str(row.get('TURNO', '')).upper()
            
            # Mostra o troféu para Separadores (Todos os turnos) e para Conferentes/Operadores (Só T3)
            if pos > 0 and ('SEPARADOR' in cargo_p or ('CONFERENTE' in cargo_p and turno_p == 'T3') or ('OPERADOR' in cargo_p and turno_p == 'T3')):
                funcao_original = row.get('FUNÇÃO', '')
                total_eq = len(df_filtrado[(df_filtrado['TURNO'] == row.get('TURNO')) & (df_filtrado['FUNÇÃO'] == funcao_original)])
                
                # Regra visual: Top 3 ganha medalhas metálicas. 4º em diante ganha medalha padrão cinza.
                if pos == 1: medalha, cor_rank = "🥇", "#ffd700" # Dourado
                elif pos == 2: medalha, cor_rank = "🥈", "#c0c0c0" # Prateado
                elif pos == 3: medalha, cor_rank = "🥉", "#cd7f32" # Bronze
                else: medalha, cor_rank = "🏅", "#555555"          # Cinza chumbo 
                
                # Se não ganhou prêmio (ex: Operador em 2º lugar), não exibe "R$ 0,00" para não desmotivar.
                if val_rank > 0:
                    texto_premio_rank = f" | <span style='color: #2ecc71;'><b>💰 Prêmio Ranking: R$ {val_rank:,.2f}</b></span>".replace(',', 'X').replace('.', ',').replace('X', '.')
                else:
                    texto_premio_rank = ""
                
                # Caixa visual do Ranking
                st.markdown(f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'><b>{medalha} Posição no Ranking:</b> {pos}º lugar de {total_eq} na equipe de {funcao_original}{texto_premio_rank}</div>", unsafe_allow_html=True)

            # --- RENDERIZA OS CARTÕES DAS MÉTRICAS ---
            cols_meta = st.columns(4) # Desenha de 4 em 4 colunas
            col_idx = 0
            grafico_dados = []

            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                if pd.isna(meta2) or str(meta2).strip() in ['0', '0.0', '-', '']: continue

                realizado = float(row.get(kpi, 0))
                meta1, meta2, meta3 = float(row.get(f"{kpi}_Meta1", 0)), float(meta2), float(row.get(f"{kpi}_Meta3", 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                valor_reais = float(row.get(f"{kpi}_Valor", 0))

                # Lógica de Semáforo (Verde, Vermelho, Azul, Amarelo)
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
                
                # Guarda as infos para desenhar o gráfico de barras lá no final
                grafico_dados.append({'Indicador': f"<b>{kpi}</b>", 'Atingimento (%)': min(real_perc, 120), 'Real': real_perc})
                html_dinheiro = f"<span style='color: {C_VERDE}; font-size: 20px; font-weight: 900; margin-left: 10px;'>💰 R$ {valor_reais:,.2f}</span>".replace(',', 'X').replace('.', ',').replace('X', '.') if valor_reais > 0 else ""

                # Mascara os textos dos cartões (Segundos viram Tempo e Decimais viram %)
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

                # Cria o Cartão (Card) da métrica injetando CSS dinamicamente
                with cols_meta[col_idx % 4]:
                    st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{kpi}</div><div class='texto-card-principal'>{val_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status} {html_dinheiro}</div></div>", unsafe_allow_html=True)
                col_idx += 1

            # --- SOMA FINAL (BARRA VERDE DE DINHEIRO) ---
            valor_final_total = row.get('Valor Final', 0)
            if valor_final_total > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {valor_final_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

            st.divider()

            # =============================================================================
            # 🗣️ GESTÃO E FEEDBACK INDIVIDUAL (Dentro do Perfil da Pessoa)
            # =============================================================================
            nome_c = row.get('NOME', pessoa_selecionada)
            cod_c = row.get('CÓD.', '')

            st.markdown(f"### 🗣️ Ações de Gestão: {nome_c}")
            col_feed_ind, col_trein_ind = st.columns(2) # Duas caixinhas dividindo a tela
            
            with col_feed_ind:
                with st.expander(f"💬 Registrar Feedback"):
                    # key=cod_c impede o botão de confundir um funcionário com outro
                    with st.form(key=f"form_feed_ind_{cod_c}"):
                        texto_feedback = st.text_area("Descreva o que foi conversado (Elogios, Alinhamentos, etc):")
                        if st.form_submit_button("Salvar no Histórico"):
                            if texto_feedback:
                                try:
                                    aba_rh = conectar_planilha().worksheet("Historico_RH")
                                    agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                    gestor = st.session_state["usuario"].capitalize() # <--- SALVA O NOME DO LÍDER AQUI
                                    aba_rh.append_row([agora, str(cod_c), nome_c, "Feedback", texto_feedback, gestor])
                                    st.success("✅ Salvo!")
                                except Exception as e: st.error(f"Erro: {e}")
                            else: st.error("⚠️ Digite algo.")
            
            with col_trein_ind:
                with st.expander(f"🎯 Solicitar Reciclagem"):
                    with st.form(key=f"form_trein_ind_{cod_c}"):
                        # Adicionado o 'Comportamental' na lista suspensa
                        motivo = st.selectbox("Motivo/Gargalo:", ["Velocidade", "Erros/Avarias", "Sistema", "Processo", "Comportamental", "Outros"])
                        if st.form_submit_button("Enviar Solicitação"):
                            try:
                                aba_rh = conectar_planilha().worksheet("Historico_RH")
                                agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                gestor = st.session_state["usuario"].capitalize() # <--- SALVA O NOME DO LÍDER AQUI
                                aba_rh.append_row([agora, str(cod_c), nome_c, "Reciclagem", motivo, gestor])
                                st.success("📧 Enviado!")
                            except Exception as e: st.error(f"Erro: {e}")

            st.divider()
            st.markdown(f"### 📊 Análise de {pessoa_selecionada}")

            # --- GRÁFICOS VISUAIS E DRILL-DOWN ---
            if grafico_dados:
                df_grafico = pd.DataFrame(grafico_dados)
                df_grafico['Cor'] = df_grafico['Real'].apply(lambda x: C_AZUL if x >= 120 else (C_VERDE if x >= 100 else (C_AMARELO if x >= 50 else C_VERMELHO)))
                df_grafico['Texto_Cor'] = df_grafico['Cor'].apply(lambda color: "black" if color == C_AMARELO else "white")
                
                # Monta a barra do gráfico Plotly
                fig = px.bar(df_grafico, x='Indicador', y='Atingimento (%)', text=df_grafico['Real'].apply(lambda x: f"<b>{x:.1f}%</b>"))
                fig.update_layout(showlegend=False, yaxis_title="<b>% da Meta Atingida</b>", xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(t=15, b=0, l=0, r=0))
                fig.add_hline(y=100, line_dash="dash", line_color="lightgray", annotation_text="<b>Meta 100%</b>", annotation_font_color="lightgray")
                fig.update_traces(textfont=dict(size=24, color=df_grafico['Texto_Cor'].tolist()), marker=dict(color=df_grafico['Cor'].tolist(), line=dict(color='white', width=1)))
                fig.update_xaxes(tickfont=dict(size=20, color="lightgray", family="Arial Black"))
                fig.update_yaxes(tickfont=dict(size=14, color="lightgray"), title_font=dict(color="lightgray"))
                
                col_grafico, col_tabela = st.columns([1.2, 1])
                with col_grafico:
                    st.plotly_chart(fig, use_container_width=True) # Renderiza o Gráfico de Barras
                
                with col_tabela:
                    cargo_p = str(row.get('FUNÇÃO', '')).upper()
                    turno_p = str(row.get('TURNO', '')).upper()

                    # =============================================================================
                    # 📅 DRILL-DOWN DIÁRIO INTELIGENTE (Separadores, Operadores e Conferentes)
                    # =============================================================================
                    # O Python descobre automaticamente qual aba da nuvem ele deve puxar
                    usa_diario = False
                    df_uso_diario = pd.DataFrame()
                    
                    if "SEPARADOR" in cargo_p:
                        usa_diario = True
                        df_uso_diario = df_diario
                    elif "OPERADOR" in cargo_p:
                        usa_diario = True
                        df_uso_diario = df_operador
                    elif "CONFERENTE" in cargo_p:
                        usa_diario = True
                        df_uso_diario = df_conferente

                    if usa_diario:
                        if not df_uso_diario.empty:
                            df_pessoa_diario = df_uso_diario[df_uso_diario['NOME'] == pessoa_selecionada]
                            if not df_pessoa_diario.empty:
                                pessoa_d_row = df_pessoa_diario.iloc[0]
                                
                                cols_datas_reais = []
                                opcoes_datas_formatadas = []
                                
                                # Caça as colunas de Datas no Excel, ignorando textos
                                for c in df_uso_diario.columns:
                                    c_str = str(c).strip()
                                    if any(char.isdigit() for char in c_str) and ('/' in c_str or '-' in c_str) and 'Inicio' not in c_str and 'Horas' not in c_str and 'Itens' not in c_str and 'JL' not in c_str and 'Mov' not in c_str and 'Frac' not in c_str and 'Grand' not in c_str:
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
                                        # Caixinha interativa para escolher qual dia olhar
                                        data_escolhida_display = st.selectbox(
                                            "Data Apuração", 
                                            opcoes_datas_formatadas, 
                                            label_visibility="collapsed", 
                                            key="sel_data_diario_alinhado"
                                        )
                                    
                                    # Baseado no dia escolhido, cruza para achar a coluna da planilha selecionada
                                    idx_escolha = opcoes_datas_formatadas.index(data_escolhida_display)
                                    nome_coluna_real = cols_datas_reais[idx_escolha]
                                    col_index = list(df_uso_diario.columns).index(nome_coluna_real)
                                    
                                    # Puxa os dados brutos de forma blindada (Se a planilha faltar coluna, ele coloca '0')
                                    try: val_1 = str(pessoa_d_row.iloc[col_index]).strip()
                                    except: val_1 = "0"
                                    
                                    try: val_2 = str(pessoa_d_row.iloc[col_index + 1]).strip()
                                    except: val_2 = "0"
                                    
                                    try: val_3 = str(pessoa_d_row.iloc[col_index + 2]).strip()
                                    except: val_3 = "0"
                                    
                                    try: val_4 = str(pessoa_d_row.iloc[col_index + 3]).strip()
                                    except: val_4 = "0"
                                    
                                    val_1 = val_1 if val_1 and val_1.lower() not in ['nan', 'none'] else "0"
                                    val_2 = val_2 if val_2 and val_2.lower() not in ['nan', 'none'] else "0"
                                    val_3 = val_3 if val_3 and val_3.lower() not in ['nan', 'none'] else "0"
                                    val_4 = val_4 if val_4 and val_4.lower() not in ['nan', 'none'] else "0"
                                    
                                    # --- MOLDAGEM VISUAL DEPENDENDO DA FUNÇÃO ---
                                    if "SEPARADOR" in cargo_p:
                                        # Formatação da Jornada Líquida %
                                        try:
                                            if val_4 and val_4.lower() not in ['nan', 'none']:
                                                val_jl_num = float(val_4.replace(',', '.').replace('%', ''))
                                                if val_jl_num <= 2.0 and "%" not in val_4: 
                                                    val_jl_num = val_jl_num * 100
                                                jl_display = f"{int(val_jl_num)}%" 
                                            else:
                                                jl_display = "0%"
                                        except:
                                            jl_display = "0%"
                                            
                                        try: v_itens = f"{float(val_1.replace(',', '.')):,.0f}".replace(',', '.')
                                        except: v_itens = "0"
                                        
                                        try: v_veloc = f"{int(round(float(val_3.replace(',', '.'))))}"
                                        except: v_veloc = "0"

                                        # Formata as horas em Decimais (1,50) para Relógio (01:30)
                                        try:
                                            horas_dec = float(val_2.replace(',', '.'))
                                            h = int(horas_dec)
                                            m = int((horas_dec - h) * 60)
                                            s = int((((horas_dec - h) * 60) - m) * 60)
                                            v_horas = f"{h:02d}:{m:02d}:{s:02d}"
                                        except:
                                            v_horas = "00:00:00"

                                        # Constrói o visual das métricas diárias (O clássico do Separador)
                                        c1, c2, c3 = st.columns(3)
                                        c1.metric("⏱️ Horas", v_horas)
                                        c2.metric("⚡ Itens/Hora", v_veloc)
                                        c3.metric("🎯 JL", jl_display)
                                        
                                        # Banner Gigante em Azul para os Itens Separados (A principal métrica)
                                        st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>Itens Separados</h4><h2 style='margin:0; color: {C_AZUL};'>{v_itens}</h2></div>", unsafe_allow_html=True)
                                        
                                    elif "CONFERENTE" in cargo_p:
                                        try: v_frac = f"{float(val_1.replace(',', '.')):,.0f}".replace(',', '.')
                                        except: v_frac = "0"
                                        try: v_grand = f"{float(val_2.replace(',', '.')):,.0f}".replace(',', '.')
                                        except: v_grand = "0"

                                        # Banners bonitos lado a lado ao invés das métricas pequenas!
                                        st.markdown("<p style='color: #888; font-size: 14px; margin-bottom: -10px;'>Métricas de Conferência</p>", unsafe_allow_html=True)
                                        c1, c2 = st.columns(2)
                                        with c1:
                                            st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Fracionado</h4><h2 style='margin:0; color: {C_AZUL};'>{v_frac}</h2></div>", unsafe_allow_html=True)
                                        with c2:
                                            st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Grandeza</h4><h2 style='margin:0; color: {C_VERDE};'>{v_grand}</h2></div>", unsafe_allow_html=True)

                                    elif "OPERADOR" in cargo_p:
                                        try: v_horiz = f"{float(val_1.replace(',', '.')):,.0f}".replace(',', '.')
                                        except: v_horiz = "0"
                                        try: v_vert = f"{float(val_2.replace(',', '.')):,.0f}".replace(',', '.')
                                        except: v_vert = "0"

                                        # Banners bonitos lado a lado ao invés das métricas pequenas!
                                        st.markdown("<p style='color: #888; font-size: 14px; margin-bottom: -10px;'>Movimentações</p>", unsafe_allow_html=True)
                                        c1, c2 = st.columns(2)
                                        with c1:
                                            st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↔️ Mov. Horizontal</h4><h2 style='margin:0; color: {C_AZUL};'>{v_horiz}</h2></div>", unsafe_allow_html=True)
                                        with c2:
                                            st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↕️ Mov. Vertical</h4><h2 style='margin:0; color: {C_VERDE};'>{v_vert}</h2></div>", unsafe_allow_html=True)

                                else:
                                    st.markdown("### 📅 Resultado Diário")
                                    st.info("Nenhuma data foi identificada no cabeçalho do Relatório Diário.")
                            else:
                                st.markdown("### 📅 Resultado Diário")
                                st.warning("Colaborador não encontrado na aba diária correspondente.")
                        else:
                            st.markdown("### 📅 Resultado Diário")
                            st.warning("⚠️ Não foi possível carregar os dados. A aba não foi encontrada na nuvem.")

                    # =============================================================================
                    # TABELA NORMAL INDIVIDUAL (Se NÃO for cargo com relatório diário)
                    # =============================================================================
                    else:
                        kpis_ativos_pessoa = []
                        for k in kpis_mapeados:
                            m2 = pd.to_numeric(row.get(f"{k}_Meta2", 0), errors='coerce')
                            if pd.notna(m2) and m2 > 0:
                                kpis_ativos_pessoa.append(k) # Só lista as métricas que a pessoa possui

                        # Prepara a mini-tabela com Dias Úteis e Faltas
                        col_uteis = ['CÓD.', 'NOME', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final'] + kpis_ativos_pessoa
                        df_tabela_mini = dados_pessoa[[c for c in col_uteis if c in df_filtrado.columns]].copy()
                        
                        if 'Tempo Médio' in df_tabela_mini.columns:
                            df_tabela_mini['Tempo Médio'] = df_tabela_mini['Tempo Médio'].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if pd.notna(s) else "00:00:00")
                        
                        # Formata o visual da tabela na tela
                        config_colunas = {'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")}
                        for col in df_tabela_mini.columns:
                            if col in ['CÓD.', 'NOME', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim', 'Valor Final']: continue 
                            elif col in ['Avaria', 'Corte %', 'Dev. %']: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                            elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                            else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")
                        
                        st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=350, column_config=config_colunas)

    # =============================================================================
    # 👥 VISÃO GERAL EQUIPE (A tela de Boas-Vindas ou os Blocos Coletivos)
    # =============================================================================
    else:
        # Testa se a caixa da barra lateral mudou de posição para saber se aplica os filtros ou deixa o Manual
        filtros_ativos = (turno_selecionado not in ["Todos", "Todos Permitidos"]) or (cargo_selecionado != "Todos")

        if not filtros_ativos:
            # --- 🚀 TELA DE BOAS-VINDAS (LANDING PAGE COM O MANUAL DE USO) ---
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
            # --- RENDERIZA OS CARDS COLETIVOS DAS EQUIPES ---
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
                        
                        # Retira os zerados da Média Geral (senão a média da equipe desaba se alguém tirou folga)
                        if racional_temp == 1: df_kpi_valido = df_cargo[df_cargo[kpi] > 0]
                        else: df_kpi_valido = df_cargo[df_cargo['Dias Trabalhados'] > 0]
                            
                        if df_kpi_valido.empty: continue

                        # 🛡️ Calcula as médias do Turno (Ignorando os zerados para não afundar a meta da equipe)
                        df_com_meta = df_kpi_valido[df_kpi_valido[f"{kpi}_Meta2"] > 0]
                        if df_com_meta.empty: continue

                        meta2_med = df_com_meta[f"{kpi}_Meta2"].mean()
                        meta1_med = df_com_meta[f"{kpi}_Meta1"].mean() if f"{kpi}_Meta1" in df_com_meta.columns else meta2_med
                        meta3_med = df_com_meta[f"{kpi}_Meta3"].mean() if f"{kpi}_Meta3" in df_com_meta.columns else meta2_med
                        
                        real_med = df_kpi_valido[kpi].mean()
                        racional = racional_temp
                        soma_total = df_kpi_valido[kpi].sum()

                        # Verifica a cor do Card da Média da Equipe
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

                        # Algumas métricas mostram apenas o número, outras mostram o "Soma de todos: 124.000" para ter visão geral
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

        # =============================================================================
        # 📋 TABELA GERENCIAL CONSOLIDADA (A matriz gigante no final do site)
        # =============================================================================
        if filtros_ativos:
            if 'cargos_render' in locals() and len(cargos_render) > 0: st.divider()
            
            st.markdown("### 📋 Tabela de Produtividade Consolidada (Relatório Gerencial)")
            
            # Filtra apenas os KPIs que a equipe possui
            kpis_ativos_tabela = []
            for kpi in kpis_mapeados:
                if f"{kpi}_Meta2" in df_filtrado.columns:
                    metas_validas = pd.to_numeric(df_filtrado[f"{kpi}_Meta2"], errors='coerce').fillna(0)
                    if metas_validas.sum() > 0:
                        kpis_ativos_tabela.append(kpi)

            colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Trabalhados', 'Dias Meta', 'Dias Uteis', 'Valor Final'] + kpis_ativos_tabela
            df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()

            # 🛡️ BLINDAGEM VISUAL DO TEMPO MÉDIO NA TABELA: Converte os segundos (3417) de volta para Relógio
            if 'Tempo Médio' in df_tabela.columns:
                df_tabela['Tempo Médio'] = pd.to_numeric(df_tabela['Tempo Médio'], errors='coerce').fillna(0)
                df_tabela['Tempo Médio'] = df_tabela['Tempo Médio'].apply(
                    lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if s > 0 else "00:00:00"
                )

            # Formata a coluna financeira para ter R$ na tela
            config = {
                'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")
            }
            
            for col in df_tabela.columns:
                if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim', 'Valor Final']: continue 
                elif col in ['Avaria', 'Corte %', 'Dev. %']: config[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                elif "Líq." in col: config[col] = st.column_config.NumberColumn(col, format="%d%%")
                else: config[col] = st.column_config.NumberColumn(col, format="%d")

            # O height=600 controla a altura da tabela antes de criar barra de rolagem
            st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

except Exception as e:
    # Se bater algum erro não previsto, o site não trava a tela preta, mas escreve essa mensagem com o motivo
    st.error(f"⚠️ Erro ao renderizar painel: {e}")
