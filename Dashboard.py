# =============================================================================
# 📦 IMPORTAÇÃO DE BIBLIOTECAS (O que o Python precisa para funcionar)
# =============================================================================
import streamlit as st          
import pandas as pd             
import datetime                 
import plotly.express as px     
import gspread                  
import io                       
import calendar                 
import re

# =============================================================================
# 🎨 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (O CSS do site)
# =============================================================================
st.set_page_config(page_title="Dashboard Expedição | TAF", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    /* Esconde as marcas e menus padrões do Streamlit para parecer um sistema web próprio */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container { padding-top: 2rem !important; }
    
    .card-meta { 
        background-color: var(--background-color); 
        padding: 15px;                             
        border-radius: 10px;                        
        border-left: 8px solid #ccc;                
        margin-bottom: 15px;                        
    }
    
    .card-detrator { 
        background-color: rgba(239, 68, 68, 0.1);  
        border: 1px solid #ef4444;                 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
    }
    
    .texto-card-principal { 
        font-size: 42px;                           
        color: var(--text-color); 
        font-weight: 900;                          
        line-height: 1.1; 
    }
    
    .texto-card-titulo { 
        font-size: 22px;                           
        color: var(--text-color); 
        font-weight: 900; 
        margin-bottom: 5px; 
    }
    
    /* 💡 CSS PARA DEIXAR A TABELA NATIVA MAIOR E MAIS BONITA */
    [data-testid="stDataFrame"] {
        zoom: 1.35;
        border: 1px solid #2ecc71;
        border-radius: 8px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }
    [data-testid="stDataFrame"] th {
        background-color: rgba(46, 204, 113, 0.15) !important;
        color: #2ecc71 !important;
        font-size: 15px !important;
        font-weight: 900 !important;
    }
    [data-testid="stDataFrame"] td {
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

C_AZUL, C_VERDE, C_AMARELO, C_VERMELHO = "#3b82f6", "#2ecc71", "#ffca28", "#ef4444"

# =============================================================================
# 🧰 FUNÇÕES DE APOIO E LIMPEZA DE DADOS
# =============================================================================

def parse_time(val):
    val = str(val).strip()
    if val in ["", "nan", "None", "—", "-", "0", "0,00", "0.00", "00:00:00"]: return "00:00:00"
    if ":" in val:
        if " " in val: val = val.split(" ")[-1]
        parts = val.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = int(parts[2]) if len(parts) > 2 else 0
            return f"{h:02d}:{m:02d}:{s:02d}"
        except:
            return val
    try:
        v = float(val.replace(',', '.'))
        if 0 < v < 1:  
            total_s = int(round(v * 24 * 3600))
            h, rem = divmod(total_s, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        else: 
            h = int(v)
            v_str = val.replace(',', '.')
            m = 0
            if '.' in v_str:
                m_str = v_str.split('.')[1]
                if len(m_str) == 1: m_str += "0"
                m = int(m_str[:2])
            return f"{h:02d}:{m:02d}:00"
    except:
        return val

def formatar_data_br(d_str):
    d_str = str(d_str).strip().split(" ")[0]
    match_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', d_str)
    if match_iso: return f"{match_iso.group(3)}/{match_iso.group(2)}/{match_iso.group(1)}"
    match_br = re.search(r'(\d{2})/(\d{2})/(\d{4})', d_str)
    if match_br: return f"{match_br.group(1)}/{match_br.group(2)}/{match_br.group(3)}"
    return d_str

def extrair_inteiro(val):
    try:
        if pd.isna(val): return 0
    except ValueError: return 0
    v_str = str(val).strip()
    if v_str.lower() in ['nan', 'none', '', '-']: return 0
    v_str = re.sub(r'[^\d.,]', '', v_str)
    if not v_str: return 0
    if ',' in v_str: v_str = v_str.split(',')[0]
    v_str = v_str.replace('.', '')
    try: return int(v_str)
    except: return 0

def obter_valor_100(turno, funcao, kpi):
    t = str(turno).strip().upper()
    f = str(funcao).strip().upper()
    k = str(kpi).strip().upper()
    
    mapa = {
        ("T1", "CONFERENTE", "PALETS CONF."): 300,
        ("T1", "CONFERENTE", "TEMPO MÉDIO"): 100,
        ("T1", "DESCARGA", "CARGA PALET."): 125,
        ("T1", "DESCARGA", "TEMPO MÉDIO"): 125,
        ("T1", "DESCARGA", "CARGA BAT."): 125,
        ("T1", "DESCARGA", "CESTA"): 60,
        ("T1", "DEVOLUÇÃO", "DEV. %"): 150,
        ("T1", "DEVOLUÇÃO", "AVARIA"): 150,
        ("T1", "LÍDER", "AVARIA"): 150,
        ("T1", "LÍDER", "MÉD. PALETS CONF."): 300,
        ("T1", "LÍDER", "TEMPO MÉDIO"): 300,
        ("T1", "OPERADOR", "MOV. VERT."): 350,
        ("T1", "OPERADOR", "TEMPO MÉDIO"): 100,
        ("T1", "PUXA", "PALETS PX."): 200,
        ("T1", "PUXA", "TEMPO MÉDIO"): 100,
        ("T1", "AVARIA", "AVARIA"): 150,
        
        ("T2", "AVARIA", "AVARIA"): 150,
        ("T2", "CONFERENTE", "ITENS CONF."): 300,
        ("T2", "CONFERENTE", "DEV. %"): 150,
        ("T2", "DEVOLUÇÃO", "DEV. %"): 150,
        ("T2", "DEVOLUÇÃO", "AVARIA"): 150,
        ("T2", "INVENTARIO", "CORTE %"): 200,
        ("T2", "LÍDER", "AVARIA"): 150,
        ("T2", "LÍDER", "RESSUP. EQ."): 240,
        ("T2", "LÍDER", "DEV. %"): 240,
        ("T2", "LÍDER", "ITENS/HORA EQ."): 240,
        ("T2", "MESA", "RESSUP. EQ."): 220,
        ("T2", "MESA", "DEV. %"): 220,
        ("T2", "MESA", "ITENS/HORA EQ."): 220,
        ("T2", "OPERADOR", "MOV. HORIZONTAL"): 450,
        ("T2", "OPERADOR", "AVARIA"): 100,
        ("T2", "CARREGAMENTO BOX", "ITENS RAMPA"): 150,
        ("T2", "CARREGAMENTO BOX", "DEV. %"): 150,
        ("T2", "CARREGAMENTO BOX", "AVARIA"): 100,
        ("T2", "SEPARADOR G", "RESSUP. AP."): 200,
        ("T2", "SEPARADOR G", "ITENS/HORA"): 200,
        ("T2", "SEPARADOR G", "ITENS SEP"): 0, 
        
        ("T3", "SEPARADOR F", "JORNADA LÍQ."): 150,
        ("T3", "SEPARADOR F", "ITENS SEP"): 150,
        ("T3", "SEPARADOR F", "ITENS/HORA"): 150,
        ("T3", "SEPARADOR G", "JORNADA LÍQ."): 150,
        ("T3", "SEPARADOR G", "ITENS SEP"): 150,
        ("T3", "SEPARADOR G", "ITENS/HORA"): 150,
        
        ("T3", "CONFERENTE", "ITENS CONF."): 350,
        ("T3", "CONFERENTE", "DEV. %"): 150,
        ("T3", "CONFERENTE GRANDEZA", "ITENS CONF."): 350,
        ("T3", "CONFERENTE GRANDEZA", "DEV. %"): 150,
        
        ("T3", "DEVOLUÇÃO", "DEV. %"): 150,
        ("T3", "DEVOLUÇÃO", "AVARIA"): 150,
        ("T3", "AVARIA", "AVARIA"): 150,
        
        ("T3", "OPERADOR", "MOV. HORIZONTAL"): 450,
        ("T3", "OPERADOR", "AVARIA"): 100,
        ("T3", "CARREGAMENTO BOX", "ITENS RAMPA"): 150,
        ("T3", "CARREGAMENTO BOX", "DEV. %"): 150,
        ("T3", "CARREGAMENTO BOX", "AVARIA"): 100,
        ("T3", "RAMPEIRO", "ITENS RAMPA"): 150, 
        ("T3", "RAMPEIRO", "DEV. %"): 150,      
        ("T3", "RAMPEIRO", "AVARIA"): 100,      
        ("T3", "MESA", "JORNADA LÍQ. EQ."): 220,
        ("T3", "MESA", "DEV. %"): 220,
        ("T3", "MESA", "CORTE %"): 220,
        ("T3", "MANOBRISTA", "ITENS MANOB."): 350,
        ("T3", "MANOBRISTA", "DEV. %"): 150,
        ("T3", "MANOBRISTA", "AVARIA"): 150,
        ("T3", "LÍDER", "JORNADA LÍQ. EQ."): 240,
        ("T3", "LÍDER", "AVARIA"): 150,
        ("T3", "LÍDER", "DEV. %"): 240,
        ("T3", "LÍDER", "ITENS/HORA EQ."): 240,
        ("T3", "RESPONSAVEL SALA BATERIAS", "ITENS/HORA"): 150,
        ("T3", "RESPONSAVEL SALA BATERIAS", "AVARIA"): 100,
        ("T3", "RESPONSAVEL SALA BATERIAS", "CHECKLIST MANUTENÇÃO"): 250,
    }
    return mapa.get((t, f, k), 0)

# =============================================================================
# 🔐 CONFIGURAÇÃO DE USUÁRIOS E SENHAS
# =============================================================================
USUARIOS = {
    "diegoc": {"senha": "ger#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "suelin": {"senha": "rh#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "rh": {"senha": "rh#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "nilo": {"senha": "esp#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "andreus": {"senha": "ana#26", "perfil": "Gerente", "turno_acesso": "Todos"},
    "gabriel": {"senha": "ana#26", "perfil": "Gerente", "turno_acesso": ["T1", "T2"]},
    "flamarion": {"senha": "sub#26", "perfil": "Líder", "turno_acesso": ["T1", "T2"]}, 
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

# =============================================================================
# 🔗 CONEXÃO COM GOOGLE SHEETS E CARREGAMENTO
# =============================================================================
def conectar_planilha():
    cred_dict = dict(st.secrets["gcp_service_account"]) 
    client = gspread.service_account_from_dict(cred_dict)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1pA4PYhyMi57YlK5qwLJZ9BSmpdyTz7frtmtTiG-CaLU/edit?usp=sharing")

@st.cache_data(ttl=60) 
def carregar_dados():
    try:
        planilha = conectar_planilha()
        aba_bruta = planilha.worksheet("Aux Calc").get_all_values()
    except Exception as e:
        st.error(f"Erro ao carregar a aba Aux Calc: {e}")
        return pd.DataFrame()
    
    header_idx = 0
    for i, row_vals in enumerate(aba_bruta):
        val_upper = [str(cell).strip().upper() for cell in row_vals]
        if "NOME" in val_upper or "CÓD." in val_upper:
            header_idx = i
            break
            
    df = pd.DataFrame(aba_bruta[header_idx+1:], columns=aba_bruta[header_idx])
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, df.columns != '']
    
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
            except IndexError: pass 

    colunas_atuais = list(df.columns)
    def achar_coluna(nome_exato, palavras_chave):
        for c in colunas_atuais:
            if str(c).strip().upper() == nome_exato.upper(): return c
        for c in reversed(colunas_atuais):
            nome_limpo = " ".join(str(c).upper().split())
            if any(p in nome_limpo for p in palavras_chave): return c
        return None

    c_corr = achar_coluna("DIAS CORRIDOS", ["DIAS CORR"])
    c_trab = achar_coluna("DIAS TRABALHADOS", ["DIAS TRAB"])
    c_meta = achar_coluna("DIAS META", ["DIAS META"])
    c_ini = achar_coluna("DATA INICIO", ["DATA INIC", "DATA INÍC"])
    c_fim = achar_coluna("DATA FIM", ["DATA FIM", "DATA APURA"])
    c_erro = achar_coluna("ERROS", ["ERRO"])

    df['Dias Corridos'] = pd.to_numeric(df[c_corr], errors='coerce').fillna(0).astype(int) if c_corr else 0
    df['Dias Trabalhados'] = pd.to_numeric(df[c_trab], errors='coerce').fillna(0).astype(int) if c_trab else 0
    df['Dias Meta'] = pd.to_numeric(df[c_meta], errors='coerce').fillna(0).astype(int) if c_meta else 0
    if c_ini: df['Data Inicio'] = df[c_ini]
    if c_fim: df['Data Fim'] = df[c_fim]
    df['ERROS'] = pd.to_numeric(df[c_erro], errors='coerce').fillna(0).astype(int) if c_erro else 0

    df = df.loc[:, ~df.columns.duplicated()].copy()
    if 'NOME' in df.columns: df = df.dropna(subset=['NOME'])
    if 'FUNÇÃO' in df.columns: df['FUNÇÃO'] = df['FUNÇÃO'].astype(str).str.upper().str.strip()
    if 'TURNO' in df.columns: df['TURNO'] = df['TURNO'].astype(str).str.upper().str.strip()
    
    colunas_texto = ["CÓD.", "NOME", "TURNO", "FUNÇÃO", "Data Inicio", "Data Fim"]
    for col in df.columns:
        if col not in colunas_texto:
            if col in ["Tempo Médio", "Tempo Médio_Meta1", "Tempo Médio_Meta2", "Tempo Médio_Meta3"]:
                texto_limpo = df[col].astype(str).str.split(".").str[0].str.strip()
                df[col] = pd.to_timedelta(texto_limpo, errors="coerce").dt.total_seconds().fillna(0)
            else:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(0)
                else:
                    s = df[col].astype(str).str.replace("R$", "", regex=False).str.replace("%", "", regex=False).str.strip()
                    s_numerico = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df[col] = pd.to_numeric(s_numerico, errors="coerce").fillna(0)
                
    df['Penalidade_Texto'] = ""
    for idx, row in df.iterrows():
        cargo_e = str(row.get('FUNÇÃO', '')).upper()
        erros_e = float(row.get('ERROS', 0))
        if erros_e > 0:
            if 'SEPARADOR' in cargo_e: df.at[idx, 'Penalidade_Texto'] = f"-{int(erros_e * 20)} Itens"
            elif 'OPERADOR' in cargo_e: df.at[idx, 'Penalidade_Texto'] = f"-{int(erros_e * 10)} Mov."
    return df

@st.cache_data(ttl=60)
def carregar_diarios():
    dfs = {'sep': pd.DataFrame(), 'op': pd.DataFrame(), 'conf': pd.DataFrame(), 'aux_jl': pd.DataFrame(), 'acomp_jl': pd.DataFrame(), 'ponto_t3': pd.DataFrame()}
    try:
        planilha = conectar_planilha()
        def processar_aba(nome_aba):
            ws = None
            for sheet in planilha.worksheets():
                if sheet.title.strip().lower() == nome_aba.strip().lower():
                    ws = sheet
                    break
            if not ws: return pd.DataFrame()
            
            aba_bruta = ws.get_all_values()
            if not aba_bruta: return pd.DataFrame()
            if nome_aba == "Acompanhamento JL": return pd.DataFrame(aba_bruta)
            
            header_idx = 0
            for i, row_vals in enumerate(aba_bruta):
                val_upper = [str(cell).strip().upper() for cell in row_vals]
                if any(k in val_upper for k in ["NOME", "NOMECOMPLETO", "CÓD.", "BOX", "OPERADOR", "CONTRATO"]):
                    header_idx = i
                    break
            
            headers = aba_bruta[header_idx]
            if header_idx > 0 and nome_aba.strip().lower() != "ponto t3":
                linha_datas = []
                for row_i in range(header_idx):
                    if any(re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', str(c)) for c in aba_bruta[row_i]):
                        linha_datas = aba_bruta[row_i]
                        break
                if linha_datas:
                    current_date = ""
                    for col_idx in range(len(headers)):
                        val_data = str(linha_datas[col_idx]).strip() if col_idx < len(linha_datas) else ""
                        match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', val_data)
                        if match: current_date = match.group(0)
                        if current_date and current_date not in str(headers[col_idx]):
                            val_head = str(headers[col_idx]).strip()
                            headers[col_idx] = current_date if val_head in ["", "None", "nan"] else f"{current_date} - {val_head}"

            df_aba = pd.DataFrame(aba_bruta[header_idx+1:], columns=headers)
            df_aba.columns = [str(c).strip() for c in df_aba.columns]
            return df_aba

        try: dfs['sep'] = processar_aba("Relatorio Diario")
        except: pass
        try: dfs['op'] = processar_aba("Relatorio Operador")
        except: pass
        try: dfs['conf'] = processar_aba("Relatorio Diario Conferente")
        except: pass
        try: dfs['aux_jl'] = processar_aba("Aux Absent")
        except: pass
        try: dfs['acomp_jl'] = processar_aba("Acompanhamento JL")
        except: pass
        try: dfs['ponto_t3'] = processar_aba("Ponto T3")
        except: pass

    except Exception as e:
        print(f"Erro ao carregar abas diárias: {e}")
    return dfs['sep'], dfs['op'], dfs['conf'], dfs['aux_jl'], dfs['acomp_jl'], dfs['ponto_t3']

# =============================================================================
# 🚀 CARREGAMENTO E ATUALIZAÇÃO GERAL DO RANKING
# =============================================================================
df = carregar_dados()
df_diario, df_operador, df_conferente, df_aux_jl, df_acomp_jl, df_ponto_t3 = carregar_diarios()

df['Valor Ranking'] = 0.0
df['Posicao Ranking'] = 0
df['Ranking_Categoria'] = "" 

for turno in ['T2', 'T3']:
    for cargo in df['FUNÇÃO'].unique():
        cargo_str = str(cargo).upper()
        df_eq = df[(df['TURNO'] == turno) & (df['FUNÇÃO'] == cargo)].copy()
        if df_eq.empty: continue
        
        kpis = [c.replace('_Racional', '') for c in df_eq.columns if '_Racional' in c]
        if not kpis: continue
        
        if 'SEPARADOR' in cargo_str:
            metrica_rank = next((c for c in df_eq.columns if 'ITENS SEPARADOS' in str(c).upper()), 
                                next((c for c in kpis if 'ITENS' in str(c).upper() and 'RAMPA' not in str(c).upper()), None))
            if not metrica_rank: continue
            df_eq[metrica_rank] = pd.to_numeric(df_eq[metrica_rank], errors='coerce').fillna(0)
            df_eq = df_eq.sort_values(by=metrica_rank, ascending=False)
            
            pos = 1
            for idx, row_eq in df_eq.iterrows():
                if float(row_eq.get(metrica_rank, 0)) <= 0: continue 
                df.at[idx, 'Posicao Ranking'] = pos
                d_corr_rank = float(row_eq.get('Dias Corridos', 0))
                d_trab_rank = float(row_eq.get('Dias Trabalhados', 0))
                prop_rank = min(d_trab_rank / d_corr_rank, 1.0) if d_corr_rank > 0 else 1.0

                if turno == 'T3': val_base = 250.0 if pos == 1 else (200.0 if pos == 2 else (100.0 if pos == 3 else 0.0))
                elif turno == 'T2': val_base = 150.0 if pos == 1 else (100.0 if pos == 2 else (80.0 if pos == 3 else 0.0))
                else: val_base = 0.0
                
                if val_base > 0: df.at[idx, 'Valor Ranking'] += (val_base * prop_rank)
                pos += 1

        elif 'CONFERENTE' in cargo_str and turno == 'T3':
            metrica_rank = next((k for k in kpis if 'ITENS CONF' in k.upper()), None)
            if not metrica_rank: continue
            racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
            df_eq[metrica_rank] = pd.to_numeric(df_eq[metrica_rank], errors='coerce').fillna(0)
            df_eq = df_eq.sort_values(by=metrica_rank, ascending=(racional != 1))
            
            pos = 1
            for idx, row_eq in df_eq.iterrows():
                val_kpi = float(row_eq.get(metrica_rank, 0))
                if val_kpi <= 0: continue
                df.at[idx, 'Posicao Ranking'] = pos
                d_corr_rank = float(row_eq.get('Dias Corridos', 0))
                d_trab_rank = float(row_eq.get('Dias Trabalhados', 0))
                prop_rank = min(d_trab_rank / d_corr_rank, 1.0) if d_corr_rank > 0 else 1.0
                if pos == 1: df.at[idx, 'Valor Ranking'] += (200.0 * prop_rank)
                cat_name = "Grandeza" if "GRANDEZA" in cargo_str else "Fracionado"
                df.at[idx, 'Ranking_Categoria'] = f"{cat_name} ({val_kpi:,.0f})".replace(',', '.')
                pos += 1

        elif 'OPERADOR' in cargo_str and turno == 'T3':
            metrica_rank = next((k for k in kpis if 'MOV' in k.upper()), kpis[0])
            racional = df_eq[f"{metrica_rank}_Racional"].mode()[0] if not df_eq[f"{metrica_rank}_Racional"].empty else 1
            df_eq[metrica_rank] = pd.to_numeric(df_eq[metrica_rank], errors='coerce').fillna(0)
            df_eq = df_eq.sort_values(by=metrica_rank, ascending=(racional != 1))
            
            pos = 1
            for idx, row_eq in df_eq.iterrows():
                if float(row_eq.get(metrica_rank, 0)) <= 0: continue
                df.at[idx, 'Posicao Ranking'] = pos
                d_corr_rank = float(row_eq.get('Dias Corridos', 0))
                d_trab_rank = float(row_eq.get('Dias Trabalhados', 0))
                prop_rank = min(d_trab_rank / d_corr_rank, 1.0) if d_corr_rank > 0 else 1.0
                if pos == 1: df.at[idx, 'Valor Ranking'] += (200.0 * prop_rank)
                pos += 1

colunas_valor = [c for c in df.columns if c.endswith('_Valor')]
df['Valor Final'] = df[colunas_valor].sum(axis=1) + df['Valor Ranking']

# =============================================================================
# 📅 3. LÓGICA DE DATAS E BARRA LATERAL
# =============================================================================
if 'Data Inicio' in df.columns and 'Data Fim' in df.columns and not df['Data Inicio'].dropna().empty:
    dt_inicio = pd.to_datetime(df['Data Inicio'].dropna().iloc[0]).date()
    data_apuracao = pd.to_datetime(df['Data Fim'].dropna().iloc[0]).date()
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)

st.sidebar.markdown(f"👤 **Logado como:** {st.session_state['usuario'].capitalize()} ({st.session_state['perfil']})")
if st.sidebar.button("Sair / Logout", use_container_width=True):
    st.session_state["logado"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("🔍 Filtros do Painel")
ver_jornada = st.sidebar.checkbox("⏱️ Acompanhamento Jornada Líquida (T3)", help="Exibe a matriz de horas diárias dos separadores")

if st.session_state.get("usuario") in ["guilherme", "nilo"]:
    is_fechado = (dt_inicio.day == 26 and data_apuracao.day == 25)
    if is_fechado:
        df_auditoria = []
        kpis_gerais = [c.replace('_Racional', '') for c in df.columns if '_Racional' in c]
        for idx, row in df.iterrows():
            cod, nome, funcao, turno = row.get('CÓD.', ''), row.get('NOME', ''), row.get('FUNÇÃO', ''), row.get('TURNO', '')
            d_corridos = float(row.get('Dias Corridos', 0))
            d_trab = float(row.get('Dias Trabalhados', 0))
            d_meta = float(row.get('Dias Meta', 0))
            funcao_upper = str(funcao).strip().upper()
            
            for kpi in kpis_gerais:
                meta2 = float(row.get(f"{kpi}_Meta2", 0))
                if meta2 > 0:
                    real = float(row.get(kpi, 0))
                    valor = float(row.get(f"{kpi}_Valor", 0))
                    meta1 = float(row.get(f"{kpi}_Meta1", 0))
                    meta3 = float(row.get(f"{kpi}_Meta3", 0))
                    racional = float(row.get(f"{kpi}_Racional", 1))
                    
                    kpi_upper = str(kpi).strip().upper()
                    is_meta_unica = ('DEVOLUÇÃO' in funcao_upper and kpi_upper == 'DEV. %') or (kpi_upper == 'AVARIA')
                    if is_meta_unica:
                        alvo_atual = 0.48 if ('DEVOLUÇÃO' in funcao_upper and kpi_upper == 'DEV. %') else 0.07
                        faixa_meta = "100%" if real <= alvo_atual else "0%"
                        if meta1 <= 0: meta1 = alvo_atual
                        if meta3 <= 0: meta3 = alvo_atual
                    else:
                        if meta1 <= 0: meta1 = meta2
                        if meta3 <= 0: meta3 = meta2
                        if racional == 1: 
                            faixa_meta = "0%" if real < meta1 else ("50%" if real < meta2 else ("100%" if real < meta3 else "120%"))
                        else: 
                            faixa_meta = "0%" if real > meta1 else ("50%" if real > meta2 else ("100%" if real > meta3 else "120%"))
                    
                    def formata(v):
                        if "Tempo" in str(kpi): return f"{int(v)//3600:02d}:{(int(v)%3600)//60:02d}:{(int(v)%60):02d}"
                        elif "LÍQ" in str(kpi).upper(): return f"{v:.1f}%".replace('.', ',')
                        elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi): return f"{v:.2f}%".replace('.', ',')
                        else: return f"{v:,.0f}".replace(',', '.')
                    
                    df_auditoria.append({
                        "CÓD.": cod, "NOME": nome, "TURNO": turno, "FUNÇÃO": funcao,
                        "DIAS CORRIDOS": int(d_corridos), "DIAS TRAB.": int(d_trab), "DIAS META": int(d_meta),
                        "INDICADOR": kpi, "REALIZADO": formata(real), "VALOR GANHO (R$)": valor, "META ATINGIDA": faixa_meta
                    })
            
            pos = int(row.get('Posicao Ranking', 0))
            if pos > 0 and ('SEPARADOR' in funcao_upper or ('CONFERENTE' in funcao_upper and turno == 'T3') or ('OPERADOR' in funcao_upper and turno == 'T3')):
                val_rank = float(row.get('Valor Ranking', 0))
                cat_rank = row.get('Ranking_Categoria', '')
                txt_indicador = f"Ranking ({cat_rank})" if ('CONFERENTE' in funcao_upper and cat_rank) else "Ranking"
                df_auditoria.append({
                    "CÓD.": cod, "NOME": nome, "TURNO": turno, "FUNÇÃO": funcao,
                    "DIAS CORRIDOS": int(d_corridos), "DIAS TRAB.": int(d_trab), "DIAS META": int(d_meta),
                    "INDICADOR": txt_indicador, "REALIZADO": f"{pos}º Lugar", "VALOR GANHO (R$)": val_rank, "META ATINGIDA": "-" if val_rank > 0 else "0%"
                })
        
        df_export = pd.DataFrame(df_auditoria)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Auditoria_Fechamento', header=False, startrow=1)
            workbook, worksheet = writer.book, writer.sheets['Auditoria_Fechamento']
            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
            formato_central = workbook.add_format({'align': 'center'})
            (max_row, max_col) = df_export.shape
            col_settings = [{'header': column} for column in df_export.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': col_settings, 'style': 'Table Style Medium 2'})
            worksheet.set_column('A:A', 10, formato_central) 
            worksheet.set_column('B:B', 38)                  
            worksheet.set_column('C:C', 12, formato_central) 
            worksheet.set_column('D:D', 22)                  
            worksheet.set_column('E:H', 13, formato_central) 
            worksheet.set_column('I:I', 25)                  
            worksheet.set_column('J:J', 15, formato_central) 
            worksheet.set_column('K:K', 20, formato_moeda)   
            worksheet.set_column('L:L', 18, formato_central) 
        
        st.sidebar.download_button(label="📥 Baixar Auditoria", data=buffer.getvalue(), file_name=f"Auditoria_Produtividade_Fechamento.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")
    else:
        st.sidebar.button("🔒 Fechamento (Auditoria)", disabled=True, use_container_width=True, help="A Auditoria é liberada apenas quando o período for exato: do dia 26 ao dia 25.")

turno_logado = st.session_state["turno_acesso"]
if turno_logado == "Todos":
    lista_turnos = ["Todos"] + sorted(df['TURNO'].dropna().unique().tolist())
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy() if turno_selecionado != "Todos" else df.copy()
elif isinstance(turno_logado, list):
    st.sidebar.info(f"🔒 Acesso restrito aos Turnos: **{', '.join(turno_logado)}**")
    lista_turnos = ["Todos Permitidos"] + turno_logado
    turno_selecionado = st.sidebar.selectbox("1. Turno:", lista_turnos)
    df_filtrado = df[df['TURNO'].isin(turno_logado)].copy() if turno_selecionado == "Todos Permitidos" else df[df['TURNO'] == turno_selecionado].copy()
else:
    turno_selecionado = turno_logado
    st.sidebar.info(f"🔒 Acesso restrito ao Turno: **{turno_selecionado}**")
    df_filtrado = df[df['TURNO'] == turno_selecionado].copy()

lista_cargos = ["Todos"] + sorted(df_filtrado['FUNÇÃO'].dropna().unique().tolist())
cargo_selecionado = st.sidebar.selectbox("2. Cargo/Função:", lista_cargos)
if cargo_selecionado != "Todos": df_filtrado = df_filtrado[df_filtrado['FUNÇÃO'] == cargo_selecionado]

lista_pessoas = ["Nenhum"] + sorted(df_filtrado['NOME'].dropna().unique().tolist())
pessoa_selecionada = st.sidebar.selectbox("🎯 Ver Metas do Colaborador:", lista_pessoas)
focar_detratores = st.sidebar.checkbox("🚨 Filtrar Desempenho Abaixo da Meta")

# =============================================================================
# 🗃️ MÓDULO DE EXTRAÇÃO DO RH 
# =============================================================================
if st.session_state["perfil"] == "Gerente":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗃️ Fechamento RH")

    if not df_filtrado.empty:
        potencial_max_list, motivos_list = [], []
        df_aux_jl_clean = df_aux_jl.copy() if (not df_aux_jl.empty and 'NOME' in df_aux_jl.columns) else pd.DataFrame()
        if not df_aux_jl_clean.empty:
            df_aux_jl_clean['NOME_CLEAN'] = df_aux_jl_clean['NOME'].astype(str).str.strip().str.upper()

        kpis_mapeados_rh = [c.replace('_Racional', '') for c in df_filtrado.columns if '_Racional' in c]

        for idx, row in df_filtrado.iterrows():
            nome_str = str(row['NOME']).strip().upper()
            valor_final = row['Valor Final']
            d_trab = int(row.get('Dias Trabalhados', 0))
            cargo_str = str(row['FUNÇÃO']).strip().upper()
            turno_str = str(row['TURNO']).strip().upper()
            
            potencial = 0
            for k in kpis_mapeados_rh:
                if pd.to_numeric(row.get(f"{k}_Meta2", 0), errors='coerce') > 0:
                    v_base = obter_valor_100(row['TURNO'], row['FUNÇÃO'], k)
                    kpi_upper = str(k).strip().upper()
                    is_meta_unica = ('DEVOLUÇÃO' in cargo_str and kpi_upper == 'DEV. %') or (kpi_upper == 'AVARIA')
                    potencial += v_base if is_meta_unica else v_base * 1.2
            
            if 'SEPARADOR' in cargo_str:
                potencial += 250 if turno_str == 'T3' else (150 if turno_str == 'T2' else 0)
            elif 'CONFERENTE' in cargo_str and turno_str == 'T3': potencial += 200
            elif 'OPERADOR' in cargo_str and turno_str == 'T3': potencial += 200
            potencial_max_list.append(potencial)
            
            motivo = "-"
            if valor_final <= 0:
                achou_motivo = False
                if not df_aux_jl_clean.empty:
                    dados_aux = df_aux_jl_clean[df_aux_jl_clean['NOME_CLEAN'] == nome_str]
                    if not dados_aux.empty:
                        linha_aux = dados_aux.iloc[0]
                        valores_aux = [str(v).strip().upper().replace('.', '') for v in linha_aux.values]
                        qtd_fi, qtd_ad, qtd_fe, qtd_at, qtd_nt = valores_aux.count('FI'), valores_aux.count('AD'), valores_aux.count('FE'), valores_aux.count('AT'), valores_aux.count('NT')
                        if qtd_fi > 0 and qtd_ad > 0: motivo, achou_motivo = "Falta Injustif. + Advertência", True
                        elif qtd_fi > 0: motivo, achou_motivo = "Falta Injustificada", True
                        elif qtd_ad > 0: motivo, achou_motivo = "Advertência", True
                        elif qtd_fe > 0: motivo, achou_motivo = "Férias", True
                        elif qtd_at > 0: motivo, achou_motivo = "Atestado", True
                        elif qtd_nt > 0 and d_trab <= 0: motivo, achou_motivo = "Não Trabalhado (NT)", True
                if not achou_motivo:
                    motivo = "Dias Trabalhados Zerados" if d_trab <= 0 else "Não atingiu a meta mínima"
            motivos_list.append(motivo)

        df_rh = df_filtrado[['CÓD.', 'NOME', 'FUNÇÃO', 'TURNO', 'Valor Final']].copy()
        df_rh['Potencial Máx. (R$)'] = potencial_max_list
        df_rh['Motivo'] = motivos_list
        df_rh = df_rh.rename(columns={'CÓD.': 'Matrícula', 'NOME': 'Nome', 'Valor Final': 'Premiação (R$)'})
        df_rh['Premiação (R$)'] = df_rh['Premiação (R$)'].round(2)
        df_rh['Potencial Máx. (R$)'] = df_rh['Potencial Máx. (R$)'].round(2)
        df_rh = df_rh[['Matrícula', 'Nome', 'FUNÇÃO', 'TURNO', 'Potencial Máx. (R$)', 'Premiação (R$)', 'Motivo']].drop_duplicates(subset=['Matrícula', 'Nome']).sort_values(by='Nome')
        
        config_rh = {
            "Matrícula": st.column_config.TextColumn("Matrícula"), 
            "Potencial Máx. (R$)": st.column_config.NumberColumn("Potencial Máx. (R$)", format="R$ %.2f"),
            "Premiação (R$)": st.column_config.NumberColumn("Premiação (R$)", format="R$ %.2f"),
            "Motivo": st.column_config.TextColumn("Motivo (Se Zerado)")
        }
        st.sidebar.dataframe(df_rh, hide_index=True, use_container_width=True, column_config=config_rh)
        
        df_download = df_rh.copy()
        df_download['Premiação (R$)'] = df_download['Premiação (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_download['Potencial Máx. (R$)'] = df_download['Potencial Máx. (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        csv_rh = df_download.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        
        try:
            ultimo_dia = calendar.monthrange(data_apuracao.year, data_apuracao.month)[1]
            data_fim_mes = f"{ultimo_dia:02d}/{data_apuracao.month:02d}/{data_apuracao.year}"
        except: data_fim_mes = dt_inicio.strftime('%d/%m/%Y')
            
        df_rh_sistema = pd.DataFrame({
            'CONTRATO': df_rh['Matrícula'], 'VDB': 2601, 'DESCRIÇÃO VDB': 'Adicional Produtividade',
            'REFERENCIA FOLHA_1': 0, 'VALOR': df_rh['Premiação (R$)'].apply(lambda x: f"{x:.2f}".replace('.', ',')),
            'REFERENCIA FOLHA_2': 11, 'ULTIMO DIA DO MÊS_1': data_fim_mes, 'ULTIMO DIA DO MÊS_2': data_fim_mes
        })
        csv_sistema = df_rh_sistema.to_csv(index=False, header=False, sep=';').encode('utf-8-sig')

        st.sidebar.markdown("<p style='font-size: 14px; margin-bottom: 5px;'>1. Visualização Padrão</p>", unsafe_allow_html=True)
        st.sidebar.download_button(label="📊 Baixar Planilha Visual (Excel)", data=csv_rh, file_name=f"Fechamento_RH_Visual_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv", mime="text/csv", use_container_width=True, key="btn_rh_visual")
        st.sidebar.markdown("<p style='font-size: 14px; margin-bottom: 5px; margin-top: 10px;'>2. Importação do Sistema (Layout Folha)</p>", unsafe_allow_html=True)
        st.sidebar.download_button(label="⚙️ Baixar Arq. do Sistema (.CSV)", data=csv_sistema, file_name=f"Importacao_Sistema_Folha_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv", mime="text/csv", type="primary", use_container_width=True, key="btn_rh_sistema")

# =============================================================================
# 🖥️ 4. RENDERIZAÇÃO DA TELA CENTRAL 
# =============================================================================

# 💡 ACOMPANHAMENTO JL NA TELA CENTRAL COM SOMA E MAIORES INTERVALOS
if ver_jornada:
    st.markdown("## ⏱️ Acompanhamento de Jornada Líquida - Separadores T3")
    
    if df_acomp_jl.empty:
        st.warning("⚠️ A aba 'Acompanhamento JL' não foi encontrada na sua planilha do Google.")
    else:
        idx_header = -1
        for i in range(min(10, len(df_acomp_jl))):
            vals = [str(x).upper().strip() for x in df_acomp_jl.iloc[i].values]
            if "NOME" in vals and "JL" in vals:
                idx_header = i
                break
        
        if idx_header == -1:
            st.warning("⚠️ O formato da aba 'Acompanhamento JL' está incorreto. Não foi possível achar a linha de cabeçalhos (NOME, JL).")
        else:
            datas_indices = {}
            for row_idx in range(idx_header):
                for col_idx, val in enumerate(df_acomp_jl.iloc[row_idx].values):
                    val_str = str(val).strip()
                    match = re.search(r'\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}', val_str)
                    if match:
                        d_str = match.group(0)
                        if '-' in d_str:
                            d_str = datetime.datetime.strptime(d_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        if d_str not in datas_indices:
                            datas_indices[d_str] = col_idx 
            
            colunas_validas = []
            for d_str in datas_indices.keys():
                try:
                    d_obj = datetime.datetime.strptime(d_str, '%d/%m/%Y').date()
                    if dt_inicio <= d_obj <= data_apuracao:
                        colunas_validas.append(d_str)
                except: pass
            
            colunas_validas = sorted(colunas_validas, key=lambda x: datetime.datetime.strptime(x, '%d/%m/%Y'))
            
            if not colunas_validas:
                st.warning(f"⚠️ Nenhuma data válida encontrada na planilha dentro do período de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')}.")
            else:
                col_sel, col_vazia = st.columns([1, 3])
                data_selecionada = col_sel.selectbox("📅 Escolha o dia para analisar:", colunas_validas, index=len(colunas_validas)-1)
                
                idx_col_inicio = datas_indices[data_selecionada]
                headers_vals = [str(x).upper().strip() for x in df_acomp_jl.iloc[idx_header].values]
                
                idx_nome = headers_vals.index("NOME") if "NOME" in headers_vals else -1
                idx_turno = headers_vals.index("TURNO") if "TURNO" in headers_vals else -1
                idx_funcao = headers_vals.index("FUNÇÃO") if "FUNÇÃO" in headers_vals else (headers_vals.index("FUNCAO") if "FUNCAO" in headers_vals else -1)
                idx_cod = headers_vals.index("CÓD.") if "CÓD." in headers_vals else (headers_vals.index("COD") if "COD" in headers_vals else 0)
                
                # Delimita as colunas disponíveis para a data selecionada
                sorted_starts = sorted(datas_indices.values())
                current_idx = sorted_starts.index(idx_col_inicio)
                end_col = sorted_starts[current_idx + 1] if current_idx + 1 < len(sorted_starts) else len(headers_vals)
                search_start = max(0, idx_col_inicio - 1)

                def find_col_in_day(keywords, fallback_offset):
                    for i in range(idx_col_inicio, end_col):
                        if i < len(headers_vals):
                            col_name = str(headers_vals[i]).upper()
                            if any(k in col_name for k in keywords):
                                return i
                    fallback = idx_col_inicio + fallback_offset
                    return fallback if fallback < len(headers_vals) else -1

                idx_jl = find_col_in_day(['JL'], 0)
                idx_ht = find_col_in_day(['HORAS TRAB', 'TRABALHADAS'], 1)
                idx_hs = find_col_in_day(['HORAS SEP', 'SEPARA'], 2)
                idx_qtd = find_col_in_day(['QTD', 'ITENS SEP'], 3)
                idx_kg = find_col_in_day(['KG', 'PESO'], 4)
                idx_ih = find_col_in_day(['ITENS/HORA', 'ITENS HORA'], 5)
                idx_b1 = find_col_in_day(['1º', '1O', 'PRIMEIRO'], 6)
                idx_bu = find_col_in_day(['ULTIMO', 'ÚLTIMO'], 7)
                
                # Buscas separadas para Janta e Intervalos
                idx_tj = find_col_in_day(['JANTA', 'ALMOÇO'], 8)
                idx_si = find_col_in_day(['SOMA', 'SOMATÓRIO'], 9)
                idx_mi = find_col_in_day(['MAIOR', 'MÁXIMO'], 10)
                
                if not df_ponto_t3.empty and any('DATA' in str(c).upper() for c in df_ponto_t3.columns):
                    col_data_ponto = next((c for c in df_ponto_t3.columns if 'DATA' in str(c).upper()), None)
                    df_ponto_t3['DATA_BUSCA'] = df_ponto_t3[col_data_ponto].astype(str).apply(formatar_data_br)
                    col_contrato = next((c for c in df_ponto_t3.columns if 'CONTRATO' in str(c).upper() or 'CÓD' in str(c).upper()), None)
                    df_ponto_t3['CONTRATO_LIMPO'] = df_ponto_t3[col_contrato].astype(str).str.replace('.0', '', regex=False).str.strip() if col_contrato else ""
                    df_ponto_filt = df_ponto_t3[df_ponto_t3['DATA_BUSCA'] == data_selecionada]
                else:
                    df_ponto_filt = pd.DataFrame()

                dados_tabela_jl = []
                soma_jl_flt = 0.0
                qtd_validos = 0
                
                for row_idx in range(idx_header + 1, len(df_acomp_jl)):
                    linha = df_acomp_jl.iloc[row_idx].values
                    
                    nome = str(linha[idx_nome]).strip() if idx_nome != -1 and idx_nome < len(linha) else ""
                    funcao = str(linha[idx_funcao]).strip().upper() if idx_funcao != -1 and idx_funcao < len(linha) else ""
                    turno = str(linha[idx_turno]).strip().upper() if idx_turno != -1 and idx_turno < len(linha) else ""
                    cod = str(linha[idx_cod]).replace('.0', '').strip() if idx_cod < len(linha) else ""
                    
                    if not nome or nome in ["nan", "None", "NOME"] or "SEPARADOR" not in funcao or "T3" not in turno:
                        continue
                        
                    jl_val = str(linha[idx_jl]).strip() if idx_jl != -1 else "0"
                    ht_val = str(linha[idx_ht]).strip() if idx_ht != -1 else "00:00:00"
                    hs_val = str(linha[idx_hs]).strip() if idx_hs != -1 else "00:00:00"
                    qtd_val = str(linha[idx_qtd]).strip() if idx_qtd != -1 else "0"
                    kg_val = str(linha[idx_kg]).strip() if idx_kg != -1 else "0"
                    ih_val = str(linha[idx_ih]).strip() if idx_ih != -1 else "0"
                    b1_val = str(linha[idx_b1]).strip() if idx_b1 != -1 else "00:00:00"
                    bu_val = str(linha[idx_bu]).strip() if idx_bu != -1 else "00:00:00"
                    tj_val = str(linha[idx_tj]).strip() if idx_tj != -1 else "00:00:00"
                    
                    si_val = str(linha[idx_si]).strip() if idx_si != -1 else "00:00:00"
                    mi_val = str(linha[idx_mi]).strip() if idx_mi != -1 else "00:00:00"
                    
                    try:
                        v_num = float(jl_val.replace('%', '').replace(',', '.'))
                        if v_num <= 2.0 and '%' not in jl_val: v_num *= 100
                        jl_float = v_num
                        if jl_float > 0:
                            soma_jl_flt += jl_float
                            qtd_validos += 1
                    except: jl_float = 0.0
                    
                    try: qtd_int = int(float(qtd_val.replace('.', '').replace(',', '.')))
                    except: qtd_int = 0
                    
                    try: kg_float = float(kg_val.replace('.', '').replace(',', '.'))
                    except: kg_float = 0.0
                    
                    try: ih_float = float(ih_val.replace('.', '').replace(',', '.'))
                    except: ih_float = 0.0
                    
                    ht_format = parse_time(ht_val)
                    hs_format = parse_time(hs_val)
                    b1_format = parse_time(b1_val)
                    bu_format = parse_time(bu_val)
                    tj_format = parse_time(tj_val)
                    si_format = parse_time(si_val)
                    mi_format = parse_time(mi_val)
                    
                    # Resgate no Ponto T3
                    if (ht_format in ["00:00:00", "—"]) and not df_ponto_filt.empty:
                        row_ponto = df_ponto_filt[df_ponto_filt['CONTRATO_LIMPO'] == cod]
                        if row_ponto.empty and nome:
                            primeiro_nome = nome.split()[0].upper()
                            col_nome_ponto = next((c for c in df_ponto_filt.columns if 'NOME' in str(c).upper()), None)
                            if col_nome_ponto:
                                row_ponto = df_ponto_filt[df_ponto_filt[col_nome_ponto].astype(str).str.upper().str.contains(primeiro_nome)]
                        if not row_ponto.empty:
                            col_jornada = next((c for c in row_ponto.columns if 'JORNADA' in str(c).upper() or 'TRAB' in str(c).upper()), None)
                            if col_jornada:
                                p_jornada = str(row_ponto.iloc[0][col_jornada]).strip()
                                if p_jornada not in ["", "nan", "None", "0", "00:00:00"]:
                                    ht_format = parse_time(p_jornada)
                    
                    if jl_float == 0.0 and ht_format == "00:00:00" and hs_format == "00:00:00" and qtd_int == 0:
                        continue
                        
                    dados_tabela_jl.append({
                        "Nome": nome,
                        "Jornada Líquida (%)": jl_float, 
                        "Horas Trabalhadas": ht_format,
                        "Horas Separação": hs_format,
                        "Qtd Itens": qtd_int,
                        "KG": kg_float,
                        "Itens/Hora": ih_float,
                        "1º Bipe": b1_format,
                        "Último Bipe": bu_format,
                        "Tempo Janta": tj_format,
                        "Soma Intervalos": si_format,
                        "Maior Intervalo": mi_format
                    })
                    
                if dados_tabela_jl:
                    df_display = pd.DataFrame(dados_tabela_jl)
                    
                    st.markdown("#### 🔍 Filtrar e Ordenar")
                    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
                    busca_texto = col_f1.text_input("Buscar Nome:", "", placeholder="Digite para pesquisar...")
                    jl_min = col_f2.number_input("Ocultar abaixo de (%):", min_value=0, max_value=200, value=0)
                    ordenacao = col_f3.selectbox("Ordenar Tabela por:", ["Ordem Decrescente (Maior JL)", "Ordem Crescente (Menor JL)", "Nome (A-Z)"])
                    
                    if busca_texto: df_display = df_display[df_display['Nome'].str.contains(busca_texto, case=False, na=False)]
                    if jl_min > 0: df_display = df_display[df_display['Jornada Líquida (%)'] >= jl_min]
                        
                    if ordenacao == "Ordem Crescente (Menor JL)": df_display = df_display.sort_values(by="Jornada Líquida (%)", ascending=True)
                    elif ordenacao == "Ordem Decrescente (Maior JL)": df_display = df_display.sort_values(by="Jornada Líquida (%)", ascending=False)
                    elif ordenacao == "Nome (A-Z)": df_display = df_display.sort_values(by="Nome", ascending=True)

                    media_equipe = (soma_jl_flt / qtd_validos) if qtd_validos > 0 else 0
                    st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 8px; border-left: 5px solid {C_VERDE}; margin-bottom: 20px;'><h4 style='margin:0; color: #888;'>Média de Jornada Líquida da Equipe (T3)</h4><h2 style='margin:0; color: {C_VERDE};'>{media_equipe:.1f}%</h2></div>", unsafe_allow_html=True)
                    
                    if df_display.empty:
                        st.warning("⚠️ Nenhum colaborador encontrado com esses filtros.")
                    else:
                        html_tabela = """
                        <style>
                        .tabela-jl { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 18px; color: #ffffff; font-weight: bold; }
                        .tabela-jl th { background-color: rgba(59, 130, 246, 0.2); padding: 14px 15px; text-align: left; border-bottom: 2px solid #3b82f6; color: #ffffff; font-size: 16px; font-weight: 800; white-space: nowrap; }
                        .tabela-jl td { padding: 12px 15px; border-bottom: 1px solid rgba(255,255,255,0.08); }
                        .tabela-jl tr:hover { background-color: rgba(255,255,255,0.05); }
                        </style>
                        <table class="tabela-jl">
                            <tr>
                                <th>Nome</th>
                                <th>Jornada Líquida (%)</th>
                                <th>Horas Trabalhadas</th>
                                <th>Horas Separação</th>
                                <th>Qtd Itens</th>
                                <th>KG</th>
                                <th>Itens/Hora</th>
                                <th>1º Bipe</th>
                                <th>Último Bipe</th>
                                <th>Tempo Janta</th>
                                <th>Soma Intervalos</th>
                                <th>Maior Intervalo</th>
                            </tr>
                        """
                        
                        for index, row_disp in df_display.iterrows():
                            jl_formatado = f"{row_disp['Jornada Líquida (%)']:.1f}%".replace('.', ',')
                            qtd_formatado = f"{int(row_disp['Qtd Itens'])}"
                            kg_formatado = f"{row_disp['KG']:.2f}".replace('.', ',')
                            ih_formatado = f"{row_disp['Itens/Hora']:.2f}".replace('.', ',')
                            
                            html_tabela += f"""<tr>
                                <td>{row_disp['Nome']}</td>
                                <td><span style='color: #2ecc71; font-size: 20px; font-weight: 900;'>{jl_formatado}</span></td>
                                <td>{row_disp['Horas Trabalhadas']}</td>
                                <td>{row_disp['Horas Separação']}</td>
                                <td>{qtd_formatado}</td>
                                <td>{kg_formatado}</td>
                                <td>{ih_formatado}</td>
                                <td style='color: #ffca28;'>{row_disp['1º Bipe']}</td>
                                <td style='color: #ffca28;'>{row_disp['Último Bipe']}</td>
                                <td style='color: #ef4444;'>{row_disp['Tempo Janta']}</td>
                                <td style='color: #ef4444;'>{row_disp['Soma Intervalos']}</td>
                                <td style='color: #ef4444;'>{row_disp['Maior Intervalo']}</td>
                            </tr>"""
                            
                        html_tabela += "</table><br><br>"
                        st.markdown(html_tabela, unsafe_allow_html=True)
                else:
                    st.info(f"Não houve operação de separação na data {data_selecionada}.")

# 💡 DASHBOARD NORMAL
else:
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

        # =============================================================================
        # 🚨 MÓDULO DETRATORES 
        # =============================================================================
        if focar_detratores:
            st.markdown("## 🚨 Plano de Atuação: Operadores Abaixo do Esperado")
            houve_detrator = False

            for idx, row in df_filtrado.iterrows():
                detalhes_gargalo = []
                cargo_c = str(row['FUNÇÃO']).strip().upper()
                
                for kpi in kpis_mapeados:
                    meta2 = row.get(f"{kpi}_Meta2", 0)
                    if pd.isna(meta2) or str(meta2).strip() in ['0', '0.0', '-', '']: continue
                    
                    realizado = float(row.get(kpi, 0))
                    racional = float(row.get(f"{kpi}_Racional", 1))
                    meta1 = float(row.get(f"{kpi}_Meta1", meta2))

                    if racional == 1 and realizado == 0: continue 
                    
                    kpi_upper = str(kpi).strip().upper()
                    is_meta_unica = ('DEVOLUÇÃO' in cargo_c and kpi_upper == 'DEV. %') or (kpi_upper == 'AVARIA')
                    
                    abaixo_da_meta = False
                    if is_meta_unica:
                        alvo_atual = 0.48 if ('DEVOLUÇÃO' in cargo_c and kpi_upper == 'DEV. %') else 0.07
                        if realizado > alvo_atual:
                            abaixo_da_meta = True
                            meta1 = alvo_atual 
                    else:
                        if racional == 1 and realizado < meta1: abaixo_da_meta = True
                        elif racional == 0 and realizado > meta1: abaixo_da_meta = True

                    if abaixo_da_meta:
                        if "LÍQ" in str(kpi).upper(): detalhes_gargalo.append(f"❌ {kpi}: {realizado:.1f}% vs Alvo Mínimo (Meta 1) {meta1:.1f}%")
                        elif "%" in kpi or "Avaria" in kpi or "Corte" in kpi or "Dev" in kpi: detalhes_gargalo.append(f"❌ {kpi}: {realizado:.2f}% vs Alvo Mínimo (Meta 1) {meta1:.2f}%")
                        else: detalhes_gargalo.append(f"❌ {kpi}: {realizado:,.0f} vs Alvo Mínimo (Meta 1) {meta1:,.0f}".replace(',', '.'))

                if detalhes_gargalo:
                    houve_detrator = True
                    nome_c, cod_c, turno_c = row['NOME'], row['CÓD.'], row['TURNO']
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
                                                gestor = st.session_state["usuario"].capitalize()
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
                                            gestor = st.session_state["usuario"].capitalize()
                                            aba_rh.append_row([agora, str(cod_c), nome_c, "Reciclagem", motivo, gestor])
                                            st.success("📧 Enviado!")
                                        except Exception as e: st.error(f"Erro: {e}")
                        st.markdown("<br>", unsafe_allow_html=True)

            if not houve_detrator: st.success("🎉 Nenhum detrator encontrado! Operação saudável.")

        # =============================================================================
        # 👤 VISÃO INDIVIDUAL DO COLABORADOR 
        # =============================================================================
        elif pessoa_selecionada != "Nenhum":
            st.subheader(f"🎯 Atingimento: {pessoa_selecionada}")
            dados_pessoa = df_filtrado[df_filtrado['NOME'] == pessoa_selecionada]

            if not dados_pessoa.empty:
                row = dados_pessoa.iloc[0]
                d_corridos_p = int(row.get('Dias Corridos', 0))
                d_trab_p = int(row.get('Dias Trabalhados', 0))
                d_meta_p = int(row.get('Dias Meta', 0))
                pos = int(row.get('Posicao Ranking', 0))
                val_rank = row.get('Valor Ranking', 0)
                cargo_p = str(row.get('FUNÇÃO', '')).strip().upper()
                turno_p = str(row.get('TURNO', '')).strip().upper()
                
                if d_trab_p < d_corridos_p and d_corridos_p > 0:
                    proporcao_tela = (d_trab_p / d_corridos_p) * 100
                    st.markdown(f"<div style='background-color: rgba(255, 202, 40, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {C_AMARELO}; font-size: 16px; color: {C_AMARELO};'>ℹ️ <b>Atenção (Proporcionalidade):</b> Colaborador atuou <b>{d_trab_p}</b> de <b>{d_corridos_p}</b> dias corridos. Os prêmios foram calculados com proporção de <b>{proporcao_tela:.1f}%</b> do valor integral.</div>", unsafe_allow_html=True)
                    
                ocorrencias_texto = []
                if not df_aux_jl.empty and 'NOME' in df_aux_jl.columns:
                    df_aux_jl['NOME_CLEAN'] = df_aux_jl['NOME'].astype(str).str.strip().str.upper()
                    dados_aux = df_aux_jl[df_aux_jl['NOME_CLEAN'] == str(pessoa_selecionada).strip().upper()]
                    if not dados_aux.empty:
                        linha_aux = dados_aux.iloc[0]
                        valores_aux = [str(v).strip().upper().replace('.', '') for v in linha_aux.values]
                        qtd_nt, qtd_fc, qtd_fe, qtd_at, qtd_fi, qtd_ad = valores_aux.count('NT'), valores_aux.count('FC'), valores_aux.count('FE'), valores_aux.count('AT'), valores_aux.count('FI'), valores_aux.count('AD')
                        qtd_sa, qtd_fb, qtd_aa = valores_aux.count('SA'), valores_aux.count('FB'), valores_aux.count('AA')
                        if qtd_nt > 0: ocorrencias_texto.append(f"🛑 <b>{qtd_nt}</b> dia(s) Não Trabalhado(s) (NT)")
                        if qtd_fc > 0: ocorrencias_texto.append(f"🔄 <b>{qtd_fc}</b> Folga(s) Compensada(s) (FC)")
                        if qtd_fe > 0: ocorrencias_texto.append(f"🌴 <b>{qtd_fe}</b> dia(s) de Férias (FE)")
                        if qtd_at > 0: ocorrencias_texto.append(f"🏥 <b>{qtd_at}</b> dia(s) de Atestado (AT)")
                        if qtd_fi > 0: ocorrencias_texto.append(f"❌ <b>{qtd_fi}</b> Falta(s) Injustificada(s) (FI)")
                        if qtd_ad > 0: ocorrencias_texto.append(f"⚠️ <b>{qtd_ad}</b> dia(s) de Suspensão/Advertência (AD)")
                        if qtd_sa > 0: ocorrencias_texto.append(f"⏱️ <b>{qtd_sa}</b> Saída(s) Antecipada(s) (SA)")
                        if qtd_fb > 0: ocorrencias_texto.append(f"🏦 <b>{qtd_fb}</b> Folga(s) Banco (FB)")
                        if qtd_aa > 0: ocorrencias_texto.append(f"🛠️ <b>{qtd_aa}</b> dia(s) em Atividade Auxiliar (AA)")
                
                if ocorrencias_texto:
                    st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {C_VERMELHO}; font-size: 15px; color: #e0e0e0;'><b>📋 Impacto no Pagamento (Redução de Dias Trabalhados):</b><br><div style='margin-top: 5px; line-height: 1.6;'>{'<br>'.join(ocorrencias_texto)}</div></div>", unsafe_allow_html=True)
                
                erros_qtd = int(row.get('ERROS', 0))
                penalidade_txt = str(row.get('Penalidade_Texto', ''))
                if erros_qtd > 0 and ('SEPARADOR' in cargo_p or 'OPERADOR' in cargo_p):
                    st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid #ef4444; font-size: 16px; color: #ef4444;'>⚠️ <b>Penalidade de Qualidade:</b> Foram identificados <b>{erros_qtd} erro(s)</b>, resultando num desconto de <b>{penalidade_txt}</b> já aplicado nos seus totais pelo Excel.</div>", unsafe_allow_html=True)
                
                is_ranking_cargo = ('SEPARADOR' in cargo_p or ('CONFERENTE' in cargo_p and turno_p == 'T3') or ('OPERADOR' in cargo_p and turno_p == 'T3'))
                if is_ranking_cargo:
                    funcao_original = row.get('FUNÇÃO', '')
                    cat_rank = str(row.get('Ranking_Categoria', '')).strip()
                    texto_funcao_rank = f"{funcao_original} <br><span style='font-size: 15px; color: #ffca28; font-weight: normal;'>📊 {cat_rank}</span>" if (cat_rank and 'CONFERENTE' in cargo_p) else funcao_original
                    total_eq = len(df_filtrado[(df_filtrado['TURNO'] == row.get('TURNO')) & (df_filtrado['FUNÇÃO'] == funcao_original)])
                    medalha, cor_rank = ("🥇", "#ffd700") if pos == 1 else (("🥈", "#c0c0c0") if pos == 2 else (("🥉", "#cd7f32") if pos == 3 else ("🏅", "#555555")))
                    val_rank_str = f"{val_rank:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    texto_premio_rank = f" | <span style='color: #2ecc71;'><b>💰 Prêmio Ranking: R$ {val_rank_str}</b></span>" if val_rank > 0 else " | <span style='color: #888;'><b>Premiação: R$ 0,00</b></span>"
                    txt_posicao = f"<b>{medalha} Posição:</b> {pos}º lugar de {total_eq}" if pos > 0 else f"<b>{medalha} Análise da Equipe</b> ({total_eq} pessoas)"
                    st.markdown(f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'>{txt_posicao} na função de {texto_funcao_rank}{texto_premio_rank}</div>", unsafe_allow_html=True)

                cols_meta = st.columns(4) 
                col_idx = 0
                grafico_dados = []

                for kpi in kpis_mapeados:
                    meta2 = row.get(f"{kpi}_Meta2", 0)
                    try: meta2_val = float(meta2)
                    except: meta2_val = 0
                    if meta2_val <= 0: continue

                    realizado = float(row.get(kpi, 0))
                    meta1, meta3 = float(row.get(f"{kpi}_Meta1", 0)), float(row.get(f"{kpi}_Meta3", 0))
                    racional = float(row.get(f"{kpi}_Racional", 1))
                    valor_reais = float(row.get(f"{kpi}_Valor", 0))

                    kpi_upper = str(kpi).strip().upper()
                    is_meta_unica = ('DEVOLUÇÃO' in cargo_p and kpi_upper == 'DEV. %') or (kpi_upper == 'AVARIA')

                    if is_meta_unica:
                        alvo_atual = 0.48 if ('DEVOLUÇÃO' in cargo_p and kpi_upper == 'DEV. %') else 0.07
                        nome_alvo = "Meta Única"
                        cor, icone, status = (C_VERDE, "🟢", "Atingiu") if realizado <= alvo_atual else (C_VERMELHO, "🔴", "Abaixo")
                        real_perc = 100.0 if realizado <= alvo_atual else ((alvo_atual / realizado * 100) if realizado > 0 else 0)
                    else:
                        if racional == 1: 
                            perc_atingimento = (realizado / meta2_val) if meta2_val > 0 else 0
                            alvo_atual, nome_alvo = (meta1, "Meta 1") if realizado < meta1 else ((meta2_val, "Meta 2") if realizado < meta2_val else ((meta3, "Meta 3") if realizado < meta3 else (meta3, "Meta Máx")))
                            cor, icone, status = (C_AZUL, "🔵", "Superou") if realizado >= meta3 else ((C_VERDE, "🟢", "Atingiu") if realizado >= meta2_val else ((C_AMARELO, "🟡", "Parcial") if realizado >= meta1 else (C_VERMELHO, "🔴", "Abaixo")))
                        else: 
                            perc_atingimento = (meta2_val / realizado) if realizado > 0 else 1.2
                            alvo_atual, nome_alvo = (meta1, "Meta 1") if realizado > meta1 else ((meta2_val, "Meta 2") if realizado > meta2_val else ((meta3, "Meta 3") if realizado > meta3 else (meta3, "Meta Máx")))
                            cor, icone, status = (C_AZUL, "🔵", "Superou") if realizado <= meta3 else ((C_VERDE, "🟢", "Atingiu") if realizado <= meta2_val else ((C_AMARELO, "🟡", "Parcial") if realizado <= meta1 else (C_VERMELHO, "🔴", "Abaixo")))
                        real_perc = perc_atingimento * 100
                    
                    grafico_dados.append({'Indicador': f"<b>{kpi}</b>", 'Atingimento (%)': min(real_perc, 120), 'Real': real_perc, 'Cor_Barra': cor})
                    html_tabela_premios = ""
                    v_100_base = obter_valor_100(turno_p, cargo_p, kpi)
                    
                    if v_100_base > 0:
                        if is_meta_unica:
                            v_unica_str = f"{v_100_base:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            html_tabela_premios = f"""<div style='margin-top: 15px; padding: 12px; background-color: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);'><div style='margin-bottom: 8px; color: #ffffff; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;'>💰 Tabela da Métrica (Mês Integral)</div><div style='display: flex; justify-content: center; font-size: 15px; color: #e0e0e0; font-weight: bold;'><div style='text-align: center;'>Meta Única<br><span style='color: #2ecc71; font-size: 17px;'>R$ {v_unica_str}</span></div></div></div>"""
                        else:
                            v_m1, v_m2, v_m3 = v_100_base * 0.5, v_100_base * 1.0, v_100_base * 1.2
                            v_m1_str, v_m2_str, v_m3_str = f"{v_m1:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), f"{v_m2:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), f"{v_m3:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            html_tabela_premios = f"""<div style='margin-top: 15px; padding: 12px; background-color: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);'><div style='margin-bottom: 8px; color: #ffffff; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;'>💰 Tabela da Métrica (Mês Integral)</div><div style='display: flex; justify-content: space-between; font-size: 15px; color: #e0e0e0; font-weight: bold;'><div style='text-align: center;'>Meta 1<br><span style='color: #ffca28; font-size: 17px;'>R$ {v_m1_str}</span></div><div style='text-align: center;'>Meta 2<br><span style='color: #2ecc71; font-size: 17px;'>R$ {v_m2_str}</span></div><div style='text-align: center;'>Meta Máx<br><span style='color: #3b82f6; font-size: 17px;'>R$ {v_m3_str}</span></div></div></div>"""
                    
                    html_dinheiro = ""
                    val_adquirido_str = f"{valor_reais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    txt_prop = " (Proporcional)" if (d_corridos_p > 0 and d_trab_p < d_corridos_p) else ""
                    if valor_reais > 0:
                        html_dinheiro = f"<div style='margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: #2ecc71; font-size: 15px;'>💵 Conquistado{txt_prop}: <b>R$ {val_adquirido_str}</b></span></div>"
                    elif v_100_base > 0:
                        html_dinheiro = f"<div style='margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: #ef4444; font-size: 15px;'>💵 Conquistado{txt_prop}: <b>R$ 0,00</b></span></div>"

                    if "Tempo" in str(kpi) or ":" in str(realizado):
                        val_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                        alvo_tela = f"{int(alvo_atual)//3600:02d}:{(int(alvo_atual)%3600)//60:02d}:{(int(alvo_atual)%60):02d}" if meta2_val > 0 else "-"
                    elif "LÍQ" in str(kpi).upper():
                        val_tela = f"{realizado:.1f}%".replace('.', ',')
                        alvo_tela = f"{alvo_atual:.1f}%".replace('.', ',') if meta2_val > 0 else "-"
                    elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi):
                        val_tela = f"{realizado:.2f}%".replace('.', ',')
                        alvo_tela = f"{alvo_atual:.2f}%".replace('.', ',') if meta2_val > 0 else "-"
                    else:
                        val_tela = f"{realizado:,.0f}".replace(',', '.')
                        alvo_tela = f"{alvo_atual:,.0f}".replace(',', '.') if meta2_val > 0 else "-"

                    alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {t_tela}</span>"
                    aviso_erro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; font-size: 14px;'>⚠️ <b>{erros_qtd} Erro(s):</b> {penalidade_txt}</div>" if (erros_qtd > 0 and (('SEPARADOR' in cargo_p and 'ITENS' in str(kpi).upper() and 'RAMPA' not in str(kpi).upper()) or ('OPERADOR' in cargo_p and 'MOV' in str(kpi).upper()))) else ""

                    with cols_meta[col_idx % 4]:
                        st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{kpi}</div><div class='texto-card-principal'>{val_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div>{html_tabela_premios}{html_dinheiro}{aviso_erro}</div>", unsafe_allow_html=True)
                    col_idx += 1

                valor_final_total = row.get('Valor Final', 0)
                if valor_final_total > 0:
                    val_tot_str = f"{valor_final_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.success(f"💰 **Premiação Variável Acumulada TOTAL Validada:** R$ {val_tot_str}")
                st.divider()

                nome_c = row.get('NOME', pessoa_selecionada)
                cod_c = row.get('CÓD.', '')
                st.markdown(f"### 🗣️ Ações de Gestão: {nome_c}")
                col_feed_ind, col_trein_ind = st.columns(2) 
                
                with col_feed_ind:
                    with st.expander(f"💬 Registrar Feedback"):
                        with st.form(key=f"form_feed_ind_{cod_c}"):
                            texto_feedback = st.text_area("Descreva o que foi conversado (Elogios, Alinhamentos, etc):")
                            if st.form_submit_button("Salvar no Histórico"):
                                if texto_feedback:
                                    try:
                                        aba_rh = conectar_planilha().worksheet("Historico_RH")
                                        agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                        gestor = st.session_state["usuario"].capitalize() 
                                        aba_rh.append_row([agora, str(cod_c), nome_c, "Feedback", texto_feedback, gestor])
                                        st.success("✅ Salvo!")
                                    except Exception as e: st.error(f"Erro: {e}")
                                else: st.error("⚠️ Digite algo.")
                
                with col_trein_ind:
                    with st.expander(f"🎯 Solicitar Reciclagem"):
                        with st.form(key=f"form_trein_ind_{cod_c}"):
                            motivo = st.selectbox("Motivo/Gargalo:", ["Velocidade", "Erros/Avarias", "Sistema", "Processo", "Comportamental", "Outros"])
                            if st.form_submit_button("Enviar Solicitação"):
                                try:
                                    aba_rh = conectar_planilha().worksheet("Historico_RH")
                                    agora = (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
                                    gestor = st.session_state["usuario"].capitalize() 
                                    aba_rh.append_row([agora, str(cod_c), nome_c, "Reciclagem", motivo, gestor])
                                    st.success("📧 Enviado!")
                                except Exception as e: st.error(f"Erro: {e}")

                st.divider()
                st.markdown(f"### 📊 Análise de {pessoa_selecionada}")
                col_grafico, col_tabelas_frequencia = st.columns([1.2, 1])
                
                with col_grafico:
                    if grafico_dados:
                        df_grafico = pd.DataFrame(grafico_dados)
                        df_grafico['Texto_Cor'] = df_grafico['Cor_Barra'].apply(lambda color: "black" if color == C_AMARELO else "white")
                        fig = px.bar(df_grafico, x='Indicador', y='Atingimento (%)', text=df_grafico['Real'].apply(lambda x: f"<b>{x:.1f}%</b>"))
                        fig.update_layout(showlegend=False, yaxis_title="<b>% do Volume Total</b>", xaxis_title=None, plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(t=15, b=0, l=0, r=0))
                        fig.add_hline(y=100, line_dash="dash", line_color="lightgray", annotation_text="<b>Meta 100%</b>", annotation_font_color="lightgray")
                        fig.update_traces(textfont=dict(size=24, color=df_grafico['Texto_Cor'].tolist()), marker=dict(color=df_grafico['Cor_Barra'].tolist(), line=dict(color='white', width=1)))
                        fig.update_xaxes(tickfont=dict(size=20, color="lightgray", family="Arial Black"))
                        fig.update_yaxes(tickfont=dict(size=14, color="lightgray"), title_font=dict(color="lightgray"))
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.info("Nenhum indicador com meta estabelecida para gerar o gráfico.")
                
                with col_tabelas_frequencia:
                    cargo_p = str(row.get('FUNÇÃO', '')).upper()
                    usa_diario = ("SEPARADOR" in cargo_p) or ("OPERADOR" in cargo_p) or ("CONFERENTE" in cargo_p)
                    df_uso_diario = df_diario if "SEPARADOR" in cargo_p else (df_operador if "OPERADOR" in cargo_p else df_conferente)

                    if usa_diario and not df_uso_diario.empty:
                        df_uso_diario['NOME_CLEAN'] = df_uso_diario['NOME'].astype(str).str.strip().str.upper()
                        df_pessoa_diario = df_uso_diario[df_uso_diario['NOME_CLEAN'] == str(pessoa_selecionada).strip().upper()]
                        
                        if not df_pessoa_diario.empty:
                            pessoa_d_row = df_pessoa_diario.iloc[0]
                            cols_datas_reais, opces_datas, datas_vistas = [], [], set()
                            
                            for c in df_uso_diario.columns:
                                c_str = str(c).strip()
                                if any(k in c_str.upper() for k in ["INICIO", "NOME", "CÓD", "TURNO", "FUNÇÃO"]): continue
                                match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', c_str)
                                if match:
                                    d_str = match.group(0)
                                    if d_str not in datas_vistas:
                                        datas_vistas.add(d_str)
                                        cols_datas_reais.append(c_str) 
                                        if '-' in d_str:
                                            ano, mes, dia = d_str.split('-')
                                            opces_datas.append(f"{dia}/{mes}/{ano}")
                                        else: opces_datas.append(d_str)
                            
                            if cols_datas_reais:
                                st.markdown("#### 📅 Detalhamento Diário")
                                data_escolhida_display = st.selectbox("Data Apuração", opces_datas, label_visibility="collapsed", key="sel_data_diario_alinhado")
                                idx_escolha = opces_datas.index(data_escolhida_display)
                                nome_coluna_real = cols_datas_reais[idx_escolha]
                                col_index = list(df_uso_diario.columns).index(nome_coluna_real)
                                
                                val_1 = str(pessoa_d_row.iloc[col_index]).strip() if col_index < len(pessoa_d_row) else "0"
                                val_2 = str(pessoa_d_row.iloc[col_index + 1]).strip() if col_index + 1 < len(pessoa_d_row) else "0"
                                val_3 = str(pessoa_d_row.iloc[col_index + 2]).strip() if col_index + 2 < len(pessoa_d_row) else "0"
                                val_4 = str(pessoa_d_row.iloc[col_index + 3]).strip() if col_index + 3 < len(pessoa_d_row) else "0"
                                
                                if "SEPARADOR" in cargo_p:
                                    try:
                                        v_num = float(val_4.replace(',', '.').replace('%', '')) if (val_4 and val_4.lower() not in ['nan', 'none']) else 0
                                        if v_num <= 2.0 and "%" not in val_4: v_num *= 100
                                        jl_display = f"{v_num:.1f}%".replace('.', ',') 
                                    except: jl_display = "0,0%"
                                    try: v_itens = f"{float(val_1.replace('.', '').replace(',', '.')):,.0f}".replace(',', '.')
                                    except: v_itens = "0"
                                    try: v_veloc = f"{int(round(float(val_3.replace('.', '').replace(',', '.'))))}"
                                    except: v_veloc = "0"
                                    try:
                                        h_dec = float(val_2.replace('.', '').replace(',', '.'))
                                        h, rem = int(h_dec), int((h_dec - int(h_dec)) * 60)
                                        s = int((((h_dec - h) * 60) - rem) * 60)
                                        v_horas = f"{h:02d}:{rem:02d}:{s:02d}"
                                    except: v_horas = "00:00:00"
                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("⏱️ Horas", v_horas)
                                    c2.metric("⚡ Itens/Hora", v_veloc)
                                    c3.metric("🎯 JL", jl_display)
                                    st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>Itens Separados</h4><h2 style='margin:0; color: {C_AZUL};'>{v_itens}</h2></div>", unsafe_allow_html=True)
                                elif "CONFERENTE" in cargo_p:
                                    try: v_frac = f"{float(val_1.replace('.', '').replace(',', '.')):,.0f}".replace(',', '.')
                                    except: v_frac = "0"
                                    try: v_grand = f"{float(val_2.replace('.', '').replace(',', '.')):,.0f}".replace(',', '.')
                                    except: v_grand = "0"
                                    c1, c2 = st.columns(2)
                                    with c1: st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Fracionado</h4><h2 style='margin:0; color: {C_AZUL};'>{v_frac}</h2></div>", unsafe_allow_html=True)
                                    with c2: st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Grandeza</h4><h2 style='margin:0; color: {C_VERDE};'>{v_grand}</h2></div>", unsafe_allow_html=True)
                                elif "OPERADOR" in cargo_p:
                                    try: v_horiz = f"{float(val_1.replace('.', '').replace(',', '.')):,.0f}".replace(',', '.')
                                    except: v_horiz = "0"
                                    try: v_vert = f"{float(val_2.replace('.', '').replace(',', '.')):,.0f}".replace(',', '.')
                                    except: v_vert = "0"
                                    c1, c2 = st.columns(2)
                                    with c1: st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↔️ Mov. Horizontal</h4><h2 style='margin:0; color: {C_AZUL};'>{v_horiz}</h2></div>", unsafe_allow_html=True)
                                    with c2: st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↕️ Mov. Vertical</h4><h2 style='margin:0; color: {C_VERDE};'>{v_vert}</h2></div>", unsafe_allow_html=True)

                    kpis_ativos_pessoa = [k for k in kpis_mapeados if pd.to_numeric(row.get(f"{k}_Meta2", 0), errors='coerce') > 0]
                    extras_ind = [c for c in df_filtrado.columns if 'ITENS SEPARADOS' in str(c).upper() and c not in kpis_ativos_pessoa]
                    extras_erros = [c for c in df_filtrado.columns if 'ERROS' in str(c).upper() and c not in kpis_ativos_pessoa and c not in extras_ind]
                    col_uteis = ['CÓD.', 'NOME', 'FUNÇÃO', 'Dias Corridos', 'Dias Trabalhados', 'Dias Meta', 'Valor Final'] + extras_ind + extras_erros + kpis_ativos_pessoa
                    df_tabela_mini = dados_pessoa[[c for c in col_uteis if c in df_filtrado.columns]].copy()
                    
                    if 'Tempo Médio' in df_tabela_mini.columns:
                        df_tabela_mini['Tempo Médio'] = df_tabela_mini['Tempo Médio'].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if pd.notna(s) else "00:00:00")
                    
                    config_colunas = {'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")}
                    for col in df_tabela_mini.columns:
                        if col in ['CÓD.', 'NOME', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim', 'Valor Final']: continue 
                        elif "LÍQ" in col.upper(): config_colunas[col] = st.column_config.NumberColumn(col, format="%.1f%%")
                        elif "%" in col or "Avaria" in col or "Corte" in col or "Dev" in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                        else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")
                    
                    st.markdown("#### 📊 Matriz de Frequência")
                    st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=220, column_config=config_colunas)

        # =============================================================================
        # 👥 VISÃO GERAL EQUIPE
        # =============================================================================
        else:
            filtros_ativos = (turno_selecionado not in ["Todos", "Todos Permitidos"]) or (cargo_selecionado != "Todos")

            if not filtros_ativos:
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown("<h2 style='text-align: center; color: lightgray;'>👋 Bem-vindo ao Painel de Comando da Expedição</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; font-size: 18px; color: #888;'>O painel de produtividade está pronto. Utilize o menu lateral para direcionar sua análise.</p>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_AZUL}; height: 100%;'><h4>👥 Visão de Equipe</h4><p style='color: #ccc; font-size: 15px;'>Filtre por <b>Turno</b> ou <b>Função</b> para carregar os indicadores coletivos.</p></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_VERDE}; height: 100%;'><h4>🎯 Análise Individual</h4><p style='color: #ccc; font-size: 15px;'>Selecione um <b>Colaborador</b> para auditar seu desempenho real, prêmios e posição no Ranking.</p></div>", unsafe_allow_html=True)
                with c3: st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; border-radius: 10px; border-top: 5px solid {C_VERMELHO}; height: 100%;'><h4>🚨 Gestão de Detratores</h4><p style='color: #ccc; font-size: 15px;'>Ative o filtro de <b>Desempenho Abaixo da Meta</b> para identify gargalos.</p></div>", unsafe_allow_html=True)
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
                            col_rac = f"{kpi}_Racional"
                            modos = df_cargo[col_rac].dropna().mode() if col_rac in df_cargo.columns else pd.Series([])
                            racional_temp = modos.iloc[0] if not modos.empty else 1
                            df_kpi_valido = (df_cargo[df_cargo[kpi] > 0] if kpi in df_cargo.columns else df_cargo) if racional_temp == 1 else (df_cargo[df_cargo['Dias Trabalhados'] > 0] if 'Dias Trabalhados' in df_cargo.columns else df_cargo)
                            if df_kpi_valido.empty: continue

                            df_com_meta = df_kpi_valido[df_kpi_valido[f"{kpi}_Meta2"] > 0] if f"{kpi}_Meta2" in df_kpi_valido.columns else pd.DataFrame()
                            if df_com_meta.empty: continue 

                            meta2_med = df_com_meta[f"{kpi}_Meta2"].mean()
                            meta1_med = df_com_meta[f"{kpi}_Meta1"].mean() if f"{kpi}_Meta1" in df_com_meta.columns else meta2_med
                            meta3_med = df_com_meta[f"{kpi}_Meta3"].mean() if f"{kpi}_Meta3" in df_com_meta.columns else meta2_med
                            real_med = df_kpi_valido[kpi].mean() if kpi in df_kpi_valido.columns else 0
                            soma_total = df_kpi_valido[kpi].sum() if kpi in df_kpi_valido.columns else 0

                            cargo_atual_upper = str(cargo_atual).strip().upper()
                            kpi_upper = str(kpi).strip().upper()
                            is_meta_unica = ('DEVOLUÇÃO' in cargo_atual_upper and kpi_upper == 'DEV. %') or (kpi_upper == 'AVARIA')

                            if is_meta_unica:
                                alvo_atual_med = 0.48 if ('DEVOLUÇÃO' in cargo_atual_upper and kpi_upper == 'DEV. %') else 0.07
                                nome_alvo = "Meta Única"
                                cor, icone, status = (C_VERDE, "🟢", "Na Meta") if real_med <= alvo_atual_med else (C_VERMELHO, "🔴", "Abaixo")
                                real_perc = 100.0 if real_med <= alvo_atual_med else ((alvo_atual_med / real_med * 100) if real_med > 0 else 0)
                            else:
                                if racional_temp == 1: 
                                    alvo_atual_med, nome_alvo = (meta1_med, "Meta 1") if real_med < meta1_med else ((meta2_med, "Meta 2") if real_med < meta2_med else ((meta3_med, "Meta 3") if real_med < meta3_med else (meta3_med, "Meta Máx")))
                                    perc = (real_med / meta2_med) if meta2_med > 0 else 0
                                else: 
                                    alvo_atual_med, nome_alvo = (meta1_med, "Meta 1") if real_med > meta1_med else ((meta2_med, "Meta 2") if real_med > meta2_med else ((meta3_med, "Meta 3") if real_med > meta3_med else (meta3_med, "Meta Máx")))
                                    perc = (meta2_med / real_med) if real_med > 0 else 1.2

                                real_perc = perc * 100
                                cor, icone, status = (C_AZUL, "🔵", "Superando") if real_perc >= 120 else ((C_VERDE, "🟢", "Na Meta") if real_perc >= 100 else ((C_AMARELO, "🟡", "Parcial") if real_perc >= 50 else (C_VERMELHO, "🔴", "Abaixo")))
                            
                            if "Tempo" in str(kpi):
                                v_tela, t_tela = f"{int(real_med)//3600:02d}:{(int(real_med)%3600)//60:02d}:{(int(real_med)%60):02d}", f"{int(alvo_atual_med)//3600:02d}:{(int(alvo_atual_med)%3600)//60:02d}:{(int(alvo_atual_med)%60):02d}"
                            elif "LÍQ" in str(kpi).upper():
                                v_tela, t_tela = f"{real_med:.1f}%".replace('.', ','), f"{alvo_atual_med:.1f}%".replace('.', ',')
                            elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi):
                                v_tela, t_tela = f"{real_med:.2f}%".replace('.', ','), f"{alvo_atual_med:.2f}%".replace('.', ',')
                            else:
                                v_tela, t_tela = f"{real_med:,.0f}".replace(',', '.'), f"{alvo_atual_med:,.0f}".replace(',', '.')

                            eh_global = any(g in str(kpi).upper() for g in ['DEV', 'CORTE', 'AVARIA', 'ITENS RAMPA', 'CARGA PALET', 'CARGA BAT', 'PALETS PX', 'TEMPO MÉDIO', 'MÉD. PALET'])
                            titulo_card = f"{kpi}" if eh_global else f"Média: {kpi} <span style='color: #888; font-weight: normal; font-size: 16px;'>(Soma: {f'{soma_total:,.0f}'.replace(',', '.')})</span>"
                            alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {t_tela}</span>"
                            val_tot_equipe = df_kpi_valido[f"{kpi}_Valor"].sum() if f"{kpi}_Valor" in df_kpi_valido.columns else 0
                            html_dinheiro_med = ""
                            
                            turno_atual = str(df_cargo['TURNO'].iloc[0]).strip().upper()
                            is_itens_t2_sepg = (turno_atual == 'T2' and 'SEPARADOR G' in str(cargo_atual).upper() and 'ITENS SEP' in str(kpi).upper())
                            if not is_itens_t2_sepg and val_tot_equipe > 0:
                                val_tot_eq_str = f"{val_tot_equipe:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                html_dinheiro_med = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: #2ecc71; font-size: 16px;'>💰 Total Adquirido (Equipe): <b>R$ {val_tot_eq_str}</b></span></div>"

                            with cols_eq[col_idx % 4]:
                                st.markdown(f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{titulo_card}</div><div class='texto-card-principal'>{v_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{icone} {status}</div>{html_dinheiro_med}</div>", unsafe_allow_html=True)
                            col_idx += 1

            if filtros_ativos:
                if 'cargos_render' in locals() and len(cargos_render) > 0: st.divider()
                st.markdown("### 📋 Tabela de Produtividade Consolidada (Relatório Gerencial)")
                kpis_ativos_tabela = [kpi for kpi in kpis_mapeados if f"{kpi}_Meta2" in df_filtrado.columns and pd.to_numeric(df_filtrado[f"{kpi}_Meta2"], errors='coerce').fillna(0).sum() > 0]
                extras_ind = [c for c in df_filtrado.columns if 'ITENS SEPARADOS' in str(c).upper() and c not in kpis_ativos_tabela]
                extras_erros = [c for c in df_filtrado.columns if 'ERROS' in str(c).upper() and c not in kpis_ativos_tabela and c not in extras_ind]
                colunas_exibicao = ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Dias Corridos', 'Dias Trabalhados', 'Dias Meta', 'Valor Final'] + extras_ind + extras_erros + kpis_ativos_tabela
                df_tabela = df_filtrado[[c for c in colunas_exibicao if c in df_filtrado.columns]].copy()

                if 'Tempo Médio' in df_tabela.columns:
                    df_tabela['Tempo Médio'] = pd.to_numeric(df_tabela['Tempo Médio'], errors='coerce').fillna(0)
                    df_tabela['Tempo Médio'] = df_tabela['Tempo Médio'].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if s > 0 else "00:00:00")

                config = {'Valor Final': st.column_config.NumberColumn("Total R$", format="R$ %.2f")}
                for col in df_tabela.columns:
                    if col in ['CÓD.', 'NOME', 'TURNO', 'FUNÇÃO', 'Tempo Médio', 'Data Inicio', 'Data Fim', 'Valor Final']: continue 
                    elif "LÍQ" in col.upper(): config[col] = st.column_config.NumberColumn(col, format="%.1f%%")
                    elif "%" in col or "Avaria" in col or "Corte" in col or "Dev" in col: config[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                    else: config[col] = st.column_config.NumberColumn(col, format="%d")

                st.dataframe(df_tabela, hide_index=True, use_container_width=True, height=600, column_config=config)

    except Exception as e:
        st.error(f"⚠️ Erro ao renderizar painel: {e}")
