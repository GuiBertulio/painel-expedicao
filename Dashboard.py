import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import calendar
import re
from utils.data_loader import carregar_dados, carregar_diarios, conectar_planilha
from utils.helpers import mostrar_erro, carregar_css, injetar_css

# =============================================================================
# 🧰 FUNÇÕES DE APOIO E LIMPEZA DE DADOS
# =============================================================================
def extrair_inteiro(val):
    try:
        if pd.isna(val): return 0
    except ValueError:
        return 0
    
    v_str = str(val).strip()
    if v_str.lower() in ['nan', 'none', '', '-']: return 0
    
    v_str = re.sub(r'[^\d.,]', '', v_str)
    if not v_str: return 0
    
    if ',' in v_str:
        v_str = v_str.split(',')[0]
        
    v_str = v_str.replace('.', '')
    
    try: return int(v_str)
    except: return 0

# =============================================================================
# 💰 DICIONÁRIO OFICIAL DE VALORES DO RH (Base 100%)
# =============================================================================
def obter_valor_100(turno, funcao, kpi):
    t, f, k = str(turno).strip().upper(), str(funcao).strip().upper(), str(kpi).strip().upper()
    mapa = {
        ("T1", "CONFERENTE", "PALETS CONF."): 300, ("T1", "CONFERENTE", "TEMPO MÉDIO"): 100,
        ("T1", "DESCARGA", "CARGA PALET."): 125, ("T1", "DESCARGA", "TEMPO MÉDIO"): 125,
        ("T1", "DESCARGA", "CARGA BAT."): 125, ("T1", "DESCARGA", "CESTA"): 60,
        ("T1", "DEVOLUÇÃO", "DEV. %"): 150, ("T1", "LÍDER", "AVARIA"): 150,
        ("T1", "LÍDER", "MÉD. PALETS CONF."): 300, ("T1", "LÍDER", "TEMPO MÉDIO"): 300,
        ("T1", "OPERADOR", "MOV. VERT."): 350, ("T1", "OPERADOR", "TEMPO MÉDIO"): 100,
        ("T1", "PUXA", "PALETS PX."): 200, ("T1", "PUXA", "TEMPO MÉDIO"): 100,
        ("T2", "AVARIA", "AVARIA"): 150, ("T2", "CONFERENTE", "ITENS CONF."): 300,
        ("T2", "CONFERENTE", "DEV. %"): 150, ("T2", "DEVOLUÇÃO", "DEV. %"): 150,
        ("T2", "INVENTARIO", "CORTE %"): 200, ("T2", "LÍDER", "AVARIA"): 150,
        ("T2", "LÍDER", "RESSUP. EQ."): 240, ("T2", "LÍDER", "DEV. %"): 240,
        ("T2", "LÍDER", "ITENS/HORA EQ."): 240, ("T2", "MESA", "RESSUP. EQ."): 220,
        ("T2", "MESA", "DEV. %"): 220, ("T2", "MESA", "ITENS/HORA EQ."): 220,
        ("T2", "OPERADOR", "MOV. HORIZONTAL"): 450, ("T2", "OPERADOR", "AVARIA"): 100,
        ("T2", "CARREGAMENTO BOX", "ITENS RAMPA"): 150, ("T2", "CARREGAMENTO BOX", "DEV. %"): 150,
        ("T2", "CARREGAMENTO BOX", "AVARIA"): 100, ("T2", "SEPARADOR G", "RESSUP. AP."): 200,
        ("T2", "SEPARADOR G", "ITENS/HORA"): 200, ("T2", "SEPARADOR G", "ITENS SEP"): 0, 
        ("T3", "SEPARADOR F", "JORNADA LÍQ."): 150, ("T3", "SEPARADOR F", "ITENS SEP"): 150,
        ("T3", "SEPARADOR F", "ITENS/HORA"): 150, ("T3", "SEPARADOR G", "JORNADA LÍQ."): 150,
        ("T3", "SEPARADOR G", "ITENS SEP"): 150, ("T3", "SEPARADOR G", "ITENS/HORA"): 150,
        ("T3", "CONFERENTE", "ITENS CONF."): 350, ("T3", "CONFERENTE", "DEV. %"): 150,
        ("T3", "CONFERENTE GRANDEZA", "ITENS CONF."): 350, ("T3", "CONFERENTE GRANDEZA", "DEV. %"): 150,
        ("T3", "OPERADOR", "MOV. HORIZONTAL"): 450, ("T3", "OPERADOR", "AVARIA"): 100,
        ("T3", "CARREGAMENTO BOX", "ITENS RAMPA"): 150, ("T3", "CARREGAMENTO BOX", "DEV. %"): 150,
        ("T3", "CARREGAMENTO BOX", "AVARIA"): 100, ("T3", "MESA", "JORNADA LÍQ. EQ."): 220,
        ("T3", "MESA", "DEV. %"): 220, ("T3", "MESA", "CORTE %"): 220,
        ("T3", "MANOBRISTA", "ITENS MANOB."): 350, ("T3", "MANOBRISTA", "DEV. %"): 150,
        ("T3", "MANOBRISTA", "AVARIA"): 150, ("T3", "LÍDER", "JORNADA LÍQ. EQ."): 240,
        ("T3", "LÍDER", "AVARIA"): 150, ("T3", "LÍDER", "DEV. %"): 240,
        ("T3", "LÍDER", "ITENS/HORA EQ."): 240, ("T3", "RESPONSAVEL SALA BATERIAS", "ITENS/HORA"): 150,
        ("T3", "RESPONSAVEL SALA BATERIAS", "AVARIA"): 100, ("T3", "RESPONSAVEL SALA BATERIAS", "CHECKLIST MANUTENÇÃO"): 250,
    }
    return mapa.get((t, f, k), 0)

st.set_page_config(page_title="Grupo TAF - Painel Operacional", layout="wide")

if "logado" not in st.session_state or not st.session_state["logado"]:
    st.warning("Acesso negado. Por favor, faça o login na página inicial.")
    st.markdown("<meta http-equiv='refresh' content='2;url=/'>", unsafe_allow_html=True)
    st.stop()

perfil_usuario = st.session_state.get("perfil", "")
nome_usuario = st.session_state.get("nome", "").strip()
is_colaborador = perfil_usuario == "Colaborador"

injetar_css("dashboard.css")

# Cores Corporativas (Puxadas do secrets.toml da TI)
C_AZUL = st.secrets["ui_colors"].get("azul", "#143559")
C_VERDE = st.secrets["ui_colors"].get("verde", "#3db887")
C_AMARELO = st.secrets["ui_colors"].get("amarelo", "#ffbc42")
C_VERMELHO = st.secrets["ui_colors"].get("vermelho", "#f74343")

df = carregar_dados()

# =============================================================================
# 🛡️ MOTOR INTELIGENTE: CARREGAR DIÁRIOS COM DATA CARIMBADA
# =============================================================================
@st.cache_data(ttl=60)
def carregar_diarios_blindado():
    dfs = {"sep": pd.DataFrame(), "op": pd.DataFrame(), "conf": pd.DataFrame(), "aux": pd.DataFrame()}
    try:
        planilha = conectar_planilha()
        if not planilha:
            return dfs["sep"], dfs["op"], dfs["conf"], dfs["aux"]

        def processar_aba(nome_aba):
            aba_bruta = planilha.worksheet(nome_aba).get_all_values()
            if not aba_bruta: return pd.DataFrame()
            
            header_idx = 0
            for i, row_vals in enumerate(aba_bruta):
                if "NOME" in [str(cell).strip().upper() for cell in row_vals]:
                    header_idx = i
                    break
            
            headers = aba_bruta[header_idx]
            
            # Carimba as datas nas colunas puxando da linha mestre de cima
            if header_idx > 0:
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
                        if match:
                            current_date = match.group(0)
                        
                        if current_date and current_date not in headers[col_idx]:
                            headers[col_idx] = f"{current_date} - {headers[col_idx]}"

            df_aba = pd.DataFrame(aba_bruta[header_idx+1:], columns=headers)
            df_aba.columns = [str(c).strip() for c in df_aba.columns]
            return df_aba

        try: dfs["sep"] = processar_aba("Relatorio Diario")
        except: pass
        try: dfs["op"] = processar_aba("Relatorio Operador")
        except: pass
        try: dfs["conf"] = processar_aba("Relatorio Diario Conferente")
        except: pass
        try: dfs["aux"] = processar_aba("Aux JL")
        except: pass

    except Exception:
        pass
    return dfs["sep"], dfs["op"], dfs["conf"], dfs["aux"]

df_diario, df_operador, df_conferente, df_aux = carregar_diarios_blindado()

if (
    "Data Inicio" in df.columns
    and "Data Fim" in df.columns
    and not df["Data Inicio"].dropna().empty
):
    dt_inicio = pd.to_datetime(df["Data Inicio"].dropna().iloc[0]).date()
    data_apuracao = pd.to_datetime(df["Data Fim"].dropna().iloc[0]).date()
else:
    hoje = datetime.date.today()
    dt_inicio = datetime.date(hoje.year, hoje.month, 26)
    data_apuracao = hoje - datetime.timedelta(days=1)

with st.sidebar:
    st.image("assets/logoGrupoTAF.png", use_container_width=True)
    st.markdown("---")
    st.write(
        f"Logado como: {st.session_state.get('usuario', '').capitalize()} ({st.session_state.get('perfil', '')})"
    )

    if st.button("Sair do Sistema", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.switch_page("main.py")

    if "tema_escuro" not in st.session_state:
        st.session_state.tema_escuro = False

    if st.button(
        "Modo Escuro" if not st.session_state.tema_escuro else "Modo Claro",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.tema_escuro = not st.session_state.tema_escuro
        st.rerun()

    from utils.helpers import aplicar_tema
    aplicar_tema()
    st.markdown("---")

    if not is_colaborador:
        if perfil_usuario in ["Gerente", "Admin", "RH"]:
            st.divider()
            if st.button(
                "Gestao de Usuarios", type="primary", use_container_width=True
            ):
                st.switch_page("pages/02_Admin_Usuarios.py")

        st.title("Filtros do Painel")

        turno_logado = st.session_state.get("turno_acesso", "Todos")
        turnos_usuario = (
            [t.strip() for t in turno_logado.split(",")]
            if turno_logado and "," in turno_logado
            else turno_logado
        )
        if "TURNO" in df.columns:
            if isinstance(turnos_usuario, list):
                st.info(f"Acesso restrito aos Turnos: {', '.join(turnos_usuario)}")
                lista_turnos = ["Todos Permitidos"] + turnos_usuario
                turno_selecionado = st.selectbox("1. Turno:", lista_turnos)
                if turno_selecionado == "Todos Permitidos":
                    df_filtrado = df[df["TURNO"].isin(turnos_usuario)].copy()
                else:
                    df_filtrado = df[df["TURNO"] == turno_selecionado].copy()
            elif turno_logado == "Todos":
                lista_turnos = ["Todos"] + sorted(
                    df["TURNO"].dropna().unique().tolist()
                )
                turno_selecionado = st.selectbox("1. Turno:", lista_turnos)
                df_filtrado = (
                    df[df["TURNO"] == turno_selecionado].copy()
                    if turno_selecionado != "Todos"
                    else df.copy()
                )
            else:
                turno_selecionado = turno_logado
                st.info(f"Acesso restrito ao Turno: {turno_selecionado}")
                df_filtrado = df[df["TURNO"] == turno_selecionado].copy()
        else:
            df_filtrado = df.copy()
            turno_selecionado = "Todos"

        if "FUNÇÃO" in df_filtrado.columns:
            lista_cargos = ["Todos"] + sorted(
                df_filtrado["FUNÇÃO"].dropna().unique().tolist()
            )
            cargo_selecionado = st.selectbox("2. Cargo/Função:", lista_cargos)
            if cargo_selecionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado["FUNÇÃO"] == cargo_selecionado]

        if "NOME" in df_filtrado.columns:
            lista_pessoas = ["Nenhum"] + sorted(
                df_filtrado["NOME"].dropna().unique().tolist()
            )
            pessoa_selecionada = st.selectbox(
                "Ver Metas do Colaborador:", lista_pessoas
            )
        else:
            pessoa_selecionada = "Nenhum"

        focar_detratores = st.checkbox("Filtrar Desempenho Abaixo da Meta")

        if perfil_usuario in ["Gerente", "Admin", "RH"]:
            st.sidebar.divider()

            periodo_fechado = dt_inicio.day == 26 and data_apuracao.day == 25
            if periodo_fechado:
                from utils.auditoria import exportar_excel_auditoria

                buffer = exportar_excel_auditoria(df_filtrado)
                st.sidebar.download_button(
                    label="Baixar Auditoria",
                    data=buffer.getvalue(),
                    file_name=(
                        f"Auditoria_Produtividade_"
                        f"{dt_inicio.strftime('%d-%m')}"
                        f"a{data_apuracao.strftime('%d-%m')}.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                    type="primary",
                )
            else:
                st.button(
                    "Auditoria (Fechamento)",
                    disabled=True,
                    use_container_width=True,
                    type="primary",
                    help="Disponivel apenas no periodo de fechamento (dia 26 ao 25).",
                )

        if perfil_usuario in ["Gerente", "Admin", "RH"]:
            st.markdown("---")
            st.markdown("### Fechamento RH")
            if not df_filtrado.empty:
                df_rh = df_filtrado[
                    ["CÓD.", "NOME", "FUNÇÃO", "TURNO", "Valor Final"]
                ].copy()
                df_rh = df_rh.rename(
                    columns={
                        "CÓD.": "Matrícula",
                        "NOME": "Nome",
                        "Valor Final": "Premiação (R$)",
                    }
                )
                df_rh["Premiação (R$)"] = df_rh["Premiação (R$)"].round(2)
                df_rh = df_rh.drop_duplicates(subset=["Matrícula", "Nome"]).sort_values(
                    by="Nome"
                )

                config_rh = {
                    "Matrícula": st.column_config.TextColumn("Matrícula"),
                    "Premiação (R$)": st.column_config.NumberColumn(
                        "Premiação (R$)", format="R$ %.2f"
                    ),
                }
                st.dataframe(
                    df_rh,
                    hide_index=True,
                    use_container_width=True,
                    column_config=config_rh,
                )

                df_download = df_rh.copy()
                df_download["Premiação (R$)"] = df_download["Premiação (R$)"].apply(
                    lambda x: f"{x:.2f}".replace(".", ",")
                )
                csv_rh = df_download.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

                try:
                    ultimo_dia = calendar.monthrange(data_apuracao.year, data_apuracao.month)[1]
                    data_fim_mes = f"{ultimo_dia:02d}/{data_apuracao.month:02d}/{data_apuracao.year}"
                except:
                    data_fim_mes = dt_inicio.strftime('%d/%m/%Y')
                    
                df_rh_sistema = pd.DataFrame({
                    'CONTRATO': df_rh['Matrícula'],
                    'VDB': 2601,
                    'DESCRIÇÃO VDB': 'Adicional Produtividade',
                    'REFERENCIA FOLHA_1': 0,
                    'VALOR': df_rh['Premiação (R$)'],
                    'REFERENCIA FOLHA_2': 11,
                    'ULTIMO DIA DO MÊS_1': data_fim_mes,
                    'ULTIMO DIA DO MÊS_2': data_fim_mes
                })
                csv_sistema = df_rh_sistema.to_csv(index=False, header=False, sep=';').encode('utf-8-sig')

                st.markdown("<p style='font-size: 14px; margin-bottom: 5px;'>1. Visualização Padrão</p>", unsafe_allow_html=True)
                st.download_button(
                    label="📊 Baixar Planilha Visual (Excel)", data=csv_rh,
                    file_name=f"Fechamento_RH_Visual_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv",
                    mime="text/csv", use_container_width=True
                )
                st.markdown("<p style='font-size: 14px; margin-bottom: 5px; margin-top: 10px;'>2. Importação do Sistema (Layout Folha)</p>", unsafe_allow_html=True)
                st.download_button(
                    label="⚙️ Baixar Arq. do Sistema (.CSV)", data=csv_sistema,
                    file_name=f"Importacao_Sistema_Folha_{dt_inicio.strftime('%d-%m')}a{data_apuracao.strftime('%d-%m')}.csv",
                    mime="text/csv", type="primary", use_container_width=True
                )
    else:
        df_filtrado = df.copy()
        if nome_usuario and "NOME" in df.columns:
            dados_colab = df[df["NOME"] == nome_usuario]
            if not dados_colab.empty:
                pessoa_selecionada = nome_usuario
            else:
                pessoa_selecionada = "Nenhum"
        else:
            pessoa_selecionada = "Nenhum"
        focar_detratores = False
        cargo_selecionado = "Todos"

try:
    kpis_mapeados = [
        c.replace("_Racional", "") for c in df_filtrado.columns if "_Racional" in c
    ]

    col_titulo, col_kpis = st.columns([1, 1.2])
    with col_titulo:
        st.title("Monitor de Produtividade")
        st.info(
            f"Período Apurado: de {dt_inicio.strftime('%d/%m/%Y')} até {data_apuracao.strftime('%d/%m/%Y')}"
        )

    if not is_colaborador:
        with col_kpis:
            st.markdown("## Visão Geral")
            kpi1, kpi2, kpi3 = st.columns(3)
            col_vol = next(
                (
                    k
                    for k in kpis_mapeados
                    if "itens" in k.lower()
                    or "palet" in k.lower()
                    or "mov" in k.lower()
                ),
                kpis_mapeados[0] if kpis_mapeados else None,
            )
            total_vol = (
                df_filtrado[col_vol].sum()
                if col_vol and col_vol in df_filtrado.columns
                else 0
            )

            kpi1.metric(f"{col_vol or 'Volume'}", f"{total_vol:,.0f}".replace(",", "."))
            kpi2.metric("Colaboradores", len(df_filtrado))
            total_horas = (
                df_filtrado["Horas"].sum() if "Horas" in df_filtrado.columns else 0
            )
            kpi3.metric(
                "Horas Registradas", f"{total_horas:.1f} h" if total_horas > 0 else "—"
            )

        st.divider()

    if focar_detratores:
        st.markdown("## Plano de Atuação: Operadores Abaixo do Esperado")
        houve_detrator = False

        for idx, row in df_filtrado.iterrows():
            detalhes_gargalo = []
            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                if pd.isna(meta2) or str(meta2).strip() in ["0", "0.0", "-", ""]:
                    continue

                realizado = float(row.get(kpi, 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                meta1 = float(row.get(f"{kpi}_Meta1", meta2))

                if racional == 1 and realizado == 0:
                    continue

                abaixo_da_meta = False
                if racional == 1 and realizado < meta1:
                    abaixo_da_meta = True
                elif racional == 0 and realizado > meta1:
                    abaixo_da_meta = True

                if abaixo_da_meta:
                    if "%" in kpi or "Avaria" in kpi or "Corte" in kpi or "Dev" in kpi:
                        detalhes_gargalo.append(
                            f"{kpi}: {realizado:.2f}% vs Alvo Mínimo (Meta 1) {meta1:.2f}%"
                        )
                    else:
                        detalhes_gargalo.append(
                            f"{kpi}: {realizado:,.0f} vs Alvo Mínimo (Meta 1) {meta1:,.0f}".replace(
                                ",", "."
                            )
                        )

            if detalhes_gargalo:
                houve_detrator = True
                nome_c, cod_c, cargo_c, turno_c = (
                    row["NOME"],
                    row["CÓD."],
                    row["FUNÇÃO"],
                    row["TURNO"],
                )
                d_trab = int(row.get("Dias Trabalhados", 0))

                with st.container():
                    st.markdown(
                        f"<div style='background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 20px; border-radius: 12px; margin-bottom: 15px;'><span style='font-size: 22px; font-weight: bold; color: {C_VERMELHO};'>[{cod_c}] {nome_c}</span><br><b>Turno:</b> {turno_c} | <b>Função:</b> {cargo_c} | <b>Dias Lançados:</b> {d_trab} dias<br><br><span style='font-weight: bold; color: #ffca28;'>Pontos de Desvio Identificados:</span><br>{'<br>'.join(detalhes_gargalo)}</div>",
                        unsafe_allow_html=True,
                    )

                    col_feed, col_trein = st.columns(2)
                    with col_feed:
                        with st.expander(f"Registrar Feedback: {nome_c}"):
                            with st.form(key=f"form_feed_{idx}"):
                                texto_feedback = st.text_area(
                                    "Descreva o que foi conversado:"
                                )
                                if st.form_submit_button("Salvar no Histórico"):
                                    if texto_feedback:
                                        try:
                                            aba_rh = conectar_planilha().worksheet(
                                                "Historico_RH"
                                            )
                                            agora = (
                                                datetime.datetime.utcnow()
                                                - datetime.timedelta(hours=3)
                                            ).strftime("%d/%m/%Y %H:%M:%S")
                                            gestor = st.session_state.get(
                                                "usuario", ""
                                            ).capitalize()
                                            aba_rh.append_row(
                                                [
                                                    agora,
                                                    str(cod_c),
                                                    nome_c,
                                                    "Feedback",
                                                    texto_feedback,
                                                    gestor,
                                                ]
                                            )
                                            st.success("Salvo com sucesso")
                                        except Exception as e:
                                            st.error(f"Erro: {e}")
                                    else:
                                        st.warning("Preencha o campo de texto.")
                    with col_trein:
                        with st.expander(f"Solicitar Reciclagem: {nome_c}"):
                            with st.form(key=f"form_trein_{idx}"):
                                motivo = st.selectbox(
                                    "Gargalo:",
                                    [
                                        "Velocidade",
                                        "Erros/Avarias",
                                        "Sistema",
                                        "Processo",
                                    ],
                                )
                                if st.form_submit_button("Enviar Solicitação"):
                                    try:
                                        aba_rh = conectar_planilha().worksheet(
                                            "Historico_RH"
                                        )
                                        agora = (
                                            datetime.datetime.utcnow()
                                            - datetime.timedelta(hours=3)
                                        ).strftime("%d/%m/%Y %H:%M:%S")
                                        gestor = st.session_state.get(
                                            "usuario", ""
                                        ).capitalize()
                                        aba_rh.append_row(
                                            [
                                                agora,
                                                str(cod_c),
                                                nome_c,
                                                "Reciclagem",
                                                motivo,
                                                gestor,
                                            ]
                                        )
                                        st.success("Enviado com sucesso")
                                    except Exception as e:
                                        st.error(f"Erro: {e}")
                    st.markdown("<br>", unsafe_allow_html=True)

        if not houve_detrator:
            st.success("Nenhum detrator encontrado no período.")

    elif pessoa_selecionada != "Nenhum":
        st.subheader(f"Atingimento: {pessoa_selecionada}")
        dados_pessoa = df_filtrado[df_filtrado["NOME"] == pessoa_selecionada]

        if not dados_pessoa.empty:
            row = dados_pessoa.iloc[0]
            
            d_uteis_p = float(row.get('Dias Uteis', 26))
            d_trab_p = float(row.get('Dias Trabalhados', d_uteis_p))
            
            pos = int(row.get("Posicao Ranking", 0))
            cargo_p = row.get("FUNÇÃO", "")
            turno_p = row.get("TURNO", "Não Informado")
            
            # 🛡️ ALERTA DE ERROS
            erros_qtd = int(row.get('ERROS', 0))
            penalidade_txt = str(row.get('Penalidade_Texto', ''))
            
            if d_trab_p < d_uteis_p and d_uteis_p > 0:
                proporcao_tela = (d_trab_p / d_uteis_p) * 100
                st.markdown(f"<div style='background-color: rgba(255, 202, 40, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {C_AMARELO}; font-size: 16px; color: {C_AMARELO};'>ℹ️ <b>Atenção (Proporcionalidade):</b> Colaborador atuou <b>{int(d_trab_p)}</b> de <b>{int(d_uteis_p)}</b> dias úteis. Os prêmios foram calculados com proporção de <b>{proporcao_tela:.1f}%</b> do valor integral.</div>", unsafe_allow_html=True)
                
                ocorrencias_texto = []
                if not df_aux.empty and 'NOME' in df_aux.columns:
                    df_aux['NOME_CLEAN'] = df_aux['NOME'].astype(str).str.strip().str.upper()
                    dados_aux = df_aux[df_aux['NOME_CLEAN'] == str(pessoa_selecionada).strip().upper()]
                    if not dados_aux.empty:
                        linha_aux = dados_aux.iloc[0]
                        valores_aux = [str(v).strip().upper() for v in linha_aux.values]
                        
                        qtd_fe = valores_aux.count('FE')
                        qtd_fi = valores_aux.count('F.I')
                        qtd_ad = valores_aux.count('A.D')
                        qtd_at = valores_aux.count('AT')
                        
                        if qtd_fi > 0: ocorrencias_texto.append(f"❌ <b>{qtd_fi}</b> Falta(s) Injustificada(s) (F.I)")
                        if qtd_ad > 0: ocorrencias_texto.append(f"⚠️ <b>{qtd_ad}</b> dia(s) de Suspensão/Advertência (A.D)")
                        if qtd_at > 0:
                            alerta_atestado = " <span style='color:#ef4444; font-weight:bold;'>(Penalidade de -0.5 aplicada por passar de 3 dias)</span>" if qtd_at > 3 else ""
                            ocorrencias_texto.append(f"🏥 <b>{qtd_at}</b> dia(s) de Atestado (AT){alerta_atestado}")
                        if qtd_fe > 0: ocorrencias_texto.append(f"🌴 <b>{qtd_fe}</b> dia(s) de Férias (FE)")
                
                if ocorrencias_texto:
                    st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {C_VERMELHO}; font-size: 15px; color: #e0e0e0;'><b>📋 Detalhamento de Ocorrências no Mês:</b><br><div style='margin-top: 5px; line-height: 1.6;'>{'<br>'.join(ocorrencias_texto)}</div></div>", unsafe_allow_html=True)
            
            if erros_qtd > 0 and ('SEPARADOR' in cargo_p.upper() or 'OPERADOR' in cargo_p.upper()):
                st.markdown(f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid #ef4444; font-size: 16px; color: #ef4444;'>⚠️ <b>Penalidade de Qualidade:</b> Foram identificados <b>{erros_qtd} erro(s)</b>, resultando num desconto de <b>{penalidade_txt}</b> já aplicado nos seus totais pelo Excel.</div>", unsafe_allow_html=True)

            if "TURNO" in df_filtrado.columns and "FUNÇÃO" in df_filtrado.columns:
                total_eq = len(
                    df_filtrado[
                        (df_filtrado["TURNO"] == turno_p)
                        & (df_filtrado["FUNÇÃO"] == cargo_p)
                    ]
                )
            else:
                total_eq = 1

            val_rank = row.get("Valor Ranking", 0)

            if pos > 0 and ("SEPARADOR" in cargo_p.upper() or ("CONFERENTE" in cargo_p.upper() and turno_p == "T3") or ("OPERADOR" in cargo_p.upper() and turno_p == "T3")):
                cat_rank = str(row.get('Ranking_Categoria', '')).strip()
                texto_funcao_rank = cargo_p
                if cat_rank and 'CONFERENTE' in cargo_p.upper():
                    texto_funcao_rank = f"{cargo_p} <br><span style='font-size: 15px; color: #ffca28; font-weight: normal;'>📊 {cat_rank}</span>"

                if pos == 1:
                    medalha, cor_rank = "🥇", "#ffd700"
                elif pos == 2:
                    medalha, cor_rank = "🥈", "#c0c0c0"
                elif pos == 3:
                    medalha, cor_rank = "🥉", "#cd7f32"
                else:
                    medalha, cor_rank = f"🏅", "gray"

                if val_rank > 0:
                    val_rank_str = f"{val_rank:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    if d_trab_p > 0 and d_trab_p < d_uteis_p:
                        proj_rank = (val_rank / d_trab_p) * d_uteis_p
                        proj_rank_str = f"{proj_rank:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        txt_proj_rank = f" <span style='color: #888; font-size: 14px; font-weight: normal;'>(Mês Cheio: R$ {proj_rank_str})</span>"
                    else:
                        txt_proj_rank = ""
                    texto_premio_rank = f" | <span style='color: #2ecc71;'><b>Prêmio Ranking: R$ {val_rank_str}</b></span>{txt_proj_rank}"
                else:
                    texto_premio_rank = f" | <span style='color: #888;'><b>Premiação: R$ 0,00</b></span>"

                txt_posicao = f"<b>{medalha} Posição no Ranking:</b> {pos}º lugar de {total_eq}" if pos > 0 else f"<b>{medalha} Análise da Equipe</b> ({total_eq} pessoas)"
                st.markdown(
                    f"<div style='background-color: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; border-left: 6px solid {cor_rank}; font-size: 18px;'>{txt_posicao} na equipe de {texto_funcao_rank}{texto_premio_rank}</div>",
                    unsafe_allow_html=True,
                )

            cols_meta = st.columns(4)
            col_idx = 0
            grafico_dados = []

            for kpi in kpis_mapeados:
                meta2 = row.get(f"{kpi}_Meta2", 0)
                try: meta2_val = float(meta2)
                except: meta2_val = 0
                
                k_up = str(kpi).upper()
                c_up = str(cargo_p).upper()
                eh_producao = False
                if 'SEPARADOR' in c_up and 'ITENS' in k_up and 'RAMPA' not in k_up: eh_producao = True
                elif 'CONFERENTE' in c_up and ('FRAC' in k_up or 'GRAND' in k_up or 'ITENS CONF' in k_up or 'PALETS CONF' in k_up): eh_producao = True
                elif 'OPERADOR' in c_up and 'MOV' in k_up: eh_producao = True
                
                if meta2_val <= 0 and not eh_producao: continue

                realizado = float(row.get(kpi, 0))
                meta1, meta3 = float(row.get(f"{kpi}_Meta1", 0)), float(row.get(f"{kpi}_Meta3", 0))
                racional = float(row.get(f"{kpi}_Racional", 1))
                valor_reais = float(row.get(f"{kpi}_Valor", 0))

                if meta2_val <= 0 and eh_producao:
                    alvo_atual, nome_alvo = 0, "Livre"
                    cor, status = C_AZUL, "Volume Total"
                    real_perc = 100
                else:
                    if racional == 1:
                        perc_atingimento = (realizado / meta2_val) if meta2_val > 0 else 0
                        if realizado < meta1: alvo_atual, nome_alvo = meta1, "Meta 1"
                        elif realizado < meta2_val: alvo_atual, nome_alvo = meta2_val, "Meta 2"
                        elif realizado < meta3: alvo_atual, nome_alvo = meta3, "Meta 3"
                        else: alvo_atual, nome_alvo = meta3, "Meta Máx"

                        if realizado >= meta3: cor, status = C_AZUL, "Superou"
                        elif realizado >= meta2_val: cor, status = C_VERDE, "Atingiu"
                        elif realizado >= meta1: cor, status = C_AMARELO, "Parcial"
                        else: cor, status = C_VERMELHO, "Abaixo"
                    else:
                        perc_atingimento = (meta2_val / realizado) if realizado > 0 else 1.2
                        if realizado > meta1: alvo_atual, nome_alvo = meta1, "Meta 1"
                        elif realizado > meta2_val: alvo_atual, nome_alvo = meta2_val, "Meta 2"
                        elif realizado > meta3: alvo_atual, nome_alvo = meta3, "Meta 3"
                        else: alvo_atual, nome_alvo = meta3, "Meta Máx"

                        if realizado <= meta3: cor, status = C_AZUL, "Superou"
                        elif realizado <= meta2_val: cor, status = C_VERDE, "Atingiu"
                        elif realizado <= meta1: cor, status = C_AMARELO, "Parcial"
                        else: cor, status = C_VERMELHO, "Abaixo"

                    real_perc = perc_atingimento * 100
                    
                grafico_dados.append({"Indicador": f"<b>{kpi}</b>", "Atingimento (%)": min(real_perc, 120), "Real": real_perc})
                
                is_itens_t2_sepg = (turno_p == 'T2' and 'SEPARADOR G' in c_up and 'ITENS SEP' in k_up)
                html_dinheiro = ""
                
                if not is_itens_t2_sepg:
                    v_100_tabela = obter_valor_100(turno_p, cargo_p, kpi)
                    v_100 = v_100_tabela if v_100_tabela > 0 else 0

                    if v_100 > 0 or valor_reais > 0:
                        val_adq_str = f"{valor_reais:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        if v_100 > 0:
                            if status == "Abaixo":
                                est_str = f"{v_100 * 0.5:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                html_dinheiro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: {C_VERMELHO}; font-size: 15px;'>💰 Adquirido até hoje: <b>R$ {val_adq_str}</b></span><br><span style='color: #888; font-size: 14px;'>🎯 Alcance a Meta 1 para estimar <b>R$ {est_str}</b></span></div>"
                            elif status == "Parcial":
                                est_str = f"{v_100 * 0.5:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                px_str = f"{v_100:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                html_dinheiro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: {C_AMARELO}; font-size: 15px;'>💰 Adquirido até hoje: <b>R$ {val_adq_str}</b></span><br><span style='color: #2ecc71; font-size: 14px;'>🎯 Mês Cheio (50%): <b>R$ {est_str}</b></span> <span style='color: #888; font-size: 14px;'>| 🚀 Próxima (100%): <b>R$ {px_str}</b></span></div>"
                            elif status == "Atingiu" or status == "Volume Total":
                                est_str = f"{v_100:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                px_str = f"{v_100 * 1.2:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                html_dinheiro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: {C_VERDE}; font-size: 15px;'>💰 Adquirido até hoje: <b>R$ {val_adq_str}</b></span><br><span style='color: #2ecc71; font-size: 14px;'>🎯 Mês Cheio (100%): <b>R$ {est_str}</b></span> <span style='color: #888; font-size: 14px;'>| 🚀 Próxima (120%): <b>R$ {px_str}</b></span></div>"
                            elif status == "Superou":
                                est_str = f"{v_100 * 1.2:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                                html_dinheiro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: {C_AZUL}; font-size: 15px;'>💰 Adquirido até hoje: <b>R$ {val_adq_str}</b></span><br><span style='color: #3b82f6; font-size: 14px;'>🏆 Mês Cheio (120% Máx): <b>R$ {est_str}</b></span></div>"
                        else:
                            html_dinheiro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: {C_VERDE}; font-size: 15px;'>💰 Adquirido até hoje: <b>R$ {val_adq_str}</b></span></div>"

                if "Tempo" in str(kpi) or ":" in str(realizado):
                    val_tela = f"{int(realizado)//3600:02d}:{(int(realizado)%3600)//60:02d}:{int(realizado)%60:02d}"
                    alvo_tela = f"{int(alvo_atual)//3600:02d}:{(int(alvo_atual)%3600)//60:02d}:{int(alvo_atual)%60:02d}" if meta2_val > 0 else "-"
                elif "%" in str(kpi) or "Avaria" in str(kpi) or "Corte" in str(kpi) or "Dev" in str(kpi):
                    val_tela = f"{realizado:.2f}%"
                    alvo_tela = f"{alvo_atual:.2f}%" if meta2_val > 0 else "-"
                else:
                    val_tela = f"{realizado:,.0f}".replace(",", ".")
                    alvo_tela = f"{alvo_atual:,.0f}".replace(",", ".") if meta2_val > 0 else "-"

                alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {alvo_tela}</span>"
                
                aviso_erro = ""
                if erros_qtd > 0:
                    if 'SEPARADOR' in c_up and 'ITENS' in k_up and 'RAMPA' not in k_up:
                        aviso_erro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; font-size: 14px;'>⚠️ <b>{erros_qtd} Erro(s):</b> {penalidade_txt}</div>"
                    elif 'OPERADOR' in c_up and 'MOV' in k_up:
                        aviso_erro = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; font-size: 14px;'>⚠️ <b>{erros_qtd} Erro(s):</b> {penalidade_txt}</div>"

                with cols_meta[col_idx % 4]:
                    st.markdown(
                        f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{kpi}</div><div class='texto-card-principal'>{val_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{status}</div>{html_dinheiro}{aviso_erro}</div>",
                        unsafe_allow_html=True,
                    )
                col_idx += 1

            valor_final_total = row.get("Valor Final", 0)
            if valor_final_total > 0:
                val_tot_str = f"{valor_final_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                txt_proj_tot = ""
                if d_trab_p > 0 and d_trab_p < d_uteis_p:
                    proj_tot = (valor_final_total / d_trab_p) * d_uteis_p
                    proj_tot_str = f"{proj_tot:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    txt_proj_tot = f" | 📈 Estimado Final (Mês Cheio): R$ {proj_tot_str}"
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"💰 Premiação Variável Acumulada TOTAL Validada: R$ {val_tot_str}{txt_proj_tot}")

            st.divider()

            # --- AÇÕES DE GESTÃO (NO PERFIL INDIVIDUAL) ---
            st.markdown(f"### Ações de Gestão: {pessoa_selecionada}")
            col_feed_ind, col_trein_ind = st.columns(2)

            with col_feed_ind:
                with st.expander("Registrar Feedback"):
                    with st.form(key=f"form_feed_ind_{row.get('CÓD.', '')}"):
                        texto_feedback = st.text_area(
                            "Descreva o que foi conversado (Elogios, Alinhamentos, etc):"
                        )
                        if st.form_submit_button("Salvar no Histórico"):
                            if texto_feedback:
                                try:
                                    aba_rh = conectar_planilha().worksheet(
                                        "Historico_RH"
                                    )
                                    agora = (
                                        datetime.datetime.utcnow()
                                        - datetime.timedelta(hours=3)
                                    ).strftime("%d/%m/%Y %H:%M:%S")
                                    gestor = st.session_state.get(
                                        "usuario", ""
                                    ).capitalize()
                                    aba_rh.append_row(
                                        [
                                            agora,
                                            str(row.get("CÓD.", "")),
                                            pessoa_selecionada,
                                            "Feedback",
                                            texto_feedback,
                                            gestor,
                                        ]
                                    )
                                    st.success("Salvo com sucesso")
                                except Exception as e:
                                    st.error(f"Erro: {e}")
                            else:
                                st.warning("Preencha o campo de texto.")

            with col_trein_ind:
                with st.expander("Solicitar Reciclagem"):
                    with st.form(key=f"form_trein_ind_{row.get('CÓD.', '')}"):
                        motivo = st.selectbox(
                            "Motivo/Gargalo:",
                            [
                                "Velocidade",
                                "Erros/Avarias",
                                "Sistema",
                                "Processo",
                                "Comportamental",
                                "Outros",
                            ],
                        )
                        if st.form_submit_button("Enviar Solicitação"):
                            try:
                                aba_rh = conectar_planilha().worksheet("Historico_RH")
                                agora = (
                                    datetime.datetime.utcnow()
                                    - datetime.timedelta(hours=3)
                                ).strftime("%d/%m/%Y %H:%M:%S")
                                gestor = st.session_state.get(
                                    "usuario", ""
                                ).capitalize()
                                aba_rh.append_row(
                                    [
                                        agora,
                                        str(row.get("CÓD.", "")),
                                        pessoa_selecionada,
                                        "Reciclagem",
                                        motivo,
                                        gestor,
                                    ]
                                )
                                st.success("Enviado com sucesso")
                            except Exception as e:
                                st.error(f"Erro: {e}")

            st.divider()
            st.markdown(f"### Análise de {pessoa_selecionada}")

            col_grafico, col_tabela = st.columns([1.2, 1])
            with col_grafico:
                if grafico_dados:
                    df_grafico = pd.DataFrame(grafico_dados)
                    df_grafico["Cor"] = df_grafico["Real"].apply(
                        lambda x: (
                            C_AZUL
                            if x >= 120
                            else (
                                C_VERDE
                                if x >= 100
                                else (C_AMARELO if x >= 50 else C_VERMELHO)
                            )
                        )
                    )
                    df_grafico["Texto_Cor"] = df_grafico["Cor"].apply(
                        lambda color: "black" if color == C_AMARELO else "white"
                    )
                    fig = px.bar(
                        df_grafico,
                        x="Indicador",
                        y="Atingimento (%)",
                        text=df_grafico["Real"].apply(lambda x: f"<b>{x:.1f}%</b>"),
                    )
                    fig.update_layout(
                        showlegend=False,
                        yaxis_title="<b>% da Meta Atingida</b>",
                        xaxis_title=None,
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=350,
                        margin=dict(t=15, b=0, l=0, r=0),
                    )
                    fig.add_hline(
                        y=100,
                        line_dash="dash",
                        line_color="lightgray",
                        annotation_text="<b>Meta 100%</b>",
                        annotation_font_color="lightgray",
                    )
                    fig.update_traces(
                        textfont=dict(size=24, color=df_grafico["Texto_Cor"].tolist()),
                        marker=dict(
                            color=df_grafico["Cor"].tolist(),
                            line=dict(color="white", width=1),
                        ),
                    )
                    fig.update_xaxes(
                        tickfont=dict(size=20, color="lightgray", family="Arial Black")
                    )
                    fig.update_yaxes(
                        tickfont=dict(size=14, color="lightgray"),
                        title_font=dict(color="lightgray"),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum indicador com meta estabelecida para gerar o gráfico.")

            with col_tabela:
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

                if usa_diario and not df_uso_diario.empty:
                    df_uso_diario['NOME_CLEAN'] = df_uso_diario['NOME'].astype(str).str.strip().str.upper()
                    df_pessoa_diario = df_uso_diario[df_uso_diario['NOME_CLEAN'] == str(pessoa_selecionada).strip().upper()]
                    
                    if not df_pessoa_diario.empty:
                        cols_datas_reais = []
                        opcoes_datas_formatadas = []
                        datas_vistas = set()
                        
                        # Varrer as colunas buscando o carimbo de data
                        for c in df_uso_diario.columns:
                            c_str = str(c).strip()
                            if "INICIO" in c_str.upper() or "NOME" in c_str.upper() or "CÓD" in c_str.upper() or "TURNO" in c_str.upper() or "FUNÇÃO" in c_str.upper():
                                continue
                            
                            match = re.search(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', c_str)
                            if match:
                                d_str = match.group(0)
                                if d_str not in datas_vistas:
                                    datas_vistas.add(d_str)
                                    cols_datas_reais.append(c_str) 
                                    
                                    if '-' in d_str:
                                        ano, mes, dia = d_str.split('-')
                                        opcoes_datas_formatadas.append(f"{dia}/{mes}/{ano}")
                                    else:
                                        opcoes_datas_formatadas.append(d_str)
                        
                        if cols_datas_reais:
                            col_tit_diario, col_data_diario = st.columns([1.6, 1])
                            with col_tit_diario:
                                st.markdown("### Resultado Diário")
                            with col_data_diario:
                                data_escolhida_display = st.selectbox(
                                    "Data Apuração",
                                    opcoes_datas_formatadas,
                                    label_visibility="collapsed",
                                    key="sel_data_diario_alinhado",
                                )

                            idx_escolha = opcoes_datas_formatadas.index(data_escolhida_display)
                            nome_coluna_real = cols_datas_reais[idx_escolha]
                            col_index = list(df_uso_diario.columns).index(nome_coluna_real)

                            try: val_1 = str(pessoa_d_row.iloc[col_index]).strip()
                            except: val_1 = "0"
                            try: val_2 = str(pessoa_d_row.iloc[col_index + 1]).strip()
                            except: val_2 = "0"
                            try: val_3 = str(pessoa_d_row.iloc[col_index + 2]).strip()
                            except: val_3 = "0"
                            try: val_4 = str(pessoa_d_row.iloc[col_index + 3]).strip()
                            except: val_4 = "0"

                            val_1 = val_1 if val_1 and val_1.lower() not in ["nan", "none"] else "0"
                            val_2 = val_2 if val_2 and val_2.lower() not in ["nan", "none"] else "0"
                            val_3 = val_3 if val_3 and val_3.lower() not in ["nan", "none"] else "0"
                            val_4 = val_4 if val_4 and val_4.lower() not in ["nan", "none"] else "0"

                            if "SEPARADOR" in cargo_p:
                                try:
                                    if val_4 and val_4.lower() not in ["nan", "none"]:
                                        val_jl_num = float(val_4.replace(",", ".").replace("%", ""))
                                        if val_jl_num <= 2.0 and "%" not in val_4:
                                            val_jl_num = val_jl_num * 100
                                        jl_display = f"{int(val_jl_num)}%"
                                    else:
                                        jl_display = "0%"
                                except: jl_display = "0%"

                                try: v_itens = f"{float(val_1.replace(',', '.')):,.0f}".replace(",", ".")
                                except: v_itens = "0"

                                try: v_veloc = f"{int(round(float(val_3.replace(',', '.'))))}"
                                except: v_veloc = "0"

                                try:
                                    horas_dec = float(val_2.replace(",", "."))
                                    h = int(horas_dec)
                                    m = int((horas_dec - h) * 60)
                                    s = int((((horas_dec - h) * 60) - m) * 60)
                                    v_horas = f"{h:02d}:{m:02d}:{s:02d}"
                                except: v_horas = "00:00:00"

                                c1, c2, c3 = st.columns(3)
                                c1.metric("Horas", v_horas)
                                c2.metric("Itens/Hora", v_veloc)
                                c3.metric("Jornada Líquida", jl_display)

                                st.markdown(
                                    f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>Itens Separados</h4><h2 style='margin:0; color: {C_AZUL};'>{v_itens}</h2></div>",
                                    unsafe_allow_html=True,
                                )

                            elif "CONFERENTE" in cargo_p:
                                try: v_frac = f"{float(val_1.replace(',', '.')):,.0f}".replace(",", ".")
                                except: v_frac = "0"
                                try: v_grand = f"{float(val_2.replace(',', '.')):,.0f}".replace(",", ".")
                                except: v_grand = "0"

                                st.markdown("<p style='color: #888; font-size: 14px; margin-bottom: -10px;'>Métricas de Conferência</p>", unsafe_allow_html=True)
                                c1, c2 = st.columns(2)
                                with c1: st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Fracionado</h4><h2 style='margin:0; color: {C_AZUL};'>{v_frac}</h2></div>", unsafe_allow_html=True)
                                with c2: st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>📦 Grandeza</h4><h2 style='margin:0; color: {C_VERDE};'>{v_grand}</h2></div>", unsafe_allow_html=True)

                            elif "OPERADOR" in cargo_p:
                                try: v_horiz = f"{float(val_1.replace(',', '.')):,.0f}".replace(",", ".")
                                except: v_horiz = "0"
                                try: v_vert = f"{float(val_2.replace(',', '.')):,.0f}".replace(",", ".")
                                except: v_vert = "0"

                                st.markdown("<p style='color: #888; font-size: 14px; margin-bottom: -10px;'>Movimentações</p>", unsafe_allow_html=True)
                                c1, c2 = st.columns(2)
                                with c1: st.markdown(f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_AZUL}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↔️ Mov. Horizontal</h4><h2 style='margin:0; color: {C_AZUL};'>{v_horiz}</h2></div>", unsafe_allow_html=True)
                                with c2: st.markdown(f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid {C_VERDE}; margin-top: 15px; margin-bottom: 15px;'><h4 style='margin:0; color: #888;'>↕️ Mov. Vertical</h4><h2 style='margin:0; color: {C_VERDE};'>{v_vert}</h2></div>", unsafe_allow_html=True)

                kpis_ativos_pessoa = []
                for k in kpis_mapeados:
                    m2 = pd.to_numeric(row.get(f"{k}_Meta2", 0), errors="coerce")
                    if pd.notna(m2) and m2 > 0:
                        kpis_ativos_pessoa.append(k)

                extras_ind = [c for c in df_filtrado.columns if 'ITENS SEPARADOS' in str(c).upper() and c not in kpis_ativos_pessoa]
                extras_erros = [c for c in df_filtrado.columns if 'ERROS' in str(c).upper() and c not in kpis_ativos_pessoa and c not in extras_ind]
                col_uteis = ["CÓD.", "NOME", "FUNÇÃO", "Dias Trabalhados", "Dias Meta", "Dias Uteis", "Valor Final"] + extras_ind + extras_erros + kpis_ativos_pessoa
                df_tabela_mini = dados_pessoa[[c for c in col_uteis if c in df_filtrado.columns]].copy()

                if "Tempo Médio" in df_tabela_mini.columns:
                    df_tabela_mini["Tempo Médio"] = df_tabela_mini["Tempo Médio"].apply(lambda s: f"{int(s) // 3600:02d}:{(int(s) % 3600) // 60:02d}:{int(s) % 60:02d}" if pd.notna(s) else "00:00:00")

                config_colunas = {"Valor Final": st.column_config.NumberColumn("Total R$", format="R$ %.2f")}
                for col in df_tabela_mini.columns:
                    if col in ["CÓD.", "NOME", "FUNÇÃO", "Tempo Médio", "Data Inicio", "Data Fim", "Valor Final"]: continue
                    elif col in ["Avaria", "Corte %", "Dev. %"]: config_colunas[col] = st.column_config.NumberColumn(col, format="%.2f%%")
                    elif "Líq." in col: config_colunas[col] = st.column_config.NumberColumn(col, format="%d%%")
                    else: config_colunas[col] = st.column_config.NumberColumn(col, format="%d")

                st.markdown("#### Matriz")
                st.dataframe(df_tabela_mini, hide_index=True, use_container_width=True, height=350, column_config=config_colunas)

    else:
        filtros_ativos = (turno_selecionado not in ["Todos", "Todos Permitidos"]) or (
            cargo_selecionado != "Todos"
        )

        if not filtros_ativos and not is_colaborador:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown(
                "<h2 style='text-align: center; color: lightgray;'>Bem-vindo ao Painel de Produtividade</h2>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align: center; font-size: 18px; color: #888;'>"
                "Utilize os filtros na barra lateral para direcionar sua analise.</p>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            cor_azul = st.secrets["ui_colors"].get("azul", "#143559")
            cor_verde = st.secrets["ui_colors"].get("verde", "#3db887")
            cor_vermelho = st.secrets["ui_colors"].get("vermelho", "#f74343")

            with c1:
                st.markdown(
                    f"<div style='background-color: rgba(59, 130, 246, 0.1); padding: 20px; "
                    f"border-radius: 10px; border-top: 5px solid {cor_azul}; height: 100%;'>"
                    f"<h4>Visão de Equipe</h4>"
                    f"<p style='color: #ccc; font-size: 15px;'>"
                    f"Filtre por Turno ou Função para carregar os indicadores coletivos.</p></div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"<div style='background-color: rgba(46, 204, 113, 0.1); padding: 20px; "
                    f"border-radius: 10px; border-top: 5px solid {cor_verde}; height: 100%;'>"
                    f"<h4>Análise Individual</h4>"
                    f"<p style='color: #ccc; font-size: 15px;'>"
                    f"Selecione um Colaborador para auditar desempenho e prêmios.</p></div>",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"<div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; "
                    f"border-radius: 10px; border-top: 5px solid {cor_vermelho}; height: 100%;'>"
                    f"<h4>Gestão de Detratores</h4>"
                    f"<p style='color: #ccc; font-size: 15px;'>"
                    f"Ative o filtro de Desempenho Abaixo da Meta para identificar gargalos.</p></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("<br><br>", unsafe_allow_html=True)
        else:
            cargos_render = (
                [cargo_selecionado]
                if cargo_selecionado != "Todos"
                else sorted(df_filtrado["FUNÇÃO"].dropna().unique().tolist())
            )

            for cargo_atual in cargos_render:
                df_cargo = df_filtrado[df_filtrado["FUNÇÃO"] == cargo_atual]
                if df_cargo.empty:
                    continue

                st.markdown(
                    f"<h4 style='color: lightgray; margin-top: 15px;'>Equipe: {cargo_atual}</h4>",
                    unsafe_allow_html=True,
                )
                cols_eq = st.columns(4)
                col_idx = 0

                for kpi in kpis_mapeados:
                    if f"{kpi}_Meta2" in df_cargo.columns:
                        racional_temp = (
                            df_cargo[f"{kpi}_Racional"].mode()[0]
                            if not df_cargo[f"{kpi}_Racional"].empty
                            else 1
                        )
                        df_kpi_valido = (
                            df_cargo[df_cargo[kpi] > 0]
                            if racional_temp == 1
                            else df_cargo[df_cargo["Dias Trabalhados"] > 0]
                        )
                        if df_kpi_valido.empty:
                            continue

                        meta2_med = df_kpi_valido[f"{kpi}_Meta2"].mean()
                        if pd.isna(meta2_med) or meta2_med <= 0:
                            continue

                        meta1_med = (
                            df_kpi_valido[f"{kpi}_Meta1"].mean()
                            if f"{kpi}_Meta1" in df_kpi_valido.columns
                            else meta2_med
                        )
                        meta3_med = (
                            df_kpi_valido[f"{kpi}_Meta3"].mean()
                            if f"{kpi}_Meta3" in df_kpi_valido.columns
                            else meta2_med
                        )

                        real_med = df_kpi_valido[kpi].mean()
                        soma_total = df_kpi_valido[kpi].sum()

                        if racional_temp == 1:
                            if real_med < meta1_med:
                                alvo_atual_med, nome_alvo = meta1_med, "Meta 1"
                            elif real_med < meta2_med:
                                alvo_atual_med, nome_alvo = meta2_med, "Meta 2"
                            elif real_med < meta3_med:
                                alvo_atual_med, nome_alvo = meta3_med, "Meta 3"
                            else:
                                alvo_atual_med, nome_alvo = meta3_med, "Meta Máx"
                            perc = (real_med / meta2_med) if meta2_med > 0 else 0
                        else:
                            if real_med > meta1_med:
                                alvo_atual_med, nome_alvo = meta1_med, "Meta 1"
                            elif real_med > meta2_med:
                                alvo_atual_med, nome_alvo = meta2_med, "Meta 2"
                            elif real_med > meta3_med:
                                alvo_atual_med, nome_alvo = meta3_med, "Meta 3"
                            else:
                                alvo_atual_med, nome_alvo = meta3_med, "Meta Máx"
                            perc = (meta2_med / real_med) if real_med > 0 else 1.2

                        real_perc = perc * 100
                        if real_perc >= 120:
                            cor, status = C_AZUL, "Superando"
                        elif real_perc >= 100:
                            cor, status = C_VERDE, "Na Meta"
                        elif real_perc >= 50:
                            cor, status = C_AMARELO, "Parcial"
                        else:
                            cor, status = C_VERMELHO, "Abaixo"

                        metricas_globais = [
                            "DEV",
                            "CORTE",
                            "AVARIA",
                            "ITENS RAMPA",
                            "CARGA PALET",
                            "CARGA BAT",
                            "PALETS PX",
                            "TEMPO",
                            "MÉD. PALET",
                        ]
                        eh_global = any(g in str(kpi).upper() for g in metricas_globais)

                        if "Tempo" in str(kpi):
                            v_tela = f"{int(real_med)//3600:02d}:{(int(real_med)%3600)//60:02d}:{(int(real_med)%60):02d}"
                            t_tela = f"{int(alvo_atual_med)//3600:02d}:{(int(alvo_atual_med)%3600)//60:02d}:{(int(alvo_atual_med)%60):02d}"
                        elif (
                            "%" in str(kpi)
                            or "Avaria" in str(kpi)
                            or "Corte" in str(kpi)
                            or "Dev" in str(kpi)
                        ):
                            v_tela = f"{real_med:.2f}%"
                            t_tela = f"{alvo_atual_med:.2f}%"
                        else:
                            v_tela = f"{real_med:,.0f}".replace(",", ".")
                            t_tela = f"{alvo_atual_med:,.0f}".replace(",", ".")

                        if eh_global:
                            titulo_card = f"{kpi}"
                        else:
                            titulo_card = f"Média: {kpi} <span style='color: #888; font-weight: normal; font-size: 16px;'>(Soma: {soma_total:,.0f})</span>".replace(
                                ",", "."
                            )

                        alvo_formatado = f"<span style='font-size: 20px; color: #888; font-weight: normal;'> | Alvo ({nome_alvo}): {t_tela}</span>"
                        
                        val_tot_equipe = df_kpi_valido[f"{kpi}_Valor"].sum() if f"{kpi}_Valor" in df_kpi_valido.columns else 0
                        html_dinheiro_med = ""
                        turno_atual = str(df_cargo['TURNO'].iloc[0]).strip().upper()
                        is_itens_t2_sepg = (turno_atual == 'T2' and 'SEPARADOR G' in str(cargo_atual).upper() and 'ITENS SEP' in str(kpi).upper())
                        
                        if not is_itens_t2_sepg and val_tot_equipe > 0:
                            val_tot_eq_str = f"{val_tot_equipe:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            html_dinheiro_med = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);'><span style='color: #2ecc71; font-size: 16px;'>💰 Total Adquirido (Equipe): <b>R$ {val_tot_eq_str}</b></span></div>"

                        with cols_eq[col_idx % 4]:
                            st.markdown(
                                f"<div class='card-meta' style='border-left-color: {cor};'><div class='texto-card-titulo'>{titulo_card}</div><div class='texto-card-principal'>{v_tela}{alvo_formatado}</div><div style='font-size: 18px; color: {cor}; font-weight: bold; margin-top: 8px;'>{status}</div>{html_dinheiro_med}</div>",
                                unsafe_allow_html=True,
                            )
                        col_idx += 1

        if (turno_selecionado not in ["Todos", "Todos Permitidos"]) or (
            cargo_selecionado != "Todos"
        ):
            if len(cargos_render) > 0:
                st.divider()
            st.markdown("### Tabela de Produtividade Consolidada (Relatório Gerencial)")

            kpis_ativos_tabela = []
            for kpi in kpis_mapeados:
                if f"{kpi}_Meta2" in df_filtrado.columns:
                    metas_validas = pd.to_numeric(
                        df_filtrado[f"{kpi}_Meta2"], errors="coerce"
                    ).fillna(0)
                    if metas_validas.sum() > 0:
                        kpis_ativos_tabela.append(kpi)

            colunas_exibicao = [
                "CÓD.",
                "NOME",
                "TURNO",
                "FUNÇÃO",
                "Dias Trabalhados",
                "Dias Meta",
                "Dias Uteis",
                "Valor Ranking",
                "Valor Final",
            ] + kpis_ativos_tabela
            
            if 'ERROS' in df_filtrado.columns and 'ERROS' not in colunas_exibicao:
                colunas_exibicao.insert(7, 'ERROS')
                
            df_tabela = df_filtrado[
                [c for c in colunas_exibicao if c in df_filtrado.columns]
            ].copy()

            config = {
                "Valor Final": st.column_config.NumberColumn(
                    "Total R$", format="R$ %.2f"
                ),
                "Valor Ranking": st.column_config.NumberColumn(
                    "Rank R$", format="R$ %.2f"
                ),
            }
            st.dataframe(
                df_tabela,
                hide_index=True,
                use_container_width=True,
                height=600,
                column_config=config,
            )
        else:
            st.info(
                "Aplique um filtro na barra lateral (Turno ou Função) para visualizar a tabela detalhada da equipe."
            )

except Exception as e:
    st.error(f"Erro ao renderizar painel: {e}")
